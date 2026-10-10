"""03c_apartes.py <corte.trans.json>

Propone tramos para el filtro de voz (eco) en frases que son un APARTE o algo «dado por hecho»:
  «y no necesitas…», «no hace falta…», «por cierto», «obviamente», «claro», «ya sabes», «como todos sabemos», «ojo», «ni siquiera»…
Imprime candidatos con tiempos del corte y el JSON para pegar en guion.json -> "voz_fx". Máximo 1-2 por vídeo (no abusar).
"""
import json
import re
import sys

P = json.load(open(sys.argv[1], encoding="utf-8"))["palabras"]
PATRON = re.compile(r"^(y\s+)?(no\s+(necesitas|hace\s+falta|tienes\s+que|es\s+necesario)|por\s+cierto|obviamente|evidentemente|claro|ya\s+sabes|como\s+(ya\s+)?sabes|ojo|ni\s+siquiera|aunque\s+parezca)", re.I)
frases, cur = [], []
for w in P:
    cur.append(w)
    if re.search(r"[.?!]$", w["w"]):
        frases.append(cur)
        cur = []
if cur:
    frases.append(cur)
cands = []
for f in frases:
    # se prueba también cada tramo tras una coma (el aparte suele ir en mitad de la frase)
    for k in range(len(f)):
        if k == 0 or f[k - 1]["w"].endswith(",") or f[k]["w"].lower() in ("y",):
            txt = " ".join(x["w"] for x in f[k:])
            if PATRON.match(txt):
                hasta = next((j for j in range(k, len(f)) if re.search(r"[,.?!]$", f[j]["w"]) and j > k + 2), len(f) - 1)
                seg = f[k: hasta + 1]
                cands.append({"t0": round(seg[0]["t0"] - 0.05, 2), "t1": round(seg[-1]["t1"], 2), "fx": "eco", "texto": " ".join(x["w"] for x in seg)})
                break
if not cands:
    print("Sin candidatos claros (no se fuerza ningún eco).")
for c in cands:
    print(f"  {c['t0']:6.2f}-{c['t1']:6.2f}s  «{c['texto']}»")
print(json.dumps([{k: v for k, v in c.items() if k != "texto"} for c in cands], ensure_ascii=False))
