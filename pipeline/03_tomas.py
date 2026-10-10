"""03_tomas.py <islas.json> <palabras.json> [--quitadas quitadas.json] [--prep tomas.prep.json]

Decide qué islas de voz (salida de 02b_islas.py) se quedan. SE QUEDA LA ÚLTIMA VERSIÓN de cada frase. Reglas automáticas:
  a) isla muy parecida (texto) o con la misma primera palabra que otra posterior cercana -> toma repetida
  b) el final de una isla que repite el principio de la siguiente -> se recorta la cola (retomada a media frase)
  c) marcadores de corrección («no, no», «perdón», «otra vez», «repito»...) y claquetas
  d) confianza baja (< 0,55) si no continúa una isla que se queda -> toma fallida o ruido
  e) coletilla final («gracias», «vale», «ya está»...) tras el cierre
Imprime TODO lo que quita para revisarlo. `--prep` permite forzar decisiones del editor:
  {"quitar": [3, 4], "dejar": [6], "recortar_cola": {"20": "para encontrar"}}
"""
import argparse
import difflib
import json
import re
import unicodedata

MARC = {"no", "perdon", "perdona", "espera", "corte", "otra vez", "repito", "repetimos", "de nuevo", "uy"}
COLET = {"gracias", "vale", "ya esta", "listo", "ya", "perfecto", "fin", "corta", "adios"}


def n(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in s if unicodedata.category(c) != "Mn")).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("islas")
    ap.add_argument("salida")
    ap.add_argument("--quitadas")
    ap.add_argument("--prep")
    a = ap.parse_args()
    d = json.load(open(a.islas, encoding="utf-8"))
    I = d["islas"]
    prep = json.load(open(a.prep, encoding="utf-8")) if a.prep else {}
    T = [n(i["texto"]) for i in I]
    motivo: dict[int, str] = {}
    cola: dict[int, int] = {}  # isla -> índice de palabra desde el que se recorta

    for k, i in enumerate(I):
        toks = T[k].split()
        if toks and (set(toks) == {"no"} or T[k] in MARC or T[k].count("no ") + (T[k].endswith(" no")) >= 2 and len(toks) <= 8):
            motivo[k] = "marcador de corrección"
        elif re.match(r"^(toma|take|accion|grabando)\b", T[k]):
            motivo[k] = "claqueta"
    for k in range(len(I)):
        if k in motivo:
            continue
        for j in range(k + 1, min(k + 9, len(I))):
            if j in motivo and motivo[j] != "toma repetida":
                continue
            sim = difflib.SequenceMatcher(None, T[k], T[j]).ratio()
            w1, w2 = T[k].split()[:1], T[j].split()[:1]
            mismo_ini = bool(w1 and w2 and len(w1[0]) >= 5 and w1[0][:5] == w2[0][:5])
            if sim >= 0.6 or (mismo_ini and I[k]["conf"] < 0.9 and sim >= 0.3):
                motivo[k] = f"toma repetida (vuelve a decirlo en la isla {j})"
                break
    for k in range(len(I) - 1):  # (b) retomada a media frase
        if k in motivo or k + 1 in motivo:
            continue
        A, B = I[k]["palabras"], I[k + 1]["palabras"]
        ta, tb = [n(w["w"]) for w in A], [n(w["w"]) for w in B]
        for pos in range(max(0, len(ta) - 8), len(ta)):
            if len(tb) >= 2 and ta[pos] and ta[pos] == tb[0] and pos + 1 < len(ta) and ta[pos + 1][:4] == tb[1][:4] and pos > 0:
                cola[k] = pos
                break
    for k, i in enumerate(I):  # (d) confianza baja
        if k in motivo or i["conf"] >= 0.55:
            continue
        prev_ok = k > 0 and (k - 1) not in motivo and i["t0"] - I[k - 1]["t1"] < 1.2
        if not prev_ok:
            motivo[k] = f"confianza baja ({i['conf']:.2f})"
    k = len(I) - 1  # (e) coletilla final
    while k >= 0 and (n(I[k]["texto"]) in COLET or k in motivo):
        motivo.setdefault(k, "coletilla final")
        k -= 1
    # decisiones del editor
    for k in prep.get("quitar", []):
        motivo[k] = "decisión del editor"
    for k in prep.get("dejar", []):
        motivo.pop(k, None)
    for k, frase in prep.get("recortar_cola", {}).items():
        k = int(k)
        toks = [n(w["w"]) for w in I[k]["palabras"]]
        for pos in range(len(toks)):
            if " ".join(toks[pos: pos + len(frase.split())]) == n(frase):
                cola[k] = pos
                break

    quedan, quitadas = [], []
    for k, i in enumerate(I):
        if k in motivo:
            quitadas.append({"isla": k, "t0": i["t0"], "t1": i["t1"], "texto": i["texto"], "motivo": motivo[k]})
            continue
        pal = i["palabras"][: cola[k]] if k in cola else i["palabras"]
        if k in cola:
            quitadas.append({"isla": k, "t0": i["palabras"][cola[k]]["t0"], "t1": i["t1"], "texto": " ".join(w["w"] for w in i["palabras"][cola[k]:]),
                             "motivo": "cola retomada en la isla siguiente"})
        quedan += [{**w, "isla": k} for w in pal]
    json.dump({"duracion": d["duracion"], "palabras": quedan}, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.quitadas:
        json.dump(quitadas, open(a.quitadas, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Islas: {len(I)} | quitadas/recortadas: {len(quitadas)} | palabras que quedan: {len(quedan)}")
    for q in quitadas:
        print(f"  QUITA isla {q['isla']:2d} [{q['t0']:6.2f}-{q['t1']:6.2f}] {q['motivo']}: «{q['texto']}»")


if __name__ == "__main__":
    main()
