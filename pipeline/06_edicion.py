"""06_edicion.py <video>   (lee videos/<video>/guion.json + corte.trans.json + corte.mp4.cuts.json)

Genera videos/<video>/edicion.json (lo que lee Remotion): subtítulos en bloques con las correcciones del guion,
escenas, efectos de sonido (con duración sacada de _shared/sfx/index.json) y zooms. Tiempos en segundos del CORTE.
"""
import json
import re
import sys

v = sys.argv[1]
base = f"videos/{v}"
G = json.load(open(f"{base}/guion.json", encoding="utf-8"))
T = json.load(open(f"{base}/corte.trans.json", encoding="utf-8"))["palabras"]
C = json.load(open(f"{base}/corte.mp4.cuts.json", encoding="utf-8"))
SFX = json.load(open("videos/_shared/sfx/index.json", encoding="utf-8"))["efectos"]
try:  # librería propia de Ángel (prefijo p/): python pipeline/00_sfx_pack.py <carpeta SOUND EFFECTS>
    SFX.update({"p/" + k: v for k, v in json.load(open("videos/_shared/sfx/pack_index.json", encoding="utf-8"))["efectos"].items()})
except FileNotFoundError:
    pass
fps = C["fps"]
frames = round(C["duracion"] * fps)

# 1) correcciones de texto sobre la secuencia de palabras (conservando los tiempos)
P = [{"w": w["w"], "t0": w["t0"], "t1": w["t1"]} for w in T]
for fx in G["correcciones"]:
    m, a = fx["match"], fx["a"]
    i = 0
    while i <= len(P) - len(m):
        if [p["w"].lower() for p in P[i: i + len(m)]] == [x.lower() for x in m]:
            t0, t1 = P[i]["t0"], P[i + len(m) - 1]["t1"]
            nuevas = [{"w": x, "t0": round(t0 + (t1 - t0) * k / len(a), 3), "t1": round(t0 + (t1 - t0) * (k + 1) / len(a), 3)} for k, x in enumerate(a)]
            P[i: i + len(m)] = nuevas
            i += len(a)
        else:
            i += 1

# 2) bloques de subtítulos: máx. 4 palabras y 28 letras, corte tras signo de puntuación; un bloque de 1 palabra corta se une al anterior
letras = lambda ws: sum(len(x["w"]) for x in ws) + len(ws)
SUELTAS = {"y", "a", "de", "en", "la", "el", "los", "las", "una", "un", "que", "para", "tu", "se", "o", "con", "por", "del", "al", "ese", "mi", "su"}
chunks, cur = [], []
for p in P:
    if cur and (len(cur) >= 4 or letras(cur + [p]) > 26):
        resto = []
        while len(cur) > 1 and cur[-1]["w"].lower().strip(".,?!¿") in SUELTAS:  # no terminar un bloque en «y», «de», «tu»...
            resto.insert(0, cur.pop())
        chunks.append(cur)
        cur = resto
    cur.append(p)
    if re.search(r"[.,?!;:]$", p["w"]):
        chunks.append(cur)
        cur = []
if cur:
    chunks.append(cur)
fin = []
for c in chunks:
    if fin and len(c) == 1 and len(c[0]["w"]) <= 4 and len(fin[-1]) < 5:
        fin[-1] += c
    else:
        fin.append(c)
chunks = [{"t0": c[0]["t0"], "t1": c[-1]["t1"], "palabras": c} for c in fin]

# 3) efectos: cada uno se alinea por su TRANSITORIO con el instante `en` del evento visual
#    ancla "inicio" (golpes, clics) | "pico" (whoosh) | "fin" (risers: el clímax cae en `en`; `largo` = segundos de subida)
sfx = []
for s in G["sfx"]:
    info = SFX[s["f"]]
    desde = s.get("desde", 0.0)
    ancla = s.get("ancla", "inicio")
    if ancla == "fin":  # riser: tramo de `largo` s que acaba en el clímax de la fuente
        largo = min(s["largo"], info["pico_t"])
        desde = max(info["pico_t"] - largo, 0.0)
        dur, ini = largo + 0.03, s["en"] - largo
        fade_in, fade_out = largo * 0.7, 0.03
    else:
        ref = max((info["pico_t"] if ancla == "pico" else info["inicio_t"]) - desde, 0.0)
        ini = s["en"] - ref
        dur = min(s.get("dur", info["duracion"] - desde), info["duracion"] - desde)
        fade_in, fade_out = s.get("fade_in", 0.003), s.get("fade_out", 0.04)
    sfx.append({"f": s["f"], "ini": round(ini, 4), "archivo": info["archivo"], "vol": s["vol"], "desde": round(desde, 4),
                "dur": round(dur, 4), "fade_in": round(fade_in, 3), "fade_out": round(fade_out, 3), "en": s["en"], "ancla": ancla})
sfx.sort(key=lambda z: z["ini"])

