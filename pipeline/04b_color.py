"""04b_color.py <entrada.mp4> <salida.mp4> --lut videos/_shared/luts/Oceano_oscuro.cube [--fuerza 0.55]

Aplica un LUT (.cube) mezclado con el original a la fuerza indicada (0 = nada, 1 = LUT completo). El audio no se toca.
Elegido tras comparar los 12 LUTs del pack de Ángel: «Oceano_oscuro» a 0,55 (frío, mantiene la piel natural, encaja con el azul de marca).
"""
import argparse
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("entrada")
ap.add_argument("salida")
ap.add_argument("--lut", default="videos/_shared/luts/Oceano_oscuro.cube")
ap.add_argument("--fuerza", type=float, default=0.55)
a = ap.parse_args()
f = f"[0:v]split[a][b];[b]lut3d={a.lut}[c];[a][c]blend=all_expr='A*(1-{a.fuerza})+B*{a.fuerza}'[v]"
r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.entrada, "-filter_complex", f, "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                    "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", a.salida], capture_output=True, text=True)
if r.returncode:
    raise SystemExit(r.stderr[-800:])
print("OK ->", a.salida)
