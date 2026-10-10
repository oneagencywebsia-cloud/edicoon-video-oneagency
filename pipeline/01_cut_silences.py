"""01_cut_silences.py <bruto> <corte.mp4> --words <palabras.json> [--ancho 1080 --alto 1920] [--lufs -16]

Corte seco palabra a palabra, exacto a fotograma:
  - ~60 ms de aire entre palabras (90 ms tras coma o punto)
  - umbral de voz RELATIVO al nivel de la voz (voz - 24 dB), no solo al ruido
  - no quita huecos con voz continua >= 0,2 s entre palabras que se quedan (Whisper coloca mal a veces)
  - palabras cortas al empezar frase: retrocede el inicio hasta 250 ms mientras haya voz clara
  - voz normalizada a -16 LUFS (loudnorm 2 pasadas, linear)
Guarda <corte>.cuts.json con el mapa origen -> corte y las palabras ya con tiempos del corte.
"""
import argparse
import json
import re
import subprocess

import numpy as np

SR = 16000
HOP = 160  # 10 ms


def sh(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def info(path: str) -> dict:
    j = json.loads(sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                       "stream=r_frame_rate,avg_frame_rate", "-of", "json", path]).stdout)["streams"][0]
    n, d = (int(x) for x in j["avg_frame_rate"].split("/"))
    return {"fps": round(n / d) if d else 30}


def envolvente(path: str) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n = len(x) // HOP
    rms = np.sqrt((x[: n * HOP].reshape(n, HOP) ** 2).mean(axis=1) + 1e-12)
    return 20 * np.log10(rms + 1e-9)  # dB por cada 10 ms



def norm(x: str) -> str:
    import unicodedata
    x = unicodedata.normalize("NFD", x.lower())
    return re.sub(r"[^a-z0-9 ]", "", "".join(c for c in x if unicodedata.category(c) != "Mn")).strip()


def restar(seg, excl):
    """Quita de los tramos [s0,s1] los intervalos excl (tiempos del bruto)."""
    for e0, e1 in excl:
        nuevo = []
        for s0, s1 in seg:
            if e1 <= s0 or e0 >= s1:
                nuevo.append([s0, s1])
                continue
            if e0 > s0:
                nuevo.append([s0, e0])
            if e1 < s1:
                nuevo.append([e1, s1])
        seg = nuevo
    return seg


