"""00a_clasificar.py <carpeta> -> <carpeta>/inventario.json
Inventario de una carpeta de brutos con archivos de cualquier tipo: para cada uno, streams, duración, resolución/fps/orientación y un veredicto:
  hablado (vídeo con voz) | b-roll (vídeo sin voz/sin audio) | audio-voz | audio-musica | otro
La voz se detecta por energía en la banda 300-3400 Hz y modulación silábica (2-8 Hz). Sirve para decidir qué es la toma principal, qué es b-roll y qué audio es el del micro.
"""
import json
import os
import subprocess
import sys

import numpy as np

carpeta = sys.argv[1]
out = []
for n in sorted(os.listdir(carpeta)):
    p = os.path.join(carpeta, n)
    if not os.path.isfile(p) or n.endswith((".json", ".log")) or n.startswith("."):
        continue
    j = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,duration:stream_side_data=rotation:format=duration",
                        "-of", "json", p], capture_output=True, text=True)
    try:
        info = json.loads(j.stdout)
    except Exception:
        out.append({"archivo": n, "tipo": "otro (no multimedia)"})
        continue
    st = info.get("streams", [])
    v = next((s for s in st if s["codec_type"] == "video"), None)
    a = next((s for s in st if s["codec_type"] == "audio"), None)
    dur = float(info.get("format", {}).get("duration", 0) or 0)
    voz = None
    if a:
        raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-t", "60", "-i", p, "-vn", "-ac", "1", "-ar", "16000", "-af", "highpass=f=300,lowpass=f=3400", "-f", "f32le", "-"], capture_output=True).stdout
        x = np.frombuffer(raw, dtype=np.float32)
        if len(x) > 16000:
            e = np.sqrt((x[: len(x) // 320 * 320].reshape(-1, 320) ** 2).mean(1)) + 1e-9
            db = 20 * np.log10(e)
            activo = db > (np.percentile(db, 95) - 25)
            mod = np.abs(np.fft.rfft(e - e.mean()))[1:]
            f = np.fft.rfftfreq(len(e), 0.02)[1:]
            ban = mod[(f >= 2) & (f <= 8)].sum() / (mod.sum() + 1e-9)
            voz = bool(activo.mean() > 0.25 and ban > 0.25 and db.max() > -45)
    if v and voz:
        tipo = "hablado"
    elif v:
        tipo = "b-roll"
    elif a and voz:
        tipo = "audio-voz (¿micro de otra toma?)"
    elif a:
        tipo = "audio-musica/ambiente"
    else:
        tipo = "otro"
    rot = None
    for sd in (v or {}).get("side_data_list", []) if v else []:
        rot = sd.get("rotation", rot)
    w, h = (v or {}).get("width"), (v or {}).get("height")
    if rot in (90, -90) and w and h:
        w, h = h, w
    out.append({"archivo": n, "tipo": tipo, "duracion_s": round(dur, 1), "resolucion": f"{w}x{h}" if w else None,
                "vertical": bool(w and h and h > w), "fps": (v or {}).get("avg_frame_rate"), "tiene_audio": bool(a), "voz": voz})
json.dump(out, open(os.path.join(carpeta, "inventario.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for o in out:
    print(o)
