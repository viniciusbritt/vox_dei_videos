"""Gera um Short de oração em pergaminho (1080x1920, 16 s, fade-in, piano livre).

Uso: python3 scripts/make_short.py specs/AAAA-MM-DD-manha.json
Saídas (pasta 'saida' do spec): <nome>.mp4 e <nome>-capa.jpg (540x960).
"""
import json, os, subprocess, sys, tempfile, wave, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H, FPS, DUR = 1080, 1920, 30, 16
MAX_W = 830  # largura máxima da linha (não ficar sob os botões do Short)

INK = (30, 22, 16); BROWN = (110, 62, 28); RED = (128, 36, 20)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def background(seed):
    rng = np.random.default_rng(seed)
    BW, BH = int(W * 1.05), int(H * 1.05)
    base = np.array([244, 230, 198], np.float32)
    n = rng.normal(0, 1, (BH // 8, BW // 8)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 30) + 128).clip(0, 255).astype(np.uint8))
                   .resize((BW, BH), Image.BICUBIC).filter(ImageFilter.GaussianBlur(18))).astype(np.float32) - 128
    fine = rng.normal(0, 6, (BH, BW)).astype(np.float32)
    y = np.linspace(-1, 1, BH)[:, None]; x = np.linspace(-1, 1, BW)[None, :]
    vig = np.clip(1 - 0.30 * (x ** 2 + (y * 0.85) ** 2) ** 1.4, 0.45, 1)
    bg = base[None, None, :] + n[..., None] * 0.35 + fine[..., None]
    bg = bg * vig[..., None] + np.array([92, 52, 22], np.float32) * (1 - vig[..., None])
    for _ in range(10):
        cx, cy = rng.uniform(-1, 1), rng.uniform(-1, 1); r = rng.uniform(0.1, 0.35)
        bg *= (1 - 0.04 * np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / r ** 2)))[..., None]
    return np.clip(bg, 0, 255).astype(np.uint8)


def layers_from_spec(spec):
    f_hook = font("lora-italic.ttf", 50)
    f_word = font("cinzel-bold.ttf", spec.get("tamanho_destaque", 150))
    f_body = font("lora-medium.ttf", spec.get("tamanho_texto", 48))
    f_ref = font("mont-semibold.ttf", 34)
    f_cta = font("mont-semibold.ttf", 40)
    lh = lambda f: int(f.size * (1.05 if f is f_word else 1.5))
    blocks = [(0.15, [spec["gancho_antes"]], f_hook, BROWN, 6),
              (0.15, [spec["destaque"]], f_word, RED, 22),
              (0.15, [spec["gancho_depois"]], f_hook, BROWN, 64)]
    starts = [0.9, 1.7, 2.2]
    for i, par in enumerate(spec["oracao"]):
        blocks.append((starts[min(i, 2)], par, f_body, INK, 34 if i < len(spec["oracao"]) - 1 else 46))
    blocks.append((2.4, [spec["referencia"].upper()], f_ref, BROWN, 0))
    total = sum(lh(f) * len(l) + g for _, l, f, _, g in blocks)
    yy = (H - total) // 2 - 150
    if yy < 120:
        raise SystemExit(f"Texto longo demais: sobra {yy}px no topo; encurte a oração.")
    out = []
    for st, lines, f, col, g in blocks:
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        for ln in lines:
            w = d.textlength(ln, font=f)
            if w > MAX_W:
                raise SystemExit(f"Linha larga demais ({int(w)}px): {ln!r}")
            d.text(((W - w) / 2, yy), ln, font=f, fill=col + (255,)); yy += lh(f)
        if lines == [spec["gancho_depois"]]:
            d.line([(W / 2 - 90, yy + 18), (W / 2 + 90, yy + 18)], fill=BROWN + (180,), width=2)
        yy += g
        out.append((st, np.asarray(L).astype(np.float32)))
    C = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(C)
    cta = spec.get("cta", "Escreva AMÉM se você recebe esta oração")
    w = d.textlength(cta, font=f_cta)
    d.rounded_rectangle([(W - w) / 2 - 36, yy + 60, (W + w) / 2 + 36, yy + 145], radius=42, fill=(70, 38, 18, 235))
    d.text(((W - w) / 2, yy + 75), cta, font=f_cta, fill=(246, 232, 200, 255))
    out.append((3.2, np.asarray(C).astype(np.float32)))
    return out


