"""03_tomas.py <transcripcion.json> <palabras.json> [--quitadas quitadas.json]

Deja solo lo que debe quedar en el vídeo y IMPRIME lo que quita para revisarlo:
  - tomas repetidas (se queda con la ÚLTIMA versión de cada frase)
  - marcadores de corrección («no», «perdón», «otra vez», «repito», «corte»...)
  - claquetas («toma 2», «acción»)
  - frases abandonadas a medias (la frase siguiente retoma lo mismo)
  - coletillas finales («ya está», «vale», «corta»)
Los tiempos de las palabras que quedan son los del bruto (no se tocan).
"""
import argparse
import difflib
import json
import re
import unicodedata

MARCADORES = {"no", "perdon", "perdona", "espera", "corte", "otra vez", "repito", "repetimos", "vuelvo a empezar",
              "empiezo otra vez", "de nuevo", "otra", "uy", "mierda", "joder"}
CLAQUETAS = re.compile(r"^(toma|take|accion|grabando|tres dos uno|1 2 3)\b")
COLETILLAS_FIN = {"ya esta", "vale", "corta", "corten", "listo", "ya", "perfecto", "fin"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", "", s).strip()


def frases(palabras):
    """Agrupa palabras en frases cortando tras . ? ! o tras una pausa larga (>1,2 s)."""
    out, cur = [], []
    for i, w in enumerate(palabras):
        cur.append(i)
        fin = re.search(r"[.?!…]$", w["w"]) is not None
        pausa = i + 1 < len(palabras) and palabras[i + 1]["t0"] - w["t1"] > 1.2
        if fin or pausa:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def texto(palabras, idx):
    return norm(" ".join(palabras[i]["w"] for i in idx))


def similar(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a.split(), b.split()).ratio()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--quitadas")
    a = ap.parse_args()
    d = json.load(open(a.entrada, encoding="utf-8"))
    P = d["palabras"]
    F = frases(P)
    T = [texto(P, f) for f in F]
    quitar: dict[int, str] = {}

    for k, t in enumerate(T):
        if CLAQUETAS.match(t):
            quitar[k] = "claqueta"
        elif t in MARCADORES or t in {norm(m) for m in MARCADORES}:
            quitar[k] = "marcador de corrección"
            # el marcador invalida la frase anterior si la siguiente la retoma
            if k > 0 and k + 1 < len(T) and similar(T[k - 1], T[k + 1]) >= 0.5 and k - 1 not in quitar:
                quitar[k - 1] = f"toma repetida (corregida tras «{P[F[k][0]]['w']}»)"

    # repeticiones sin marcador: una frase seguida (hasta 3 después) de otra que empieza igual o es muy parecida
    for k in range(len(T)):
        if k in quitar or len(T[k].split()) < 3:
            continue
        for j in range(k + 1, min(k + 4, len(T))):
            if j in quitar:
                continue
            ini = " ".join(T[k].split()[:3]) == " ".join(T[j].split()[:3])
            if similar(T[k], T[j]) >= 0.6 or (ini and similar(T[k], T[j]) >= 0.4):
                quitar[k] = "toma repetida (se queda la última versión)"
                break

    # coletillas al final
    k = len(T) - 1
    while k >= 0 and (k in quitar or T[k] in COLETILLAS_FIN):
        quitar.setdefault(k, "coletilla final")
        k -= 1

    quitadas = [{"frase": " ".join(P[i]["w"] for i in F[k]), "t0": P[F[k][0]]["t0"], "t1": P[F[k][-1]]["t1"], "motivo": m}
                for k, m in sorted(quitar.items())]
    idx_quitar = {i for k in quitar for i in F[k]}
    quedan = [w for i, w in enumerate(P) if i not in idx_quitar]
    json.dump({"duracion": d["duracion"], "palabras": quedan}, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if a.quitadas:
        json.dump(quitadas, open(a.quitadas, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"Frases: {len(F)} | quitadas: {len(quitadas)} | palabras que quedan: {len(quedan)}/{len(P)}")
    for q in quitadas:
        print(f"  QUITA [{q['t0']:6.2f}-{q['t1']:6.2f}] {q['motivo']}: «{q['frase']}»")


if __name__ == "__main__":
    main()
