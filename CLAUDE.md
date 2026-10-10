# Proyecto: edición de vídeo con IA (marca blanca) — O.N.E-Agency

**ANTES DE EDITAR CUALQUIER VÍDEO: lee `memoria/MEMORY.md` y todos los archivos que enlaza. Son las preferencias de Ángel y se aplican en TODOS los vídeos.**
Si Ángel da un consejo nuevo: actualiza el archivo de memoria que lo cubra (no dupliques) y haz commit.

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

## Procedimiento de cámara (probado en video1)
1. `python pipeline/drive_api.py get <id> --dest raw/<video>`
2. `python pipeline/02b_islas.py raw/<video>/<bruto>.MOV videos/<video>/islas.json` (transcripción por islas de voz; ~90 s por 77 s de vídeo en CPU)
3. `python pipeline/03_tomas.py videos/<video>/islas.json videos/<video>/palabras.json --quitadas videos/<video>/quitadas.json [--prep tomas.prep.json]`
   - Revisar lo que imprime. Se queda la ÚLTIMA versión de cada frase.
4. `python pipeline/01_cut_silences.py raw/<video>/<bruto>.MOV videos/<video>/corte.mp4 --words videos/<video>/palabras.json`
   - Verifica solo: transcribe el corte y recorta voz de más. Deja `corte.mp4.cuts.json` (mapa origen->corte).
5. `python pipeline/02_transcribe.py videos/<video>/corte.mp4 videos/<video>/corte.trans.json` -> palabras en tiempos del corte (texto de los subtítulos y anclas).
## Reglas técnicas añadidas (video1)
- Whisper estira palabras sobre tomas fallidas que no transcribe. Usar islas de voz (02b) para decidir tomas y recortes.
- Nunca cortar solo por tiempos de palabra: hay respiros DENTRO de las islas. El corte recorta cada tramo a su extensión vocal real
  (voz-22 dB, márgenes 60 ms antes y 80/120 ms después) y quita silencios internos >= 0,12 s (voz-17 dB).
- Un cortador con ffmpeg `trim`+`concat` sobre un 4K en un solo filtro agota la memoria: cortar por tramos y unir con concat demuxer (copy).
- Umbrales demasiado agresivos recortan inicios/finales suaves («a otro» -> «u otro»): comprobar siempre transcribiendo el corte.
- El suelo de ruido de la sala de Ángel es ~-77 dB; la voz ~-31 dB (p90).
- Nombres propios: Whisper escribe «one -agency .es»/«guangianagency»: corregir con glosario en los subtítulos.

## Procedimiento de edición completa (probado en video1)
Después de los pasos 1-5 de cámara:
6. `python pipeline/04_voz.py videos/<v>/corte.mp4 videos/<v>/corte_voz.mp4` (EQ + de-esser + compresor 1,8:1, -16 LUFS; SIN reducción de ruido: la sala ya está a -77 dB).
7. `python pipeline/05_matte.py videos/<v>/corte.mp4 videos/<v>/matte --ventanas 3.5-5.0,...` (recorte de persona SOLO en las ventanas de rótulos «detrás de ti»; rembg u2net_human_seg en CPU, ~1 s/fotograma).
8. B-roll: `ffmpeg -i raw/<v>/<b-roll>.MOV -map 0:v:0 -an -vf "fps=30,scale=1080:1920,format=yuv420p" -c:v libx264 -crf 20 -g 30 videos/<v>/broll1.mp4`
9. Escribir `videos/<v>/guion.json` (escenas por tiempos del corte, correcciones de texto, efectos con `en` = instante del evento).
10. `python pipeline/06_edicion.py <v>` -> `edicion.json` (subtítulos en bloques + posiciones exactas de efectos).
11. `python pipeline/08_sfx_bed.py <v>` -> `sfx_bed.wav` (mezcla a nivel de muestra + ducking bajo la voz).
12. `cd remotion && export REMOTION_BROWSER=$PWD/../tools/chrome-nosandbox.sh && npx tsc --noEmit` y fotogramas de control `npx remotion still src/index.ts Vertical ../out/qa/x.png --frame=N`
13. `npx remotion render src/index.ts Vertical ../out/<v>.mp4 --codec=h264 --crf=18 --audio-bitrate=256k --concurrency=3` (~4 min para 37 s, CPU).
14. `python pipeline/07_final.py out/final/<v>.mp4 out/<v>.mp4` (-14 LUFS) + `out/final/descripcion.txt`.

## Catálogo de rótulos clave (variar SIEMPRE el formato; no repetir el mismo dos veces seguidas)
- `claveDetras` + `estilo`: `centro` (2 líneas enormes), `diagonal` (inclinado a la izquierda con barra), `gigante` (palabra enorme + una pequeña encima). Van detrás de la persona (necesitan matte).
- `claveFrente` + `estilo: marcador` (delante, con subrayado de rotulador animado).
- Otras escenas: `lowerThird`, `reloj`, `notas`, `copiar`, `periodico`, `broll`, `cta`.

