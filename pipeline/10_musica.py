"""10_musica.py <video> <pista.mp3> [--nivel -27] [--inicio-pista auto]
Música de fondo sincronizada y mezclada para retención.
 - Detecta el pulso de la pista (tempo + fase) y busca desplazamiento y pequeño ajuste de tempo (±4 %) para que los pulsos caigan sobre los
   golpes de los rótulos clave y el clic del CTA (edicion.json).
 - Entrada filtrada que se abre hasta el primer golpe; el compás se «levanta» +2,5 dB en cada rótulo clave; salida con fundido tras el CTA.
 - Hueco para la voz: EQ -4 dB en 300-3500 Hz y ducking siguiendo la envolvente de la voz (corte_voz.mp4), -5 dB mientras habla.
 - Escribe videos/<video>/musica.wav (48 kHz estéreo). Remotion lo reproduce si existe; 07_final.py normaliza todo a -14 LUFS.
"""
import argparse
import json
import subprocess

import numpy as np

SR = 48000
ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("pista")
ap.add_argument("--nivel", type=float, default=-27.0, help="LUFS integrados aprox. de la música sola (la voz va a -16)")
ap.add_argument("--habla", type=float, default=-5.0, help="dB de ducking mientras habla")
a = ap.parse_args()
V = a.video
ed = json.load(open(f"videos/{V}/edicion.json", encoding="utf-8"))
dur = ed["frames"] / ed["fps"]
golpes = sorted({round(e["t0"], 3) for e in ed["escenas"] if e["tipo"] == "clave"} | {round(e["clicT"] + 0.3, 3) for e in ed["escenas"] if e["tipo"] == "cta"})
print("golpes a sincronizar:", golpes)


