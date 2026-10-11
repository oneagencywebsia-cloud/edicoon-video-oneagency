"""09_mirada.py <entrada.mp4> <salida.mp4> [--fuerza 0.9] [--max 0.30] [--antes-despues out/qa/mirada.png]

Corrige la MIRADA para que mire a cámara. Por fotograma:
  1. MediaPipe Face Landmarker (iris) localiza ojos, párpados e iris (se recorta la zona de la cara para que detecte bien).
  2. Desvío = (centro de la apertura del ojo) - (centro del iris). Se limita a `--max` x ancho del ojo y se multiplica por `--fuerza`.
  3. Deformación local (remap) SOLO dentro de la apertura del ojo (máscara suave): el iris se desplaza hacia el centro; párpados y gafas no se mueven.
  4. Suavizado temporal (mediana 5 + EMA) y sin corrección en parpadeos (ojo casi cerrado) o si no se detecta la cara.
El audio no se toca. Requiere: pip install mediapipe opencv-python-headless y videos/_shared/modelos/face_landmarker.task
(en el contenedor hacen falta libegl1 y libgles2: apt-get install -y libegl1 libgles2).
"""
import argparse
import subprocess

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mpt
from mediapipe.tasks.python import vision

OJOS = [
    {"cont": [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246], "anillo": [469, 470, 471, 472], "c1": 33, "c2": 133, "sup": 159, "inf": 145},
    {"cont": [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398], "anillo": [474, 475, 476, 477], "c1": 362, "c2": 263, "sup": 386, "inf": 374},
]
S = 768  # lado del recorte para el detector


def crear_detector():
    o = vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path="videos/_shared/modelos/face_landmarker.task"), running_mode=vision.RunningMode.IMAGE,
                                     output_face_blendshapes=True, num_faces=1, min_face_detection_confidence=0.15, min_face_presence_confidence=0.15, min_tracking_confidence=0.15)
    return vision.FaceLandmarker.create_from_options(o)


def detectar(det, fr, caja):
    """caja = (x0,y0,x1,y1) en píxeles del fotograma. Devuelve landmarks en píxeles del fotograma, o None."""
    x0, y0, x1, y1 = caja
    crop = cv2.resize(fr[y0:y1, x0:x1], (S, S))
    r = det.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)))
    if not r.face_landmarks:
        return None, None
    L = r.face_landmarks[0]
    pts = np.array([[x0 + p.x * (x1 - x0), y0 + p.y * (y1 - y0)] for p in L])
    bs = {c.category_name: c.score for c in r.face_blendshapes[0]}
    return pts, bs


def caja_cara(pts, w, h):
    mn, mx = pts.min(0), pts.max(0)
    c = (mn + mx) / 2
    lado = max(mx - mn) * 1.9
    x0, y0 = int(max(c[0] - lado / 2, 0)), int(max(c[1] - lado / 2, 0))
    x1, y1 = int(min(c[0] + lado / 2, w)), int(min(c[1] + lado / 2, h))
    return (x0, y0, x1, y1)


def senal(bs, e):
    """Mirada por ojo a partir de los blendshapes: (horizontal con signo, vertical: abajo-arriba). e=0 -> ojo del lado imagen-izquierda."""
    lado = "Right" if e == 0 else "Left"
    return bs[f"eyeLookOut{lado}"] - bs[f"eyeLookIn{lado}"], (bs[f"eyeLookDown{lado}"] - bs[f"eyeLookUp{lado}"])


def desvio(pts, o, fuerza, maximo, bs=None, e=0, cal=None, vy=1.0):
    a = pts[o["anillo"]]
    c = a.mean(0)
    r = np.linalg.norm(a - c, axis=1).mean()
    p1, p2 = pts[o["c1"]], pts[o["c2"]]
    ancho = np.linalg.norm(p1 - p2)
    objetivo = np.array([(p1[0] + p2[0]) / 2, (pts[o["sup"]][1] + pts[o["inf"]][1]) / 2])
    abierto = np.linalg.norm(pts[o["sup"]] - pts[o["inf"]]) / max(ancho, 1)
    d = (objetivo - c) * fuerza
    if bs is not None and cal is not None:
        sx, sy = senal(bs, e)
        # desplazamiento del iris que provoca esa mirada (calibrado con los datos del propio vídeo) -> se deshace
        d = -np.array([cal[e]["kx"] * sx, cal[e]["ky"] * sy * vy]) * ancho * fuerza
    n = np.linalg.norm(d)
    if n > maximo * ancho:
        d *= maximo * ancho / n
    return c, r, ancho, d, abierto