# 3b) zoom de ÉNFASIS: en cada rótulo clave (y en los `enfasis` del guion). Alterna zoom-in (golpe y vuelta) y zoom-out (arranca cerca y se abre)
enfasis = [dict(e) for e in G.get("enfasis", [])]
for k, e in enumerate([x for x in G["escenas"] if x.get("tipo") == "clave"]):
    enfasis.append({"t0": round(e["t0"] - 0.03, 3), "t1": round(e["t1"] - 0.1, 3), "modo": "in" if k % 2 == 0 else "out", "escala": 0.09})
enfasis.sort(key=lambda z: z["t0"])
if G.get("sfx_zoom", True):
    for z in enfasis:  # efecto de sonido sincronizado al fotograma del zoom (el pico del whoosh cae a mitad de la rampa)
        f = "p/loud_whip" if z["modo"] == "in" else "p/vs_short_whoosh_6"
        info = SFX.get(f)
        if info:
            ini = z["t0"] + 0.2 - info["pico_t"]
            sfx.append({"f": f, "ini": round(ini, 4), "archivo": info["archivo"], "vol": 0.32, "desde": 0.0, "dur": round(info["duracion"], 4),
                        "fade_in": 0.003, "fade_out": 0.05, "en": z["t0"] + 0.2, "ancla": "pico"})
    sfx.sort(key=lambda z: z["ini"])

# 3c) CURVA DE ZOOM única y continua (un valor por fotograma). Reglas (feedback de Ángel):
#   - zoom-in 12 fotogramas (0,4 s) con suavizado; vuelta (zoom-out) 18 fotogramas (0,6 s), nunca de golpe
#   - amplitud mínima visible (in 0,11 / out 0,10 / manuales ~0,09)
#   - los escalones del punch-in base (que disimulan cortes) se hacen SUAVES (12 fotogramas) y se apartan de cualquier énfasis
#     (se quedan fuera de [t0-0,2 s ; t1+0,7 s]); un énfasis siempre termina de volver a la base antes del siguiente escalón
import numpy as np
def _suave(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)
def _sale(x):  # entrada rápida pero sin arranque brusco (seno)
    x = np.clip(x, 0, 1)
    return np.sin(x * np.pi / 2)
fr = np.arange(frames)
base_pts = [(float(t), float(e)) for t, e in G["zooms"]]
vent = [(z["t0"] - 0.2, z["t1"] + 0.7) for z in enfasis]
base_pts = [(t, e) for k, (t, e) in enumerate(base_pts) if k == 0 or not any(a <= t <= b for a, b in vent)]
curva = np.full(frames, base_pts[0][1])
for t, e in base_pts[1:]:
    f0 = int(round(t * fps))
    curva = curva + (e - curva[min(f0, frames - 1)] if False else 0)  # (se compone abajo)
nivel = np.full(frames, base_pts[0][1])
for t, e in base_pts[1:]:
    f0 = int(round(t * fps))
    prev = nivel[min(f0, frames - 1)]
    nivel = nivel + (e - prev) * _suave((fr - f0) / 12.0)
extra = np.zeros(frames)
for z in enfasis:
    f0, f1 = int(round(z["t0"] * fps)), int(round(z["t1"] * fps))
    if z["modo"] == "out":
        amp = max(z["escala"], 0.10)
        v = amp * _sale((fr - f0) / 10.0) * (1 - _suave((fr - (f0 + 10)) / 28.0))
    else:
        amp = max(z["escala"], 0.11) if z["escala"] >= 0.08 else max(z["escala"], 0.09)
        f1 = max(f1, f0 + 12 + 8)  # mantiene al menos 8 fotogramas el zoom completo
        subida = amp * _sale((fr - f0) / 12.0)
        bajada = amp * (1 - _suave((fr - f1) / 18.0))
        v = np.where(fr < f1, subida, np.minimum(bajada, amp))
    extra += v
zoom_curva = np.minimum(nivel + extra, 1.18)
maxpaso = float(np.abs(np.diff(zoom_curva)).max())
print(f"curva de zoom: {len(zoom_curva)} valores, paso máx. entre fotogramas {maxpaso:.4f} en t={int(np.abs(np.diff(zoom_curva)).argmax())/fps:.2f}s (suave si < 0,02), rango {zoom_curva.min():.3f}-{zoom_curva.max():.3f}")

ed = {"id": G["id"], "fps": fps, "frames": frames, "camara": G["camara"], "chunks": chunks,
      "escenas": G["escenas"], "sfx": sfx, "sfx_gain": G.get("sfx_gain", 1.0), "vozFx": G.get("voz_fx", []), "enfasis": enfasis, "zoomCurva": [round(float(x), 4) for x in zoom_curva], "zooms": G["zooms"]}
json.dump(ed, open(f"{base}/edicion.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(chunks)} bloques de subtítulos, {len(G['escenas'])} escenas, {len(sfx)} efectos, {frames} fotogramas a {fps} fps")
print("Subtítulos:", " / ".join(" ".join(p["w"] for p in c["palabras"]) for c in chunks))
