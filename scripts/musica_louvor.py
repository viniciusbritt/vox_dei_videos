"""Trilhas instrumentais de louvor, otimistas e celestiais, COMPOSTAS e sintetizadas aqui (sem Content ID).
6 faixas diferentes (tom, andamento, progressão e instrumentos). Sempre em tom maior, terminam resolvidas no I.

Uso: musica_louvor.trilha("aurora", dur_segundos, "saida.wav")      # nomes em FAIXAS
     python3 scripts/musica_louvor.py amostras PASTA [dur]          # grava uma amostra mp3 de cada faixa
"""
import os, subprocess, sys, wave
import numpy as np


def fftconvolve(x, h):
    n = len(x) + len(h) - 1; m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(h, m), m)[:n]

SR = 44100
MAJ = {"I": [0, 4, 7], "ii": [2, 5, 9], "IV": [5, 9, 12], "V": [7, 11, 14], "vi": [9, 12, 16], "V/vi": [4, 8, 11],
       "Isus": [0, 5, 7], "I6": [4, 7, 12], "IVadd": [5, 9, 14]}

# nome: tom (MIDI da tônica), bpm, progressão, camadas
FAIXAS = {
    "aurora":   dict(key=62, bpm=84, prog=["I", "V", "vi", "IV"], camadas=["pad_cordas", "harpa", "sino_agudo"]),
    "ceu-azul": dict(key=67, bpm=92, prog=["I", "IV", "vi", "V"], camadas=["coro", "piano_suave", "celesta"]),
    "graca":    dict(key=60, bpm=76, prog=["I", "vi", "IV", "V"], camadas=["piano_suave", "cordas_lentas", "coro_leve"]),
    "alvorada": dict(key=64, bpm=100, prog=["I", "V", "IV", "V"], camadas=["violao", "pad_cordas", "sino_agudo"]),
    "luz":      dict(key=65, bpm=72, prog=["IV", "I", "V", "I"], camadas=["caixa_musica", "coro", "pad_cordas"]),
    "esperanca": dict(key=69, bpm=88, prog=["I", "IV", "I6", "V"], camadas=["harpa", "piano_suave", "cordas_lentas"]),
}
mid = lambda m: 440.0 * 2 ** ((m - 69) / 12)


class Mix:
    def __init__(self, dur):
        self.N = int(dur * SR); self.L = np.zeros(self.N); self.R = np.zeros(self.N)

    def add(self, sig, t0, pan=0.0, g=1.0):
        s = int(t0 * SR); n = min(len(sig), self.N - s)
        if n <= 0:
            return
        self.L[s:s + n] += sig[:n] * g * (1 - max(pan, 0)); self.R[s:s + n] += sig[:n] * g * (1 + min(pan, 0))


def t_(d):
    return np.arange(int(d * SR)) / SR


def ar(t, att, dec_rate=0.0, rel=None, d=None):
    e = (1 - np.exp(-t / max(att, 1e-3) * 3)) * np.exp(-t * dec_rate)
    if rel is not None and d is not None:
        e *= np.clip((d - t) / rel, 0, 1)
    return e


def piano(f, d, bright=1.0):
    t = t_(d)
    s = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.1 + 0.9 * k)) for k, a in [(1, 1), (2, .5 * bright), (3, .22 * bright), (4, .08 * bright)])
    return s * (1 - np.exp(-t * 400))


def harpa(f, d):
    t = t_(d)
    s = sum(a * np.sin(2 * np.pi * f * k * 1.0005 ** (k * k) * t) * np.exp(-t * (1.6 + 1.3 * k)) for k, a in [(1, 1), (2, .4), (3, .2), (4, .1)])
    return s * (1 - np.exp(-t * 600))


def sino(f, d):
    t = t_(d)
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dc) for r, a, dc in [(1, 1, 1.1), (2.76, .35, 1.8), (5.4, .15, 2.6), (8.93, .06, 3.5)])
    return s * (1 - np.exp(-t * 800))


def celesta(f, d):
    t = t_(d)
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dc) for r, a, dc in [(1, 1, 2.2), (4.0, .25, 5), (6.0, .1, 7)])
    return s * (1 - np.exp(-t * 800))


def caixa(f, d):
    t = t_(d)
    s = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * dc) for r, a, dc in [(1, 1, 3.0), (2, .3, 4.5), (3.01, .12, 6)])
    return s * (1 - np.exp(-t * 900))


def violao(f, d):
    """Pluck de violão (Karplus-Strong curto, vetorizado por blocos)."""
    n = int(d * SR); p = max(int(SR / f), 2)
    rng = np.random.default_rng(int(f * 10))
    buf = rng.uniform(-1, 1, p); buf = np.convolve(buf, np.ones(3) / 3, "same")
    out = np.empty(n); cur = buf.copy(); i = 0
    while i < n:
        out[i:i + p] = cur[:min(p, n - i)]
        cur = 0.5 * (cur + np.roll(cur, -1)) * 0.997
        i += p
    t = t_(d)
    return out * np.exp(-t * 1.2) * (1 - np.exp(-t * 500))


def cordas(f, d, att=0.7, vib=5.0):
    t = t_(d); out = 0
    for det in (-0.004, 0.0, 0.004):
        ph = 2 * np.pi * f * (1 + det) * t + 0.004 * np.sin(2 * np.pi * vib * t + det * 300)
        out = out + sum(np.sin(ph * k) / k ** 1.15 for k in range(1, 9))
    return out * ar(t, att, 0, 0.8, d) / 3


