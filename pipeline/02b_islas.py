"""02b_islas.py <vídeo> <salida.json> [--modelo turbo] [--idioma es]

Transcripción POR ISLAS DE VOZ: separa el audio por pausas reales (voz - 17 dB, hueco >= 0,3 s) y transcribe cada isla
por separado. Evita que Whisper estire palabras sobre tomas fallidas que no transcribe (caso real: «necesita» de 6 s).
Salida: {"duracion", "islas":[{"t0","t1","texto","conf","palabras":[...]}], "palabras":[...]} con tiempos del bruto.
`conf` = probabilidad media de las palabras: una isla con conf baja suele ser una toma fallida o ruido.
"""
import argparse
import json
import subprocess
import time

import numpy as np
from faster_whisper import WhisperModel

SR = 16000


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--modelo", default="turbo")
    ap.add_argument("--idioma", default="es")
    a = ap.parse_args()
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", a.entrada, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n = len(x) // 160
    db = 20 * np.log10(np.sqrt((x[: n * 160].reshape(n, 160) ** 2).mean(1) + 1e-12) + 1e-9)
    voz = np.percentile(db[db > np.percentile(db, 40)], 90)
    v = db > voz - 17
    islas, i = [], 0
    while i < n:
        if v[i]:
            j = i
            while j < n and (v[j] or v[j: j + 30].any()):  # une huecos < 0,3 s
                j += 1
            if (j - i) / 100 >= 0.25:
                islas.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    try:
        m = WhisperModel(a.modelo, device="cuda", compute_type="float16")
    except Exception:
        m = WhisperModel(a.modelo, device="cpu", compute_type="int8", cpu_threads=4)
    t = time.time()
    out, todas = [], []
    for t0, t1 in islas:
        o = max(t0 - 0.15, 0.0)
        seg = x[int(o * SR): int((t1 + 0.15) * SR)]
        ss, _ = m.transcribe(seg, language=a.idioma, word_timestamps=True, condition_on_previous_text=False, beam_size=5,
                             no_speech_threshold=0.9, log_prob_threshold=-3)
        pal = [{"w": w.word.strip(), "t0": round(o + w.start, 3), "t1": round(o + w.end, 3), "p": round(w.probability, 3)}
               for s in ss for w in (s.words or [])]
        if not pal:
            continue
        out.append({"t0": round(t0, 3), "t1": round(t1, 3), "texto": " ".join(w["w"] for w in pal),
                    "conf": round(float(np.mean([w["p"] for w in pal])), 3), "palabras": pal})
        todas += pal
    json.dump({"duracion": round(len(x) / SR, 3), "nivel_voz_db": round(float(voz), 1), "islas": out, "palabras": todas},
              open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(out)} islas, {len(todas)} palabras en {time.time() - t:.0f}s")
    for k, s in enumerate(out):
        print(f"{k:2d} {s['t0']:6.2f}-{s['t1']:6.2f} conf={s['conf']:.2f}  {s['texto']}")


if __name__ == "__main__":
    main()
