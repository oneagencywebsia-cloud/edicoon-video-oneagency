"""09b_medir_mirada.py <video> [<video2> ...] — mide hacia dónde mira (blendshapes de iris), 1 de cada 6 fotogramas.
Imprime media/p90 de mirada hacia abajo/arriba/lados y % de fotogramas con desvío notable (>0,25) y fuerte (>0,4)."""
import sys

import cv2
import numpy as np

sys.path.insert(0, "pipeline")
import importlib.util

spec = importlib.util.spec_from_file_location("mirada", "pipeline/09_mirada.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

det = mod.crear_detector()
for ruta in sys.argv[1:]:
    cap = cv2.VideoCapture(ruta)
    W, H = int(cap.get(3)), int(cap.get(4))
    cajas, i, caja, V = [], 0, None, []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i % 6 == 0:
            pts = bs = None
            for cj in ([caja] if caja else []) + [(130, 420, 950, 1260)]:
                pts, bs = mod.detectar(det, fr, cj)
                if pts is not None:
                    break
            if pts is not None:
                caja = mod.caja_cara(pts, W, H)
                m = lambda k: bs[k]
                V.append({"abajo": (m("eyeLookDownLeft") + m("eyeLookDownRight")) / 2, "arriba": (m("eyeLookUpLeft") + m("eyeLookUpRight")) / 2,
                          "izq": (m("eyeLookOutRight") + m("eyeLookInLeft")) / 2, "der": (m("eyeLookOutLeft") + m("eyeLookInRight")) / 2})
        i += 1
    a = {k: np.array([v[k] for v in V]) for k in V[0]}
    off = np.max(np.stack(list(a.values())), axis=0)
    print(f"{ruta}: " + " | ".join(f"{k} media {v.mean():.2f} p90 {np.percentile(v, 90):.2f}" for k, v in a.items()) + f" | desvío>0,25: {(off > 0.25).mean():.0%}  >0,4: {(off > 0.4).mean():.0%}")