def coro(f, d):
    """'Aaah' sintetizado: harmônicos moldados por formantes de vogal aberta, vibrato lento."""
    t = t_(d); out = 0
    for det in (-0.006, 0.0, 0.005):
        vib = 1 + 0.003 * np.sin(2 * np.pi * 5.2 * t + det * 200)
        for k in range(1, 20):
            fk = f * k
            amp = sum(a * np.exp(-((fk - fc) / bw) ** 2) for fc, a, bw in [(750, 1.0, 280), (1150, .6, 260), (2500, .15, 400)])
            out = out + amp / (k ** 0.4) * np.sin(2 * np.pi * fk * (1 + det) * vib * t) * 0.2
    return out * ar(t, 1.0, 0, 1.0, d) / 3


def reverb(L, R, dur=2.4, wet=0.32, seed=5):
    rng = np.random.default_rng(seed)
    n = int(dur * SR); tt = np.arange(n) / SR
    outs = []
    for x in (L, R):
        ir = rng.normal(0, 1, n) * np.exp(-tt * 2.6); ir[:int(0.012 * SR)] *= 0.1
        ir = np.convolve(ir, np.ones(4) / 4, "same")
        y = fftconvolve(x, ir)[:len(x)]
        outs.append(x * (1 - wet) + y * wet * 0.045)
    return outs


def render(nome, dur):
    cfg = FAIXAS[nome]; key, bpm = cfg["key"], cfg["bpm"]
    prog = [MAJ[c] for c in cfg["prog"]] + [MAJ["I"]]
    beat = 60 / bpm; M = Mix(dur)
    bar = (dur - 1.0) / len(prog) if dur < 14 else beat * 4
    camadas = cfg["camadas"]
    t0 = 0.1
    for bi, ch in enumerate(prog):
        last = bi == len(prog) - 1
        if t0 > dur - 0.8:
            break
        d = bar + 0.7
        root = key + ch[0] - 12
        for lay in camadas:
            if lay in ("pad_cordas", "cordas_lentas"):
                for m in ch:
                    M.add(cordas(mid(key + m - 12 + (12 if lay == "cordas_lentas" else 0)), d, 0.9 if lay == "cordas_lentas" else 0.6), t0, 0.15, 0.05)
            elif lay in ("coro", "coro_leve"):
                for k, m in enumerate(ch):
                    M.add(coro(mid(key + m), d), t0, (-0.3, 0, 0.3)[k], 0.05 if lay == "coro" else 0.03)
            elif lay == "piano_suave":
                M.add(piano(mid(root), bar * 1.3, 0.6), t0, 0, 0.17)
                arp = [ch[0], ch[1], ch[2], ch[0] + 12, ch[2], ch[1]]
                step = bar / 6 if not last else bar / 3
                for j, m in enumerate(arp if not last else arp[:3]):
                    M.add(piano(mid(key + m), 2.4), t0 + j * step, -0.1, 0.075)
            elif lay == "harpa":
                step = bar / 8
                arp = [ch[0], ch[1], ch[2], ch[0] + 12, ch[1] + 12, ch[0] + 12, ch[2], ch[1]]
                for j, m in enumerate(arp if not last else arp[:3]):
                    M.add(harpa(mid(key + m), 2.6), t0 + j * step, 0.2 - 0.05 * j, 0.09)
            elif lay == "violao":
                step = bar / 8
                for j, m in enumerate([ch[0], ch[2], ch[1] + 12, ch[2], ch[0] + 12, ch[2], ch[1] + 12, ch[2]]):
                    if last and j > 2:
                        break
                    M.add(violao(mid(key + m - 12 * (j % 4 == 0)), 1.8), t0 + j * step, -0.2, 0.11)
            elif lay == "sino_agudo":
                for j, m in enumerate([ch[2] + 12, ch[1] + 24] if not last else [ch[0] + 24]):
                    M.add(sino(mid(key + m), 3.0), t0 + bar * (0.1 + 0.5 * j), 0.35, 0.045)
            elif lay == "celesta":
                for j, m in enumerate([ch[1] + 24, ch[2] + 24, ch[0] + 24]):
                    if last and j > 0:
                        break
                    M.add(celesta(mid(key + m), 2.0), t0 + bar * (0.08 + 0.3 * j), 0.3, 0.04)
            elif lay == "caixa_musica":
                step = bar / 8
                for j, m in enumerate([ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24, ch[2] + 12, ch[1] + 12, ch[0] + 12, ch[2] + 12]):
                    if last and j > 2:
                        break
                    M.add(caixa(mid(key + m), 1.4), t0 + j * step, 0.1, 0.07)
        t0 += bar
    L, R = reverb(M.L, M.R)
    st = np.stack([L, R], 1)
    st /= max(np.abs(st).max(), 1e-6); st *= 0.6
    n = len(st); fo = int(min(1.8, dur / 4) * SR)
    st[-fo:] *= (np.linspace(1, 0, fo) ** 1.5)[:, None]
    st[:int(0.04 * SR)] *= np.linspace(0, 1, int(0.04 * SR))[:, None]
    return st


def trilha(nome, dur, path):
    st = render(nome, dur)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    if sys.argv[1] == "amostras":
        pasta = sys.argv[2]; dur = float(sys.argv[3]) if len(sys.argv) > 3 else 10
        os.makedirs(pasta, exist_ok=True)
        for nome in FAIXAS:
            w = f"/tmp/{nome}.wav"; trilha(nome, dur, w)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", w, "-b:a", "160k", os.path.join(pasta, f"trilha-{nome}.mp3")], check=True)
            print(nome)
