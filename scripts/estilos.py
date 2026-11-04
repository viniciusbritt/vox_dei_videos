"""Estilos de layout dos Shorts escolhidos pela Helo em 02/11/2026 (estudo de design).

gigante      = variação 8 (manhã, 7h): preto, letras condensadas enormes, destaque amarelo.
marca-texto  = variação 4 (12h): branco, letras grossas, destaque com marca-texto amarelo.
manuscrito   = variação 3 (noite, 20h): pergaminho, moldura dourada, letra capitular.

Cada função recebe o spec e devolve (fundo RGB numpy, [(inicio_s, camada RGBA float32)]).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H = 1080, 1920
MAXW = 860          # largura útil (fora dos botões do Short)
LIMITE = 1660       # o CTA precisa terminar acima disto (área do título do Short)
T_GANCHO, T_PAR, T_REF, T_CTA = 0.15, [0.9, 1.7, 2.2], 2.4, 3.2


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


_m = ImageDraw.Draw(Image.new("L", (1, 1)))


def tl(s, f):
    return _m.textlength(s, font=f)


def wrap(text, f, maxw):
    """Quebra equilibrada: mesma quantidade de linhas, mas sem palavra sozinha na última."""
    base = _wrap(text, f, maxw)
    if len(base) < 2:
        return base
    best, w = base, maxw
    while w > maxw * 0.5:
        w -= 10
        t = _wrap(text, f, w)
        if len(t) != len(base):
            break
        best = t
    return best


def _wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tl(t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(name, size, lines, maxw=MAXW, minsize=20):
    while size > minsize and max(tl(l, font(name, size)) for l in lines) > maxw:
        size -= 2
    return font(name, size)


def layer():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    return L, ImageDraw.Draw(L)


def arr(L):
    return np.asarray(L).astype(np.float32)


def center(d, lines, f, y, fill, lh, cx=W / 2):
    for ln in lines:
        d.text((cx - tl(ln, f) / 2, y), ln, font=f, fill=fill)
        y += int(f.size * lh)
    return y


def pill(d, text, f, y, bg, fg, pad=36, h=86):
    w = tl(text, f)
    d.rounded_rectangle([(W - w) / 2 - pad, y, (W + w) / 2 + pad, y + h], radius=h // 2, fill=bg)
    d.text(((W - w) / 2, y + (h - f.size) / 2 - 4), text, font=f, fill=fg)
    return y + h


def cross(d, cx, cy, h, color):
    w = max(4, h // 7)
    d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=color)
    d.rectangle([cx - h * 0.32, cy - h * 0.22 - w / 2, cx + h * 0.32, cy - h * 0.22 + w / 2], fill=color)


def solid(rgb, noise=0, seed=0):
    a = np.full((int(H * 1.05), int(W * 1.05), 3), rgb, np.float32)
    if noise:
        a += np.random.default_rng(seed).normal(0, noise, a.shape[:2])[..., None]
    return np.clip(a, 0, 255).astype(np.uint8)


def _cta(spec):
    return spec.get("cta", "Escreva AMÉM se você recebe esta oração")


def _try_sizes(build, sizes):
    for s in sizes:
        out, bottom = build(s)
        if bottom <= LIMITE:
            dy = int(min((LIMITE - bottom) // 2, 180))   # centraliza quando sobra espaço
            if dy > 0:
                out = [(t, np.concatenate([np.zeros((dy, W, 4), np.float32), a[:-dy]])) for t, a in out]
            return out
    raise SystemExit(f"Texto longo demais para o estilo (termina em {bottom}px); encurte a oração.")


# ---------------- variação 8 ----------------
def gigante(spec, seed):
    WHITE, YEL, GREY = (255, 255, 255, 255), (255, 214, 10, 255), (210, 210, 210, 255)

    def build(bs):
        out = []
        hook = 150 if bs >= 40 else 128
        fa = font("bebasneue-400.ttf", hook)
        la = wrap(spec["gancho_antes"].upper(), fa, MAXW)
        if len(la) > 2:
            fa = font("bebasneue-400.ttf", 118); la = wrap(spec["gancho_antes"].upper(), fa, MAXW)
        fw = fit("bebasneue-400.ttf", 330, [spec["destaque"].upper()])
        fd = font("bebasneue-400.ttf", 120)
        ld = wrap(spec["gancho_depois"].upper(), fd, MAXW)
        L, d = layer(); y = 140
        y = center(d, la, fa, y, WHITE, 0.95)
        y = center(d, [spec["destaque"].upper()], fw, y - 10, YEL, 0.9)
        y = center(d, ld, fd, y + 10, WHITE, 1.0) + 30
        d.rectangle([W / 2 - 60, y, W / 2 + 60, y + 6], fill=YEL)
        out.append((T_GANCHO, arr(L))); y += 50
        fb = fit("inter-600.ttf", bs, [l for p in spec["oracao"] for l in p])
        for i, par in enumerate(spec["oracao"]):
            L, d = layer(); y = center(d, par, fb, y, GREY, 1.45) + 28
            out.append((T_PAR[min(i, 2)], arr(L)))
        L, d = layer(); y = center(d, [spec["referencia"].upper()], font("montserrat-800.ttf", 32), y - 8, YEL, 1.0)
        out.append((T_REF, arr(L)))
        L, d = layer(); y = pill(d, _cta(spec), fit("montserrat-800.ttf", 36, [_cta(spec)], 800), y + 40, YEL, (10, 10, 10, 255))
        out.append((T_CTA, arr(L)))
        return out, y
    return solid((10, 10, 10)), _try_sizes(build, [44, 42, 40, 38, 36, 34])


# ---------------- variação 4 ----------------
def marca_texto(spec, seed):
    INK, BODY, YEL = (18, 18, 18, 255), (55, 55, 55, 255), (255, 222, 0, 255)

    def build(bs):
        out = []
        fh = font("montserrat-800.ttf", 62 if bs >= 42 else 54)
        la, ld = wrap(spec["gancho_antes"], fh, MAXW), wrap(spec["gancho_depois"], fh, MAXW)
        word = spec["destaque"].upper()
        fw = fit("montserrat-800.ttf", 200, [word], MAXW - 60)
        L, d = layer(); y = 190
        y = center(d, la, fh, y, INK, 1.2)
        ww = tl(word, fw); top = y + fw.size * 0.35
        d.rectangle([(W - ww) / 2 - 24, top, (W + ww) / 2 + 24, top + fw.size * 0.8], fill=YEL)
        y = center(d, [word], fw, y, INK, 1.12)
        y = center(d, ld, fh, y + 10, INK, 1.2) + 40
        out.append((T_GANCHO, arr(L)))
        fb = fit("inter-600.ttf", bs, [l for p in spec["oracao"] for l in p])
        for i, par in enumerate(spec["oracao"]):
            L, d = layer(); y = center(d, par, fb, y, BODY, 1.5) + 36
            out.append((T_PAR[min(i, 2)], arr(L)))
        L, d = layer(); y = center(d, [spec["referencia"].upper()], font("montserrat-800.ttf", 34), y - 10, (120, 120, 120, 255), 1.0)
        out.append((T_REF, arr(L)))
        L, d = layer(); y = pill(d, _cta(spec), fit("montserrat-800.ttf", 36, [_cta(spec)], 800), y + 40, YEL, INK)
        out.append((T_CTA, arr(L)))
        return out, y
    return solid((250, 250, 247)), _try_sizes(build, [46, 44, 42, 40, 38, 36])


# ---------------- variação 3 ----------------
def manuscrito(spec, seed, background):
    GOLD, RED, INK = (176, 126, 40, 255), (140, 30, 22, 255), (40, 28, 18, 255)
    X0, X1 = 70, W - 140            # moldura
    TX0, TX1 = 128, W - 190         # texto

    def build(bs):
        out = []
        fh = font("cormorantgaramond-600.ttf", 58)
        la, ld = wrap(spec["gancho_antes"], fh, MAXW - 120), wrap(spec["gancho_depois"], fh, MAXW - 120)
        fw = fit("cinzel-bold.ttf", 160, [spec["destaque"].upper()], MAXW - 140)
        cx = (X0 + X1) / 2
        L, d = layer(); y = 185
        y = center(d, la, fh, y, INK, 1.15, cx)
        y = center(d, [spec["destaque"].upper()], fw, y, RED, 1.05, cx)
        y = center(d, ld, fh, y + 4, INK, 1.15, cx) + 36
        out.append((T_GANCHO, arr(L)))
        fb = font("cormorantgaramond-600.ttf", bs); lh = int(bs * 1.28)
        for i, par in enumerate(spec["oracao"]):
            text = " ".join(par)
            L, d = layer()
            if i == 0 and text[0].isalpha():
                capsz = int(lh * 3.1)
                cap = font("cinzel-bold.ttf", int(capsz * 1.05))
                cw = max(capsz * 0.85, tl(text[0], cap) + 30)
                d.rectangle([TX0, y + 4, TX0 + cw, y + 4 + capsz], fill=RED)
                bb = d.textbbox((0, 0), text[0], font=cap)
                d.text((TX0 + (cw - (bb[2] - bb[0])) / 2 - bb[0], y + 4 + (capsz - (bb[3] - bb[1])) / 2 - bb[1]),
                       text[0], font=cap, fill=(245, 215, 140, 255))
                ind = TX0 + cw + 22
                words, lines, cur = text[1:].split(" "), [], ""
                n_side = max(1, int((capsz + 8) // lh))
                # linhas ao lado da capitular
                k = 0
                while words and len(lines) < n_side:
                    w = words.pop(0); t = (cur + " " + w) if cur else w
                    if tl(t, fb) <= TX1 - ind or not cur:
                        cur = t
                    else:
                        lines.append(cur); cur = w
                if len(lines) < n_side and cur and not words:
                    lines.append(cur); cur = ""
                for ln in lines:
                    d.text((ind, y), ln, font=fb, fill=INK); y += lh
                y = max(y, y)  # continua abaixo
                rest = wrap((cur + " " + " ".join(words)).strip(), fb, TX1 - TX0)
            else:
                rest = wrap(text, fb, TX1 - TX0)
            for ln in rest:
                d.text((TX0, y), ln, font=fb, fill=INK); y += lh
            y += int(bs * 0.6)
            out.append((T_PAR[min(i, 2)], arr(L)))
        L, d = layer(); fr = font("cinzel-bold.ttf", 34); ref = spec["referencia"].upper(); rw = tl(ref, fr)
        d.text((cx - rw / 2, y), ref, font=fr, fill=GOLD)
        for sx in (cx - rw / 2 - 40, cx + rw / 2 + 40):
            cross(d, sx, y + 20, 34, GOLD)
        y += 70
        out.append((T_REF, arr(L)))
        Lf, df = layer()
        df.rectangle([X0, 120, X1, y], outline=GOLD, width=4)
        df.rectangle([X0 + 16, 136, X1 - 16, y - 16], outline=GOLD, width=1)
        out.insert(0, (0.0, arr(Lf)))
        L, d = layer(); y = pill(d, _cta(spec), fit("mont-semibold.ttf", 38, [_cta(spec)], 820), y + 36, RED, (255, 238, 210, 255))
        out.append((T_CTA, arr(L)))
        return out, y
    return background(seed), _try_sizes(build, [50, 48, 46, 44, 42, 40])
