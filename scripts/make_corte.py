"""Gera um corte vertical (Short 1080x1920, 30 fps) de um longo da Vox Dei a partir dos blocos de narração.

Uso: python3 scripts/make_corte.py <pasta_do_video> <spec.json> [--work DIR] [--frame T]
  --frame T : só salva um quadro de teste no tempo T (s) em vez de renderizar o vídeo.

Spec (json): {"nome", "blocos": [11,12,13], "gap": 0.6, "cena": 2, "crop_x": 0.72, "layout": "A|B|C|D",
              "gancho": ["LINHA 1", "LINHA 2"], "destaque": "PALAVRA", "frase": "...", "ref": "SALMO 91", "seed": 1}
Layouts: A imagem cheia · B só o texto (linha ativa em destaque) · C tela dividida · D figura + frase de oração.
Depende de scripts/make_salmos.py (voz, piano, chuva, anéis de cena) e de work/ring<N>_clean.mp4.
"""
import difflib, importlib.util, json, os, re, subprocess, sys, unicodedata, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec_ = importlib.util.spec_from_file_location("ms", os.path.join(ROOT, "scripts", "make_salmos.py"))
ms = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(ms)

W, H, FPS, SR = 1080, 1920, 30, ms.SR
GOLD = (255, 214, 102); CREAM = (252, 244, 226)
F = lambda n, s: ImageFont.truetype(os.path.join(ms.FONTS, n), s)


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in w if unicodedata.category(c) != "Mn"))


def align(script_words, whisper):
    """Tempo (início,fim) de cada palavra do roteiro, a partir do Whisper (casamento por sequência)."""
    a = [norm(w) for w in script_words]; b = [norm(w[0]) for w in whisper]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    st = [None] * len(a); en = [None] * len(a)
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            st[i + k] = whisper[j + k][1]; en[i + k] = whisper[j + k][2]
    idx = [i for i, v in enumerate(st) if v is not None]
    if not idx:
        raise SystemExit("alinhamento falhou")
    for i in range(len(a)):
        if st[i] is None:
            lo = max([k for k in idx if k < i], default=None); hi = min([k for k in idx if k > i], default=None)
            if lo is None:
                st[i] = max(0.0, st[hi] - 0.3 * (hi - i)); en[i] = st[i] + 0.3
            elif hi is None:
                st[i] = en[lo] + 0.3 * (i - lo - 1) + 0.05; en[i] = st[i] + 0.3
            else:
                f = (i - lo) / (hi - lo); st[i] = en[lo] + (st[hi] - en[lo]) * (f - 0.5 / (hi - lo)); en[i] = st[i] + 0.3
    for i in range(len(a) - 1):
        en[i] = min(en[i], st[i + 1]) if st[i + 1] > st[i] else en[i]
    return list(zip(st, en))


def fit_font(draw, text, name, size, maxw, minsize=40):
    while size > minsize:
        f = F(name, size)
        if draw.textlength(text, font=f) <= maxw:
            return f
        size -= 4
    return F(name, minsize)


def outlined(d, xy, text, f, fill, stroke=7, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))


def chunks(words):
    """Agrupa as palavras em páginas de 2 a 4 palavras, quebrando em pontuação."""
    pages, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        end = re.search(r"[.!?:;,]$", w) is not None
        if len(cur) >= 4 or (end and len(cur) >= 2) or (len(cur) == 3 and len(" ".join(words[k] for k in cur)) > 22):
            pages.append(cur); cur = []
    if cur:
        if pages and len(cur) == 1:
            pages[-1] += cur
        else:
            pages.append(cur)
    return pages


