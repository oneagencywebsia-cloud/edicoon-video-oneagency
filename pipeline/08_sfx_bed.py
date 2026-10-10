"""08_sfx_bed.py <video>

Mezcla TODOS los efectos de videos/<video>/edicion.json en una sola pista (videos/<video>/sfx_bed.wav, 48 kHz mono) con
precisión de muestra: cada efecto se coloca por su transitorio en el instante exacto del evento (`ini` ya calculado en
06_edicion.py), con recorte (`desde`,`dur`), fundidos y volumen. Los risers acaban en su clímax en el evento.
DUCKING: la pista baja sola mientras hablas, según el tipo de sonido (risers -7 dB, whoosh -6, papel/interfaz -4,
golpes -3, clics y teclas 0) con ataque 15 ms y relajación 150 ms, para que ningún efecto tape una palabra.
Avisa si algo satura. Remotion reproduce esta pista junto a la voz.
"""
import json
import sys
import wave

import numpy as np

SR = 48000
DUCK_DB = {"riser": 7, "whoosh": 6, "papel": 4, "interfaz": 4, "reloj": 6, "golpe": 3, "boom": 3, "sub_drop": 3, "click": 0, "tecla": 0, "teclado": 2, "camara": 1, "marcador": 3, "pop": 1, "escribir": 3, "ambiente": 6}
v = sys.argv[1]
ed = json.load(open(f"videos/{v}/edicion.json", encoding="utf-8"))
total = int(round(ed["frames"] / ed["fps"] * SR))
INFO = json.load(open("videos/_shared/sfx/index.json", encoding="utf-8"))["efectos"]
try:
    INFO.update({"p/" + k: v for k, v in json.load(open("videos/_shared/sfx/pack_index.json", encoding="utf-8"))["efectos"].items()})
except FileNotFoundError:
    pass


def actividad_voz():
    """0..1 por muestra: 1 cuando la voz suena (suavizada con ataque 15 ms y relajación 150 ms)."""
    import subprocess
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", f"videos/{ed['camara']}".replace(f"videos/{ed['id']}/", f"videos/{ed['id']}/"), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    h = SR // 100
    n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[: n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    a = np.clip((db - (db.max() - 42)) / 8, 0, 1)  # voz activa a partir de ~42 dB bajo su pico
    g = np.zeros(n)
    for i in range(n):  # ataque 15 ms ~ 1-2 pasos, relajación 150 ms ~ 15 pasos
        g[i] = max(a[i], g[i - 1] * 0.9) if i else a[i]
    out = np.repeat(g, h)
    out = np.pad(out, (0, max(total - len(out), 0)))[:total]
    return out


VOZ = actividad_voz()
bed = np.zeros(total, dtype=np.float64)
for s in ed["sfx"]:
    with wave.open(f"videos/_shared/{s['archivo']}") as w:
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32768
    a, b = int(round(s["desde"] * SR)), int(round((s["desde"] + s["dur"]) * SR))
    seg = x[a:b].copy() * s["vol"]
    n = len(seg)
    fi, fo = min(int(s["fade_in"] * SR), n), min(int(s["fade_out"] * SR), n)
    if fi:
        seg[:fi] *= np.linspace(0, 1, fi) ** (2 if s["ancla"] == "fin" else 1)
    if fo:
        seg[n - fo:] *= np.linspace(1, 0, fo)
    i0 = int(round(s["ini"] * SR))
    if i0 < 0:
        seg, i0 = seg[-i0:], 0
    i1 = min(i0 + len(seg), total)
    seg = seg[: i1 - i0]
    d = DUCK_DB.get(INFO[s["f"]]["tipo"], 0)
    if d:  # ducking bajo la voz
        seg = seg * (1 - (1 - 10 ** (-d / 20)) * VOZ[i0:i1])
    bed[i0:i1] += seg
pico = np.abs(bed).max()
if pico > 0.95:
    bed *= 0.95 / pico
with wave.open(f"videos/{v}/sfx_bed.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(bed, -1, 1) * 32767).astype("<i2").tobytes())
print(f"{len(ed['sfx'])} efectos mezclados, {total / SR:.2f}s, pico {20 * np.log10(max(pico, 1e-9)):.1f} dBFS")
for s in ed["sfx"]:
    print(f"  {s['en']:6.2f}s  {s['f']:18s} ancla={s['ancla']:6s} vol={s['vol']:.2f}  inicio de archivo en {s['ini']:.3f}s")
