"""Sincroniza un audio externo (micro aparte/grabadora) con el vídeo y lo pone como pista de audio.
Correlación cruzada del audio del vídeo con el externo -> desfase; si hay deriva (relojes distintos) se corrige con atempo.
El vídeo se copia sin recodificar (-c:v copy). Sale <salida>.mp4 con el audio externo alineado, listo para 01_cut_silences.py.
Uso: python pipeline/00b_sync_audio.py raw/video2/bruto.MOV raw/video2/audio.wav raw/video2/bruto_sync.mp4
"""
import argparse
import subprocess

import numpy as np
from scipy.signal import correlate

SR = 16000


def leer(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR),
                          "-af", "highpass=f=80,lowpass=f=4000", "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
    return x


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def norm(x):
    x = x - x.mean()
    return x / (x.std() + 1e-9)


def lag(x, y):
    """x[n+L] ~ y[n]: el audio externo y empieza en el segundo L del vídeo. Devuelve (L_s, confianza)."""
    c = correlate(norm(x), norm(y), mode="full", method="fft")
    k = int(np.argmax(np.abs(c)))
    L = k - (len(y) - 1)
    conf = float(np.abs(c[k]) / (np.median(np.abs(c)) * 1.0 + 1e-9))
    return L / SR, conf, float(np.sign(c[k]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("audio")
    ap.add_argument("salida")
    ap.add_argument("--ventana", type=float, default=12.0, help="segundos para medir la deriva al principio y al final")
    a = ap.parse_args()
    x, y = leer(a.video), leer(a.audio)
    dv, da = len(x) / SR, len(y) / SR
    L, conf, signo = lag(x, y)
    print(f"vídeo {dv:.2f}s  audio {da:.2f}s  desfase {L:+.3f}s  confianza {conf:.0f}x" + ("  (¡FASE INVERTIDA!)" if signo < 0 else ""))
    if conf < 8:
        raise SystemExit("Correlación débil: no parecen la misma grabación. No se genera nada.")
    # deriva: desfase local al principio y al final
    w = int(a.ventana * SR)
    tempo = 1.0
    if len(x) > 3 * w and len(y) > 3 * w:
        try:
            t1, t2 = max(0.0, L) + 1.0, min(dv, L + da) - a.ventana - 1.0
            if t2 - t1 > 10:
                def abs_lag(t):
                    i0 = int((t - L) * SR)
                    seg = y[i0:i0 + w]
                    x0 = max(0, int((t - 2) * SR))
                    xs = x[x0: int((t + a.ventana + 2) * SR)]
                    l, _, _ = lag(xs, seg)
                    return x0 / SR + l - (t - L)   # desfase medido en ese punto
                d1, d2 = abs_lag(t1), abs_lag(t2)
                deriva = (d2 - d1) / (t2 - t1)
                print(f"deriva medida: {deriva * 1e6:+.0f} ppm ({(d2 - d1) * 1000:+.1f} ms entre t={t1:.0f}s y t={t2:.0f}s)")
                if abs(deriva) > 2e-4:
                    tempo = 1.0 / (1.0 + deriva)
        except Exception as e:  # la deriva es opcional
            print("deriva no medida:", e)
    filtro = []
    if L >= 0:
        ms = int(round(L * tempo * 1000))   # atempo estira también el silencio: se precompensa
        filtro.append(f"adelay={ms}|{ms}")
    else:
        filtro.append(f"atrim=start={-L:.4f},asetpts=PTS-STARTPTS")
    if tempo != 1.0:
        filtro.append(f"atempo={tempo:.6f}")
        print(f"se corrige la deriva con atempo={tempo:.6f}")
    filtro.append("apad")
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.video, "-i", a.audio, "-map", "0:v:0", "-map", "1:a:0",
                        "-c:v", "copy", "-af", ",".join(filtro), "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                        "-t", f"{dv:.4f}", "-movflags", "+faststart", a.salida], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-800:])
    # comprobación: el resultado debe quedar a ~0 s del audio del vídeo
    z = leer(a.salida)
    n = min(len(x), len(z))
    L2, c2, _ = lag(x[:n], z[:n])
    print(f"comprobación: desfase residual {L2 * 1000:+.1f} ms (confianza {c2:.0f}x) -> {a.salida}")


if __name__ == "__main__":
    main()
