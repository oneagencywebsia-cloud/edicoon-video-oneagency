"""04c_voz_fx.py <entrada.mp4> <salida.mp4> --guion videos/<v>/guion.json

Efectos de VOZ por tramos para apartes / paréntesis / ideas «que se dan por hechas» (guion.json -> "voz_fx": [{"t0","t1","fx"}]).
  eco       : repeticiones a 180/360 ms (como pensar en voz alta o decirlo «de pasada»)   <- el que pidió Ángel
  reverb    : sala/hall corto (cercano a un recuerdo o a algo enorme)
  telefono  : banda 400-3200 Hz (voz de llamada o de «lo que dicen»)
Mezcla seco/húmedo con fundidos (entrada 60 ms, salida 250 ms para que la cola del eco suene). El vídeo no se recodifica.
"""
import argparse
import json
import subprocess
import wave

import numpy as np

SR = 48000
FX = {
    "eco": "aecho=0.85:0.9:180|360:0.45|0.28,lowpass=f=7000",
    "reverb": "aecho=0.8:0.88:40|70|110|170:0.35|0.3|0.25|0.2,highpass=f=140",
    "telefono": "highpass=f=420,lowpass=f=3200,acompressor=threshold=0.1:ratio=3:makeup=2",
}
GANANCIA_HUMEDO = {"eco": 1.12, "reverb": 1.1, "telefono": 1.1}

ap = argparse.ArgumentParser()
ap.add_argument("entrada")
ap.add_argument("salida")
ap.add_argument("--guion", required=True)
a = ap.parse_args()
ventanas = json.load(open(a.guion, encoding="utf-8")).get("voz_fx", [])
if not ventanas:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.entrada, "-c", "copy", a.salida], check=True)
    print("sin voz_fx: copia sin cambios")
    raise SystemExit


def leer(ruta, filtro=None):
    c = ["ffmpeg", "-loglevel", "error", "-i", ruta, "-vn", "-ac", "1", "-ar", str(SR)]
    if filtro:
        c += ["-af", filtro]
    return np.frombuffer(subprocess.run(c + ["-f", "f32le", "-"], capture_output=True).stdout, dtype=np.float32).astype(np.float64)


seco = leer(a.entrada)
n = len(seco)
salida = seco.copy()
for v in ventanas:
    humedo = leer(a.entrada, FX[v["fx"]])[:n] * GANANCIA_HUMEDO[v["fx"]]
    humedo = np.pad(humedo, (0, n - len(humedo)))
    m = np.zeros(n)
    i0, i1 = int((v["t0"] - 0.06) * SR), int(v["t1"] * SR)
    m[i0:i1] = 1
    fin = int(0.25 * SR)
    m[i1: i1 + fin] = np.linspace(1, 0, min(fin, n - i1))[: max(n - i1, 0)] if i1 < n else 0
    ent = int(0.06 * SR)
    m[i0: i0 + ent] = np.linspace(0, 1, ent)
    salida = salida * (1 - m) + humedo * m
pico = np.abs(salida).max()
if pico > 0.95:
    salida *= 0.95 / pico
tmp = a.salida + ".fx.wav"
with wave.open(tmp, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(salida, -1, 1) * 32767).astype("<i2").tobytes())
r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.entrada, "-i", tmp, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", a.salida], capture_output=True, text=True)
if r.returncode:
    raise SystemExit(r.stderr[-800:])
import os
os.remove(tmp)
print("OK ->", a.salida, "|", ", ".join(f"{v['fx']} {v['t0']:.2f}-{v['t1']:.2f}s" for v in ventanas))