def piano(path, seed):
    rng = np.random.default_rng(seed)
    sr = 44100; N = sr * DUR; out = np.zeros(N)
    mid = lambda m: 440 * 2 ** ((m - 69) / 12)
    progs = [[[57, 64, 69, 72], [53, 60, 65, 69], [48, 55, 60, 64], [55, 62, 67, 71]],   # Am F C G
             [[48, 55, 60, 64], [55, 62, 67, 71], [57, 64, 69, 72], [53, 60, 65, 69]],   # C G Am F
             [[50, 57, 62, 65], [55, 62, 67, 71], [48, 55, 60, 64], [57, 64, 69, 72]],   # Dm G C Am
             [[53, 60, 65, 69], [48, 55, 60, 64], [55, 62, 67, 71], [57, 64, 69, 72]]]   # F C G Am
    prog = progs[int(rng.integers(len(progs)))]
    tempo = float(rng.uniform(0.56, 0.68))

    def note(f, t0, dur, amp):
        s = int(t0 * sr); n = min(int(dur * sr), N - s)
        if n <= 0:
            return
        tt = np.arange(n) / sr
        env = np.exp(-tt * 1.6) * (1 - np.exp(-tt * 200))
        out[s:s + n] += amp * env * sum(a * np.sin(2 * np.pi * f * k * tt) for k, a in [(1, 1), (2, .35), (3, .12), (4, .05)])
    t0 = 0.2
    for bar in range(5):
        ch = prog[bar % 4]
        note(mid(ch[0] - 12), t0, 4.0, 0.22)
        for j, m in enumerate([ch[1], ch[2], ch[3], ch[2], ch[3] + 12 if bar % 2 else ch[3], ch[2]]):
            note(mid(m), t0 + j * tempo, 3.0, 0.12)
        t0 += tempo * 6.3
    for dl, g in [(0.11, .35), (0.23, .25), (0.37, .18), (0.53, .12)]:
        k = int(dl * sr); out[k:] += g * out[:-k]
    fl = int(1.5 * sr); out[-fl:] *= np.linspace(1, 0, fl)
    out = out / np.abs(out).max() * 0.6
    st = np.stack([out, np.roll(out, int(0.012 * sr))], 1)
    with wave.open(path, "wb") as w_:
        w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(sr)
        w_.writeframes((st * 32767).astype(np.int16).tobytes())


def main(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    outdir = os.path.join(ROOT, spec["saida"]); os.makedirs(outdir, exist_ok=True)
    name = spec["nome"]; seed = zlib.crc32(name.encode())
    BG = background(seed); BH, BW = BG.shape[:2]
    layers = layers_from_spec(spec)
    tmp = tempfile.mkdtemp()
    vid, wav = os.path.join(tmp, "v.mp4"), os.path.join(tmp, "a.wav")
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-preset", "medium", vid], stdin=subprocess.PIPE)
    cover = None
    for i in range(FPS * DUR):
        t = i / FPS; z = 1.0 + 0.04 * t / DUR
        cw, ch = min(int(W * 1.05 / z), BW), min(int(H * 1.05 / z), BH)
        x0, y0 = (BW - cw) // 2, (BH - ch) // 2
        fr = np.asarray(Image.fromarray(BG[y0:y0 + ch, x0:x0 + cw]).resize((W, H), Image.BILINEAR)).astype(np.float32)
        for st, Lr in layers:
            if t < st:
                continue
            a = min(1, (t - st) / 0.8); a = a * a * (3 - 2 * a)
            al = Lr[..., 3:4] / 255 * a; fr = fr * (1 - al) + Lr[..., :3] * al
        fr *= min(1, t / 0.3 + 0.0001)
        frame = np.clip(fr, 0, 255).astype(np.uint8)
        ff.stdin.write(frame.tobytes())
        if i == FPS * 8:
            cover = frame
    ff.stdin.close(); ff.wait()
    piano(wav, seed)
    mp4 = os.path.join(outdir, name + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    jpg = os.path.join(outdir, name + "-capa.jpg")
    Image.fromarray(cover).resize((540, 960), Image.LANCZOS).save(jpg, quality=80)
    print(mp4); print(jpg)


if __name__ == "__main__":
    main(sys.argv[1])
