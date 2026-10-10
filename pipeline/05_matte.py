"""05_matte.py <corte.mp4> <salida_dir> --ventanas 3.6-5.0,10-11.2 [--fps 30]

Recorte de persona (rembg u2net_human_seg, CPU) SOLO en las ventanas (segundos del corte) donde un rótulo va DETRÁS de la persona.
Escribe m_<fotograma>.png (RGBA 540x960: alfa = persona) con el número de fotograma del corte, para usarlo como máscara en Remotion.
"""
import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageFilter
from rembg import new_session, remove


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("corte")
    ap.add_argument("salida")
    ap.add_argument("--ventanas", required=True)
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    ses = new_session("u2net_human_seg", providers=["CPUExecutionProvider"])
    for v in a.ventanas.split(","):
        t0, t1 = (float(x) for x in v.split("-"))
        f0, f1 = round(t0 * a.fps), round(t1 * a.fps)
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.corte, "-vf", f"select='between(n,{f0},{f1})',scale=540:960",
                            "-vsync", "0", "-start_number", str(f0), os.path.join(td, "f_%05d.png")], check=True)
            for f in range(f0, f1 + 1):
                p = os.path.join(td, f"f_{f:05d}.png")
                if not os.path.exists(p):
                    continue
                m = remove(Image.open(p).convert("RGB"), session=ses, only_mask=True, post_process_mask=True)
                m = m.filter(ImageFilter.GaussianBlur(1.2))
                rgba = Image.merge("RGBA", [Image.new("L", m.size, 0)] * 3 + [m])
                rgba.save(os.path.join(a.salida, f"m_{f}.png"), optimize=True)
        print(f"ventana {v}: fotogramas {f0}-{f1} listos", flush=True)


if __name__ == "__main__":
    main()
