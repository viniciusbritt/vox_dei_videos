"""Short de Bíblia no molde "Fábio Pires" (Mentor, 19/11): 10 s, texto cobrindo a tela,
frase de abertura + referência grande + versículo + aplicação + "escreva Amém", 2-3 marca-textos verde-limão,
fundo DIFERENTE a cada vídeo. Tudo aparece desde o quadro 0 (o feed decide em 0-3 s). Música: piano de sempre.

Spec (json): saida, nome, duracao (10), fundo (pergaminho|por-do-sol|vela|ceu|lapis|preto-branco), musica (aurora|ceu-azul|graca|alvorada|luz|esperanca),
 abertura, referencia, versiculo, aplicacao (lista), cta. Marca-texto: ==assim==.
Uso: python3 scripts/make_fabio.py specs/fabio/NOME.json
"""
import json, os, re, subprocess, sys, tempfile, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_short, musica_louvor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "fonts")
W, H, FPS = 1080, 1920, 30
LIME = (186, 244, 108)
X_MARGIN, TOP, BOTTOM = 110, 190, 1560      # zona segura: fora dos botões e da legenda do Short


def fnt(n, s):
    return ImageFont.truetype(os.path.join(FONTS, n), int(s))


# ---------------------------------------------------------------- fundos
def _grad(top, bot, gamma=1.0):
    t = (np.linspace(0, 1, H) ** gamma)[:, None, None]
    return np.repeat(np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t, W, axis=1)


def _vig(img, k=0.35):
    y = np.linspace(-1, 1, H)[:, None]; x = np.linspace(-1, 1, W)[None, :]
    v = np.clip(1 - k * (x ** 2 + (y * 0.9) ** 2) ** 1.3, 0.4, 1)
    return img * v[..., None]


def _glow(cx, cy, r, color, strength):
    y = np.arange(H)[:, None]; x = np.arange(W)[None, :]
    g = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * r * r)))
    return g[..., None] * np.array(color, np.float32) * strength


