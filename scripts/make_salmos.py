"""Monta o longo "Salmos para dormir" da Vox Dei (1920x1080, 24 fps).

Cenas animadas (clipes do Sora/Gemini em loop sem emenda), bloco de texto do salmo (paginado, letra grande e
semi-negrito para público idoso), narração + piano lento + chuva sintética. Os salmos são rezados 3 vezes
(cada vez mais devagar) e os últimos minutos são só chuva e piano.

Uso:
  python3 scripts/make_salmos.py <pasta_do_video> [--work DIR] [--preview N_EVENTOS] [--fonte lora-medium.ttf]

<pasta_do_video> precisa ter: roteiro-*.txt, audio/NN.wav, cenas/cena1..4.mp4, words.json (tempos de palavra)
Saída: <work>/salmos.mp4 e <work>/timeline.json
"""
import glob, json, os, re, subprocess, sys, wave, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H, FPS, SR = 1920, 1080, 24, 44100
INTRO = 3.0
RING_P, RING_D = 8.5, 1.5          # período do loop sem emenda e duração do cross-fade
GOLD = (233, 196, 106); CREAM = (250, 240, 218)
BODY_FONT = "lora-medium.ttf"; BODY_STROKE = 1
TRANS = 2.5                         # troca de cena (cross-fade)
RAIN_FINAL = 11 * 60                # minutos finais só com chuva e piano

# unidades de leitura: (rótulo na tela, [blocos])
INTRO_B = [1, 2, 3]
UNITS = [("SALMO 4", [4, 5, 6]), ("SALMO 23", [7, 8, 9]), ("SALMO 91", [10, 11, 12, 13]),
         ("SALMO 121", [14, 15, 16]), ("SALMO 131", [17, 18]), ("SALMO 139", [19, 20, 21]),
         ("SALMO 27", [22, 23])]
PONTE, FINAL = [24], [25, 26]
# passada: (gap entre blocos, gap extra depois de cada unidade)
PASSES = [(3.0, 3.0), (12.0, 30.0), (18.0, 50.0)]
HOLD = 6.0                          # texto fica na tela até 6 s depois da fala
SCENE_SEQ = [1, 2, 3, 1]            # troca a cada ~10 min; a 4 é a chuva final
SCENE_EVERY = 600.0
SHADE = {1: 0.55, 2: 0.55, 3: 0.72, 4: 0.0}   # escurecimento do lado esquerdo (onde entra o texto)
MAXCH = 270                          # máx. de caracteres por página de texto


def run(cmd, quiet=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(" ".join(cmd[:6]) + "\n" + r.stderr[-2500:]); raise SystemExit("ffmpeg falhou")


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


# ---------------------------------------------------------------- roteiro e voz
def load_blocks(pasta):
    txt = open(glob.glob(os.path.join(pasta, "roteiro-*.txt"))[0], encoding="utf-8").read()
    parts = re.split(r"^\[(\d\d)\]\n", txt, flags=re.M)
    return {int(parts[i]): " ".join(l.strip() for l in parts[i + 1].strip().split("\n") if l.strip())
            for i in range(1, len(parts), 2)}


def read_audio(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True)
    a = np.frombuffer(r.stdout, np.float32).copy()
    nz = np.where(np.abs(a) > 0.01)[0]
    lead = 0
    if len(nz):
        lead = max(0, nz[0] - int(0.05 * SR))
        a = a[lead: nz[-1] + int(0.15 * SR)]
    return a, lead / SR


def split_pages(text):
    """Divide o texto em páginas de até MAXCH caracteres, sempre no fim de uma frase."""
    sents = re.findall(r"[^.!?]+[.!?]+(?:\s|$)|[^.!?]+$", text)
    pages, cur = [], ""
    for s in sents:
        s = s.strip()
        if cur and len(cur) + 1 + len(s) > MAXCH:
            pages.append(cur); cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        pages.append(cur)
    # evita página final minúscula
    if len(pages) > 1 and len(pages[-1]) < 70:
        pages[-2] += " " + pages[-1]; pages.pop()
    return pages


# ---------------------------------------------------------------- imagens
def text_image(page, title, out):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    X, MAXW = 110, 1010
    size = 68 if len(page) < 110 else 60 if len(page) < 200 else 54
    f_body = font(BODY_FONT, size); f_tit = font("montserrat-800.ttf", 34)
    lines = []
    cur = ""
    for w_ in page.split():
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f_body) <= MAXW:
            cur = t
        else:
            lines.append(cur); cur = w_
    lines.append(cur)
    lh = int(size * 1.46); ht = 86 if title else 0
    y = (H - (ht + lh * len(lines))) // 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    if title:
        ds.text((X + 2, y + 3), title, font=f_tit, fill=(0, 0, 0, 230))
        d.text((X, y), title, font=f_tit, fill=GOLD + (255,))
        tw = d.textlength(title, font=f_tit)
        d.line([(X, y + 56), (X + min(tw, 300), y + 56)], fill=GOLD + (170,), width=3)
        y += ht
    for l in lines:
        ds.text((X + 2, y + 3), l, font=f_body, fill=(0, 0, 0, 235), stroke_width=BODY_STROKE, stroke_fill=(0, 0, 0, 235))
        d.text((X, y), l, font=f_body, fill=CREAM + (255,), stroke_width=BODY_STROKE, stroke_fill=CREAM + (255,))
        y += lh
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    Image.alpha_composite(sh, L).save(out)


