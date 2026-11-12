"""Short de ORAÇÃO NA ÍNTEGRA (Vox Dei, 12/11/2026): voz calma rezando + texto que acende palavra por palavra.

Formato novo para quebrar o molde "Bíblia" (queda de alcance em 09/11): fundo escuro com luz de vela,
gancho "Pare um instante" já visível no 1º quadro, oração inteira em blocos, CTA "escreva Amém".

Uso: python3 scripts/make_oracao.py specs/<spec>.json
Spec: nome, saida, voz (edge-tts, ex. pt-BR-AntonioNeural), rate ("-12%"), titulo_topo,
      blocos: [{"tipo": "gancho"|"oracao"|"cta", "texto": "..."}]
A voz é gerada com edge-tts (pip install edge-tts) e guardada em <saida>/voz/<nome>.mp3 (+ .json com os tempos).
"""
import asyncio, json, os, subprocess, sys, tempfile, wave, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_short

W, H, FPS = 1080, 1920, 30
GOLD = (236, 196, 110); CREAM = (248, 240, 222)
FONTS = os.path.join(ROOT, "fonts")


def font(n, s):
    return ImageFont.truetype(os.path.join(FONTS, n), s)


def tts(text, voice, rate, mp3):
    js = mp3 + ".json"
    if os.path.exists(mp3) and os.path.exists(js):
        return json.load(open(js))
    import certifi
    if os.path.exists("/root/.ccr/ca-bundle.crt"):
        certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
    import edge_tts

    async def go():
        c = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary", proxy=os.environ.get("HTTPS_PROXY"))
        out = []
        with open(mp3, "wb") as f:
            async for ch in c.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    out.append([ch["offset"] / 1e7, ch["duration"] / 1e7, ch["text"]])
        return out
    words = asyncio.run(go())
    json.dump(words, open(js, "w"), ensure_ascii=False)
    return words


def background(seed):
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([10, 11, 20]); bot = np.array([26, 16, 18])
    bg = top * (1 - y) + bot * y + np.zeros((1, W, 1))
    xx, yy = np.meshgrid(np.linspace(-1, 1, W), np.linspace(-1, 1, H))
    vig = np.clip(1 - 0.45 * (xx ** 2 + (yy * 0.8) ** 2), 0.35, 1)[..., None]
    noise = np.random.default_rng(seed).normal(0, 2.2, (H, W, 1))
    return bg * vig + noise


def glow_mask():
    xx, yy = np.meshgrid(np.linspace(-1, 1, W), np.linspace(-1, 1, H))
    d = np.sqrt((xx / 0.95) ** 2 + ((yy - 0.02) / 0.62) ** 2)
    return (np.clip(1 - d, 0, 1) ** 1.8)[..., None]


def wrap(draw, words, f, maxw):
    lines, cur = [], []
    for k, w in enumerate(words):
        test = " ".join(x for _, x in cur + [(k, w)])
        if cur and draw.textlength(test, font=f) > maxw:
            lines.append(cur); cur = []
        cur.append((k, w))
    if cur:
        lines.append(cur)
    return lines


