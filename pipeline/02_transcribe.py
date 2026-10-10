"""02_transcribe.py <vídeo|audio> <salida.json> [--modelo turbo] [--idioma es]

Transcribe con marcas de tiempo por palabra (faster-whisper). En la nube va en CPU (int8);
con NVIDIA usa CUDA si está disponible. Salida: {"duracion", "palabras": [{"w","t0","t1","p"}]}.
"""
import argparse
import json
import subprocess
import tempfile
import time

from faster_whisper import WhisperModel


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    ap.add_argument("salida")
    ap.add_argument("--modelo", default="turbo")
    ap.add_argument("--idioma", default="es")
    a = ap.parse_args()
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.entrada, "-vn", "-ac", "1", "-ar", "16000", tmp.name], check=True)
        try:
            m = WhisperModel(a.modelo, device="cuda", compute_type="float16")
        except Exception:
            m = WhisperModel(a.modelo, device="cpu", compute_type="int8", cpu_threads=4)
        t = time.time()
        segs, info = m.transcribe(tmp.name, language=a.idioma, word_timestamps=True, vad_filter=False,
                                  condition_on_previous_text=False, beam_size=5)
        palabras = [{"w": w.word.strip(), "t0": round(w.start, 3), "t1": round(w.end, 3), "p": round(w.probability, 3)}
                    for s in segs for w in (s.words or [])]
    json.dump({"duracion": round(info.duration, 3), "palabras": palabras}, open(a.salida, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(palabras)} palabras de {info.duration:.1f}s en {time.time() - t:.1f}s")


if __name__ == "__main__":
    main()
