"""05_matte.py <corte.mp4> <salida_dir> --ventanas 3.6-5.0,10-11.2 [--fps <los del corte>]  |  --edicion videos/<v>/edicion.json [--parte 0/2]

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
    ap.add_argument("--ventanas", help="t0-t1,t0-t1 (segundos del corte)")
    ap.add_argument("--edicion", help="edicion.json: usa sus ventanasMatte y mattePaso (salida de 06_edicion.py)")
    ap.add_argument("--paso", type=int, default=1, help="1 = todos los fotogramas; 2 = solo los pares (Remotion reutiliza el anterior)")
    ap.add_argument("--parte", default="0/1", help="k/n: reparte el trabajo entre n procesos (lanzar los n)")
    ap.add_argument("--fps", type=int, help="por defecto, los fps del corte")
    a = ap.parse_args()
    os.makedirs(a.salida, exist_ok=True)
    if not a.fps:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=avg_frame_rate", "-of", "csv=p=0", a.corte], capture_output=True, text=True).stdout.strip()
        n, d = (int(x) for x in r.split("/"))
        a.fps = round(n / d)
    import onnxruntime as ort
    prov = ["CUDAExecutionProvider", "CPUExecutionProvider"] if "CUDAExecutionProvider" in ort.get_available_providers() else ["CPUExecutionProvider"]
    ses = new_session("u2net_human_seg", providers=prov)
    if a.edicion:
        import json
        ed = json.load(open(a.edicion, encoding="utf-8"))
        a.paso = ed.get("mattePaso", a.paso)
        vs = [f"{x}-{y}" for x, y in ed["ventanasMatte"]]
    else:
        vs = a.ventanas.split(",")
    k, n = (int(x) for x in a.parte.split("/"))
    for v in vs:
        t0, t1 = (float(x) for x in v.split("-"))
        f0, f1 = round(t0 * a.fps), round(t1 * a.fps)
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.corte, "-vf", f"select='between(n,{f0},{f1})',scale=540:960",
                            "-vsync", "0", "-start_number", str(f0), os.path.join(td, "f_%05d.png")], check=True)
            for f in range(f0, f1 + 1):
                if f % a.paso or (f // a.paso) % n != k:
                    continue
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
