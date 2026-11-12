"""Monta um vídeo longo estático da Vox Dei (1920x1080, 24 fps).

Fundo fixo (imagem do ChatGPT), brilho de vela piscando, partículas douradas leves,
bloco de texto à esquerda (título + oração + contador) e piano sereno de fundo.

Uso:
  python3 scripts/make_longo.py longos/<pasta>/roteiro-tts.json [--sem-voz] [--preview SEG]

Áudios da narração: longos/<pasta>/audio/NN.wav (ou .mp3), um por "audio" do roteiro.
Sem os áudios (ou com --sem-voz), cada fala dura o tempo estimado (palavras / 2,3 por segundo).
--preview SEG: monta só os primeiros SEG segmentos (teste rápido).
Saída: longos/<pasta>/saida/<pasta>.mp4
"""
import json, os, subprocess, sys, wave, zlib, textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H, FPS, SR = 1920, 1080, 24, 44100
WPS = 2.3            # palavras por segundo (estimativa sem voz)
INTRO, OUTRO = 3.0, 4.0
GOLD = (233, 196, 106); CREAM = (246, 236, 214)
PLOOP = 20.0         # loop das partículas (s)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.stderr.write(r.stderr[-3000:]); raise SystemExit("ffmpeg falhou")


# ---------------------------------------------------------------- imagens
def base_image(path, out):
    im = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    x = np.linspace(0, 1, W)[None, :, None]
    shade = np.clip(1 - 0.35 * np.clip((0.55 - x) / 0.55, 0, 1), 0, 1)   # escurece um pouco a área do texto
    Image.fromarray(np.clip(a * shade, 0, 255).astype(np.uint8)).save(out)


def glow_image(out, r=260):
    s = 2 * r; y, x = np.mgrid[-r:r, -r:r] / r
    d = np.sqrt(x ** 2 + (y * 1.15) ** 2)
    a = np.clip(1 - d, 0, 1) ** 2.2 * 150
    rgba = np.zeros((s, s, 4), np.uint8); rgba[..., 0] = 255; rgba[..., 1] = 176; rgba[..., 2] = 92
    rgba[..., 3] = a.astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(out)


def particles_video(out, seed=7, n=70):
    """Loop perfeito de 20 s com partículas douradas subindo devagar (RGBA, qtrle)."""
    if os.path.exists(out):
        return
    rng = np.random.default_rng(seed)
    px = rng.uniform(0, W, n); py = rng.uniform(0, H, n)
    k = rng.integers(1, 3, n)                         # voltas por loop -> velocidade H*k/20
    pr = rng.uniform(1.2, 3.2, n); ph = rng.uniform(0, 2 * np.pi, n); m = rng.integers(1, 3, n)
    fr = os.path.join(os.path.dirname(out), "_pfr"); os.makedirs(fr, exist_ok=True)
    N = int(PLOOP * FPS)
    for i in range(N):
        t = i / FPS; w = 2 * np.pi * t / PLOOP
        L = Image.new("L", (W, H), 0); d = ImageDraw.Draw(L)
        for j in range(n):
            cy = (py[j] - H * k[j] * t / PLOOP) % H
            cx = px[j] + 18 * np.sin(w * m[j] + ph[j])
            a = int(110 + 80 * np.sin(w * 3 * m[j] + ph[j]))
            d.ellipse([cx - pr[j], cy - pr[j], cx + pr[j], cy + pr[j]], fill=max(0, a))
        core = np.asarray(L.filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32)
        halo = np.asarray(L.filter(ImageFilter.GaussianBlur(7))).astype(np.float32) * 1.4
        al = np.clip(np.maximum(core, halo), 0, 255).astype(np.uint8)
        rgba = np.zeros((H, W, 4), np.uint8); rgba[..., 0] = 255; rgba[..., 1] = 214; rgba[..., 2] = 140; rgba[..., 3] = al
        Image.fromarray(rgba, "RGBA").save(os.path.join(fr, f"{i:04d}.png"), compress_level=1)
    run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(fr, "%04d.png"), "-c:v", "qtrle", out])
    for f in os.listdir(fr):
        os.remove(os.path.join(fr, f))
    os.rmdir(fr)