def main(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    name = spec["nome"]; seed = zlib.crc32(name.encode())
    outdir = os.path.join(ROOT, spec["saida"]); os.makedirs(os.path.join(outdir, "voz"), exist_ok=True)
    blocos = spec["blocos"]
    text = "\n".join(b["texto"] for b in blocos)
    mp3 = os.path.join(outdir, "voz", name + ".mp3")
    times = tts(text, spec.get("voz", "pt-BR-AntonioNeural"), spec.get("rate", "-12%"), mp3)
    # liga cada palavra exibida ao tempo da voz (mesma ordem)
    k = 0; B = []
    for b in blocos:
        ws = b["texto"].split()
        tw = []
        for w in ws:
            tw.append(times[k][0]); k += 1
        B.append({**b, "words": ws, "t": tw})
    assert k == len(times), f"palavras {k} != tempos {len(times)}"
    voice_end = times[-1][0] + times[-1][1]
    DUR = voice_end + 3.0
    for i, b in enumerate(B):
        b["start"] = 0 if i == 0 else b["t"][0] - 0.25
    for i, b in enumerate(B):
        b["end"] = B[i + 1]["start"] if i + 1 < len(B) else DUR + 1

    # layout de cada bloco
    tmpd = ImageDraw.Draw(Image.new("L", (1, 1)))
    f_or = font("lora-bold.ttf", 82); f_hook = font("cinzel-bold.ttf", 104); f_hsub = font("lora-medium.ttf", 64)
    f_cta = font("lora-bold.ttf", 76); f_amem = font("cinzel-bold.ttf", 150)
    for b in B:
        if b["tipo"] == "gancho":
            # 1ª frase curta em destaque (dourado, caixa alta), resto menor
            n1 = next(i for i, w in enumerate(b["words"]) if w.endswith(".")) + 1
            b["n1"] = n1
            L1 = wrap(tmpd, [w.upper() for w in b["words"][:n1]], f_hook, 900)
            L2 = wrap(tmpd, b["words"][n1:], f_hsub, 900)
            b["lines"] = [(l, f_hook, 128) for l in L1] + [(None, None, 50)] + [([(i + n1, w) for i, w in l], f_hsub, 88) for l in L2]
        elif b["tipo"] == "cta":
            b["lines"] = [(l, f_cta, 104) for l in wrap(tmpd, b["words"], f_cta, 900)] + [(None, None, 40), ("AMEM", f_amem, 170)]
        else:
            b["lines"] = [(l, f_or, 112) for l in wrap(tmpd, b["words"], f_or, 920)]
        b["h"] = sum(lh for _, _, lh in b["lines"])

    BG = background(seed); G = glow_mask()
    rng = np.random.default_rng(seed + 1); n = 34
    P = (rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(14, 34, n), rng.uniform(2, 4.2, n), rng.uniform(0, 6.28, n))
    make_short.W, make_short.H = W, H

    # topo fixo
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(top)
    ft = font("cinzel-bold.ttf", 40); tt = spec.get("titulo_topo", "ORAÇÃO")
    tw_ = d.textlength(tt, font=ft); d.text(((W - tw_) / 2, 250), tt, font=ft, fill=GOLD + (230,))
    d.line([(W / 2 - 230, 318), (W / 2 + 230, 318)], fill=GOLD + (120,), width=2)
    fs = font("lora-italic.ttf", 40); st_ = spec.get("subtitulo_topo", "reze comigo, em voz baixa")
    sw = d.textlength(st_, font=fs); d.text(((W - sw) / 2, 336), st_, font=fs, fill=CREAM + (170,))
    TOP = np.asarray(top).astype(np.float32)

    tmp = tempfile.mkdtemp(); vid = os.path.join(tmp, "v.mp4")
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-preset", "medium", vid], stdin=subprocess.PIPE)
    cover = None
    nfr = int(DUR * FPS)
    for i in range(nfr):
        t = i / FPS
        flick = 0.82 + 0.10 * np.sin(t * 7.3) + 0.06 * np.sin(t * 13.1 + 1) + 0.04 * np.sin(t * 2.1)
        fr = BG + G * np.array([150, 92, 40]) * flick
        pl = make_short.particles_layer(t, P) * 0.5
        fr = fr * (1 - pl) + np.array([210, 150, 60]) * pl
        al = TOP[..., 3:4] / 255; fr = fr * (1 - al) + TOP[..., :3] * al
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        for b in B:
            if not (b["start"] - 0.01 <= t < b["end"] + 0.3):
                continue
            a_in = 1 if b["tipo"] == "gancho" else min(1, (t - b["start"]) / 0.3)
            a_out = min(1, max(0, (b["end"] + 0.3 - t) / 0.3)) if t > b["end"] else 1
            A = a_in * a_out
            y = 960 - b["h"] / 2 + (40 if b["tipo"] == "gancho" else 0)
            for line, f, lh in b["lines"]:
                if line is None:
                    y += lh; continue
                if line == "AMEM":
                    ok = t >= b["t"][-1]
                    s = "AMÉM"; w_ = d.textlength(s, font=f)
                    if ok:
                        aa = min(1, (t - b["t"][-1]) / 0.4) * A
                        d.text(((W - w_) / 2, y), s, font=f, fill=GOLD + (int(255 * aa),))
                    y += lh; continue
                full = " ".join(w for _, w in line); x = (W - d.textlength(full, font=f)) / 2
                for kk, w in line:
                    if b["tipo"] == "gancho":
                        col = GOLD if kk < b["n1"] else CREAM; a = 255
                    else:
                        tw = b["t"][kk]
                        nxt = b["t"][kk + 1] if kk + 1 < len(b["t"]) else tw + 0.6
                        if t < tw:
                            col, a = CREAM, 80
                        elif t < nxt:
                            col, a = GOLD, 255
                        else:
                            col, a = CREAM, 255
                    d.text((x, y), w, font=f, fill=col + (int(a * A),))
                    x += d.textlength(w + " ", font=f)
                y += lh
        Lr = np.asarray(layer).astype(np.float32)
        sh = np.asarray(layer.split()[3].filter(ImageFilter.GaussianBlur(6))).astype(np.float32)[..., None] / 255 * 0.7
        fr = fr * (1 - sh)
        al = Lr[..., 3:4] / 255; fr = fr * (1 - al) + Lr[..., :3] * al
        frame = np.clip(fr, 0, 255).astype(np.uint8)
        ff.stdin.write(frame.tobytes())
        if i == 0:
            cover = frame
    ff.stdin.close(); ff.wait()

    piano = os.path.join(tmp, "p.wav"); make_short.DUR = int(np.ceil(DUR)); make_short.piano(piano, seed)
    out = os.path.join(outdir, name + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", vid, "-i", mp3, "-i", piano, "-filter_complex",
                    "[1:a]adelay=0|0,volume=1.0,aresample=44100,pan=stereo|c0=c0|c1=c0[v];[2:a]volume=0.22[p];"
                    "[v][p]amix=inputs=2:duration=longest:normalize=0,afade=t=out:st=%.2f:d=1.5[a]" % (DUR - 1.5),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", "%.2f" % DUR,
                    "-movflags", "+faststart", out], check=True)
    jpg = os.path.join(outdir, name + "-capa.jpg")
    Image.fromarray(cover).resize((540, 960), Image.LANCZOS).save(jpg, quality=82)
    print(out); print(jpg); print("duração %.1fs" % DUR)


if __name__ == "__main__":
    main(sys.argv[1])
