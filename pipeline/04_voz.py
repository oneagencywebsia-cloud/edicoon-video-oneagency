"""04_voz.py <entrada.mp4> <salida.mp4> [--lufs -16]

Mejora la voz del corte (el vídeo no se recodifica):
  filtro de graves 75 Hz -> menos «barro» (250 Hz -2 dB) -> presencia (3 kHz +2,5 dB)
  -> aire (shelf 8 kHz +1,5 dB) -> de-esser -> compresor suave 1,8:1 -> limitador -> loudnorm 2 pasadas a -16 LUFS.
Imprime LUFS, rango y ruido antes/después.
"""
import argparse
import json
import subprocess

import numpy as np

CADENA = ("highpass=f=75,"
          "equalizer=f=250:t=q:w=1.0:g=-2,equalizer=f=3000:t=q:w=1.0:g=2.5,equalizer=f=8000:t=h:w=0.7:g=1.5,"
          "deesser=i=0.35:m=0.5:f=0.5,"
          "acompressor=threshold=0.18:ratio=1.8:attack=10:release=200:makeup=1,alimiter=limit=0.9")
# Sin reducción de ruido a propósito: la sala de Ángel ya está a -77 dB y afftdn no mejora nada (solo añade artefactos).


def sh(c):
    return subprocess.run(c, capture_output=True, text=True)


def medir(p):
    s = sh(["ffmpeg", "-hide_banner", "-i", p, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    g = lambda k: float(s.split(k)[-1].split()[0])
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n = len(x) // 160
    db = 20 * np.log10(np.sqrt((x[: n * 160].reshape(n, 160) ** 2).mean(1)) + 1e-9)
    voz = np.percentile(db[db > np.percentile(db, 40)], 90)
    return {"LUFS": g("I:"), "LRA": g("LRA:"), "ruido_p10_dB": round(float(np.percentile(db, 10)), 1), "voz_p90_dB": round(float(voz), 1)}


ap = argparse.ArgumentParser()
ap.add_argument("entrada")
ap.add_argument("salida")
ap.add_argument("--lufs", type=float, default=-16)
a = ap.parse_args()
print("antes  :", medir(a.entrada))
p1 = sh(["ffmpeg", "-hide_banner", "-i", a.entrada, "-af", f"{CADENA},loudnorm=I={a.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"]).stderr
m = json.loads(p1[p1.rindex("{"): p1.rindex("}") + 1])
ln = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
      f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
r = sh(["ffmpeg", "-loglevel", "error", "-y", "-i", a.entrada, "-c:v", "copy", "-af", f"{CADENA},{ln}", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", a.salida])
if r.returncode:
    raise SystemExit(r.stderr[-800:])
print("después:", medir(a.salida))
