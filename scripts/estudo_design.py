"""Estudo de design: 10 variações do Short do Salmo 51 (mesmo texto, layouts diferentes).

Uso: python3 scripts/estudo_design.py <pasta_saida>
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "fonts")
W, H = 1080, 1920
SAFE_W = 860  # largura útil: fora dos botões laterais do Short

H1, WORD, H2 = "Você pediu um sinal de", "DEUS?", "Aqui está."
P1 = ["Senhor, cria em mim", "um coração puro e renova", "em mim um espírito firme.", "Lava-me de toda culpa,",
      "purifica-me dos meus pecados", "e não afastes de mim o teu Espírito."]
P2 = ["Devolve-me a alegria da salvação.", "Tira do meu coração toda mágoa,", "todo medo e toda inveja,",
      "e enche-o com o teu amor.", "Em nome de Jesus, amém."]
REF = "SALMO 51,12-14"
CTA = "Escreva AMÉM se você recebe esta oração"


def font(name, size):
    return ImageFont.truetype(os.path.join(F, name), size)


def fit(name, size, lines, maxw=SAFE_W):
    """Reduz a fonte até a linha mais larga caber na zona segura."""
    while size > 20:
        f = font(name, size)
        if max(ImageDraw.Draw(Image.new("L", (1, 1))).textlength(l, font=f) for l in lines) <= maxw:
            return f
        size -= 2
    return font(name, size)


def text_block(d, lines, f, y, fill, lh=1.45, x_center=W / 2, align="center", x_left=110, shadow=None):
    for ln in lines:
        w = d.textlength(ln, font=f)
        x = x_center - w / 2 if align == "center" else x_left
        if shadow:
            d.text((x + 3, y + 4), ln, font=f, fill=shadow)
        d.text((x, y), ln, font=f, fill=fill)
        y += int(f.size * lh)
    return y


def gradient(top, bottom, w=W, h=H):
    t = np.linspace(0, 1, h)[:, None, None]
    g = np.array(top, np.float32) * (1 - t) + np.array(bottom, np.float32) * t
    return Image.fromarray(np.broadcast_to(g, (h, w, 3)).astype(np.uint8))


def radial(img, cx, cy, r, color, strength):
    y, x = np.mgrid[0:H, 0:W]
    m = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (r ** 2)))[..., None] * strength
    a = np.asarray(img).astype(np.float32)
    return Image.fromarray(np.clip(a * (1 - m) + np.array(color) * m, 0, 255).astype(np.uint8))


def noise(img, amt=6, seed=1):
    a = np.asarray(img).astype(np.float32)
    a += np.random.default_rng(seed).normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def particles(img, n, color, seed=3, rmax=5, area=(0, 0, W, H)):
    L = Image.new("L", (W, H), 0); d = ImageDraw.Draw(L)
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = rng.uniform(area[0], area[2]), rng.uniform(area[1], area[3]); r = rng.uniform(1.5, rmax)
        d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(140, 255)))
    m = np.maximum(np.asarray(L.filter(ImageFilter.GaussianBlur(1))), np.asarray(L.filter(ImageFilter.GaussianBlur(8))) * 1.4)
    m = np.clip(m, 0, 255)[..., None] / 255
    a = np.asarray(img).astype(np.float32)
    return Image.fromarray(np.clip(a * (1 - m) + np.array(color) * m, 0, 255).astype(np.uint8))


def pill(d, text, f, y, bg, fg, pad=36, h=86):
    w = d.textlength(text, font=f)
    d.rounded_rectangle([(W - w) / 2 - pad, y, (W + w) / 2 + pad, y + h], radius=h // 2, fill=bg)
    d.text(((W - w) / 2, y + (h - f.size) / 2 - 4), text, font=f, fill=fg)


def cross(d, cx, cy, h, color, w=None):
    w = w or max(4, h // 7)
    d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=color)
    d.rectangle([cx - h * 0.32, cy - h * 0.22 - w / 2, cx + h * 0.32, cy - h * 0.22 + w / 2], fill=color)


def body(d, y, f, ink, gap=34, lh=1.45, **kw):
    y = text_block(d, P1, f, y, ink, lh, **kw) + gap
    return text_block(d, P2, f, y, ink, lh, **kw)


# ---------- 10 variações ----------

def v01_noite_dourada():
    img = gradient((6, 10, 28), (14, 22, 52)); img = radial(img, W / 2, 330, 420, (60, 50, 30), 0.55)
    img = particles(img, 60, (240, 200, 120), rmax=4); d = ImageDraw.Draw(img)
    GOLD = (240, 198, 110)
    y = text_block(d, [H1], font("lora-italic.ttf", 52), 190, (215, 200, 170))
    y = text_block(d, [WORD], font("cinzel-bold.ttf", 170), y + 4, GOLD, 1.05, shadow=(0, 0, 0))
    y = text_block(d, [H2], font("lora-italic.ttf", 52), y + 10, (215, 200, 170)) + 40
    d.line([(W / 2 - 90, y), (W / 2 + 90, y)], fill=GOLD, width=2)
    y = body(d, y + 50, fit("lora-medium.ttf", 48, P1 + P2), (240, 236, 228))
    text_block(d, [REF], font("mont-semibold.ttf", 34), y + 30, GOLD)
    pill(d, CTA, font("mont-semibold.ttf", 38), y + 110, GOLD, (20, 18, 30))
    return img


def v02_faixa_vermelha():
    img = noise(Image.new("RGB", (W, H), (243, 231, 205)), 5); d = ImageDraw.Draw(img)
    RED = (178, 28, 28)
    d.rectangle([0, 150, W, 560], fill=RED)
    y = text_block(d, [H1], font("montserrat-500.ttf", 50), 195, (255, 235, 220))
    y = text_block(d, [WORD], font("montserrat-800.ttf", 190), y, (255, 255, 255), 1.0)
    text_block(d, [H2], font("montserrat-500.ttf", 50), y + 6, (255, 235, 220))
    y = body(d, 650, fit("lora-medium.ttf", 48, P1 + P2), (30, 22, 16))
    text_block(d, [REF], font("mont-semibold.ttf", 34), y + 26, RED)
    pill(d, CTA, font("mont-semibold.ttf", 38), y + 100, (30, 22, 16), (255, 240, 220))
    return img


def v03_manuscrito():
    img = noise(Image.new("RGB", (W, H), (238, 224, 190)), 7, seed=4)
    img = radial(img, W / 2, H / 2, 1300, (120, 80, 40), 0.0)
    d = ImageDraw.Draw(img)
    GOLD, RED, INK = (176, 126, 40), (140, 30, 22), (40, 28, 18)
    d.rectangle([70, 120, W - 140, H - 380], outline=GOLD, width=4)
    d.rectangle([86, 136, W - 156, H - 396], outline=GOLD, width=1)
    y = text_block(d, [H1], font("cormorantgaramond-600.ttf", 58), 190, INK)
    y = text_block(d, [WORD], font("cinzel-bold.ttf", 160), y, RED, 1.05)
    y = text_block(d, [H2], font("cormorantgaramond-600.ttf", 58), y + 4, INK) + 40
    # capitular "S" iluminada
    cap = font("cinzel-bold.ttf", 210)
    d.rectangle([130, y, 300, y + 200], fill=RED)
    d.text((152, y - 22), "S", font=cap, fill=(245, 215, 140))
    f = font("cormorantgaramond-600.ttf", 50)
    first = ["enhor, cria em mim", "um coração puro e", "renova em mim um", "espírito firme."]
    yy = text_block(d, first, f, y + 6, INK, 1.25, align="left", x_left=330)
    rest = ["Lava-me de toda culpa, purifica-me", "dos meus pecados e não afastes", "de mim o teu Espírito.", "",
            "Devolve-me a alegria da salvação.", "Tira do meu coração toda mágoa,", "todo medo e toda inveja,",
            "e enche-o com o teu amor.", "Em nome de Jesus, amém."]
    yy = text_block(d, rest, f, yy + 10, INK, 1.3, align="left", x_left=135)
    fr = font("cinzel-bold.ttf", 34); rw = d.textlength(REF, font=fr)
    text_block(d, [REF], fr, yy + 14, GOLD)
    for sx in (W / 2 - rw / 2 - 40, W / 2 + rw / 2 + 40):
        cross(d, sx, yy + 34, 34, GOLD)
    pill(d, CTA, font("mont-semibold.ttf", 38), H - 330, RED, (255, 238, 210))
    return img


def v04_marca_texto():
    img = Image.new("RGB", (W, H), (250, 250, 247)); d = ImageDraw.Draw(img)
    INK = (18, 18, 18)
    y = text_block(d, [H1], font("montserrat-800.ttf", 64), 210, INK, 1.2)
    f = font("montserrat-800.ttf", 200); w = d.textlength(WORD, font=f)
    d.rectangle([(W - w) / 2 - 24, y + 70, (W + w) / 2 + 24, y + 230], fill=(255, 222, 0))
    y = text_block(d, [WORD], f, y, INK, 1.12)
    y = text_block(d, [H2], font("montserrat-800.ttf", 64), y + 10, INK, 1.2) + 40
    y = body(d, y, fit("inter-600.ttf", 46, P1 + P2), (55, 55, 55), gap=36, lh=1.5)
    text_block(d, [REF], font("montserrat-800.ttf", 34), y + 26, (120, 120, 120))
    pill(d, CTA, font("montserrat-800.ttf", 36), y + 100, (255, 222, 0), INK)
    return img


def v05_roxo_liturgico():
    img = gradient((46, 16, 74), (16, 6, 34)); img = radial(img, W / 2, 360, 460, (120, 60, 160), 0.45)
    d = ImageDraw.Draw(img)
    GOLD = (246, 205, 112)
    cross(d, W / 2, 160, 70, GOLD)
    y = text_block(d, [H1], font("playfairdisplay-400i.ttf", 54), 230, (230, 215, 245))
    y = text_block(d, [WORD], font("playfairdisplay-900.ttf", 190), y, GOLD, 1.05, shadow=(20, 0, 30))
    y = text_block(d, [H2], font("playfairdisplay-400i.ttf", 54), y + 10, (230, 215, 245)) + 60
    y = body(d, y, fit("lora-medium.ttf", 47, P1 + P2), (250, 245, 255))
    text_block(d, [REF], font("mont-semibold.ttf", 34), y + 28, GOLD)
    pill(d, CTA, font("mont-semibold.ttf", 38), y + 104, GOLD, (40, 10, 60))
    return img


def v06_notificacao():
    img = gradient((20, 24, 40), (8, 10, 18)); img = particles(img, 30, (180, 190, 255), rmax=3)
    d = ImageDraw.Draw(img)
    # cartão de notificação (quebra de padrão no 1º segundo)
    d.rounded_rectangle([90, 170, W - 150, 560], radius=44, fill=(250, 250, 252))
    d.ellipse([130, 210, 210, 290], fill=(212, 170, 60))
    cross(d, 170, 250, 46, (255, 255, 255))
    d.text((235, 224), "Vox Dei  ·  agora", font=font("inter-600.ttf", 34), fill=(120, 120, 130))
    d.text((130, 315), H1, font=font("montserrat-800.ttf", 52), fill=(20, 20, 30))
    d.text((130, 380), WORD, font=font("montserrat-800.ttf", 110), fill=(196, 30, 58))
    wx = 130 + d.textlength(WORD, font=font("montserrat-800.ttf", 110)) + 24
    d.text((wx, 422), H2, font=font("montserrat-500.ttf", 50), fill=(20, 20, 30))
    y = body(d, 650, fit("inter-600.ttf", 46, P1 + P2), (235, 238, 248), lh=1.5)
    text_block(d, [REF], font("mont-semibold.ttf", 34), y + 26, (212, 170, 60))
    pill(d, CTA, font("mont-semibold.ttf", 38), y + 100, (196, 30, 58), (255, 255, 255))
    return img


def v07_luz_divina():
    img = gradient((250, 236, 200), (205, 170, 120))
    a = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    ang = np.arctan2(yy + 300, xx - W / 2)
    rays = (0.5 + 0.5 * np.sin(ang * 22)) ** 3 * np.clip(1 - yy / 1300, 0, 1) * 0.35
    a = a * (1 - rays[..., None]) + 255 * rays[..., None]
    img = radial(Image.fromarray(a.astype(np.uint8)), W / 2, 0, 700, (255, 250, 230), 0.8)
    img = particles(img, 45, (255, 255, 240), rmax=4, area=(0, 0, W, 900)); d = ImageDraw.Draw(img)
    BROWN, RED = (90, 50, 20), (150, 40, 20)
    y = text_block(d, [H1], font("lora-italic.ttf", 54), 220, BROWN)
    y = text_block(d, [WORD], font("cinzel-bold.ttf", 180), y, RED, 1.05)
    y = text_block(d, [H2], font("lora-italic.ttf", 54), y + 8, BROWN) + 50
    d.rounded_rectangle([90, y - 10, W - 150, y + 900], radius=30, fill=(255, 250, 240))
    y = body(d, y + 40, fit("lora-medium.ttf", 45, P1 + P2, 780), (35, 25, 18), x_center=(90 + W - 150) / 2)
    text_block(d, [REF], font("mont-semibold.ttf", 32), y + 20, BROWN, x_center=(90 + W - 150) / 2)
    pill(d, CTA, font("mont-semibold.ttf", 38), y + 140, RED, (255, 240, 220))
    return img


def v08_tipografia_gigante():
    img = Image.new("RGB", (W, H), (10, 10, 10)); d = ImageDraw.Draw(img)
    YEL = (255, 214, 10)
    y = text_block(d, ["VOCÊ PEDIU", "UM SINAL DE"], font("bebasneue-400.ttf", 150), 150, (255, 255, 255), 0.95)
    y = text_block(d, ["DEUS?"], font("bebasneue-400.ttf", 330), y - 10, YEL, 0.9)
    y = text_block(d, ["AQUI ESTÁ."], font("bebasneue-400.ttf", 130), y + 10, (255, 255, 255), 1.0) + 30
    d.rectangle([W / 2 - 60, y, W / 2 + 60, y + 6], fill=YEL)
    y = body(d, y + 50, fit("inter-600.ttf", 42, P1 + P2), (210, 210, 210), gap=28, lh=1.45)
    text_block(d, [REF], font("montserrat-800.ttf", 32), y + 20, YEL)
    pill(d, CTA, font("montserrat-800.ttf", 36), y + 90, YEL, (10, 10, 10))
    return img


def v09_carta_manuscrita():
    img = noise(Image.new("RGB", (W, H), (252, 248, 236)), 4, seed=9); d = ImageDraw.Draw(img)
    for yy in range(700, 1560, 62):
        d.line([(90, yy), (W - 150, yy)], fill=(190, 205, 225), width=2)
    d.line([(150, 640), (150, 1580)], fill=(230, 150, 150), width=2)
    BLUE, INK = (24, 52, 120), (40, 40, 60)
    y = text_block(d, [H1], font("dancingscript-700.ttf", 74), 180, BLUE, 1.2)
    y = text_block(d, [WORD], font("playfairdisplay-900.ttf", 190), y, (170, 30, 40), 1.02)
    text_block(d, [H2], font("dancingscript-700.ttf", 74), y, BLUE, 1.2)
    f = fit("dancingscript-700.ttf", 52, P1 + P2, 780)
    y = text_block(d, P1, f, 660, INK, 1.19, x_center=(150 + W - 150) / 2)
    y = text_block(d, P2, f, y + 6, INK, 1.19, x_center=(150 + W - 150) / 2)
    text_block(d, [REF], font("mont-semibold.ttf", 32), y + 26, BLUE)
    pill(d, CTA, font("mont-semibold.ttf", 38), y + 100, BLUE, (255, 255, 255))
    return img


def v10_cartao_esperanca():
    img = gradient((196, 214, 192), (140, 166, 138)); img = noise(img, 4); d = ImageDraw.Draw(img)
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle([100, 200, W - 160, 1560], radius=44, fill=110)
    img = Image.composite(Image.new("RGB", (W, H), (60, 80, 60)), img, sh.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([90, 180, W - 170, 1540], radius=44, fill=(255, 253, 246))
    GREEN, GOLD = (32, 82, 52), (190, 140, 40)
    cx = (90 + W - 170) / 2
    y = text_block(d, [H1], font("playfairdisplay-400i.ttf", 50), 250, GREEN, x_center=cx)
    y = text_block(d, [WORD], font("playfairdisplay-900.ttf", 170), y, GREEN, 1.05, x_center=cx)
    y = text_block(d, [H2], font("playfairdisplay-400i.ttf", 50), y + 6, GREEN, x_center=cx) + 30
    d.line([(cx - 80, y), (cx + 80, y)], fill=GOLD, width=3)
    y = body(d, y + 40, fit("lora-medium.ttf", 44, P1 + P2, 740), (40, 44, 40), x_center=cx, lh=1.45)
    text_block(d, [REF], font("mont-semibold.ttf", 32), y + 20, GOLD, x_center=cx)
    pill(d, CTA, font("mont-semibold.ttf", 38), 1590, GREEN, (255, 253, 246))
    return img


VARIANTS = [v01_noite_dourada, v02_faixa_vermelha, v03_manuscrito, v04_marca_texto, v05_roxo_liturgico,
            v06_notificacao, v07_luz_divina, v08_tipografia_gigante, v09_carta_manuscrita, v10_cartao_esperanca]

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for i, fn in enumerate(VARIANTS, 1):
        p = os.path.join(out, f"{i:02d}-{fn.__name__[4:].replace('_', '-')}.png")
        fn().save(p); print(p)
