# Proyecto: edición de vídeo con IA (marca blanca) — O.N.E-Agency

Ver `ESTADO.md` para el estado y las decisiones. Identidad solo desde `marca/` (nada fijo en el código).

## Entorno de trabajo: la NUBE (contenedor Linux, 4 CPU, 15 GB, sin GPU)
- Python: `.venv` (Python 3.13). Activar con `. .venv/bin/activate`.
- Transcripción: `faster-whisper`, modelo `turbo`, `device="cpu"`, `compute_type="int8"`.
- Remotion: `cd remotion && export REMOTION_BROWSER=$PWD/../tools/chrome-nosandbox.sh`
  - QA: `npx remotion still src/index.ts <Comp> ../out/qa/x.png --frame=N`
  - Antes de cada render: `npx tsc --noEmit`.

## Reglas técnicas (fallos conocidos)
- `faster-whisper` 1.2.1 falla con PyAV 19 (`metadata_errors`): fijar `av>=14,<16`.
- Python 3.14 (PC de Ángel) no sirve para faster-whisper: usar 3.12 o el Python de la nube.
- Chromium como root en el contenedor no arranca: usar el wrapper `tools/chrome-nosandbox.sh` (añade `--no-sandbox`)
  apuntando al headless shell de Remotion (`npx remotion browser ensure`).
- Chromium no confía en el certificado del proxy de la nube: NO cargar fuentes ni recursos de internet desde Remotion.
  Descargarlos con curl a `videos/_shared/` y usar `staticFile()`. Las fuentes están en `videos/_shared/fonts/`.
- `publicDir` de Remotion = `videos/` (así llega a `_shared/` y a cada `<id>/`).
- Fuentes en Remotion: cargar con `FontFace` + `delayRender` (ver `remotion/src/fuentes.ts`) y poner `fontFamily` en el contenedor raíz.
- La webcam/móvil entra a ~30 fps aunque grabe a 60: `mpdecimate` antes de `fps` si se ve a saltos.
- Umbral de voz relativo al nivel de la voz (voz − 24 dB). Palabras de Whisper con duración ~0 mal colocadas: no quitar huecos con voz ≥ 0,2 s.
- Procesar siempre desde disco local; brutos de Drive por API a `raw/<id>/`. Nada de apps de escritorio sincronizadas.
