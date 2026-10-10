"""07_final.py <salida.mp4> <parte1.mp4> [parte2.mp4 ...] [--lufs -14]

Une las partes (si hay varias, con concat demuxer y mismos parámetros) y normaliza a -14 LUFS (loudnorm 2 pasadas, linear=true,
pico real -1,5 dB). El vídeo no se recodifica.
"""
import argparse
import json
import os
import subprocess
import tempfile


def sh(c):
    return subprocess.run(c, capture_output=True, text=True)


ap = argparse.ArgumentParser()
ap.add_argument("salida")
ap.add_argument("partes", nargs="+")
ap.add_argument("--lufs", type=float, default=-14)
a = ap.parse_args()
os.makedirs(os.path.dirname(os.path.abspath(a.salida)), exist_ok=True)
with tempfile.TemporaryDirectory() as td:
    src = a.partes[0]
    if len(a.partes) > 1:
        lst = os.path.join(td, "l.txt")
        open(lst, "w").write("".join(f"file '{os.path.abspath(p)}'\n" for p in a.partes))
        src = os.path.join(td, "unido.mp4")
        r = sh(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", src])
        if r.returncode:
            raise SystemExit(r.stderr[-800:])
    p1 = sh(["ffmpeg", "-hide_banner", "-i", src, "-af", f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"]).stderr
    m = json.loads(p1[p1.rindex("{"): p1.rindex("}") + 1])
    ln = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    r = sh(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-c:v", "copy", "-af", ln, "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-movflags", "+faststart", a.salida])
    if r.returncode:
        raise SystemExit(r.stderr[-800:])
print(f"antes: {m['input_i']} LUFS (pico {m['input_tp']} dB)  ->  {a.lufs} LUFS  | {a.salida}")
