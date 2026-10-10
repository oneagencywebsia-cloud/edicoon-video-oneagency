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

ed = {"id": G["id"], "fps": fps, "frames": frames, "camara": G["camara"], "chunks": chunks,
      "escenas": G["escenas"], "sfx": sfx, "sfx_gain": G.get("sfx_gain", 1.0), "vozFx": G.get("voz_fx", []), "zooms": G["zooms"]}
json.dump(ed, open(f"{base}/edicion.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{len(chunks)} bloques de subtítulos, {len(G['escenas'])} escenas, {len(sfx)} efectos, {frames} fotogramas a {fps} fps")
print("Subtítulos:", " / ".join(" ".join(p["w"] for p in c["palabras"]) for c in chunks))