## Sonido (reglas)
- Solo efectos REALES (Mixkit, `videos/_shared/sfx/`, regenerables con `python pipeline/00_sfx.py`; hay que tener el catálogo en `/tmp/mixkit_catalogo.json`).
- Sincronía por TRANSITORIO: `ancla: inicio` (golpes, clics), `pico` (whoosh), `fin` (risers: el clímax cae en `en`, `largo` = segundos de subida).
- Solo hay 2 risers reales en el catálogo (`riser_suspense`, `riser_trailer`); el resto son tonos planos. Se recortan al tramo que acaba en el clímax.
- Risers antes de los momentos clave (gancho, pregunta, CTA); golpe en el inicio de la palabra clave; efecto específico por acción
  (grapadora, lápiz, rotulador, notificación de mensaje, interruptor de luz, abrir/cerrar interfaz, teclas sueltas en copiar-pegar).
- Ducking en `08_sfx_bed.py`; comprobar con la medición «efecto a menos de 6 dB de la voz» que solo quedan golpes en el arranque de palabras.

## Librería PROPIA de Ángel (PACKS FOR EDITORS.zip, 2,1 GB, en Drive)
- Id de Drive: 1cpTu1-qJYjlcqQAE_ZbxURD8vNxiLV6d. Se baja con `drive_api.py get` a `raw/sfx_pack/` y se descomprime en `raw/sfx_pack/x/` (carpeta aislada).
- Contenido: SOUND EFFECTS (122 archivos), BROLL CINEMÁTICO (175 clips 720x1280, 24 fps, sin nombres), LUTS (12 .cube), CINEMATIC OVERLAYS (1),
  MÚSICA (5, de artistas comerciales: NO usar sin permiso), presets de CapCut/Premiere/DaVinci (no sirven con Remotion), BRUTOS PARA PRACTICAR.
- `python pipeline/00_sfx_pack.py "raw/sfx_pack/x/PACKS/SOUND EFFECTS"` -> `videos/_shared/sfx/pack/*.wav` + `pack_index.json` (95 sonidos con tipo, pico, inicio y subida).
  En el guion se usan con prefijo `p/` (ej. `p/02_riser`). NO se sube a git (licencia sin verificar).
- Risers reales del pack: `p/02_riser` (3,9 s, pico 3,19), `p/01_riser` (5,8 s, pico 5,38), `p/riser_1`, `p/riser` (1,8 s). `p/reloj` = tic cada 0,2 s; `p/106_counter_9` = contador de dígitos.
- Descartados: «among us», «Windows_error», «CENSORED», música.
- Se mide el enmascarado en la BANDA DEL HABLA (300-3500 Hz): los graves (sub drops) casi no tapan; los golpes/risers deben quedar >= 8 dB bajo la voz salvo el transitorio del arranque.

## Presets de rótulo clave (remotion/src/presets.tsx) — iluminación, sombras y animación por letras
- `preset`: `neon` (tubo azul con parpadeo y bloom), `cromo` (metal con extrusión azul y barrido de luz), `ambar` (oro/fuego con extrusión),
  `cristal` (letras de vidrio con borde y reflejo), `foco` (blanco cálido con haz de luz), `hielo` (azul helado). No usar siempre el mismo ni todo naranja.
- Escena `clave`: `plano: detras|frente`, `layout: centro|diagonal|gigante`, `preset`, `lineas`. Detrás de la persona requiere matte de esa ventana (05_matte.py).
- Subtítulos normales: palabra activa en píldora que alterna azul / blanco / naranja.
- Escenas que conectan con el cliente ideal (pymes): `sectores` (comercio, clínica, despacho, obra, transporte), `movil` (avisos sin contestar),
  `noche` (oscurece y enfría = «segundo turno»), `donut` (lo que solo tú puedes hacer vs. lo que se repite; SIN cifras inventadas),
  `sello` (pegatina «GRATIS»), más `notas`, `copiar`, `periodico`, `broll`, `cta`. Las tarjetas de cristal son OSCURAS (contraste con la pared clara).
## Sonido audible (ajustes tras el feedback de Ángel)
- Riser DESDE EL INICIO del hook (acaba en el golpe de la 1.ª palabra clave), clic + golpe en cada rótulo clave, efecto por cada acción.
- `sfx_gain` 1.7 en el guion, ducking suave y limitador a -6 dBFS en la pista de efectos. Objetivo: pista de efectos ~7 dB (LUFS) por debajo de la voz.
## Color y b-roll del pack de Ángel
- LUT: `python pipeline/04b_color.py corte_voz.mp4 corte_color.mp4` (Oceano_oscuro a 0,55). Los otros 11 LUTs ensucian la piel.
- De 175 b-rolls solo encajan 2-3 (131 = casa/papeles/velas día->noche; 7 = estadio vacío de noche, parece de PELÍCULA: licencia dudosa). Es stock de estilo de vida/viajes.
- OVERLAY 4.mp4 es un croma verde (inservible).

## Voz FX en apartes (eco) — `voz_fx` en guion.json
- `python pipeline/03c_apartes.py videos/<v>/corte.trans.json` propone tramos (frases tipo «y no necesitas…», «por cierto», «obviamente»).
- `python pipeline/04c_voz_fx.py videos/<v>/corte_voz.mp4 videos/<v>/corte_vozfx.mp4 --guion videos/<v>/guion.json` (eco | reverb | telefono) y DESPUÉS `04b_color.py corte_vozfx.mp4 corte_color.mp4`.
- Orden de voz/color: corte -> 04_voz (EQ) -> 04c_voz_fx -> 04b_color. Los subtítulos dejan un rastro visual de eco durante el tramo (`vozFx` en edicion.json).