def leer(path, filtro=None, sr=SR, ch=1, t=None):
    c = ["ffmpeg", "-loglevel", "error"] + (["-t", str(t)] if t else []) + ["-i", path, "-vn", "-ac", str(ch), "-ar", str(sr)] + (["-af", filtro] if filtro else []) + ["-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(c, capture_output=True).stdout, dtype=np.float32).astype(np.float64)


# ---- pulso de la pista
x = leer(a.pista, sr=11025)
hop = 110
fs = 11025 / hop
e = np.sqrt((x[: len(x) // hop * hop].reshape(-1, hop) ** 2).mean(1))
on = np.maximum(np.diff(e), 0)
on = on / (on.max() + 1e-9)
mejor = None
for bpm in np.arange(80, 180, 0.25):
    per = fs * 60 / bpm
    for fase in np.arange(0, per, 0.5):
        k = np.arange(fase, len(on) - 1, per).astype(int)
        s = on[k].sum() / len(k)
        if mejor is None or s > mejor[0]:
            mejor = (s, bpm, fase)
_, bpm, fase = mejor
print(f"pulso: {bpm:.2f} BPM, primer pulso en {fase / fs:.3f}s")
per_s = 60 / bpm
# ---- ajuste: tempo (factor r) y desplazamiento (t_pista = t_video*r + o) para que los golpes caigan en pulso
mejor = None
for r in np.arange(0.96, 1.0401, 0.002):
    pulso = per_s / r  # periodo en tiempo de vídeo
    for off in np.arange(0, pulso, 0.004):
        d = [min((g - off) % pulso, pulso - (g - off) % pulso) for g in golpes]
        c = np.mean(np.square(d)) + 0.02 * abs(r - 1) ** 2 * 1e3  # preferir poco cambio de tempo
        if mejor is None or c < mejor[0]:
            mejor = (c, r, off)
_, r, off = mejor
pulso = per_s / r
print(f"tempo x{r:.3f} -> {bpm * r:.1f} BPM; error medio de los golpes {np.sqrt(np.mean([min((g - off) % pulso, pulso - (g - off) % pulso) ** 2 for g in golpes])) * 1000:.0f} ms")
# el primer pulso de vídeo en 'off'; en la pista cae en 'fase/fs' -> inicio de lectura en la pista (en segundos de pista)
ini_pista = fase / fs + per_s * 4  # saltamos 4 pulsos (1 compás) de la entrada de la pista
# lo que suena en t_video=off corresponde a t_pista = ini_pista -> t_pista(t) = ini_pista + (t - off) * r ; arrancamos 'off' - n*pulso antes
n_ant = int(np.floor(off / pulso)) + 0
t_ini_video = off - n_ant * pulso  # >=0, primer pulso del vídeo
t_pista0 = ini_pista - (off - 0) * r  # tiempo de pista que suena en t_video=0
if t_pista0 < 0:
    t_pista0 += per_s * 8 * np.ceil(-t_pista0 / (per_s * 8))  # múltiplos de 2 compases para conservar la fase
print(f"la pista arranca en {t_pista0:.2f}s")
largo = dur * r + 3
pista = leer(a.pista, filtro=f"atempo={1 / r:.5f}" if False else None, ch=2, t=t_pista0 + largo + 2)
pista = pista.reshape(-1, 2)
i0 = int(t_pista0 * SR)
seg = pista[i0: i0 + int(largo * SR)]
if len(seg) < int(dur * r * SR):
    seg = np.concatenate([seg, seg[: int(dur * r * SR) - len(seg)]])
# cambio de tempo por remuestreo con atempo de ffmpeg (conserva tono)
tmp = f"videos/{V}/_mus_raw.wav"
import wave
with wave.open(tmp, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(seg, -1, 1) * 32767).astype("<i2").tobytes())
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-af", f"atempo={r:.5f}", "-t", f"{dur:.3f}", f"videos/{V}/_mus_t.wav"], check=True)
m = leer(f"videos/{V}/_mus_t.wav", ch=2).reshape(-1, 2)
n = int(dur * SR)
if len(m) < n:
    m = np.concatenate([m, np.zeros((n - len(m), 2))])
m = m[:n]
t = np.arange(n) / SR
# ---- EQ para dejar sitio a la voz y quitar graves excesivos
EQ = f"videos/{V}/_mus_eq.wav"
with wave.open(f"videos/{V}/_mus_t2.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(m, -1, 1) * 32767).astype("<i2").tobytes())
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", f"videos/{V}/_mus_t2.wav", "-af",
                "highpass=f=45,equalizer=f=250:t=q:w=0.9:g=-2,equalizer=f=1200:t=q:w=0.8:g=-4,equalizer=f=3000:t=q:w=0.8:g=-4,equalizer=f=9000:t=h:w=0.7:g=-2", EQ], check=True)
m = leer(EQ, ch=2).reshape(-1, 2)[:n]
# ---- envolvente de la voz -> ducking
voz = leer(f"videos/{V}/corte_voz.mp4", sr=16000)
h = 160
ev = 20 * np.log10(np.sqrt((voz[: len(voz) // h * h].reshape(-1, h) ** 2).mean(1)) + 1e-9)
tv = np.arange(len(ev)) * h / 16000
vref = np.percentile(ev[ev > np.percentile(ev, 40)], 90)
habla = (ev > vref - 20).astype(float)
# suavizado: ataque rápido (60 ms) y relajación lenta (450 ms)
g = np.zeros_like(habla)
act = 0.0
for i, hb in enumerate(habla):
    k = 1 - np.exp(-0.01 / (0.06 if hb > act else 0.45))
    act += (hb - act) * k
    g[i] = act
duck = np.interp(t, tv, g)
gain_db = a.habla * duck
# ---- entrada, levantamientos en rótulos y salida
gain_db += np.where(t < golpes[0], np.interp(t, [0, golpes[0]], [-8, 0]), 0)
for gp in golpes:
    gain_db += 2.5 * np.exp(-np.square((t - (gp + 0.25)) / 0.35))
fin = dur
gain_db += np.where(t > fin - 1.6, -40 * ((t - (fin - 1.6)) / 1.6) ** 2, 0)
# entrada «amortiguada» que se abre hasta el primer golpe (paso bajo en mezcla seca/húmeda)
ent = int(golpes[0] * SR)
if ent > 0:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", EQ, "-af", "lowpass=f=650", f"videos/{V}/_mus_lp.wav"], check=True)
    lp = leer(f"videos/{V}/_mus_lp.wav", ch=2).reshape(-1, 2)[:n]
    w_ = np.clip(t / golpes[0], 0, 1) ** 2
    w_[ent:] = 1.0
    m = lp * (1 - w_)[:, None] + m * w_[:, None]
m = m * (10 ** (gain_db / 20))[:, None]
m = np.clip(m, -1, 1)
# ---- nivel: medir LUFS de la música ya con ducking y llevarla a --nivel
out = f"videos/{V}/musica.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((m * 32767 * 0.5).astype("<i2").tobytes())
p1 = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
li = float(p1.split("I:")[-1].split()[0])
gdb = a.nivel - li
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", out, "-af", f"volume={gdb:.2f}dB,alimiter=limit=0.8", "-ar", str(SR), f"videos/{V}/_mus_fin.wav"], check=True)
subprocess.run(["mv", f"videos/{V}/_mus_fin.wav", out], check=True)
for f in ("_mus_raw.wav", "_mus_t.wav", "_mus_t2.wav", "_mus_eq.wav", "_mus_lp.wav"):
    subprocess.run(["rm", "-f", f"videos/{V}/{f}"])
ed["musica"] = True
json.dump(ed, open(f"videos/{V}/edicion.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"musica.wav listo ({li:.1f} -> {a.nivel} LUFS, ganancia {gdb:+.1f} dB)")
