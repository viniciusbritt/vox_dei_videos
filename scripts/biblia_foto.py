"""Estilo "biblia-foto" (Helo, 04/11/2026): foto realista de uma página de Bíblia com o texto grifado em amarelo.

Imagem PARADA (sem fade, sem animação do grifo); o make_short.py só acrescenta partículas leves e a música.
Vários modelos de página, alternados a cada vídeo (campo "modelo" do spec, ou pelo seed):
  1 "folha-fina"  folha fina de Bíblia em close, texto do verso aparecendo por trás, leve inclinação
  2 "aberta"      Bíblia aberta sobre a mesa, lombada à esquerda, cabeçalho e números de versículo
  3 "antiga"      página envelhecida, moldura de filetes, manchas e bordas queimadas
  4 "branca"      Bíblia de papel branco e borda dourada, duas linhas no título, luz de janela

Spec: {"estilo": "biblia-foto", "modelo": 1-4 (opcional), "titulo_leitura": "Jeremias 29,11",
       "texto": ["parágrafo com ==trecho grifado==", "^11 parágrafo começando com número de versículo", ...]}
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H = 1080, 1920
SS = 2                          # supersampling: a página é desenhada em 2x e reduzida no fim
MODELOS = ["folha-fina", "aberta", "antiga", "branca"]

FILLER = ("O Senhor é a minha luz e a minha salvação, de quem terei medo? Ele me guarda à sombra das suas asas "
          "e me conduz por caminhos retos. Ainda que eu ande pelo vale escuro, não temerei mal algum, porque tu estás "
          "comigo. Bendize, ó minha alma, ao Senhor, e não te esqueças de nenhum dos seus benefícios. Ele perdoa as "
          "tuas culpas e cura todas as tuas enfermidades. Os que esperam no Senhor renovam as suas forças, sobem com "
          "asas como águias, correm e não se cansam. Clamei ao Senhor na minha angústia e ele me respondeu. Tu és o "
          "meu refúgio e a minha fortaleza, o meu Deus, em quem confio. Ensina-nos a contar os nossos dias para que "
          "alcancemos um coração sábio. A tua palavra é lâmpada para os meus pés e luz para o meu caminho.").split()


def F(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), int(size))


def tl(s, f):
    return f.getlength(s)


# ---------------- texto ----------------
def parse(par):
    """'a ==b c== ^11 d' -> lista de palavras [(texto, grifo, sobrescrito)]"""
    out, hl, cur = [], False, ""
    toks = []
    i = 0
    while i < len(par):
        if par[i:i + 2] == "==":
            if cur:
                toks.append((cur, hl)); cur = ""
            hl = not hl; i += 2; continue
        c = par[i]
        if c == " ":
            if cur:
                toks.append((cur, hl)); cur = ""
            toks.append((" ", hl))
        else:
            cur += c
        i += 1
    if cur:
        toks.append((cur, hl))
    words, buf = [], []
    for t, h in toks:
        if t == " ":
            if buf:
                words.append(buf); buf = []
        else:
            buf.append((t, h))
    if buf:
        words.append(buf)
    res = []
    for w in words:
        if w[0][0].startswith("^"):
            res.append([(w[0][0][1:], w[0][1], True)])
        else:
            res.append([(s, h, False) for s, h in w])
    return res


def layout(pars, f, fsup, maxw, lh, gap, justify=True):
    """devolve [(y, [(x, texto, grifo, sup, largura)], fim_de_paragrafo)] e a altura total"""
    sp = tl(" ", f)
    wl = lambda w: sum(tl(s, fsup if u else f) for s, h, u in w)
    y, out = 0, []
    for pi, par in enumerate(pars):
        words = parse(par)
        lines, cur, cw = [], [], 0
        for w in words:
            L = wl(w)
            if cur and cw + sp + L > maxw:
                lines.append((cur, cw)); cur, cw = [w], L
            else:
                cw = cw + (sp if cur else 0) + L; cur.append(w)
        if cur:
            lines.append((cur, cw))
        for li, (ln, cw) in enumerate(lines):
            last = li == len(lines) - 1
            extra = (maxw - cw) / (len(ln) - 1) if justify and not last and len(ln) > 1 else 0
            if extra > sp * 2.0:
                extra = 0
            x, segs = 0, []
            for wi, w in enumerate(ln):
                if wi:
                    g = sp + extra
                    segs.append((x, " ", w[0][1] and ln[wi - 1][-1][1], False, g)); x += g
                for s, h, u in w:
                    ff = fsup if u else f; L = tl(s, ff)
                    segs.append((x, s, h, u, L)); x += L
            out.append((y, segs, last))
            y += lh
        y += gap
    return out, y - gap


def draw_text(d, lines, x0, y0, f, fsup, ink, sup_ink):
    for y, segs, _ in lines:
        for x, s, h, u, L in segs:
            if s == " ":
                continue
            if u:
                d.text((x0 + x, y0 + y - f.size * 0.05), s, font=fsup, fill=sup_ink)
            else:
                d.text((x0 + x, y0 + y), s, font=f, fill=ink)


def hl_mask(shape, lines, x0, y0, f, rng):
    """máscara (0-1) do marca-texto: faixas irregulares, com riscos e pontas mais carregadas"""
    Hh, Ww = shape
    M = Image.new("L", (Ww, Hh), 0); d = ImageDraw.Draw(M)
    size = f.size
    bb = f.getbbox("ÁgjÉ")
    top_o, bot_o = bb[1] - size * 0.10, bb[3] + size * 0.10
    for y, segs, _ in lines:
        runs, run = [], None
        for x, s, h, u, L in segs:
            if h:
                run = [x, x + L] if run is None else [run[0], x + L]
            elif run is not None:
                runs.append(run); run = None
        if run is not None:
            runs.append(run)
        for a, b in runs:
            xa, xb = x0 + a - rng.uniform(4, 12) * SS, x0 + b + rng.uniform(4, 14) * SS
            ta = y0 + y + top_o + rng.uniform(-3, 3) * SS
            tb = ta + rng.uniform(-4, 4) * SS                     # faixa um pouco torta
            ba, bb_ = y0 + y + bot_o + rng.uniform(-3, 3) * SS, y0 + y + bot_o + rng.uniform(-3, 3) * SS
            tb += 0; bb_ += tb - ta
            pts = [(xa + rng.uniform(-3, 3) * SS, ta), (xb, tb), (xb + rng.uniform(-5, 2) * SS, bb_),
                   (xa + rng.uniform(-2, 4) * SS, ba)]
            d.polygon(pts, fill=int(rng.uniform(205, 230)))
            # pontas com tinta dobrada (quem grifa volta a caneta no começo e no fim)
            for xe in (xa, xb - rng.uniform(10, 22) * SS):
                w_ = rng.uniform(10, 22) * SS
                d.polygon([(xe, ta + (tb - ta) * (xe - xa) / max(1, xb - xa)), (xe + w_, ta + (tb - ta) * (xe + w_ - xa) / max(1, xb - xa)),
                           (xe + w_, ba + (bb_ - ba) * (xe + w_ - xa) / max(1, xb - xa)), (xe, ba + (bb_ - ba) * (xe - xa) / max(1, xb - xa))],
                          fill=255)
    m = np.asarray(M).astype(np.float32) / 255
    # riscos horizontais da ponta do marca-texto (variam na vertical, quase constantes na horizontal)
    streak = rng.normal(0, 1, (Hh // (3 * SS) + 2, Ww // (60 * SS) + 2)).astype(np.float32)
    streak = np.asarray(Image.fromarray(((streak * 40) + 128).clip(0, 255).astype(np.uint8)).resize((Ww, Hh), Image.BICUBIC)).astype(np.float32)
    m = m * (0.86 + (streak - 128) / 128 * 0.16)
    M2 = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2 * SS))
    return np.asarray(M2).astype(np.float32) / 255


# ---------------- papel ----------------
def noise(shape, cell, rng, amp=1.0):
    Hh, Ww = shape
    n = rng.normal(0, 1, (max(2, Hh // cell), max(2, Ww // cell))).astype(np.float32)
    im = Image.fromarray(((n * 30) + 128).clip(0, 255).astype(np.uint8)).resize((Ww, Hh), Image.BICUBIC)
    return (np.asarray(im).astype(np.float32) - 128) / 30 * amp


def paper(shape, base, rng, fiber=1.0, stains=0.0):
    Hh, Ww = shape
    p = np.ones((Hh, Ww, 3), np.float32) * np.array(base, np.float32)
    p += (noise(shape, 90 * SS, rng, 3.0) + noise(shape, 14 * SS, rng, 1.6 * fiber) +
          rng.normal(0, 1.8 * fiber, (Hh, Ww)).astype(np.float32))[..., None]
    if stains:
        s = np.clip(noise(shape, 160 * SS, rng, 1.0) + noise(shape, 50 * SS, rng, 0.5) - 0.6, 0, None)
        p *= (1 - stains * s * np.array([0.10, 0.16, 0.28]))[None] if False else (1 - stains * s[..., None] * np.array([0.10, 0.16, 0.28]))
    return p


def show_through(shape, f, rng, alpha, mirror=True, x0=0, maxw=None, lh=None):
    """texto da outra face da folha aparecendo por transparência"""
    Hh, Ww = shape
    L = Image.new("L", (Ww, Hh), 0); d = ImageDraw.Draw(L)
    lh = lh or int(f.size * 1.18)
    k = int(rng.integers(0, len(FILLER)))
    y = int(rng.uniform(0.3, 1.0) * lh)
    maxw = maxw or Ww
    while y < Hh:
        line, w = [], 0
        while True:
            wd = FILLER[k % len(FILLER)]; L_ = tl(wd + " ", f)
            if w + L_ > maxw:
                break
            line.append(wd); w += L_; k += 1
        d.text((x0, y), " ".join(line), font=f, fill=255)
        y += lh
    if mirror:
        L = L.transpose(Image.FLIP_LEFT_RIGHT)
    L = L.filter(ImageFilter.GaussianBlur(3.0 * SS))
    return np.asarray(L).astype(np.float32)[..., None] / 255 * alpha


# ---------------- geometria (página -> foto) ----------------
def sample(img, U, V):
    """amostragem bilinear de img (h, w, c) nas coordenadas U (x), V (y)"""
    h, w = img.shape[:2]
    U = np.clip(U, 0, w - 1.001); V = np.clip(V, 0, h - 1.001)
    x0 = U.astype(np.int32); y0 = V.astype(np.int32)
    fx = (U - x0)[..., None]; fy = (V - y0)[..., None]
    a = img[y0, x0]; b = img[y0, x0 + 1]; c = img[y0 + 1, x0]; d = img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def downs(a):
    h, w = a.shape[:2]
    return a.reshape(h // SS, SS, w // SS, SS, -1).mean(axis=(1, 3))


def desk(rng, tone):
    Hh, Ww = H * SS, W * SS
    g = np.linspace(0, 1, Hh)[:, None, None]
    base = np.array(tone[0], np.float32) * (1 - g) + np.array(tone[1], np.float32) * g
    wood = noise((Hh, Ww), 8 * SS, rng, 1.0)
    grain = np.asarray(Image.fromarray(((wood * 40) + 128).clip(0, 255).astype(np.uint8)).resize((Ww // 40, Hh), Image.BILINEAR)
                       .resize((Ww, Hh), Image.BICUBIC)).astype(np.float32) - 128
    return base * np.ones((Hh, Ww, 3)) + grain[..., None] * 0.10 + rng.normal(0, 2, (Hh, Ww, 1))


def grade(img, rng, warm=(1.03, 1.0, 0.93), vign=0.35, hot=(0.55, 0.35), dof=0.0):
    """luz, vinheta, foco raso e granulação de foto (img em resolução final)"""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = ((xx / W - hot[0]) ** 2 * 1.4 + (yy / H - hot[1]) ** 2) ** 0.5
    light = 1.06 - vign * np.clip(r - 0.15, 0, None) ** 1.5 * 1.6
    out = img * light[..., None] * np.array(warm)
    if dof:
        bl = np.asarray(Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(dof))).astype(np.float32)
        k = np.clip((np.abs(yy / H - 0.47) - 0.36) / 0.12, 0, 1)[..., None]
        out = out * (1 - k) + bl * k
    out += rng.normal(0, 2.6, out.shape)
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------- modelos ----------------
CFG = {
    "folha-fina": dict(paper=(232, 226, 208), ink=(30, 27, 24), body="tinos-400.ttf", head="tinos-700.ttf",
                       hl=(255, 232, 64), fiber=0.7, stains=0.0, through=0.06, x0=70, x1=965, top=150, bottom=1690,
                       sizes=range(86, 39, -2), lh=1.13, rot=-1.6, gut=(-120, 140), desk=((40, 30, 22), (20, 14, 10)),
                       edge_r=1020, edge_t=None, edge_b=None),
    "aberta": dict(paper=(240, 228, 198), ink=(34, 28, 22), body="tinos-400.ttf", head="librebaskerville-700.ttf",
                   hl=(255, 228, 60), fiber=1.0, stains=0.25, through=0.045, x0=250, x1=1000, top=250, bottom=1660,
                   sizes=range(74, 33, -2), lh=1.17, rot=0.9, gut=(150, 120), desk=((52, 36, 24), (24, 16, 10)),
                   edge_r=1050, edge_t=70, edge_b=1840),
    "antiga": dict(paper=(226, 204, 160), ink=(46, 32, 20), body="librebaskerville-400.ttf", head="librebaskerville-700.ttf",
                   hl=(255, 226, 56), fiber=1.3, stains=0.5, through=0.05, x0=125, x1=955, top=230, bottom=1640,
                   sizes=range(70, 31, -2), lh=1.30, rot=-0.8, gut=(-200, 100), desk=((30, 22, 16), (14, 10, 8)),
                   edge_r=1035, edge_t=55, edge_b=1860, edge_l=40),
    "branca": dict(paper=(246, 244, 238), ink=(26, 26, 28), body="tinos-400.ttf", head="tinos-700.ttf",
                   hl=(255, 236, 70), fiber=0.5, stains=0.0, through=0.05, x0=95, x1=960, top=330, bottom=1680,
                   sizes=range(82, 37, -2), lh=1.15, rot=1.3, gut=(-90, 130), desk=((70, 62, 58), (34, 30, 30)),
                   edge_r=1010, edge_t=120, edge_b=None, gold=True),
}


def render(spec, seed):
    rng = np.random.default_rng(seed)
    nm = spec.get("modelo")
    if isinstance(nm, int):
        nm = MODELOS[(nm - 1) % len(MODELOS)]
    nm = nm or MODELOS[seed % len(MODELOS)]
    c = CFG[nm]
    PH, PW = H * SS, W * SS
    P = paper((PH, PW), c["paper"], rng, c["fiber"], c["stains"])
    pg = Image.new("L", (PW, PH), 0); dp = ImageDraw.Draw(pg)      # tinta (para multiplicar)
    title = spec["titulo_leitura"]
    x0, x1 = c["x0"] * SS, c["x1"] * SS
    maxw = x1 - x0
    # ---- cabeçalho por modelo
    if nm == "folha-fina":
        ft = F(c["head"], 120 * SS)
        while tl(title.upper(), ft) > maxw * 0.98:
            ft = F(c["head"], ft.size - 4)
        cx = (x0 + x1) / 2
        dp.text((cx - tl(title.upper(), ft) / 2, c["top"] * SS), title.upper(), font=ft, fill=255)
        ytxt = c["top"] * SS + ft.size * 1.12
        dp.line([(x0, ytxt), (x1, ytxt)], fill=235, width=3 * SS)
        ytxt += 26 * SS
    elif nm == "aberta":
        livro = title.split()[0] if title.split() else title
        fh = F("tinos-400.ttf", 30 * SS)
        cap = title.split()[-1].split(",")[0] if any(ch.isdigit() for ch in title) else ""
        dp.text((x0, c["top"] * SS - 120 * SS), f"{livro.upper()} {cap}", font=fh, fill=200)
        dp.text((x1 - tl(cap, fh), c["top"] * SS - 120 * SS), cap, font=fh, fill=200)
        dp.line([(x0, c["top"] * SS - 78 * SS), (x1, c["top"] * SS - 78 * SS)], fill=170, width=2 * SS)
        ft = F(c["head"], 96 * SS)
        while tl(title, ft) > maxw * 0.98:
            ft = F(c["head"], ft.size - 4)
        dp.text((x0, c["top"] * SS - 40 * SS), title, font=ft, fill=255)
        ytxt = c["top"] * SS - 40 * SS + ft.size * 1.35
        # página esquerda: texto normal, entrando na lombada (só a ponta aparece)
        fl = F("tinos-400.ttf", 34 * SS)
        gx = c["gut"][0] * SS
        LP = Image.new("L", (240 * SS, PH), 0); dl = ImageDraw.Draw(LP)
        k = int(rng.integers(0, len(FILLER))); yy = c["top"] * SS - 40 * SS
        while yy < c["bottom"] * SS + 120 * SS:
            dl.text((-int(rng.uniform(0, 80)) * SS, yy), " ".join(FILLER[(k + i) % len(FILLER)] for i in range(9)), font=fl, fill=240)
            k += 7; yy += int(34 * SS * 1.17)
        pg.paste(LP, (gx - 200 * SS, 0), LP); dp = ImageDraw.Draw(pg)
    elif nm == "antiga":
        # moldura de filetes duplos
        bx0, bx1, by0, by1 = (x0 - 45 * SS, x1 + 45 * SS, c["top"] * SS - 150 * SS, c["bottom"] * SS + 70 * SS)
        for k, wdt in ((0, 4), (14, 2)):
            dp.rectangle([bx0 + k * SS, by0 + k * SS, bx1 - k * SS, by1 - k * SS], outline=210, width=wdt * SS)
        ft = F(c["head"], 104 * SS)
        while tl(title, ft) > maxw * 0.95:
            ft = F(c["head"], ft.size - 4)
        cx = (x0 + x1) / 2
        dp.text((cx - tl(title, ft) / 2, c["top"] * SS - 95 * SS), title, font=ft, fill=255)
        ytxt = c["top"] * SS - 95 * SS + ft.size * 1.3
        dp.line([(cx - 160 * SS, ytxt), (cx + 160 * SS, ytxt)], fill=200, width=2 * SS)
        ytxt += 34 * SS
    else:  # branca
        ft = F(c["head"], 112 * SS)
        while tl(title, ft) > maxw * 0.98:
            ft = F(c["head"], ft.size - 4)
        fs = F("tinos-400.ttf", 40 * SS)
        chamada = spec.get("chamada", "Palavra do Senhor")
        dp.text((x0, c["top"] * SS - 170 * SS), chamada.upper(), font=fs, fill=150)
        dp.text((x0, c["top"] * SS - 120 * SS), title, font=ft, fill=255)
        ytxt = c["top"] * SS - 120 * SS + ft.size * 1.2
        dp.line([(x0, ytxt), (x0 + 220 * SS, ytxt)], fill=230, width=5 * SS)
        ytxt += 34 * SS
    # ---- corpo do texto (maior tamanho que caiba)
    avail = c["bottom"] * SS - ytxt
    for s in c["sizes"]:
        f = F(c["body"], s * SS); fsup = F("tinos-700.ttf", s * SS * 0.55)
        lines, hgt = layout(spec["texto"], f, fsup, maxw, int(s * SS * c["lh"]), int(s * SS * 0.28))
        if hgt <= avail:
            break
    else:
        raise SystemExit("Texto longo demais para o estilo biblia-foto.")
    ytxt += max(0, (avail - hgt) * 0.5)
    draw_text(dp, lines, x0, ytxt, f, fsup, 255, 255)
    ink = np.asarray(pg.filter(ImageFilter.GaussianBlur(0.55 * SS))).astype(np.float32)[..., None] / 255
    ink *= (0.9 + 0.1 * noise((PH, PW), 6 * SS, rng, 0.6)[..., None]).clip(0.7, 1.05)   # tinta irregular
    # ---- composição da página: papel x verso x tinta x marca-texto (multiplicação)
    through = show_through((PH, PW), F(c["body"], f.size / SS * SS), rng, c["through"], True, x0=PW - x1, maxw=maxw)
    page = P * (1 - through * 0.55)
    page = page * (1 - ink) + np.array(c["ink"], np.float32) * ink
    hm = hl_mask((PH, PW), lines, x0, ytxt, f, rng)[..., None]
    hlc = np.array(c["hl"], np.float32) / 255
    page = page * (1 - hm + hm * hlc)
    if c.get("stains"):
        burn = np.zeros((PH, PW), np.float32)
        yy, xx = np.mgrid[0:PH, 0:PW].astype(np.float32)
        dedge = np.minimum.reduce([xx - c.get("edge_l", 0) * SS, (c["edge_r"] * SS) - xx,
                                   yy - (c["edge_t"] or 0) * SS, (c["edge_b"] or H) * SS - yy]) / SS
        burn = np.exp(-np.clip(dedge, 0, None) / 55) * (0.4 + 0.25 * noise((PH, PW), 40 * SS, rng, 1.0)) * c["stains"]
        page *= (1 - np.clip(burn, 0, 0.7)[..., None] * np.array([0.35, 0.45, 0.6]))
        del yy, xx, dedge
    # ---- foto: rotação + curvatura da lombada + sombra
    oy, ox = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32)
    cxo, cyo = W * SS / 2, H * SS / 2
    a = np.deg2rad(c["rot"])
    U = (ox - cxo) * np.cos(a) + (oy - cyo) * np.sin(a) + cxo
    V = -(ox - cxo) * np.sin(a) + (oy - cyo) * np.cos(a) + cyo
    del ox, oy
    gx, gL = c["gut"][0] * SS, c["gut"][1] * SS
    du = np.clip(U - gx, 0, None)
    bend = np.exp(-du / gL)
    V = V + bend * 60 * SS * ((V - cyo) / cyo) * -0.5            # linhas curvam junto da lombada
    U = U - bend * 30 * SS
    pageimg = sample(page.astype(np.float32), U, V)
    shade = (1 - 0.62 * np.exp(-du / (gL * 0.55))) * (1 + 0.05 * np.exp(-((du - gL * 1.4) / gL) ** 2))
    pageimg *= shade[..., None]
    # máscara da folha
    inside = np.ones_like(U)
    soft = 1.2 * SS
    if c.get("edge_r"):
        inside *= np.clip((c["edge_r"] * SS - U) / soft, 0, 1)
    if c.get("edge_t") is not None:
        inside *= np.clip((V - c["edge_t"] * SS) / soft, 0, 1)
    if c.get("edge_b") is not None:
        inside *= np.clip((c["edge_b"] * SS - V) / soft, 0, 1)
    if c.get("edge_l") is not None:
        inside *= np.clip((U - c["edge_l"] * SS) / soft, 0, 1)
    if nm == "aberta":
        inside = np.where(U < gx, np.clip((U - (gx - 130 * SS)) / soft, 0, 1) * inside, inside)
        # página esquerda: escurecida e um pouco mais curva
        pageimg = np.where((U < gx)[..., None], pageimg * (0.45 + 0.45 * np.clip((gx - U) / (130 * SS), 0, 1))[..., None], pageimg)
    D = desk(rng, c["desk"])
    # sombra da folha na mesa
    sh = Image.fromarray((inside * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14 * SS))
    shm = np.asarray(sh).astype(np.float32)[..., None] / 255
    shm = np.roll(np.roll(shm, 10 * SS, 0), 8 * SS, 1)
    D = D * (1 - 0.6 * shm)
    # folhas empilhadas na borda (miolo da Bíblia)
    if c.get("edge_r"):
        er = c["edge_r"] * SS
        stack = ((U > er) & (U < er + 16 * SS)).astype(np.float32)
        lines_ = 0.75 + 0.25 * np.sin((U - er) / (2.2 * SS) * np.pi) ** 2
        col = np.array([214, 190, 120] if c.get("gold") else [205, 192, 168], np.float32)
        D = D * (1 - stack[..., None]) + (col * lines_[..., None] * 0.8) * stack[..., None]
    out = D * (1 - inside[..., None]) + pageimg * inside[..., None]
    del U, V, du, bend, shade, pageimg, D, P, page
    out = downs(out.astype(np.float32))
    return grade(out, rng, hot=(0.58, 0.32) if nm != "antiga" else (0.5, 0.45),
                 vign=0.45 if nm in ("aberta", "antiga") else 0.32, dof=2.2 if nm == "aberta" else 0), nm