def _noise(rng, amp, scale=8, blur=14):
    n = rng.normal(0, 1, (H // scale, W // scale)).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 40 + 128).clip(0, 255).astype(np.uint8))
                   .resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) - 128
    return n[..., None] * amp / 40


def bg_pergaminho(rng):
    """Bege liso com folha de papel creme no meio (cartão escrito)."""
    base = _grad((214, 176, 138), (200, 160, 122)) + _noise(rng, 6)
    return _vig(base, 0.25), dict(card=True, ink=(28, 20, 14), accent=(28, 20, 14))


def bg_por_do_sol(rng):
    base = _grad((255, 196, 96), (250, 150, 120), 1.2)
    base += _glow(540, 1250, 420, (255, 240, 190), 0.9) + _glow(540, 1250, 900, (255, 170, 90), 0.35)
    # faixas de nuvem
    for i in range(7):
        cy = rng.uniform(250, 1700); cw = rng.uniform(500, 1100)
        y = np.arange(H)[:, None]; x = np.arange(W)[None, :]
        c = np.exp(-(((x - rng.uniform(100, 980)) / cw * 2) ** 2 + ((y - cy) / 26) ** 2))
        base += c[..., None] * np.array([255, 225, 190], np.float32) * 0.22
    base = np.asarray(Image.fromarray(base.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32)
    return _vig(base, 0.18), dict(card=False, ink=(70, 30, 12), accent=(70, 30, 12))


def bg_ceu(rng):
    base = _grad((92, 160, 230), (205, 228, 250), 0.9)
    for i in range(14):
        cx, cy = rng.uniform(0, W), rng.uniform(150, 1750); r = rng.uniform(120, 300)
        base += _glow(cx, cy, r, (255, 255, 255), rng.uniform(0.25, 0.5))
        base += _glow(cx + r * 0.7, cy + r * 0.1, r * 0.8, (255, 255, 255), 0.25)
    base += _glow(850, 150, 330, (255, 255, 235), 0.55)
    return _vig(base, 0.12), dict(card=False, ink=(14, 36, 70), accent=(14, 36, 70))


def bg_vela(rng):
    base = _grad((14, 10, 10), (30, 16, 8), 1.0)
    base += _glow(540, 1640, 520, (255, 150, 50), 0.9) + _glow(540, 1640, 1100, (190, 80, 20), 0.35)
    for i in range(26):         # bokeh
        cx, cy = rng.uniform(0, W), rng.uniform(1100, 1900); r = rng.uniform(14, 48)
        base += _glow(cx, cy, r, (255, 190, 90), rng.uniform(0.08, 0.2))
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((500, 1640, 580, 1860), 14, fill=(236, 220, 190))                 # vela
    d.ellipse((520, 1625, 560, 1650), fill=(255, 210, 120))
    fl = Image.new("L", (W, H), 0); fd = ImageDraw.Draw(fl)
    fd.ellipse((518, 1535, 562, 1640), fill=255)
    fl = fl.filter(ImageFilter.GaussianBlur(7))
    base = np.asarray(im, np.float32)
    base += (np.asarray(fl, np.float32) / 255)[..., None] * np.array([255, 200, 90], np.float32) * 0.9
    base += _glow(540, 1590, 90, (255, 220, 140), 0.7)
    return _vig(base, 0.2), dict(card=False, ink=(246, 236, 220), accent=(246, 236, 220), dark=True)


def bg_lapis(rng):
    """Papel claro com desenho a lápis (traços) nas laterais, estilo caderno de artista."""
    base = _grad((238, 236, 232), (222, 220, 216)) + _noise(rng, 5)
    im = Image.fromarray(base.clip(0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    for _ in range(260):         # rabiscos de grafite
        x0 = rng.uniform(0, W); y0 = rng.uniform(1300, H)
        pts = [(x0 + k * rng.uniform(8, 20), y0 + k * rng.uniform(-30, 5)) for k in range(5)]
        d.line(pts, fill=(int(rng.integers(120, 170)),) * 3, width=int(rng.integers(1, 3)))
    base = np.asarray(im.filter(ImageFilter.GaussianBlur(1.1)), np.float32)
    return _vig(base, 0.2), dict(card=False, ink=(30, 30, 32), accent=(30, 30, 32))


def bg_preto_branco(rng):
    base = _grad((60, 60, 62), (14, 14, 16)) + _glow(540, 350, 520, (200, 200, 200), 0.55) + _noise(rng, 6)
    return _vig(base, 0.4), dict(card=False, ink=(240, 240, 240), accent=(240, 240, 240), dark=True)


FUNDOS = {"pergaminho": bg_pergaminho, "por-do-sol": bg_por_do_sol, "ceu": bg_ceu, "vela": bg_vela,
          "lapis": bg_lapis, "preto-branco": bg_preto_branco}


# ---------------------------------------------------------------- texto
def words_of(text):
    """'==a b== c' -> [(palavra, destaque)]; pontuação colada fica junto da palavra anterior."""
    out, hl, glued = [], False, False
    for tok in re.split(r"(==)", text):
        if tok == "==":
            hl = not hl; continue
        if not tok:
            continue
        ws = tok.split()
        if out and glued and not tok[0].isspace():
            w, h = out[-1]; out[-1] = (w + ws[0], h); ws = ws[1:]
        out += [(w, hl) for w in ws]
        glued = not tok[-1].isspace()
    return out


def wrap(words, font, maxw):
    lines, cur = [], []
    sp = font.getlength(" ")
    for w, h in words:
        trial = cur + [(w, h)]
        width = sum(font.getlength(x) for x, _ in trial) + sp * (len(trial) - 1)
        if cur and width > maxw:
            lines.append(cur); cur = [(w, h)]
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def build(spec, scale, ink):
    """Retorna lista de linhas (cada linha: palavras, fonte, cor, alinhamento, espaço antes)."""
    f_open = fnt("lora-italic.ttf", 50 * scale)
    f_ref = fnt("playfairdisplay-900.ttf", 112 * scale)
    f_verse = fnt("lora-bold.ttf", 54 * scale)
    f_app = fnt("lora-medium.ttf", 48 * scale)
    f_cta = fnt("lora-bold.ttf", 56 * scale)
    mw = W - 2 * X_MARGIN
    rows = []

    def add(text, font, gap, align="center", lh=1.28):
        for i, ln in enumerate(wrap(words_of(text), font, mw)):
            rows.append(dict(words=ln, font=font, gap=gap if i == 0 else 0, align=align, lh=lh))

    add(spec["abertura"], f_open, 0)
    add(spec["referencia"], f_ref, 18, lh=1.1)
    add(spec["versiculo"], f_verse, 34, lh=1.3)
    for i, a in enumerate(spec["aplicacao"]):
        add(a, f_app, 40 if i == 0 else 26)
    add(spec["cta"], f_cta, 46)
    total = sum(r["gap"] + int(r["font"].size * r["lh"]) for r in rows)
    return rows, total


def render_text(spec, accent, dark):
    avail = BOTTOM - TOP
    scale = 1.25
    while True:
        rows, total = build(spec, scale, accent)
        if total <= avail or scale < 0.6:
            break
        scale -= 0.02
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hlayer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d, hd = ImageDraw.Draw(layer), ImageDraw.Draw(hlayer)
    y = TOP + (avail - total) // 2
    rng = np.random.default_rng(7)
    bounds = [y, y]
    for r in rows:
        y += r["gap"]; f = r["font"]; sp = f.getlength(" ")
        lw = sum(f.getlength(w) for w, _ in r["words"]) + sp * (len(r["words"]) - 1)
        x = (W - lw) / 2 if r["align"] == "center" else X_MARGIN
        lh = int(f.size * r["lh"]); asc, desc = f.getmetrics()
        # marca-texto (corre antes do texto, atrás)
        i = 0; xs = []
        for w, h in r["words"]:
            wl = f.getlength(w); xs.append((x, x + wl, h)); x += wl + sp
        i = 0
        while i < len(xs):
            if xs[i][2]:
                j = i
                while j + 1 < len(xs) and xs[j + 1][2]:
                    j += 1
                x0, x1 = xs[i][0] - 10, xs[j][1] + 10
                top, bot = y + (lh - (asc + desc)) // 2 + int(asc * 0.12), y + (lh - (asc + desc)) // 2 + asc + desc - int(desc * 0.2)
                hd.rounded_rectangle((x0, top + rng.integers(-2, 3), x1, bot + rng.integers(-2, 3)), radius=10, fill=LIME + (235,))
                i = j + 1
            else:
                i += 1
        for (x0, x1, h), (w, _) in zip(xs, r["words"]):
            d.text((x0, y + (lh - (asc + desc)) // 2), w, font=f, fill=((24, 24, 20) if h else accent) + (255,))
        bounds[1] = y + lh
        y += lh
    return layer, hlayer, (bounds[0], bounds[1], scale)


def card_layer(box):
    top, bot = box[0] - 70, box[1] + 70
    x0, x1 = 50, W - 50
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((x0 + 8, top + 14, x1 + 8, bot + 14), 14, fill=(40, 20, 8, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    rng = np.random.default_rng(3)
    paper = np.full((H, W, 3), (247, 238, 214), np.float32) + _noise(rng, 5, 6, 10) + rng.normal(0, 2.5, (H, W, 1))
    ph = Image.fromarray(paper.clip(0, 255).astype(np.uint8)).convert("RGBA")
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).rounded_rectangle((x0, top, x1, bot), 12, fill=255)
    ph.putalpha(mask)
    return sh, ph


# ---------------------------------------------------------------- molde "grifado" (Helo 19/11, ref. João 16:33 / Mateus 21:22)
def bg_biblia_desfocada(rng, modelo=2, zoom=1.35, rot=-4, quente=True):
    import biblia_foto as bf
    BG, _ = bf.render({"titulo_leitura": "Salmo 27,1", "modelo": modelo,
                       "texto": [" ".join(bf.FILLER[:70]), " ".join(bf.FILLER[30:100])]},
                      int(rng.integers(1 << 30)))
    im = Image.fromarray(BG).rotate(rot, Image.BICUBIC, expand=False, fillcolor=(40, 28, 18))
    cw, ch = int(W / zoom), int(H / zoom)
    x0, y0 = (W - cw) // 2, int((H - ch) * 0.85)
    im = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(11))
    a = np.asarray(im, np.float32)
    a = a * np.array([1.0, 0.93, 0.80]) + np.array([12, 4, -8]) if quente else a * np.array([0.97, 0.99, 1.03])
    return _vig(a, 0.45), dict(card=False)


def bg_cartao_bege(rng):
    base = _grad((214, 178, 140), (198, 160, 122)) + _noise(rng, 6)
    return _vig(base, 0.22), dict(card=True)


FUNDOS.update({"biblia-desfocada": lambda r: bg_biblia_desfocada(r, 2, 1.35, -4),
               "biblia-antiga": lambda r: bg_biblia_desfocada(r, 3, 1.5, 3),
               "biblia-branca": lambda r: bg_biblia_desfocada(r, 4, 1.4, -2, False),
               "cartao-bege": bg_cartao_bege})


def render_grifado(spec):
    """Texto preto grande, TODAS as linhas grifadas em verde-limão (linha a linha), sem abertura."""
    ink = (12, 12, 10, 255)
    mw = W - 2 * X_MARGIN - 20
    def rows_for(sc):
        f_ref = fnt("tinos-700.ttf", 118 * sc); f_txt = fnt("tinos-700.ttf", 70 * sc)
        rows = []
        for i, (txt, f, gap) in enumerate([(spec["referencia"], f_ref, 0), (spec["versiculo"], f_txt, 40)] +
                                           [(a, f_txt, 30) for a in spec["aplicacao"]] + [(spec["cta"], f_txt, 30)]):
            txt = txt.replace("==", "")
            ws = words_of(txt); n0 = len(wrap(ws, f, mw)); lo, hi = mw * 0.4, mw
            while hi - lo > 4:                       # quebra equilibrada: menor largura com o mesmo nº de linhas
                mid_ = (lo + hi) / 2
                if len(wrap(ws, f, mid_)) > n0: lo = mid_
                else: hi = mid_
            for k, ln in enumerate(wrap(ws, f, hi)):
                rows.append((" ".join(w for w, _ in ln), f, gap if k == 0 else 0))
        total = sum(g + int(f.size * 1.18) for _, f, g in rows)
        return rows, total
    sc = 1.3
    while True:
        rows, total = rows_for(sc)
        if total <= BOTTOM - TOP or sc < 0.6:
            break
        sc -= 0.02
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    y = TOP + (BOTTOM - TOP - total) // 2; top0 = y
    for txt, f, gap in rows:
        y += gap; lh = int(f.size * 1.18); asc, desc = f.getmetrics()
        lw = f.getlength(txt); x = (W - lw) / 2
        ty = y + (lh - asc - desc) // 2
        d.rounded_rectangle((x - 16, y + 2, x + lw + 16, y + lh - 2), radius=12, fill=LIME + (240,))
        d.text((x, ty), txt, font=f, fill=ink)
        y += lh
    return layer, (top0, y, sc)


def render_quadro(texto, big=False):
    """Um quadro de texto grande e centralizado (teste em 7-8 s): todas as linhas grifadas."""
    ink = (12, 12, 10, 255); mw = W - 2 * X_MARGIN - 20
    def rows_for(sc):
        f = fnt("tinos-700.ttf", (104 if big else 82) * sc); rows = []
        for blk in texto.split("\n"):
            ws = words_of(blk.replace("==", "")); n0 = len(wrap(ws, f, mw)); lo, hi = mw * 0.4, mw
            while hi - lo > 4:
                m_ = (lo + hi) / 2
                if len(wrap(ws, f, m_)) > n0: lo = m_
                else: hi = m_
            for k, ln in enumerate(wrap(ws, f, hi)):
                rows.append((" ".join(w for w, _ in ln), f, 34 if k == 0 and rows else 0))
        return rows, sum(g + int(f.size * 1.2) for _, f, g in rows)
    sc = 1.3
    while True:
        rows, total = rows_for(sc)
        if total <= BOTTOM - TOP - 200 or sc < 0.6:
            break
        sc -= 0.02
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    y = TOP + 100 + (BOTTOM - TOP - 200 - total) // 2
    for txt, f, gap in rows:
        y += gap; lh = int(f.size * 1.2); asc, desc = f.getmetrics(); lw = f.getlength(txt); x = (W - lw) / 2
        d.rounded_rectangle((x - 16, y + 2, x + lw + 16, y + lh - 2), radius=12, fill=LIME + (240,))
        d.text((x, y + (lh - asc - desc) // 2), txt, font=f, fill=ink); y += lh
    return layer


def main(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    outdir = os.path.join(ROOT, spec["saida"]); os.makedirs(outdir, exist_ok=True)
    name = spec["nome"]; seed = zlib.crc32(name.encode()); rng = np.random.default_rng(seed)
    DUR = int(spec.get("duracao", 10))
    bg, st = FUNDOS[spec["fundo"]](rng)
    quadros = None
    if spec.get("molde") == "quadros":
        text = hl = None; box = (0, 0, 0)
        quadros = [(q["t0"], q["t1"], render_quadro(q["texto"], q.get("grande", False))) for q in spec["quadros"]]
    elif spec.get("molde", "grifado") == "grifado":
        text, box = render_grifado(spec); hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    else:
        text, hl, box = render_text(spec, st["accent"], st.get("dark", False))
    comp0 = Image.fromarray(bg.clip(0, 255).astype(np.uint8)).convert("RGBA")
    if quadros:
        comps = [Image.alpha_composite(comp0, q[2]).convert("RGB") for q in quadros]; comp = comps[0]
    else:
        comp = comp0
        if st.get("card"):
            sh, ph = card_layer(box); comp = Image.alpha_composite(Image.alpha_composite(comp, sh), ph)
        comp = Image.alpha_composite(Image.alpha_composite(comp, hl), text).convert("RGB"); comps = [comp]
    print("escala da fonte:", round(box[2], 2))
    tmp = tempfile.mkdtemp(); vid, wav = os.path.join(tmp, "v.mp4"), os.path.join(tmp, "a.wav")
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19",
                           "-preset", "medium", vid], stdin=subprocess.PIPE)
    bigs = []
    for c_ in comps:
        b_ = Image.fromarray(np.asarray(c_)).resize((int(W * 1.04), int(H * 1.04)), Image.LANCZOS); bigs.append(np.asarray(b_))
    BH, BW = bigs[0].shape[:2]
    for i in range(FPS * DUR):
        t = i / FPS; k = 0
        if quadros:
            k = max([j for j, q in enumerate(quadros) if t >= q[0]] or [0])
        z = 1.0 + 0.03 * i / (FPS * DUR)
        cw, ch = int(BW / z), int(BH / z); x0, y0 = (BW - cw) // 2, (BH - ch) // 2
        fr = Image.fromarray(bigs[k][y0:y0 + ch, x0:x0 + cw]).resize((W, H), Image.BILINEAR)
        ff.stdin.write(np.asarray(fr).tobytes())
    ff.stdin.close(); ff.wait()
    musica_louvor.trilha(spec.get("musica", "aurora"), DUR, wav)
    mp4 = os.path.join(outdir, name + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", vid, "-i", wav, "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    jpg = os.path.join(outdir, name + "-capa.jpg")
    comp.resize((540, 960), Image.LANCZOS).save(jpg, quality=82)
    print(mp4); print(jpg)


if __name__ == "__main__":
    main(sys.argv[1])