def verificar(bruto, seg_f, W, fps, max_iter=3):
    import difflib
    import os
    import tempfile
    from faster_whisper import WhisperModel
    modelo = WhisperModel("turbo", device="cpu", compute_type="int8", cpu_threads=4)
    esperado = [t for w in W for t in norm(w["w"]).split()]
    excl = []
    seg = [list(x) for x in seg_f]
    for it in range(max_iter):
        graf = ";".join(f"[0:a:0]atrim=start={s0:.5f}:end={s1:.5f},asetpts=PTS-STARTPTS[a{k}]" for k, (s0, s1) in enumerate(seg))
        graf += ";" + "".join(f"[a{k}]" for k in range(len(seg))) + f"concat=n={len(seg)}:v=0:a=1,aresample=16000[o]"
        with tempfile.TemporaryDirectory() as td:
            wav = os.path.join(td, "v.wav")
            r = sh(["ffmpeg", "-loglevel", "error", "-y", "-i", bruto, "-filter_complex", graf, "-map", "[o]", "-ac", "1", wav])
            if r.returncode:
                raise SystemExit(r.stderr[-800:])
            ss, _ = modelo.transcribe(wav, language="es", word_timestamps=True, condition_on_previous_text=False, beam_size=5)
            got = [(t, w.start, w.end) for sg in ss for w in (sg.words or []) for t in norm(w.word).split()]
        sm = difflib.SequenceMatcher(None, esperado, [g[0] for g in got], autojunk=False)
        malos = []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op in ("insert", "replace") and (j2 - j1) - (i2 - i1) >= 4 and got[j2 - 1][2] - got[j1][1] >= 1.0:
                malos.append((got[j1][1], got[j2 - 1][2], " ".join(g[0] for g in got[j1:j2])))
        if not malos:
            print(f"verificación: limpio tras {it} correcciones")
            break
        cum, mapa = 0.0, []
        for s0, s1 in seg:
            mapa.append((cum, s0, s1))
            cum += s1 - s0
        def a_src(t):
            for c0, s0, s1 in mapa:
                if c0 <= t <= c0 + (s1 - s0) + 1e-3:
                    return s0 + (t - c0)
            return mapa[-1][2]
        for c0, c1, txt in malos:
            e0, e1 = a_src(c0) - 0.05, a_src(c1) + 0.05
            print(f"  voz de más en el corte {c0:.1f}-{c1:.1f}s (bruto {e0:.1f}-{e1:.1f}s): «{txt}» -> se recorta")
            excl.append((e0, e1))
        seg = restar([list(x) for x in seg_f], excl)
    f = lambda t: round(t * fps) / fps
    return [[f(s0), max(f(s1), f(s0) + 1 / fps)] for s0, s1 in seg if s1 - s0 > 0.05]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bruto")
    ap.add_argument("corte")
    ap.add_argument("--words", required=True)
    ap.add_argument("--ancho", type=int, default=1080)
    ap.add_argument("--alto", type=int, default=1920)
    ap.add_argument("--lufs", type=float, default=-16)
    ap.add_argument("--fps", type=int)
    ap.add_argument("--sin-verificar", action="store_true")
    a = ap.parse_args()

    W = json.load(open(a.words, encoding="utf-8"))["palabras"]
    fps = a.fps or info(a.bruto)["fps"]
    env = envolvente(a.bruto)
    voz = np.percentile(env[env > np.percentile(env, 40)], 90)  # nivel típico de la voz
    umbral = voz - 24
    hay = lambda t: env[min(int(t * 100), len(env) - 1)] > umbral
    print(f"fps={fps} nivel voz={voz:.1f} dB umbral={umbral:.1f} dB")

    # 1) límites de cada palabra afinados con la energía
    seg = []
    for i, w in enumerate(W):
        t0, t1 = w["t0"], w["t1"]
        prev_fin = W[i - 1]["t1"] if i else 0.0
        inicio_frase = i == 0 or re.search(r"[.?!]$", W[i - 1]["w"]) is not None
        back = 0.25 if (inicio_frase or t1 - t0 < 0.12) else 0.04
        while t0 - 0.01 > prev_fin and t0 > 0 and t1 - t0 < 3 and (t0_orig := w["t0"]) - t0 < back and hay(t0 - 0.01):
            t0 -= 0.01
        nxt = W[i + 1]["t0"] if i + 1 < len(W) else 1e9
        while t1 + 0.01 < nxt and t1 - w["t1"] < 0.08 and env[min(int((t1 + 0.01) * 100), len(env) - 1)] > voz - 20:
            t1 += 0.01
        aire = 0.09 if re.search(r"[,.?!;:]$", w["w"]) else 0.06
        seg.append([t0, t1, aire])

    # 2) aire a cada lado y unión de huecos con voz continua >= 0,2 s
    out = []
    for i, (t0, t1, aire) in enumerate(seg):
        s0 = max(0.0, t0 - 0.03)
        s1 = t1 + aire - 0.03 if i + 1 < len(seg) else t1 + 0.12
        out.append([s0, s1])
    fuerte = voz - 17  # voz clara: una palabra mal colocada por Whisper deja >= 0,12 s seguidos por encima de este nivel
    for i in range(1, len(out)):
        gap0, gap1 = seg[i - 1][1], seg[i][0]
        if gap1 - gap0 >= 0.2 and W[i]["t0"] - W[i - 1]["t1"] < 1.0:
            tramo = env[int(gap0 * 100): int(gap1 * 100)] > fuerte
            run = best = 0
            for b in tramo:
                run = run + 1 if b else 0
                best = max(best, run)
            if best >= 12:  # voz continua: no se corta
                out[i - 1][1] = out[i][0] = gap1
    # 2b) silencios REALES dentro de los tramos (Whisper reparte palabras sin hueco sobre los respiros):
    #     cualquier tramo por debajo de voz-17 dB durante >= 0,12 s se deja en ~80 ms
    sil = env < voz - 17
    partido = []
    for s0, s1 in out:
        i0, i1 = int(s0 * 100), int(s1 * 100)
        i = i0
        corte0 = s0
        while i < i1:
            if sil[min(i, len(sil) - 1)]:
                j = i
                while j < i1 and sil[min(j, len(sil) - 1)]:
                    j += 1
                if (j - i) >= 12 and i > i0 + 5 and j < i1 - 5:
                    partido.append([corte0, i / 100 + 0.04])
                    corte0 = j / 100 - 0.04
                i = j
            else:
                i += 1
        partido.append([corte0, s1])
    # 2c) recorte a la extensión VOCAL real de cada tramo: 60 ms antes de la primera voz y 80 ms (120 tras coma/punto) después
    #     de la última; un tramo sin voz clara (chasquido, respiro, cola) se descarta
    voc = env > voz - 22
    def fin_puntuado(t):
        j = min(range(len(W)), key=lambda q: abs(W[q]["t1"] - t))
        return abs(W[j]["t1"] - t) < 0.4 and re.search(r"[,.?!;:]$", W[j]["w"]) is not None
    afinado = []
    for s0, s1 in partido:
        i0, i1 = int(s0 * 100), min(int(s1 * 100) + 1, len(voc))
        idx = np.nonzero(voc[i0:i1])[0]
        if len(idx) < 4:  # menos de 40 ms de voz clara: no es voz
            continue
        v0, v1 = (i0 + idx[0]) / 100, (i0 + idx[-1] + 1) / 100
        s0n = max(s0, v0 - 0.06)
        s1n = min(s1, v1 + (0.12 if fin_puntuado(v1) else 0.08))
        if s1n - s0n >= 0.1:
            afinado.append([s0n, s1n])
    out = afinado
    # 3) a fotograma exacto y fusión de solapes
    f = lambda t: round(t * fps) / fps
    seg_f = []
    for s0, s1 in out:
        s0, s1 = f(s0), max(f(s1), f(s0) + 1 / fps)
        if seg_f and s0 <= seg_f[-1][1] + 1e-6:
            seg_f[-1][1] = max(seg_f[-1][1], s1)
        else:
            seg_f.append([s0, s1])

    # 3b) VERIFICACIÓN: transcribe el corte (solo audio) y recorta voz de más (tomas que Whisper no vio la primera vez)
    if not a.sin_verificar:
        seg_f = verificar(a.bruto, seg_f, W, fps)

    # mapa origen -> corte y palabras en tiempos del corte
    acum, mapa = 0.0, []
    for s0, s1 in seg_f:
        mapa.append({"src0": round(s0, 4), "src1": round(s1, 4), "cut0": round(acum, 4)})
        acum += s1 - s0
    def a_corte(t):
        for m in mapa:
            if m["src0"] - 1e-3 <= t <= m["src1"] + 1e-3:
                return m["cut0"] + (t - m["src0"])
        return None
    palabras_corte = []
    for w in W:
        c0, c1 = a_corte(w["t0"]), a_corte(w["t1"])
        if c0 is not None and c1 is not None:
            palabras_corte.append({**w, "c0": round(c0, 3), "c1": round(c1, 3)})
    print(f"{len(seg_f)} tramos | {acum:.2f}s de {W[-1]['t1']:.1f}s | palabras mapeadas {len(palabras_corte)}/{len(W)}")

    # 4) render por tramos (en paralelo), unión sin recodificar, audio a WAV con fades de 8 ms y loudnorm 2 pasadas
    import concurrent.futures as cf
    import os
    import shutil
    import tempfile
    tmpd = tempfile.mkdtemp(prefix="corte_")

    def tramo(k):
        s0, s1 = seg_f[k]
        nf = round((s1 - s0) * fps)
        v = os.path.join(tmpd, f"v{k:03d}.mp4")
        au = os.path.join(tmpd, f"a{k:03d}.wav")
        r = sh(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{s0:.5f}", "-i", a.bruto, "-map", "0:v:0", "-frames:v", str(nf),
                "-vf", f"fps={fps},scale={a.ancho}:{a.alto}:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-preset", "fast",
                "-crf", "16", "-g", str(fps * 2), "-an", "-r", str(fps), v])
        if r.returncode:
            raise SystemExit(r.stderr[-800:])
        d = nf / fps
        r = sh(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{s0:.5f}", "-i", a.bruto, "-map", "0:a:0", "-t", f"{d:.5f}", "-ac", "1", "-ar", "48000",
                "-af", f"afade=t=in:d=0.008,afade=t=out:st={max(d - 0.008, 0):.5f}:d=0.008", "-c:a", "pcm_s16le", au])
        if r.returncode:
            raise SystemExit(r.stderr[-800:])
        return v, au

    with cf.ThreadPoolExecutor(3) as ex:
        res = list(ex.map(tramo, range(len(seg_f))))
    lv, la = os.path.join(tmpd, "v.txt"), os.path.join(tmpd, "a.txt")
    open(lv, "w").write("".join(f"file '{v}'\n" for v, _ in res))
    open(la, "w").write("".join(f"file '{x}'\n" for _, x in res))
    vid, wav = os.path.join(tmpd, "video.mp4"), os.path.join(tmpd, "audio.wav")
    for cmd in (["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lv, "-c", "copy", vid],
                ["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", la, "-c", "copy", wav]):
        r = sh(cmd)
        if r.returncode:
            raise SystemExit(r.stderr[-800:])
    p1 = sh(["ffmpeg", "-hide_banner", "-i", wav, "-af", f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"]).stderr
    m = json.loads(p1[p1.rindex("{"): p1.rindex("}") + 1])
    ln = (f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    r = sh(["ffmpeg", "-loglevel", "error", "-y", "-i", vid, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", ln,
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", a.corte])
    if r.returncode:
        raise SystemExit(r.stderr[-800:])
    shutil.rmtree(tmpd, ignore_errors=True)
    json.dump({"fps": fps, "tramos": mapa, "duracion": round(acum, 3), "palabras": palabras_corte},
              open(a.corte + ".cuts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("OK ->", a.corte)


if __name__ == "__main__":
    main()