def shade_png(strength, out):
    x = np.linspace(0, 1, W)[None, :]
    a = (np.clip((0.70 - x) / 0.70, 0, 1) ** 0.8) * strength + 0.0
    a = np.repeat(a, H, axis=0)
    rgba = np.zeros((H, W, 4), np.uint8); rgba[..., 3] = (a * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(out)


def make_ring(src, scene, out, tmp):
    """Loop sem emenda de 8,5 s (cross-fade do fim para o começo) em 1920x1080 já com o escurecimento do texto."""
    sh = os.path.join(tmp, f"shade{scene}.png"); shade_png(SHADE[scene], sh)
    base = f"fps={FPS},scale={W}:{H}:flags=lanczos,setsar=1,format=yuv420p"
    ts, te = RING_P, RING_P + RING_D
    fg = (f"[0:v]{base},split=3[a][b][c];"
          f"[a]trim=start={ts}:end={te},setpts=PTS-STARTPTS[tail];"
          f"[b]trim=start=0:end={RING_D},setpts=PTS-STARTPTS[head];"
          f"[c]trim=start={RING_D}:end={ts},setpts=PTS-STARTPTS[mid];"
          f"[tail][head]xfade=transition=fade:duration={RING_D}:offset=0[x];"
          f"[x][mid]concat=n=2:v=1:a=0[r];"
          f"[r][1:v]overlay=0:0:format=auto,format=yuv420p[o]")
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-loop", "1", "-framerate", str(FPS), "-i", sh,
         "-filter_complex", fg, "-map", "[o]", "-t", f"{RING_P}", "-r", str(FPS), "-an", "-c:v", "libx264",
         "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", out])


# ---------------------------------------------------------------- áudio
def piano_bed(dur, seed):
    rng = np.random.default_rng(seed)
    N = int(dur * SR); out = np.zeros(N, np.float32)
    mid = lambda m_: 440 * 2 ** ((m_ - 69) / 12)
    I, IV, V, vi, ii = [0, 4, 7], [5, 9, 12], [7, 11, 14], [9, 12, 16], [2, 5, 9]
    progs = [[I, V, vi, IV], [I, IV, vi, V], [vi, IV, I, V], [I, ii, IV, I]]
    key = 57 + int(rng.choice([0, 2, 5, -5]))
    bar = 9.0

    def note(f, t0, d_, amp, bright=1.0):
        s_ = int(t0 * SR); n = min(int(d_ * SR), N - s_)
        if n <= 0:
            return
        tt = np.arange(n, dtype=np.float32) / SR
        env = np.exp(-tt * 0.6) * (1 - np.exp(-tt * 90))
        out[s_:s_ + n] += amp * env * sum(a_ * np.sin(2 * np.pi * f * k_ * tt) for k_, a_ in
                                          [(1, 1), (2, .35 * bright), (3, .1 * bright)])

    def pad(ch, t0, d_, amp):
        s_ = int(t0 * SR); n = min(int(d_ * SR), N - s_)
        if n <= 0:
            return
        tt = np.arange(n, dtype=np.float32) / SR
        env = np.minimum(tt / 2.5, 1) * np.minimum((d_ - tt) / 2.5, 1)
        for m_ in ch:
            f = mid(key + m_ - 12)
            out[s_:s_ + n] += amp * env * (np.sin(2 * np.pi * f * tt) + .25 * np.sin(2 * np.pi * f * 2.003 * tt))

    t0 = 0.3
    while t0 < dur:
        prog = progs[int(rng.integers(len(progs)))]
        for ch in prog:
            if t0 > dur:
                break
            note(mid(key + ch[0] - 12), t0, bar * 1.3, 0.12, 0.5)
            pad(ch, t0, bar + 1.5, 0.02)
            beats = sorted(rng.choice(np.arange(0, 6), size=int(rng.integers(1, 3)), replace=False))
            for b in beats:
                m_ = ch[int(rng.integers(3))] + 12 * int(rng.integers(0, 2))
                note(mid(key + m_), t0 + b * bar / 6 + rng.uniform(0, .05), 6, 0.06, 1.0)
            t0 += bar
    dry = out.copy(); r = np.random.default_rng(seed + 7)
    for _ in range(10):
        k = int(r.uniform(0.04, 0.25) * SR); out[k:] += r.uniform(0.04, 0.10) * dry[:-k]
    del dry
    return out / (np.abs(out).max() + 1e-9) * 0.5


