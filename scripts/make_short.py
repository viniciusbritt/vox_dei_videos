"""Gera um Short de oração em pergaminho (1080x1920, 16 s, fade-in, piano livre).

Estilos ("estilo" no spec): pergaminho (padrão antigo), gigante (7h), marca-texto (12h), manuscrito (20h).
"particulas": true | "leve" | false.

Uso: python3 scripts/make_short.py specs/AAAA-MM-DD-manha.json
Saídas (pasta 'saida' do spec): <nome>.mp4 e <nome>-capa.jpg (540x960).
"""
import json, os, subprocess, sys, tempfile, wave, zlib
import numpy as np
import estilos
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
    """Piano devocional e esperançoso (tons maiores, termina resolvido no I). Pedido da Helo em 03/11."""
    rng = np.random.default_rng(seed)
    sr = 44100; N = sr * DUR; out = np.zeros(N)
    mid = lambda m: 440 * 2 ** ((m - 69) / 12)
    # graus em tom maior (semitons a partir da tônica): I, IV, V, vi
    I, IV, V, vi = [0, 4, 7], [5, 9, 12], [7, 11, 14], [9, 12, 16]
    progs = [[I, V, vi, IV], [I, IV, I, V], [I, vi, IV, V], [IV, I, V, I]]
    prog = progs[int(rng.integers(len(progs)))] + [I]          # sempre fecha na tônica
    key = 60 + int(rng.choice([0, 2, 5, 7, -5]))               # Dó, Ré, Fá, Sol ou Sol grave
    beat = float(rng.uniform(0.50, 0.58))

    def note(f, t0, dur, amp, bright=1.0, attack=200):
        s_ = int(t0 * sr); n = min(int(dur * sr), N - s_)
        if n <= 0:
            return
        tt = np.arange(n) / sr
        env = np.exp(-tt * 1.1) * (1 - np.exp(-tt * attack))
        out[s_:s_ + n] += amp * env * sum(a * np.sin(2 * np.pi * f * k * tt)
                                          for k, a in [(1, 1), (2, .45 * bright), (3, .18 * bright), (4, .06 * bright)])

    def pad(chord, t0, dur, amp):
        s_ = int(t0 * sr); n = min(int(dur * sr), N - s_)
        if n <= 0:
            return
        tt = np.arange(n) / sr
        env = np.minimum(tt / 0.9, 1) * np.minimum((dur - tt) / 0.9, 1)
        for m in chord:
            f = mid(key + m - 12)
            out[s_:s_ + n] += amp * env * (np.sin(2 * np.pi * f * tt) + .3 * np.sin(2 * np.pi * f * 2.003 * tt))

    t0 = 0.15; bar_len = beat * 6
    for i, ch in enumerate(prog):
        last = i == len(prog) - 1
        note(mid(key + ch[0] - 12), t0, bar_len * 1.2, 0.16, 0.6)            # baixo suave
        pad(ch, t0, bar_len + 0.6, 0.025)                                   # cama quente
        arp = [ch[0], ch[1], ch[2], ch[0] + 12, ch[2], ch[1]]
        for j, m in enumerate(arp if not last else arp[:4]):
            note(mid(key + m), t0 + j * beat, 2.4, 0.10)
        top = ch[1] + 12 if i % 2 == 0 else ch[2] + 12                     # melodia simples no agudo
        note(mid(key + top), t0 + 0.02, 2.8, 0.07, 1.3)
        note(mid(key + (ch[0] + 12 if last else ch[2] + 12)), t0 + beat * 3, 2.8, 0.06, 1.3)
        t0 += bar_len
        if t0 > DUR - 1.2:
            break
    # reverb difusa (muitos ecos curtos e fracos, sem efeito de "eco de suspense")
    dry = out.copy(); r = np.random.default_rng(seed + 7)
    for _ in range(14):
        k = int(r.uniform(0.025, 0.16) * sr); g = r.uniform(0.05, 0.13)
        out[k:] += g * dry[:-k]
    fl = int(1.8 * sr); out[-fl:] *= np.linspace(1, 0, fl) ** 1.5
    out = out / np.abs(out).max() * 0.55
    st = np.stack([out, np.roll(out, int(0.009 * sr))], 1)
    with wave.open(path, "wb") as w_:
        w_.setnchannels(2); w_.setsampwidth(2); w_.setframerate(sr)
        w_.writeframes((st * 32767).astype(np.int16).tobytes())


