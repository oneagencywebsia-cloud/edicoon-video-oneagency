"""01b_cola.py <corte.mp4> [--seg 0.9]
Alarga el final del corte congelando el último fotograma y añadiendo silencio, para que la última animación (p. ej. el comentario del CTA)
tenga tiempo de verse tras la última palabra. Actualiza `duracion` en <corte>.cuts.json. Hacerlo ANTES de 04_voz.py (idempotente: marca `cola`).
"""
import argparse
import json
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("corte")
ap.add_argument("--seg", type=float, default=0.9)
a = ap.parse_args()
cj = a.corte + ".cuts.json"
C = json.load(open(cj, encoding="utf-8"))
if C.get("cola"):
    raise SystemExit(f"ya tiene cola de {C['cola']} s")
tmp = a.corte + ".tmp.mp4"
r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.corte, "-vf", f"tpad=stop_mode=clone:stop_duration={a.seg}", "-af", f"apad=pad_dur={a.seg}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", tmp],
                   capture_output=True, text=True)
if r.returncode:
    raise SystemExit(r.stderr[-600:])
subprocess.run(["mv", tmp, a.corte], check=True)
C["cola"] = a.seg
C["duracion"] = round(C["duracion"] + a.seg, 3)
json.dump(C, open(cj, "w", encoding="utf-8"), ensure_ascii=False)
print(f"cola de {a.seg}s añadida; duración {C['duracion']}s")