def rain_bed(dur, out_wav):
    d = f"{dur:.2f}"
    fg = (f"anoisesrc=d={d}:c=pink:r={SR}:a=0.8:seed=11,highpass=f=700,lowpass=f=9500,tremolo=f=0.1:d=0.10[a];"
          f"anoisesrc=d={d}:c=pink:r={SR}:a=0.8:seed=23,highpass=f=1500,lowpass=f=6000,tremolo=f=0.13:d=0.18[b];"
          f"anoisesrc=d={d}:c=brown:r={SR}:a=0.9:seed=5,lowpass=f=350[c];"
          f"[a][b][c]amix=inputs=3:weights=1 0.6 0.9:normalize=0,aformat=sample_fmts=flt:channel_layouts=mono[o]")
    run(["ffmpeg", "-y", "-v", "error", "-filter_complex", fg, "-map", "[o]", "-ar", str(SR), out_wav])
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", out_wav, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True)
    a = np.frombuffer(r.stdout, np.float32).copy()
    return a / (np.sqrt(np.mean(a ** 2)) + 1e-9) * 0.10     # rms ~ -20 dBFS


# ---------------------------------------------------------------- principal
def main():
    global BODY_FONT
    args = sys.argv[1:]
    pasta = os.path.abspath(args[0])
    work = args[args.index("--work") + 1] if "--work" in args else os.path.join(pasta, "_work")
    nprev = int(args[args.index("--preview") + 1]) if "--preview" in args else None
    if "--fonte" in args:
        BODY_FONT = args[args.index("--fonte") + 1]
    os.makedirs(work, exist_ok=True)
    tmp = os.path.join(work, "tmp"); os.makedirs(tmp, exist_ok=True)

    blocks = load_blocks(pasta)
    words = json.load(open(os.path.join(pasta, "words.json"), encoding="utf-8"))
    aud, lead = {}, {}
    for n in blocks:
        aud[n], lead[n] = read_audio(os.path.join(pasta, "audio", f"{n:02d}.wav"))
    dur = {n: len(a) / SR for n, a in aud.items()}

    # ---- linha do tempo de blocos
    events, t = [], INTRO

    def add(n, label, gap, passe):
        nonlocal t
        events.append(dict(blk=n, t0=t, dur=dur[n], gap=gap, label=label, passe=passe)); t += dur[n] + gap

    for n in INTRO_B:
        add(n, None, PASSES[0][0], 1)
    for pi, (g, e) in enumerate(PASSES, 1):
        for lab, bl in UNITS:
            for k, n in enumerate(bl):
                add(n, lab, g + (e if k == len(bl) - 1 else 0), pi)
        if pi < 3:
            for n in PONTE:
                add(n, None, g + 3, pi)
    for k, n in enumerate(FINAL):
        add(n, None, 3.0 if k == 0 else 0.0, 4)
    t_rain = t
    total = t_rain + RAIN_FINAL
    if nprev:
        events = events[:nprev]; total = events[-1]["t0"] + events[-1]["dur"] + events[-1]["gap"] + 2
        t_rain = None
    print(f"duração total: {total/60:.1f} min · eventos {len(events)}")

    # ---- páginas de texto (início de cada página pelo tempo das palavras)
    for ev in events:
        n = ev["blk"]; pages = split_pages(blocks[n]); ws = words.get(f"{n:02d}.wav", [])
        tw = sum(len(p.split()) for p in pages); acc = 0; starts = []
        for i, p in enumerate(pages):
            if i == 0 or not ws:
                st = ev["t0"] if i == 0 else ev["t0"] + ev["dur"] * acc / tw
            else:
                j = min(len(ws) - 1, int(round(len(ws) * acc / tw)))
                st = ev["t0"] + max(0.0, ws[j][1] - lead[n]) - 0.35
            starts.append(st); acc += len(p.split())
        ev["pages"] = list(zip(pages, starts))

    # ---- peças de vídeo (cada uma = um quadro de texto ou nada) sobre a cena corrente
    F = lambda x: int(round(x * FPS))
    pieces = []     # dict(f0, f1, text(page,title)|None, trans(bool))
    for i, ev in enumerate(events):
        nxt = events[i + 1]["t0"] if i + 1 < len(events) else (t_rain if t_rain else ev["t0"] + ev["dur"] + ev["gap"])
        end_text = min(ev["t0"] + ev["dur"] + min(ev["gap"], HOLD), nxt)
        for k, (pg, st) in enumerate(ev["pages"]):
            en = ev["pages"][k + 1][1] if k + 1 < len(ev["pages"]) else end_text
            pieces.append(dict(t0=st, t1=en, page=pg, title=ev["label"], blk=ev["blk"]))
        if end_text < nxt - 0.05:
            pieces.append(dict(t0=end_text, t1=nxt, page=None, title=None, blk=None))
    if t_rain:
        pieces.append(dict(t0=t_rain, t1=total, page=None, title=None, blk=None))
    else:
        pieces.append(dict(t0=pieces[-1]["t1"], t1=total, page=None, title=None, blk=None))
    pieces = [p for p in pieces if p["t1"] - p["t0"] > 0.04]
    # primeira peça cobre a introdução
    pieces[0]["t0"] = 0.0
    for a, b in zip(pieces, pieces[1:]):      # emenda exata
        b["t0"] = a["t1"]

    # ---- trocas de cena (só em pausas sem texto com >= 4 s)
    sc_idx, next_change = 0, SCENE_EVERY
    for p in pieces:
        p["trans_to"] = None
        long_pause = p["page"] is None and p["t1"] - p["t0"] >= 4.0
        if t_rain and p["t0"] >= t_rain - 0.01:
            p["trans_to"] = 4
            sc_idx = 99
        elif long_pause and p["t0"] >= next_change and sc_idx < len(SCENE_SEQ) - 1:
            sc_idx += 1; p["trans_to"] = SCENE_SEQ[sc_idx]; next_change += SCENE_EVERY
    # propaga a cena depois de uma troca
    scene = 1
    for p in pieces:
        p["scene_from"] = scene
        if p["trans_to"]:
            scene = p["trans_to"]
        p["scene_to"] = scene

    json.dump(dict(total=total, t_rain=t_rain,
                   eventos=[dict(blk=e["blk"], t0=round(e["t0"], 2), dur=round(e["dur"], 2), label=e["label"], passe=e["passe"])
                            for e in events]), open(os.path.join(work, "timeline.json"), "w"), ensure_ascii=False, indent=1)

    # ---- anéis de cena
    rings = {}
    for sc in (1, 2, 3, 4):
        src = os.path.join(pasta, "cenas", f"cena{sc}.mp4")
        if not os.path.exists(src):
            continue
        out = os.path.join(work, f"ring{sc}.mp4"); rings[sc] = out
        if not os.path.exists(out):
            make_ring(src, sc, out, tmp)
    print("anéis prontos:", sorted(rings))

    # ---- trilha de áudio
    N = int(total * SR)
    narr = np.zeros(N, np.float32)
    for ev in events:
        a = aud[ev["blk"]]; i = int(ev["t0"] * SR); narr[i:i + len(a)] += a[:N - i]
    narr = narr / (np.abs(narr).max() + 1e-9) * 0.9
    pn = piano_bed(total + 1, 4242)[:N]
    pn = np.pad(pn, (0, N - len(pn)))
    lvl = np.convolve(np.abs(narr), np.ones(SR // 4) / (SR // 4), "same") > 0.01
    env = np.where(lvl, 0.30, 1.0).astype(np.float32)
    k = SR; env = np.convolve(env, np.ones(k) / k, "same").astype(np.float32)
    rain = rain_bed(total + 1, os.path.join(tmp, "rain.wav"))[:N]
    rain = np.pad(rain, (0, N - len(rain)))
    renv = np.ones(N, np.float32)
    if t_rain:
        a0 = int(t_rain * SR); ramp = int(20 * SR)
        renv[a0:a0 + ramp] = np.linspace(1, 1.35, ramp); renv[a0 + ramp:] = 1.35
    mix = narr + pn * env * 0.42 + rain * renv * 1.0
    fi, fo = int(3 * SR), int(10 * SR)
    mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
    wav = os.path.join(work, "trilha.wav")
    with wave.open(wav, "wb") as w_:
        w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
        w_.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    del narr, pn, env, rain, renv, mix

    # ---- render das peças
    parts, cache = [], {}
    nparts = len(pieces); frames_done = 0
    for i, p in enumerate(pieces):
        f0, f1 = F(p["t0"]), F(p["t1"])
        if i == nparts - 1:
            f1 = F(total)
        nfr = f1 - f0
        if nfr <= 0:
            continue
        d_ = nfr / FPS
        off = (f0 / FPS) % RING_P
        pout = os.path.join(tmp, f"p_{i:04d}.mp4"); parts.append(pout)
        inputs = ["-stream_loop", "-1", "-ss", f"{off:.3f}", "-i", rings[p["scene_from"]]]
        fg = []
        last = "0:v"
        if p["trans_to"]:
            inputs += ["-stream_loop", "-1", "-ss", f"{off:.3f}", "-i", rings[p["trans_to"]]]
            dt = min(TRANS, d_)
            fg.append(f"[0:v]trim=duration={dt:.3f},setpts=PTS-STARTPTS[xa];[1:v]setpts=PTS-STARTPTS[xb];"
                      f"[xa][xb]xfade=transition=fade:duration={dt:.3f}:offset=0,format=yuv420p[xo]")
            last = "xo"
        n_vid = 2 if p["trans_to"] else 1
        if p["page"]:
            key = (p["page"], p["title"])
            if key not in cache:
                cache[key] = os.path.join(tmp, f"txt_{len(cache):04d}.png"); text_image(p["page"], p["title"], cache[key])
            inputs += ["-loop", "1", "-framerate", str(FPS), "-i", cache[key]]
            fi_ = f"fade=t=in:st=0:d=0.5:alpha=1,"
            fo_ = f"fade=t=out:st={max(0, d_ - 0.5):.3f}:d=0.5:alpha=1"
            fg.append(f"[{n_vid}:v]format=rgba,{fi_}{fo_}[tx];[{last}][tx]overlay=0:0:format=auto[tv]")
            last = "tv"
        if i == 0:
            fg.append(f"[{last}]fade=t=in:st=0:d=3[fa]"); last = "fa"
        if i == nparts - 1:
            fg.append(f"[{last}]fade=t=out:st={max(0, d_ - 8):.3f}:d=8[fb]"); last = "fb"
        cmd = ["ffmpeg", "-y", "-v", "error", *inputs]
        if fg:
            cmd += ["-filter_complex", ";".join(fg), "-map", f"[{last}]"]
        else:
            cmd += ["-map", "0:v"]
        cmd += ["-frames:v", str(nfr), "-r", str(FPS), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-pix_fmt", "yuv420p", "-video_track_timescale", "24000", pout]
        run(cmd)
        frames_done += nfr
        print(f"  peça {i+1}/{nparts} ({frames_done/FPS/60:.1f} min)", end="\r", flush=True)
    lst = os.path.join(tmp, "lista.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    final = os.path.join(work, "salmos-preview.mp4" if nprev else "salmos.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-shortest",
         "-movflags", "+faststart", final])
    print(f"\nok: {final}")


if __name__ == "__main__":
    main()
