"""01c_remapear_guion.py <guion_viejo.json> <cuts_viejo.json> <cuts_nuevo.json> <guion_nuevo.json>
Si se re-corta un vídeo, traslada TODOS los tiempos del guion (escenas, sfx, enfasis, voz_fx, zooms) del corte viejo al nuevo pasando por el
tiempo del bruto (origen). Lo posterior al último tramo conserva su distancia al final.
"""
import json
import sys

gv, cv, cn, out = sys.argv[1:5]
G = json.load(open(gv, encoding="utf-8"))
V = json.load(open(cv, encoding="utf-8"))
N = json.load(open(cn, encoding="utf-8"))


def fin(C):
    t = C["tramos"][-1]
    return t["cut0"] + (t["src1"] - t["src0"])


def a_src(t):
    for m in V["tramos"]:
        d = m["src1"] - m["src0"]
        if m["cut0"] - 1e-6 <= t <= m["cut0"] + d + 1e-6:
            return m["src0"] + (t - m["cut0"])
    for m in V["tramos"]:  # en un hueco: al inicio del siguiente tramo
        if m["cut0"] > t:
            return m["src0"]
    return None


def a_nuevo(src):
    for m in N["tramos"]:
        if m["src0"] - 1e-6 <= src <= m["src1"] + 1e-6:
            return m["cut0"] + (src - m["src0"])
    for m in N["tramos"]:
        if m["src0"] > src:
            return m["cut0"]
    return fin(N)


def r(t):
    s = a_src(t)
    if s is None:
        return round(fin(N) + (t - fin(V)), 3)
    return round(a_nuevo(s), 3)


TCAMPOS = {"t0", "t1", "t", "en", "partirT", "resaltarT", "clicT", "escribeT", "enviaT"}


def rec(o):
    if isinstance(o, dict):
        return {k: (r(v) if k in TCAMPOS and isinstance(v, (int, float)) else rec(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [rec(x) for x in o]
    return o


H = rec({k: v for k, v in G.items() if k not in ("zooms", "correcciones")})
H["correcciones"] = G["correcciones"]
H["zooms"] = [[r(t), e] for t, e in G["zooms"]]
json.dump(H, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("remapeado:", out)