def deformar(fr, pts, o, c, r, d, factor):
    if np.linalg.norm(d) < 0.4 or factor <= 0:
        return fr
    cont = pts[o["cont"]].astype(np.int32)
    x, y, w, h = cv2.boundingRect(cont)
    m = int(max(w, h) * 0.5)
    H, W = fr.shape[:2]
    X0, Y0, X1, Y1 = max(x - m, 0), max(y - m, 0), min(x + w + m, W), min(y + h + m, H)
    roi = fr[Y0:Y1, X0:X1]
    mask = np.zeros(roi.shape[:2], np.float32)
    cv2.fillPoly(mask, [cont - [X0, Y0]], 1.0)
    mask = cv2.erode(mask, np.ones((3, 3), np.uint8))
    mask = cv2.GaussianBlur(mask, (0, 0), max(r * 0.22, 1.0))
    gy, gx = np.mgrid[0:roi.shape[0], 0:roi.shape[1]].astype(np.float32)
    cn = c + d * factor - [X0, Y0]  # nuevo centro del iris
    R = max(r * 1.9, 4.0)
    wgt = np.exp(-(((gx - cn[0]) ** 2 + (gy - cn[1]) ** 2) / (R * R))) * mask
    mapx = (gx - (d[0] * factor) * wgt).astype(np.float32)
    mapy = (gy - (d[1] * factor) * wgt).astype(np.float32)
    out = cv2.remap(roi, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    fr = fr.copy()
    fr[Y0:Y1, X0:X1] = out
    return fr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--fuerza", type=float, default=0.9)
    ap.add_argument("--max", type=float, default=0.30)
    ap.add_argument("--vy", type=float, default=1.0, help="ganancia extra del desplazamiento vertical")
    ap.add_argument("--antes-despues")
    a = ap.parse_args()
    det = crear_detector()
    cap = cv2.VideoCapture(a.entrada)
    W, H, fps, N = int(cap.get(3)), int(cap.get(4)), cap.get(5), int(cap.get(7))
    # pasada 1: landmarks y desvíos por fotograma
    frames_pts, bs_list, caja, i = [], [], None, 0
    desv = []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        pts = None
        for cj in ([caja] if caja else []) + [(130, 420, 950, 1260)]:
            pts, bs = detectar(det, fr, cj)
            if pts is not None:
                break
        if pts is not None:
            caja = caja_cara(pts, W, H)
        frames_pts.append(pts)
        bs_list.append(bs if pts is not None else None)
        i += 1
    n = len(frames_pts)
    # calibración: cuánto se desplaza el iris (en anchos de ojo) por unidad de mirada, con los datos de ESTE vídeo
    cal = []
    for e, o in enumerate(OJOS):
        X, Y, SX, SY = [], [], [], []
        for pts, bs in zip(frames_pts, bs_list):
            if pts is None:
                continue
            ar = pts[o["anillo"]].mean(0)
            p1, p2 = pts[o["c1"]], pts[o["c2"]]
            w_ = np.linalg.norm(p1 - p2)
            sx, sy = senal(bs, e)
            X.append((ar[0] - (p1[0] + p2[0]) / 2) / w_)
            Y.append((ar[1] - (p1[1] + p2[1]) / 2) / w_)
            SX.append(sx)
            SY.append(sy)
        kx = float(np.polyfit(SX, X, 1)[0])
        ky = float(np.polyfit(SY, Y, 1)[0])
        # límites razonables: si la regresión sale degenerada, valores típicos (iris ~0,22 anchos de ojo en horizontal, ~0,12 en vertical por unidad)
        kx = kx if abs(kx) > 0.05 else (-0.22 if e == 0 else 0.22)
        ky = ky if ky > 0.04 else 0.12
        cal.append({"kx": kx, "ky": ky})
    print("calibración mirada (anchos de ojo por unidad):", cal)
    desv = [None if frames_pts[k] is None else [desvio(frames_pts[k], o, a.fuerza, a.max, bs_list[k], e, cal, a.vy) for e, o in enumerate(OJOS)] for k in range(n)]
    # suavizado temporal por ojo: mediana 5 + EMA; factor de parpadeo
    D = np.zeros((n, 2, 2))
    F = np.zeros((n, 2))
    ult = np.zeros((2, 2))
    for k in range(n):
        for e in range(2):
            if desv[k] is not None:
                ult[e] = desv[k][e][3]
                F[k, e] = float(np.clip((desv[k][e][4] - 0.12) / 0.10, 0, 1))  # 0 con el ojo casi cerrado
            D[k, e] = ult[e]
    for e in range(2):
        for ax in range(2):
            v = D[:, e, ax]
            med = np.array([np.median(v[max(0, k - 2): k + 3]) for k in range(n)])
            ema = np.zeros(n)
            ema[0] = med[0]
            for k in range(1, n):
                ema[k] = 0.6 * ema[k - 1] + 0.4 * med[k]
            D[:, e, ax] = ema
    # pasada 2: aplicar y escribir
    cap.release()
    cap = cv2.VideoCapture(a.entrada)
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", f"{fps}", "-i", "-", "-i", a.entrada,
                          "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "14", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", a.salida],
                         stdin=subprocess.PIPE)
    muestras = {}
    k = 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        orig = fr
        pts = frames_pts[k]
        if pts is not None:
            for e, o in enumerate(OJOS):
                c, r, ancho, _, _ = desv[k][e]
                fr = deformar(fr, pts, o, c, r, D[k, e], F[k, e])
        if a.antes_despues and k in (60, 150, 300, 450, 600, 800) and pts is not None:
            muestras[k] = (orig, fr, pts)
        p.stdin.write(fr.tobytes())
        k += 1
    p.stdin.close()
    p.wait()
    activos = int(((np.abs(D).sum((1, 2)) > 0.8) & (F.min(1) > 0)).sum())
    print(f"OK -> {a.salida} | fotogramas con corrección activa: {activos}/{n} | desvío medio (px): {np.abs(D).mean():.1f}")
    if a.antes_despues and muestras:
        filas = []
        for kk, (o, f, pts) in muestras.items():
            c = (pts[[33, 133, 362, 263]]).mean(0)
            x0, y0 = int(c[0] - 150), int(c[1] - 55)
            ra, rb = o[y0:y0 + 110, x0:x0 + 300], f[y0:y0 + 110, x0:x0 + 300]
            filas.append(cv2.resize(np.hstack([ra, rb]), None, fx=2.2, fy=2.2, interpolation=cv2.INTER_CUBIC))
        cv2.imwrite(a.antes_despues, np.vstack(filas))


if __name__ == "__main__":
    main()