def wrap(d, text, f, maxw):
    out = []
    for par in text.split("\n"):
        if not par.strip():
            out.append(""); continue
        words = par.split(); cur = ""
        for w_ in words:
            t = (cur + " " + w_).strip()
            if d.textlength(t, font=f) <= maxw:
                cur = t
            else:
                out.append(cur); cur = w_
        out.append(cur)
    return out


def text_image(seg, out):
    """Bloco de texto à esquerda: título dourado, oração em creme, contador grande."""
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    X, MAXW = 120, 820
    f_tit = font("montserrat-800.ttf", 30)
    body = seg["tela"]
    size = 54 if len(body) < 140 else 46 if len(body) < 260 else 40 if len(body) < 380 else 35
    f_body = font("lora-medium.ttf", size)
    f_cnt = font("cinzel-bold.ttf", 96); f_cnt2 = font("montserrat-500.ttf", 28)
    lines = wrap(d, body, f_body, MAXW)
    lh = int(size * 1.42)
    hb = sum(lh if l else lh // 2 for l in lines)
    ht = 70 if seg["titulo"] else 0
    hc = 150 if seg["contador"] else 0
    y = (H - (ht + hb + hc)) // 2
    if seg["titulo"]:
        tit = " ".join(seg["titulo"])  # espaçamento entre letras
        d.text((X, y), seg["titulo"], font=f_tit, fill=GOLD + (255,))
        tw = d.textlength(seg["titulo"], font=f_tit)
        d.line([(X, y + 48), (X + min(tw, 360), y + 48)], fill=GOLD + (170,), width=2)
        y += ht
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
    yy = y
    for l in lines:
        if l:
            ds.text((X + 2, yy + 3), l, font=f_body, fill=(0, 0, 0, 230))
            d.text((X, yy), l, font=f_body, fill=CREAM + (255,)); yy += lh
        else:
            yy += lh // 2
    if seg["contador"]:
        a, b = seg["contador"].split("/")
        cy = yy + 30
        ds.text((X + 3, cy + 4), a, font=f_cnt, fill=(0, 0, 0, 230))
        d.text((X, cy), a, font=f_cnt, fill=GOLD + (255,))
        aw = d.textlength(a, font=f_cnt)
        d.text((X + aw + 18, cy + 52), f"de {b}", font=f_cnt2, fill=CREAM + (220,))
        # bolinhas do terço
        n = int(b); bx = X + aw + 120
        for i in range(n):
            cx = bx + i * 34; on = i < int(a)
            d.ellipse([cx - 9, cy + 58, cx + 9, cy + 76], fill=(GOLD + (255,)) if on else (0, 0, 0, 0),
                      outline=GOLD + (200,), width=2)
    sh = sh.filter(ImageFilter.GaussianBlur(4))
    Image.alpha_composite(sh, L).save(out)


# ---------------------------------------------------------------- áudio
def read_audio(path):
    """Lê wav/mp3 da narração como float32 mono 44,1 kHz."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       capture_output=True)
    a = np.frombuffer(r.stdout, np.float32).copy()
    # corta silêncio do começo e do fim
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz):
        a = a[max(0, nz[0] - int(0.05 * SR)): nz[-1] + int(0.15 * SR)]
    return a


def piano_bed(dur, seed):
    """Piano sereno e lento (tom maior, acordes longos, poucas notas)."""
    rng = np.random.default_rng(seed)
    N = int(dur * SR); out = np.zeros(N, np.float32)
    mid = lambda m_: 440 * 2 ** ((m_ - 69) / 12)
    I, IV, V, vi, ii = [0, 4, 7], [5, 9, 12], [7, 11, 14], [9, 12, 16], [2, 5, 9]
    progs = [[I, V, vi, IV], [I, IV, vi, V], [vi, IV, I, V], [I, ii, IV, I]]
    key = 60 + int(rng.choice([0, 2, 5, -5]))
    bar = 7.5

    def note(f, t0, d_, amp, bright=1.0):
        s_ = int(t0 * SR); n = min(int(d_ * SR), N - s_)
        if n <= 0:
            return
        tt = np.arange(n, dtype=np.float32) / SR
        env = np.exp(-tt * 0.7) * (1 - np.exp(-tt * 120))
        out[s_:s_ + n] += amp * env * sum(a_ * np.sin(2 * np.pi * f * k_ * tt) for k_, a_ in
                                          [(1, 1), (2, .4 * bright), (3, .12 * bright)])

    def pad(ch, t0, d_, amp):
        s_ = int(t0 * SR); n = min(int(d_ * SR), N - s_)
        if n <= 0:
            return
        tt = np.arange(n, dtype=np.float32) / SR
        env = np.minimum(tt / 2.0, 1) * np.minimum((d_ - tt) / 2.0, 1)
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
            pad(ch, t0, bar + 1.5, 0.018)
            beats = sorted(rng.choice(np.arange(0, 6), size=int(rng.integers(2, 4)), replace=False))
            for b in beats:
                m_ = ch[int(rng.integers(3))] + 12 * int(rng.integers(0, 2))
                note(mid(key + m_), t0 + b * bar / 6 + rng.uniform(0, .05), 5, 0.065, 1.1)
            t0 += bar
    dry = out.copy(); r = np.random.default_rng(seed + 7)
    for _ in range(12):
        k = int(r.uniform(0.03, 0.22) * SR); out[k:] += r.uniform(0.04, 0.10) * dry[:-k]
    del dry
    return out / (np.abs(out).max() + 1e-9) * 0.5


# ---------------------------------------------------------------- principal
def main():
    args = sys.argv[1:]
    spec_path = args[0]; sem_voz = "--sem-voz" in args
    nprev = int(args[args.index("--preview") + 1]) if "--preview" in args else None
    pasta = os.path.dirname(os.path.abspath(spec_path)); nome = os.path.basename(pasta)
    spec = json.load(open(spec_path, encoding="utf-8"))
    segs = spec["segmentos"][:nprev] if nprev else spec["segmentos"]
    tmp = os.path.join(pasta, "_tmp"); os.makedirs(tmp, exist_ok=True)
    outdir = os.path.join(pasta, "saida"); os.makedirs(outdir, exist_ok=True)
    seed = zlib.crc32(nome.encode())

    # 1) narração e tempos
    voz = {}
    if not sem_voz:
        for s in segs:
            for ext in ("wav", "mp3", "flac", "m4a"):
                p = os.path.join(pasta, "audio", f"{s['audio']}.{ext}")
                if os.path.exists(p) and s["audio"] not in voz:
                    voz[s["audio"]] = read_audio(p)
    t = INTRO; tl = []
    for s in segs:
        a = voz.get(s["audio"])
        fala = len(a) / SR if a is not None else len(s["fala"].split()) / WPS
        dur = fala + s.get("pausa", 1.0)
        tl.append((t, dur, fala)); t += dur
    total = t + OUTRO
    falt = sorted({s["audio"] for s in segs} - set(voz))
    print(f"duração: {total/60:.1f} min · áudios encontrados: {len(voz)} · faltando: {len(falt)}")

    # 2) trilha: narração + piano (abaixa sob a voz)
    N = int(total * SR); narr = np.zeros(N, np.float32)
    for s, (st, _, _) in zip(segs, tl):
        a = voz.get(s["audio"])
        if a is not None:
            i = int(st * SR); narr[i:i + len(a)] += a[:N - i]
    if voz:
        narr = narr / (np.abs(narr).max() + 1e-9) * 0.9
    pn = piano_bed(total, seed)[:N]
    env = np.ones(N, np.float32)
    if voz:
        lvl = np.convolve(np.abs(narr), np.ones(SR // 4) / (SR // 4), "same") > 0.01
        env = np.where(lvl, 0.35, 1.0).astype(np.float32)
        k = SR // 2; env = np.convolve(env, np.ones(k) / k, "same").astype(np.float32)
    mix = narr + pn * env * (0.55 if voz else 0.8)
    fi, fo = int(2 * SR), int(OUTRO * SR)
    mix[:fi] *= np.linspace(0, 1, fi); mix[-fo:] *= np.linspace(1, 0, fo)
    wav = os.path.join(tmp, "trilha.wav")
    with wave.open(wav, "wb") as w_:
        w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(SR)
        w_.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
    del narr, pn, env, mix

    # 3) camadas fixas
    base = os.path.join(tmp, "base.png"); base_image(os.path.join(pasta, spec["fundo"]), base)
    glow = os.path.join(tmp, "glow.png"); glow_image(glow)
    part = os.path.join(ROOT, "longos", "_cache", "particulas.mov"); os.makedirs(os.path.dirname(part), exist_ok=True)
    particles_video(part)
    gx, gy = spec.get("vela", [0.93, 0.75]); gx = int(gx * W) - 260; gy = int(gy * H) - 260

    # 4) partes: intro (só fundo), um trecho por segmento, final
    parts = []
    pieces = [(0, INTRO, None)] + [(st, d_, s) for s, (st, d_, _) in zip(segs, tl)] + [(total - OUTRO, OUTRO, None)]
    prev_txt = None
    for i, (st, d_, s) in enumerate(pieces):
        txt = None
        if s is not None and (s["tela"] or s["titulo"]):
            txt = os.path.join(tmp, f"txt_{i:03d}.png"); text_image(s, txt)
        key = (s["tela"], s["titulo"]) if s else None
        nxt = pieces[i + 1][2] if i + 1 < len(pieces) else None
        nkey = (nxt["tela"], nxt["titulo"]) if nxt else None
        fin = key != prev_txt; fout = key != nkey; prev_txt = key
        pout = os.path.join(tmp, f"p_{i:03d}.mp4"); parts.append(pout)
        inputs = ["-loop", "1", "-framerate", str(FPS), "-i", base,
                  "-stream_loop", "-1", "-ss", f"{st % PLOOP:.3f}", "-i", part,
                  "-loop", "1", "-framerate", str(FPS), "-i", glow]
        flick = (f"0.80+0.10*sin(2*PI*(T+{st:.3f})*1.3)+0.06*sin(2*PI*(T+{st:.3f})*3.7)"
                 f"+0.04*sin(2*PI*(T+{st:.3f})*7.9)")
        fg = (f"[2:v]format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*({flick})'[gl];"
              f"[0:v][gl]overlay={gx}:{gy}:format=auto[b1];"
              f"[1:v]format=rgba,colorchannelmixer=aa=0.75[pt];[b1][pt]overlay=0:0[b2]")
        last = "b2"
        if txt:
            inputs += ["-loop", "1", "-framerate", str(FPS), "-i", txt]
            tf = "[3:v]format=rgba"
            if fin:
                tf += ",fade=t=in:st=0:d=0.6:alpha=1"
            if fout:
                tf += f",fade=t=out:st={max(0, d_ - 0.6):.3f}:d=0.6:alpha=1"
            fg += f";{tf}[tx];[b2][tx]overlay=0:0[b3]"; last = "b3"
        if i == 0:
            fg += f";[{last}]fade=t=in:st=0:d=2[o]"; last = "o"
        if i == len(pieces) - 1:
            fg += f";[{last}]fade=t=out:st={d_ - 3:.3f}:d=3[o2]"; last = "o2"
        run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fg, "-map", f"[{last}]",
             "-t", f"{d_:.3f}", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", pout])
        print(f"  parte {i+1}/{len(pieces)}", end="\r", flush=True)
    lst = os.path.join(tmp, "lista.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    final = os.path.join(outdir, f"{nome}{'-preview' if nprev else ''}{'-sem-voz' if not voz else ''}.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
         "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
         "-movflags", "+faststart", final])
    for p in parts:
        os.remove(p)
    print(f"\nok: {final}")


if __name__ == "__main__":
    main()