def caption_image(words, page, hi, out, band_h=520, upper=False):
    img = Image.new("RGBA", (W, band_h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    words = [w.rstrip(".,;:") for w in words]
    txt = " ".join(words[i] for i in page).upper() if upper else " ".join(words[i] for i in page)
    f = fit_font(d, txt, "montserrat-800.ttf", 96, 960, 54)
    # duas linhas se muito largo
    toks = [words[i].upper() if upper else words[i] for i in page]
    lines = [toks]
    if d.textlength(" ".join(toks), font=f) > 960 and len(toks) > 2:
        lines = [toks[: len(toks) // 2], toks[len(toks) // 2:]]
    f = fit_font(d, max((" ".join(l) for l in lines), key=len), "montserrat-800.ttf", 96, 960, 54)
    lh = int(f.size * 1.25); y0 = band_h // 2 - lh * (len(lines) - 1) // 2
    k = 0
    for li, l in enumerate(lines):
        sp = d.textlength(" ", font=f); widths = [d.textlength(t, font=f) for t in l]
        total = sum(widths) + sp * (len(l) - 1); x = (W - total) / 2
        for t, wd in zip(l, widths):
            idx = page[k]; k += 1
            col = GOLD if idx == hi else CREAM
            d.text((x, y0 + li * lh), t, font=f, fill=col, anchor="lm", stroke_width=8, stroke_fill=(0, 0, 0, 255))
            x += wd + sp
    img.save(out)


def hook_image(lines, destaque, out):
    img = Image.new("RGBA", (W, 460), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = fit_font(d, max(lines, key=len), "montserrat-800.ttf", 92, 960, 56)
    lh = int(f.size * 1.22); y = 230 - lh * (len(lines) - 1) // 2
    for l in lines:
        toks = l.split(); sp = d.textlength(" ", font=f)
        total = sum(d.textlength(t, font=f) for t in toks) + sp * (len(toks) - 1); x = (W - total) / 2
        for t in toks:
            col = GOLD if norm(t) == norm(destaque or "") else CREAM
            d.text((x, y), t, font=f, fill=col, anchor="lm", stroke_width=8, stroke_fill=(0, 0, 0, 255))
            x += d.textlength(t, font=f) + sp
        y += lh
    img.save(out)


def cta_image(out):
    img = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = F("montserrat-800.ttf", 92); fc = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    t = "Escreva AMÉM"; w = d.textlength(t, font=f)
    d.text((W / 2 - 50, 150), t, font=f, fill=GOLD, anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0, 255))
    d.text((W / 2 + w / 2 + 10, 150), "✝", font=fc, fill=CREAM, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0, 255))
    img.save(out)


def phrase_image(text, out, h=520, left=False):
    img = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = F("lora-bold.ttf", 72 if left else 84); maxw = 440 if left else 900
    words = text.split(); lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur); lh = 92 if left else 112; y = h // 2 - lh * (len(lines) - 1) // 2
    for l in lines:
        if left:
            d.text((60, y), l, font=f, fill=GOLD, anchor="lm", stroke_width=7, stroke_fill=(0, 0, 0, 255))
        else:
            d.text((W / 2, y), l, font=f, fill=GOLD, anchor="mm", stroke_width=7, stroke_fill=(0, 0, 0, 255))
        y += lh
    img.save(out)


def wrap_lines(d, text, f, maxw=900):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            out.append(cur); cur = w
    out.append(cur)
    return out


def verses_image(lines, active, ref, out):
    """Layout B: página de versos no centro, a frase falada em dourado e as outras apagadas."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f = F("lora-bold.ttf", 62); lh = 84
    wrapped = []
    for i, l in enumerate(lines):
        for w_ in wrap_lines(d, l, f):
            wrapped.append((i, w_))
    total = len(wrapped) * lh + (len(lines) - 1) * 26
    y = 1060 - total // 2; prev = None
    if ref:
        d.text((W / 2, y - 80), ref, font=F("montserrat-800.ttf", 46), fill=GOLD + (255,), anchor="mm",
               stroke_width=5, stroke_fill=(0, 0, 0, 255))
    for i, l in wrapped:
        if prev is not None and i != prev:
            y += 26
        prev = i
        col = GOLD + (255,) if i == active else CREAM + (120,)
        d.text((W / 2, y), l, font=f, fill=col, anchor="mm", stroke_width=5 if i == active else 3,
               stroke_fill=(0, 0, 0, 255 if i == active else 150))
        y += lh
    img.save(out)


def ref_label(text, out):
    img = Image.new("RGBA", (W, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.text((W / 2, 60), text, font=F("montserrat-800.ttf", 46), fill=GOLD + (255,), anchor="mm")
    img.save(out)


def main():
    args = sys.argv[1:]
    pasta = os.path.abspath(args[0]); spec = json.load(open(args[1], encoding="utf-8"))
    work = args[args.index("--work") + 1] if "--work" in args else os.path.join(pasta, "_work")
    frame_t = float(args[args.index("--frame") + 1]) if "--frame" in args else None
    nome = spec["nome"]; tmp = os.path.join(work, "cut_" + nome); os.makedirs(tmp, exist_ok=True)
    blocks = ms.load_blocks(pasta); words_all = json.load(open(os.path.join(pasta, "words.json"), encoding="utf-8"))
    gap, tail, lead_in = spec.get("gap", 0.6), 1.6, 0.15

    # ---- narração + tempos de cada palavra
    aud, t, allw, times, lines_by_blk = [], lead_in, [], [], []
    for n in spec["blocos"]:
        a, lead = ms.read_audio(os.path.join(pasta, "audio", f"{n:02d}.wav"))
        sw = blocks[n].split(); al = align(sw, words_all[f"{n:02d}.wav"])
        for w_, (s, e) in zip(sw, al):
            allw.append(w_); times.append((t + max(0.0, s - lead), t + max(0.0, e - lead)))
        aud.append((t, a)); lines_by_blk.append((t, t + len(a) / SR, blocks[n]))
        t += len(a) / SR + gap
    voice_end = t - gap
    T = voice_end + tail
    print(f"{nome}: {T:.1f} s · {len(allw)} palavras")

    # ---- imagens
    hook = os.path.join(tmp, "hook.png"); hook_image(spec["gancho"], spec.get("destaque"), hook)
    cta = os.path.join(tmp, "cta.png"); cta_image(cta)
    layout = spec["layout"]
    pages = chunks(allw)
    cap_list = []   # (arquivo, duração)
    if layout != "B":
        k = 0; cur_t = 0.0
        for page in pages:
            for hi in page:
                st = times[hi][0]
                nxt_i = hi + 1
                en = times[nxt_i][0] if nxt_i < len(allw) and nxt_i in page else min(times[hi][1] + 0.18, T)
                if st > cur_t + 0.01:
                    cap_list.append((None, st - cur_t)); cur_t = st
                p = os.path.join(tmp, f"cap_{k:04d}.png"); k += 1
                caption_image(allw, page, hi, p, upper=False)
                cap_list.append((p, max(0.05, en - cur_t))); cur_t = en
        if T > cur_t:
            cap_list.append((None, T - cur_t))
    blank = os.path.join(tmp, "blank.png"); Image.new("RGBA", (W, 520), (0, 0, 0, 0)).save(blank)
    if layout != "B":
        lst = os.path.join(tmp, "caps.txt")
        with open(lst, "w") as f_:
            for p, d_ in cap_list:
                f_.write(f"file '{p or blank}'\nduration {d_:.4f}\n")
            f_.write(f"file '{blank}'\n")
    b_list = None
    if layout == "B":
        # linhas do salmo: uma por frase; ativa = a que está sendo dita
        sents = []
        for bi, (b0, b1, txt) in enumerate(lines_by_blk):
            pass
        sent_words = []   # (texto, t_ini, t_fim)
        i0 = 0
        for n_, (b0, b1, txt) in zip(spec["blocos"], lines_by_blk):
            sw = txt.split(); idxs = range(i0, i0 + len(sw)); cur = []
            for w_i in idxs:
                cur.append(w_i)
                if re.search(r"[.!?]$", allw[w_i]):
                    sent_words.append(cur); cur = []
            if cur:
                sent_words.append(cur)
            i0 += len(sw)
        sent = [(" ".join(allw[i] for i in s), times[s[0]][0], times[s[-1]][1]) for s in sent_words]
        probe = ImageDraw.Draw(Image.new("RGBA", (10, 10))); f62 = F("lora-bold.ttf", 62)
        pages_b, cur, nl = [], [], 0
        for si, (tx, s0, s1) in enumerate(sent):
            n_ = len(wrap_lines(probe, tx, f62))
            if cur and nl + n_ > 8:
                pages_b.append(cur); cur, nl = [], 0
            cur.append(si); nl += n_
        if cur:
            pages_b.append(cur)
        lst = os.path.join(tmp, "vers.txt"); seq = []
        for pi_, pg in enumerate(pages_b):
            lines = [sent[i][0] for i in pg]
            for k_, si in enumerate(pg):
                p = os.path.join(tmp, f"ver_{si:02d}.png"); verses_image(lines, k_, spec.get("ref", ""), p)
                s0 = sent[si][1] if si > 0 else 0.0
                s1 = sent[si + 1][1] if si + 1 < len(sent) else T
                seq.append((p, s1 - s0))
        with open(lst, "w") as f_:
            for p, d_ in seq:
                f_.write(f"file '{p}'\nduration {d_:.4f}\n")
            f_.write(f"file '{seq[-1][0]}'\n")
    phrase = None
    if layout == "D":
        phrase = os.path.join(tmp, "frase.png"); phrase_image(spec["frase"], phrase, left=spec.get("frase_pos") == "left")

    # ---- vídeo base
    ring = os.path.join(work, f"ring{spec['cena']}_clean.mp4")
    if not os.path.exists(ring):
        src = os.path.join(pasta, "cenas", f"cena{spec['cena']}.mp4")
        ms.make_ring(src, 4, ring, tmp)          # cena 4 = sem escurecimento
    cx = spec.get("crop_x", 0.5)
    zoom = "(1+0.04*t/%.2f)" % T
    if layout in ("A", "D"):
        base = (f"[0:v]crop=608:1080:x='min(max({cx}*1920-304,0),1312)':y=0,scale={W}:{H}:flags=lanczos,"
                f"scale=w='{W}*{zoom}':h=-2:eval=frame,crop={W}:{H},unsharp=5:5:0.6,format=yuv420p[bg]")
    elif layout == "C":
        base = (f"[0:v]crop=1215:1080:x='min(max({cx}*1920-607,0),705)':y=0,scale={W}:960:flags=lanczos,"
                f"scale=w='{W}*{zoom}':h=-2:eval=frame,crop={W}:960,unsharp=5:5:0.5,format=yuv420p[top];"
                f"color=c=0x0a0f1e:s={W}x960:r={FPS}[bot];[top][bot]vstack[bg0];"
                f"[bg0]drawbox=x=0:y=958:w={W}:h=4:color=0xe9c46a@0.9:t=fill[bg]")
    else:  # B: cena escurecida
        base = (f"[0:v]crop=608:1080:x='min(max({cx}*1920-304,0),1312)':y=0,scale={W}:{H}:flags=lanczos,"
                f"scale=w='{W}*{zoom}':h=-2:eval=frame,crop={W}:{H},eq=brightness=-0.12:saturation=0.95,format=yuv420p[bg]")
    inputs = ["-stream_loop", "-1", "-i", ring]
    n_in = 1
    fg = [base]
    last = "bg"
    if layout == "B":
        inputs += ["-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "vers.txt")]
        fg.append(f"[{n_in}:v]fps={FPS},format=rgba[vs];[{last}][vs]overlay=0:0:format=auto[v1]"); last = "v1"; n_in += 1
    else:
        inputs += ["-f", "concat", "-safe", "0", "-i", os.path.join(tmp, "caps.txt")]
        capy = 1180 if layout in ("A", "D") else 1190
        fg.append(f"[{n_in}:v]fps={FPS},format=rgba[cp];[{last}][cp]overlay=0:{capy}:format=auto[v1]"); last = "v1"; n_in += 1
    if layout == "C" and spec.get("ref"):
        rl = os.path.join(tmp, "ref.png"); ref_label(spec["ref"], rl)
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", rl]
        fg.append(f"[{n_in}:v]format=rgba[rf];[{last}][rf]overlay=0:1000:format=auto[vr]"); last = "vr"; n_in += 1
    inputs += ["-loop", "1", "-framerate", str(FPS), "-i", hook]
    fg.append(f"[{n_in}:v]format=rgba[hk];[{last}][hk]overlay=0:150:format=auto[v2]"); last = "v2"; n_in += 1
    if phrase:
        inputs += ["-loop", "1", "-framerate", str(FPS), "-i", phrase]
        fg.append(f"[{n_in}:v]format=rgba,fade=t=in:st=0.2:d=0.5:alpha=1,fade=t=out:st=8.5:d=0.6:alpha=1[ph];"
                  f"[{last}][ph]overlay=0:{spec.get('frase_y', 520)}:format=auto[v3]"); last = "v3"; n_in += 1
    inputs += ["-loop", "1", "-framerate", str(FPS), "-i", cta]
    fg.append(f"[{n_in}:v]format=rgba,fade=t=in:st={T-3:.2f}:d=0.4:alpha=1[ct];[{last}][ct]overlay=0:1500:format=auto:enable='gte(t,{T-3:.2f})'[v4]")
    last = "v4"
    fg.append(f"[{last}]fade=t=out:st={T-0.3:.2f}:d=0.3[vout]")

    # ---- áudio
    wav = os.path.join(tmp, "audio.wav")
    if frame_t is None:
        N = int(T * SR); narr = np.zeros(N, np.float32)
        for st, a in aud:
            i = int(st * SR); narr[i:i + len(a)] += a[:N - i]
        narr = narr / (np.abs(narr).max() + 1e-9) * 0.9
        pn = ms.piano_bed(T + 1, 100 + spec.get("seed", 1))[:N]; pn = np.pad(pn, (0, N - len(pn)))
        rain = ms.rain_bed(T + 1, os.path.join(tmp, "rain.wav"))[:N]; rain = np.pad(rain, (0, N - len(rain)))
        lvl = np.convolve(np.abs(narr), np.ones(SR // 4) / (SR // 4), "same") > 0.01
        env = np.convolve(np.where(lvl, 0.30, 1.0).astype(np.float32), np.ones(SR // 2) / (SR // 2), "same").astype(np.float32)
        mix = narr + pn * env * 0.40 + rain * 0.55
        fi, fo = int(0.3 * SR), int(0.3 * SR); mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
        with wave.open(wav, "wb") as w_:
            w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
            w_.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

    outdir = os.path.join(work, "cortes"); os.makedirs(outdir, exist_ok=True)
    if frame_t is not None:
        out = os.path.join(outdir, f"{nome}_frame_{frame_t:.0f}.jpg")
        ms.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(fg), "-map", "[vout]",
                "-ss", f"{frame_t}", "-frames:v", "1", out])
        print("frame:", out); return
    out = os.path.join(outdir, f"{nome}.mp4")
    ms.run(["ffmpeg", "-y", "-v", "error", *inputs, "-i", wav, "-filter_complex", ";".join(fg) +
            f";[{n_in + 1}:a]loudnorm=I=-14:TP=-1.5:LRA=7,aformat=sample_rates=44100:channel_layouts=stereo[aout]",
            "-map", "[vout]", "-map", "[aout]", "-t", f"{T:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
            "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out])
    ms.run(["ffmpeg", "-y", "-v", "error", "-i", out, "-frames:v", "1", "-q:v", "3", os.path.join(outdir, f"{nome}.jpg")])
    print("ok:", out)


if __name__ == "__main__":
    main()
