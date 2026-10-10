"""00_sfx.py — descarga, limpia y mide la librería de efectos REALES (Mixkit) de videos/_shared/sfx/lista.json.

Para cada efecto: quita silencio al principio y al final, normaliza el pico a -3 dBFS y mide
  pico_t  = instante (s) del pico de energía  -> los whoosh se alinean por el PICO con el evento
  inicio_t= primer instante con energía clara -> los golpes/clics se alinean por el INICIO
  fin_t   = duración útil                      -> los risers se alinean por el FINAL (clímax) con el evento
Escribe index.json. Los efectos de tipo `riser` reciben un recorte de medios (-5 dB a 2,5 kHz) para no tapar la voz.
"""
import json
import os
import re
import subprocess

import numpy as np

D = "videos/_shared/sfx"
L = json.load(open(f"{D}/lista.json", encoding="utf-8"))
CAT = json.load(open(os.environ.get("MIXKIT_CATALOGO", "/tmp/mixkit_catalogo.json"), encoding="utf-8"))
SR = 48000


def leer(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def env_db(x, ms=10):
    h = SR * ms // 1000
    n = len(x) // h
    return 20 * np.log10(np.sqrt((x[: n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)


idx = {}
for nom, (i, tipo, uso) in L["efectos"].items():
    mp3 = f"/tmp/sfx_{i}.mp3"
    if not os.path.exists(mp3):
        subprocess.run(["curl", "-sS", "-L", "-m", "60", "-o", mp3, CAT[str(i)]["url"]], check=True)
    filtro = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.015,areverse,silenceremove=start_periods=1:start_threshold=-55dB:start_silence=0.05,areverse"
    if tipo == "riser":
        filtro += ",equalizer=f=2500:t=q:w=0.8:g=-5"
    tmp = f"/tmp/sfx_{nom}.wav"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", mp3, "-af", filtro, "-ac", "1", "-ar", str(SR), tmp], check=True)
    x = leer(tmp)
    pico = np.abs(x).max()
    x = x * (10 ** (-3 / 20) / pico)
    out = f"{D}/{nom}.wav"
    import wave
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())
    e = env_db(x)
    pk = int(np.argmax(e))
    ini = int(np.argmax(e > e.max() - 18))  # primer instante a menos de 18 dB del pico
    idx[nom] = {"archivo": f"sfx/{nom}.wav", "tipo": tipo, "uso": uso, "titulo_original": CAT[str(i)]["titulo"], "id_mixkit": i,
                "duracion": round(len(x) / SR, 3), "pico_t": round(pk / 100, 3), "inicio_t": round(ini / 100, 3)}
    print(f"{nom:20s} {tipo:8s} dur={len(x)/SR:5.2f}s  inicio={ini/100:5.2f}s  pico={pk/100:5.2f}s")

# teclas sueltas: transitorios de una fuente
for nom, (fuente, k) in L["recortes"].items():
    x = leer(f"{D}/{fuente}.wav")
    e = env_db(x, 5)
    cand, i = [], 0
    while i < len(e) - 2:
        if e[i] > e.max() - 14 and (not cand or i - cand[-1] > 14):
            cand.append(i)
            i += 14
        else:
            i += 1
    if k >= len(cand):
        continue
    s0 = max(cand[k] * 240 - 240, 0)
    seg = x[s0: s0 + int(0.12 * SR)].copy()
    seg *= np.linspace(1, 0, len(seg)) ** 0.5
    seg *= 10 ** (-3 / 20) / np.abs(seg).max()
    import wave
    with wave.open(f"{D}/{nom}.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(seg, -1, 1) * 32767).astype("<i2").tobytes())
    idx[nom] = {"archivo": f"sfx/{nom}.wav", "tipo": "tecla", "uso": "pulsación suelta", "titulo_original": "(recorte de teclado)", "id_mixkit": L["efectos"][fuente][0],
                "duracion": round(len(seg) / SR, 3), "pico_t": 0.005, "inicio_t": 0.0}
    print(f"{nom:20s} tecla    dur={len(seg)/SR:.2f}s")
json.dump({"licencia": L["licencia"], "efectos": idx}, open(f"{D}/index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