def particles_layer(t, P):
    """Partículas douradas subindo devagar, com brilho pulsando (por trás do texto)."""
    px, py, vs, pr, ph = P
    L = Image.new("L", (W, H), 0); d = ImageDraw.Draw(L)
    for k in range(len(px)):
        cy = (py[k] - vs[k] * t) % H; cx = px[k] + 14 * np.sin(t * 0.5 + ph[k])
        a = int(170 + 85 * np.sin(t * 1.4 + ph[k]))
        d.ellipse([cx - pr[k], cy - pr[k], cx + pr[k], cy + pr[k]], fill=max(0, min(255, a)))
    core = np.asarray(L.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32)
    halo = np.asarray(L.filter(ImageFilter.GaussianBlur(9))).astype(np.float32) * 1.6
    return np.clip(np.maximum(core, halo), 0, 255)[..., None] / 255


def main(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    outdir = os.path.join(ROOT, spec["saida"]); os.makedirs(outdir, exist_ok=True)
    name = spec["nome"]; seed = zlib.crc32(name.encode())
    global DUR
    DUR = int(spec.get("duracao", DUR))
    estilo = spec.get("estilo", "pergaminho")
    if estilo == "gigante":
        BG, layers = estilos.gigante(spec, seed)
    elif estilo == "marca-texto":
        BG, layers = estilos.marca_texto(spec, seed)
    elif estilo == "biblia-foto":       # Helo 04/11: foto parada, sem fade nem animação, só partículas e música
        import biblia_foto
        BG, modelo = biblia_foto.render(spec, seed); layers = []
        spec.setdefault("particulas", "leve")
        print("modelo de página:", modelo)
    elif estilo == "biblia":
        BG, layers = estilos.biblia(spec, seed)
    elif estilo == "manuscrito":
        BG, layers = estilos.manuscrito(spec, seed, background)
    else:
        BG = background(seed); layers = layers_from_spec(spec)
    BH, BW = BG.shape[:2]
    tmp = tempfile.mkdtemp()
    vid, wav = os.path.join(tmp, "v.mp4"), os.path.join(tmp, "a.wav")
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
                           "-preset", "medium", vid], stdin=subprocess.PIPE)
    cover = None
    P = None
    leve = spec.get("particulas") == "leve"
    if spec.get("particulas"):
        rng = np.random.default_rng(seed + 1); n = 38 if leve else 60
        P = (rng.uniform(0, W, n), rng.uniform(0, H, n), rng.uniform(14, 38, n),
             rng.uniform(2, 4.5, n) if leve else rng.uniform(3, 7, n), rng.uniform(0, 6.28, n))
    P_ALPHA = 0.55 if leve else 1.0
    frames = [int(os.environ["SO_QUADRO"])] if os.environ.get("SO_QUADRO") else range(FPS * DUR)
    for i in frames:
        t = i / FPS; z = 1.0 + 0.04 * t / DUR
        cw, ch = min(int(W * 1.05 / z), BW), min(int(H * 1.05 / z), BH)
        x0, y0 = (BW - cw) // 2, (BH - ch) // 2
        if BG.shape[:2] == (H, W):      # fundo fixo (biblia-foto): sem zoom, para o texto não escorregar
            fr = BG.astype(np.float32)
        else:
            fr = np.asarray(Image.fromarray(BG[y0:y0 + ch, x0:x0 + cw]).resize((W, H), Image.BILINEAR)).astype(np.float32)
        if P is not None:
            pl = particles_layer(t, P) * P_ALPHA
            fr = fr * (1 - pl) + np.array([200, 132, 38]) * pl
        for item in layers:
            st, Lr = item[0], item[1]
            if t < st:
                continue
            if len(item) > 2:          # marca-texto passando da esquerda para a direita
                p = min(1, max(0, (t - st - 0.5) / 0.9))
                if p <= 0:
                    continue
                m = (np.arange(W) < p * W).astype(np.float32)[None, :, None]
                al = Lr[..., 3:4] / 255 * m
            else:
                a = min(1, (t - st) / 0.8); a = a * a * (3 - 2 * a)
                al = Lr[..., 3:4] / 255 * a
            fr = fr * (1 - al) + Lr[..., :3] * al
        if estilo != "biblia-foto":
            fr *= min(1, t / 0.3 + 0.0001)
        frame = np.clip(fr, 0, 255).astype(np.uint8)
        ff.stdin.write(frame.tobytes())
        if i == FPS * 8 or os.environ.get("SO_QUADRO"):
            cover = frame
    if os.environ.get("SO_QUADRO"):
        ff.stdin.close(); ff.wait()
        Image.fromarray(cover).save(os.path.join(tmp, "quadro.png")); print(os.path.join(tmp, "quadro.png")); return
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
