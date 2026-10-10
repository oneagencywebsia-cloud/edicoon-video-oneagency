"""00_sfx_pack.py <carpeta_SOUND_EFFECTS> — cataloga la librería PROPIA de efectos de Ángel (PACKS FOR EDITORS).

Convierte cada sonido a WAV 48 kHz mono (sin silencio en los extremos, pico a -3 dBFS) en videos/_shared/sfx/pack/ y mide:
  duracion, inicio_t, pico_t, brillo (centroide espectral, Hz), subida_db (energía final - energía inicial) y forma
Clasifica por nombre + forma: riser | sub_drop | golpe | boom | whoosh | click | tecla | camara | marcador | reloj | escribir | pop | ambiente | otro.
Descarta lo no apto (música, «among us», «Windows_error», censura). Escribe videos/_shared/sfx/pack_index.json.
"""
import json
import os
import re
import subprocess
import sys
import unicodedata
import wave

import numpy as np

SR = 48000
RAIZ = sys.argv[1]
OUT = "videos/_shared/sfx/pack"
os.makedirs(OUT, exist_ok=True)
DESCARTAR = re.compile(r"among us|windows_error|censored|primer proyecto|\.json$", re.I)


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def clasifica(nombre, dur, subida, brillo, pico_t):
    n = nombre.lower()
    if re.search(r"riser|riseer|rise\b", n) or (subida > 12 and pico_t > dur * 0.6 and dur > 1.2 and "drop" not in n and "whoosh" not in n and "woosh" not in n):
        return "riser"
    if "sub bass drop" in n or "bass drop" in n or "downer" in n:
        return "sub_drop"
    if re.search(r"boom|impact|bass hit|cinematic bass|deep bass|throbbing", n):
        return "boom" if "boom" in n or "impact" in n else "golpe"
    if re.search(r"whoosh|woosh|swoosh|whip|tumbling|disappear|film burn|laser", n):
        return "whoosh"
    if re.search(r"camera|camara|shutter|flash|chasquido", n):
        return "camara"
    if re.search(r"marker|highlighter|resaltador", n):
        return "marcador"
    if re.search(r"keyboard|click|lighter|mouse", n):
        return "tecla" if "keyboard" in n else "click"
    if re.search(r"reloj|counter", n):
        return "reloj"
    if re.search(r"type|typing|letras", n):
        return "escribir"
    if re.search(r"pop up|acierto|error", n):
        return "pop"
    if re.search(r"drone|ambient|wind|thunder", n):
        return "ambiente"
    return "otro"


idx = {}
for raiz, _, fs in os.walk(RAIZ):
    for f in sorted(fs):
        if DESCARTAR.search(f) or not re.search(r"\.(wav|mp3|mpeg|m4a|MP3)$", f, re.I):
            continue
        src = os.path.join(raiz, f)
        base = os.path.splitext(f)[0]
        s = slug(base)
        if s in idx:  # duplicados entre packs
            continue
        out = f"{OUT}/{s}.wav"
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-af",
                            "silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.01,areverse,silenceremove=start_periods=1:start_threshold=-60dB:start_silence=0.05,areverse",
                            "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
        x = np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)
        if len(x) < SR * 0.02:
            continue
        x *= 10 ** (-3 / 20) / np.abs(x).max()
        with wave.open(out, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
        h = SR // 100
        n = len(x) // h
        e = 20 * np.log10(np.sqrt((x[: n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
        pk = int(np.argmax(e))
        ini = int(np.argmax(e > e.max() - 18))
        k = max(n // 5, 1)
        subida = float(np.mean(e[-k:]) - np.mean(e[:k])) if n > 10 else 0.0
        sp = np.abs(np.fft.rfft(x[: min(len(x), SR * 3)])) + 1e-9
        fr = np.fft.rfftfreq(min(len(x), SR * 3), 1 / SR)
        brillo = float((fr * sp).sum() / sp.sum())
        dur = len(x) / SR
        tipo = clasifica(base, dur, subida, brillo, pk / 100)
        idx[s] = {"archivo": f"sfx/pack/{s}.wav", "origen": os.path.relpath(src, RAIZ), "nombre": base, "tipo": tipo,
                  "duracion": round(dur, 3), "inicio_t": round(ini / 100, 3), "pico_t": round(pk / 100, 3),
                  "brillo_hz": round(brillo), "subida_db": round(subida, 1)}
json.dump({"licencia": "PACKS FOR EDITORS (librería de Ángel): procedencia y licencia SIN verificar; no usar la música ni «among us»/«Windows_error»", "efectos": idx},
          open("videos/_shared/sfx/pack_index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(len(idx), "sonidos:", dict(Counter(v["tipo"] for v in idx.values())))
for t in ("riser", "sub_drop", "golpe", "boom", "marcador", "reloj", "escribir", "pop", "camara", "tecla", "click"):
    print(f"\n## {t}")
    for k, v in idx.items():
        if v["tipo"] == t:
            print(f"  {k:46s} dur={v['duracion']:5.2f}s inicio={v['inicio_t']:5.2f} pico={v['pico_t']:5.2f} subida={v['subida_db']:5.1f}dB brillo={v['brillo_hz']}Hz")
