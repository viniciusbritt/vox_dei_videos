"""Estilos de layout dos Shorts escolhidos pela Helo em 02/11/2026 (estudo de design).

gigante      = variação 8 (manhã, 7h): preto, letras condensadas enormes, destaque amarelo.
marca-texto  = variação 4 (12h): branco, letras grossas, destaque com marca-texto amarelo.
manuscrito   = variação 3 (noite, 20h): pergaminho, moldura dourada, letra capitular.

Cada função recebe o spec e devolve (fundo RGB numpy, [(inicio_s, camada RGBA float32)]).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
                out = [(it[0], np.concatenate([np.zeros((dy, W, 4), np.float32), it[1][:-dy]])) + tuple(it[2:]) for it in out]
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


# ---------------- Bíblia grifada (teste pedido pela Helo em 04/11/2026) ----------------
# Página de Bíblia, referência grande no topo, versículo e reflexão com marca-texto (==texto==)
# e palavras sublinhadas em negrito (__texto__). Cada parágrafo usa uma cor de marca-texto.
HL = {"amarelo": (255, 224, 70), "verde": (160, 232, 150), "rosa": (255, 176, 206), "azul": (150, 215, 255)}


def _rich(text):
    """'a ==b c== __d__' -> [(palavra, grifo, sublinhado)]"""
    out, hl, ul, cur = [], False, False, ""
    i = 0
    while i < len(text):
        two = text[i:i + 2]
        if two in ("==", "__"):
            if cur:
                out.append((cur, hl, ul)); cur = ""
            if two == "==":
                hl = not hl
            else:
                ul = not ul
            i += 2; continue
        c = text[i]
        if c == " ":
            if cur:
                out.append((cur, hl, ul)); cur = ""
            out.append((" ", hl, ul))
        else:
            cur += c
        i += 1
    if cur:
        out.append((cur, hl, ul))
    # junta pedaços colados (ex.: 'palavra' + ',') numa unidade sem espaço
    words, buf = [], []
    for tok in out:
        if tok[0] == " ":
            if buf:
                words.append(buf); buf = []
        else:
            buf.append(tok)
    if buf:
        words.append(buf)
    return words


def _rich_lines(words, fonts, maxw):
    sp = tl(" ", fonts[0])
    wlen = lambda w: sum(tl(s, fonts[1] if u else fonts[0]) for s, h, u in w)
    lines, cur, cw = [], [], 0
    for w in words:
        L = wlen(w)
        if cur and cw + sp + L > maxw:
            lines.append(cur); cur, cw = [w], L
        else:
            cw = cw + (sp if cur else 0) + L; cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def _draw_rich(dt, dh, lines, fonts, x0, y, lh, ink, ul_col, hl_col, rng):
    sp = tl(" ", fonts[0]); size = fonts[0].size
    bb = fonts[0].getbbox("ÁgjÉ")
    _HLBOX["box"] = ((bb[1] - size * 0.06) / size, (bb[3] + size * 0.08) / size)
    for ln in lines:
        x = x0; run = None
        segs = []
        for wi, w in enumerate(ln):
            if wi:
                segs.append((" ", w[0][1] and ln[wi - 1][-1][1], False, x, sp)); x += sp
            for s, h, u in w:
                f = fonts[1] if u else fonts[0]; L = tl(s, f)
                segs.append((s, h, u, x, L)); x += L
        for s, h, u, sx, L in segs:            # marca-texto (camada de baixo)
            if h:
                run = [sx, sx + L] if run is None else [run[0], sx + L]
            elif run is not None:
                _hl(dh, run, y, size, hl_col, rng); run = None
        if run is not None:
            _hl(dh, run, y, size, hl_col, rng)
        for s, h, u, sx, L in segs:  # texto
            if s == " ":
                continue
            f = fonts[1] if u else fonts[0]
            dt.text((sx, y), s, font=f, fill=ink)
            if u:
                dt.line([(sx, y + size * 1.13), (sx + L, y + size * 1.13)], fill=ul_col, width=max(3, size // 14))
        y += lh
    return y


_HLBOX = {}


def _hl(d, run, y, size, col, rng):
    x0, x1 = run[0] - 6, run[1] + 6
    t_, b_ = _HLBOX.get("box", (0.12, 1.18))
    top, bot = y + size * t_ + rng.uniform(-3, 3), y + size * b_ + rng.uniform(-3, 3)
    d.polygon([(x0, top + rng.uniform(-4, 4)), (x1, top + rng.uniform(-4, 4)),
               (x1 + rng.uniform(-4, 4), bot), (x0 + rng.uniform(-4, 4), bot)], fill=col + (175,))


def _pagina(seed):
    rng = np.random.default_rng(seed)
    BW, BH = int(W * 1.05), int(H * 1.05)
    base = np.array([247, 240, 224], np.float32)
    n = rng.normal(0, 1, (BH // 6, BW // 6)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 24) + 128).clip(0, 255).astype(np.uint8)).resize((BW, BH), Image.BICUBIC)).astype(np.float32) - 128
    bg = base[None, None, :] + n[..., None] * 0.18 + rng.normal(0, 3, (BH, BW))[..., None]
    x = np.linspace(0, 1, BW)[None, :]
    gut = np.clip(1 - np.exp(-x / 0.06) * 0.75, 0, 1)                    # sombra da lombada à esquerda
    yy = np.linspace(-1, 1, BH)[:, None]
    vig = np.clip(1 - 0.18 * (yy ** 4) - 0.10 * ((x - 0.5) * 2) ** 4, 0.6, 1)
    edge = np.clip(1 - np.exp(-(1 - x) / 0.012) * 0.25, 0, 1)            # borda das folhas à direita
    m = gut * edge * vig
    bg = bg * m[..., None] + np.array([90, 62, 34]) * (1 - m)[..., None] * 0.45
    for k in range(6):                                                    # folhas empilhadas
        xx = BW - 6 - k * 5
        bg[:, xx:xx + 1] *= 0.93
    return np.clip(bg, 0, 255).astype(np.uint8)


def biblia(spec, seed):
    INK, UL, TITLE = (24, 20, 16, 255), (40, 96, 60, 255), (18, 16, 14, 255)
    X0, MAXT = 110, W - 110 - 130
    cores = spec.get("cores", ["amarelo", "verde", "rosa", "amarelo"])
    pars = [spec["versiculo_texto"]] + spec["reflexao"]

    def build(bs):
        rng = np.random.default_rng(seed)
        out = []
        ft = fit("librebaskerville-700.ttf", 128, [spec["titulo_leitura"]], MAXT)
        L, d = layer(); y = 150
        if spec.get("chamada"):
            fc = font("librebaskerville-400.ttf", 40)
            y = center(d, [spec["chamada"]], fc, y, (90, 70, 50, 255), 1.3, (X0 + X0 + MAXT) / 2)
        y = center(d, [spec["titulo_leitura"]], ft, y, TITLE, 1.25, (X0 + X0 + MAXT) / 2) + 10
        cx = (X0 + X0 + MAXT) / 2
        d.line([(cx - 120, y), (cx - 18, y)], fill=(150, 120, 70, 255), width=2)
        d.line([(cx + 18, y), (cx + 120, y)], fill=(150, 120, 70, 255), width=2)
        d.regular_polygon((cx, y, 9), 4, fill=(150, 120, 70, 255))
        out.append((T_GANCHO, arr(L))); y += 44
        for i, p in enumerate(pars):  # noqa
            verse = i == 0
            fonts = (font("librebaskerville-700.ttf" if verse else "librebaskerville-400.ttf", bs + (2 if verse else 0)),
                     font("lora-bold.ttf", bs + 4))
            lines = _rich_lines(_rich(p), fonts, MAXT)
            Lt, dt = layer(); Lh, dh = layer()
            col = HL[cores[min(i, len(cores) - 1)]]
            y2 = _draw_rich(dt, dh, lines, fonts, X0, y, int(fonts[0].size * 1.42), INK, UL, col, rng)
            # Helo 04/11: todos os textos entram juntos no fade; os grifos passam em sequência
            out.append((0.4 + 0.75 * i, arr(Lh), "wipe")); out.append((T_GANCHO, arr(Lt)))
            y = y2 + int(bs * 0.75)
        return out, y
    return _pagina(seed), _try_sizes(build, [44, 42, 40, 38, 36, 34, 32])


# ---------------- Bíblia fotografada (Helo 04/11/2026: "como se fosse retirado da Bíblia") ----------------
# Página de Bíblia aberta fotografada de cima, título em caixa alta, texto em fonte de Bíblia,
# linhas grifadas de marca-texto laranja. Fundo escuro e leve perspectiva.
def _persp_coeffs(src, dst):
    """coeficientes para Image.transform(PERSPECTIVE): mapeia dst (saída) -> src (entrada)."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def biblia_foto(spec, seed):
    rng = np.random.default_rng(seed)
    SW, SH = 1180, 1900                       # "folha dupla": sobra da página esquerda + página direita
    PX0, PX1 = 210, SW - 150                   # área de texto da página direita
    INK = (22, 18, 14, 255)
    ORANGE = (255, 150, 40)
    cor = HL.get(spec.get("cor"), ORANGE) if spec.get("cor") else ORANGE

    # papel
    paper = np.full((SH, SW, 3), (238, 226, 200), np.float32)
    n = rng.normal(0, 1, (SH // 5, SW // 5)).astype(np.float32)
    n = np.asarray(Image.fromarray(((n * 20) + 128).clip(0, 255).astype(np.uint8)).resize((SW, SH), Image.BICUBIC)).astype(np.float32) - 128
    paper += n[..., None] * 0.2 + rng.normal(0, 3, (SH, SW))[..., None]
    P = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8)); dp = ImageDraw.Draw(P)
    # texto apagado da página esquerda (só a pontinha aparece)
    fl = font("tinos-400.ttf", 30)
    vocab = [w.strip("=_“”\".,;:!?") for p_ in spec["texto"] for w in p_.split()] or ["Senhor"]
    LP = Image.new("RGBA", (150, SH), (0, 0, 0, 0)); dl = ImageDraw.Draw(LP)
    for k, yy in enumerate(range(120, SH - 80, 40)):
        linha = " ".join(vocab[int(i)] for i in rng.integers(0, len(vocab), 9))
        dl.text((-40 - int(rng.integers(0, 60)), yy), linha, font=fl, fill=(120, 110, 95, 255))
    P.paste(LP, (0, 0), LP)
    # números de versículo e cabeçalho na página direita, como numa Bíblia
    def build(bs, top=300):
        out = []
        L, d = layer_s(SW, SH)
        ft = fit("tinos-700.ttf", 118, [spec["titulo_leitura"].upper()], PX1 - PX0)
        d.text((PX0, top - ft.size * 1.1), spec["titulo_leitura"].upper(), font=ft, fill=INK)
        d.line([(PX0, top), (PX1, top)], fill=(40, 32, 26, 255), width=4)
        d.line([(PX0, top + 10), (PX1, top + 10)], fill=(40, 32, 26, 255), width=2)
        fonts = (font("tinos-400.ttf", bs), font("tinos-700.ttf", bs))
        y = top + 40; lh = int(bs * 1.2)
        Lh, dh = layer_s(SW, SH)
        for i, ptxt in enumerate(spec["texto"]):
            lines = _rich_lines(_rich(ptxt), fonts, PX1 - PX0 - 10)
            y = _draw_rich(d, dh, lines, fonts, PX0, y, lh, INK, INK, cor, rng)
            y += int(bs * 0.25)
        return [(0.6, Lh, "wipe"), (T_GANCHO, L)], y

    for bs in [72, 70, 68, 66, 64, 62, 60, 58, 56, 54, 52, 50, 48, 46, 44]:
        raw, bottom = build(bs)
        if bottom <= SH - 220:
            raw, bottom = build(bs, 300 + max(0, (SH - 220 - bottom) // 2))
            break
    else:
        raise SystemExit("Texto longo demais para o estilo biblia-foto.")

    # perspectiva: a folha inclinada levemente, ocupando quase todo o quadro
    j = lambda: rng.uniform(-12, 12)
    dst = [(-150 + j(), 40 + j()), (W + 20 + j(), 10 + j()), (W + 60 + j(), H - 20 + j()), (-110 + j(), H + 10 + j())]
    src = [(0, 0), (SW, 0), (SW, SH), (0, SH)]
    co = _persp_coeffs(src, dst)
    # luz: sombra da lombada (esquerda), centro mais claro, cantos mais escuros
    yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
    gutter = 1 - 0.75 * np.exp(-((xx - 170) / 45) ** 2)
    gutter[:, :170] = np.minimum(gutter[:, :170], 0.55 + 0.35 * (1 - np.exp(-(170 - xx[:, :170]) / 60)))
    light = gutter * (1 - 0.18 * ((xx / SW - 0.6) ** 2 + (yy / SH - 0.45) ** 2) * 2)
    LIGHT = Image.fromarray((np.clip(light, 0, 1) * 255).astype(np.uint8))

    def warp(img, fill):
        return img.transform((W, H), Image.PERSPECTIVE, co, Image.BICUBIC, fillcolor=fill)

    lw = np.asarray(warp(LIGHT, 0)).astype(np.float32)[..., None] / 255
    mask = np.asarray(warp(Image.new("L", (SW, SH), 255), 0)).astype(np.float32)[..., None] / 255
    # fundo: mesa escura
    g = np.linspace(0, 1, H)[:, None, None]
    desk = (np.array([38, 26, 18]) * (1 - g) + np.array([18, 12, 8]) * g) * np.ones((H, W, 3))
    desk += rng.normal(0, 4, (H, W))[..., None]
    page = np.asarray(warp(P, (0, 0, 0))).astype(np.float32) * lw
    bg = desk * (1 - mask) + page * mask
    bg = np.clip(bg, 0, 255).astype(np.uint8)
    layers = []
    for item in raw:
        im = warp(item[1], (0, 0, 0, 0)).filter(ImageFilter.GaussianBlur(0.5))
        a = np.asarray(im).astype(np.float32)
        a[..., :3] *= lw          # a luz da página também escurece o texto e o grifo
        layers.append((item[0], a) + tuple(item[2:]))
    return bg, layers


def layer_s(w, h):
    L = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return L, ImageDraw.Draw(L)
