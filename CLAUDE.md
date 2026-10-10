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

## Entregable: descripcion.txt (por vídeo)
Se genera a partir de la transcripción del vídeo, nunca genérica. Estructura:
1. Gancho (1-2 líneas): el problema que resuelve el vídeo, con las palabras de la audiencia (pymes, poco técnicos).
2. Resumen con valor: qué va a aprender/llevarse, en 2-4 líneas, sin humo.
3. Estrategia: por qué este vídeo (objetivo: concienciar sobre la IA y conectar), a quién va y qué acción buscamos.
4. CTAs inteligentes ligados al tema (elegir 2-3): p. ej. «comenta qué tarea repites cada día» (si habla de tareas),
   «guárdalo para cuando automatices X», y el CTA principal: diagnóstico gratuito de 30 min en https://one-agency.es.
   El CTA de venta va el último y suave; primero valor.
5. Hashtags y palabras clave del tema (5-8) y 3 opciones de título/primera línea.
Tono: cercano, tuteo, sin jerga, honesto con los límites de la IA.

## Regla de b-roll (prioridad alta)
- Un b-roll solo se coloca donde lo que muestra tiene sentido directo con lo que dice Ángel en ese instante.
  Antes de colocarlo: mirar fotogramas del clip (qué muestra de verdad), leer la transcripción de ese tramo y justificar
  la pareja en una línea en el guion (`motivo`). Si no hay pareja clara, NO se coloca; no se rellena por rellenar.
- Anclar a la palabra exacta (inicio y fin), sin tapar frases clave del discurso ni los rótulos. Sin audio del b-roll.
- Lo mismo vale para las animaciones: cada una refuerza lo que se dice en ese momento (dato → recorte de prensa/blog, etc.),
  con variedad de formato y fondo entre una y otra.

## Móvil de Ángel (observado en el vídeo de prueba)
- Los .MOV son HEVC 3840x2160 con rotación -90 guardada (se ven 2160x3840 vertical). ffmpeg autorrota; no desactivarlo.
- El vídeo hablado a cámara llegó a 30 fps y el b-roll a 60 fps: normalizar todo a 60 fps de salida (o decidir con Ángel).
- Los .MOV traen pistas de datos extra; usar `-map 0:v:0 -map 0:a:0` al cortar.
- Drive: `python pipeline/drive_api.py info|ls|get <id|enlace> [--dest raw/<id>]` (solo lectura, reanudable, comprueba tamaño y ffprobe).
  El conector de Drive de la sesión NO sirve; usar la API con las variables GOOGLE_* (nunca imprimirlas).
- Transcripción: `python pipeline/02_transcribe.py <vídeo> videos/<id>/transcripcion.json` (CPU turbo: ~2,5 min para 77 s la primera vez por la descarga del modelo, ~20 s de cálculo).
