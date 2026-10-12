---
name: feedback_mirada
description: Corrección de mirada DESCARTADA (2026-10-12): Ángel mirará a cámara al grabar; no aplicar 09_mirada salvo que lo pida
metadata:
  type: feedback
---
Ángel pidió (2026-10-11) corregir la mirada para que mire a cámara.
**Diagnóstico en su vídeo 1:** mira ABAJO (media 0,35, picos 0,70) y algo a su derecha (0,21) en el ~90 % de los fotogramas: mira su propia imagen/pantalla del móvil bajo el objetivo. Lleva gafas.
**Qué se hace:** `pipeline/09_mirada.py` (MediaPipe Face Landmarker + deformación local del iris dentro de la apertura del ojo, suavizado temporal, sin actuar en parpadeos) y se MIDE con `09b_medir_mirada.py`. Orden: 04_voz -> 04c_voz_fx -> **09_mirada** -> 04b_color. Parámetros usados: `--fuerza 2.4 --max 0.45 --vy 1.0`.
**Límites (honestos):** corrige bien el desvío HORIZONTAL (0,21 -> 0,12) pero el vertical solo mejora un poco (0,35 -> 0,32): su «mirar abajo» es sobre todo párpado caído. Subir la ganancia vertical (`--vy 3`) deja los ojos entrecerrados y artificiales: NO usarlo. Para un efecto fuerte hace falta un modelo neuronal de redirección de mirada (NVIDIA Broadcast «Eye Contact», o herramientas tipo Descript/CapCut si lo incluyen) que no está disponible en la nube.
**How to apply:** pasar siempre 09_mirada y enseñar antes/después (`--antes-despues`). Recomendar a Ángel al grabar: mirar al OBJETIVO (no a la pantalla), apagar la previsualización, pegar una marca junto a la lente o usar un teleprompter con el texto pegado al objetivo, y subir el móvil a la altura de los ojos.
**Requisitos del contenedor:** `pip install mediapipe opencv-python-headless`, `apt-get install -y libegl1 libgles2`, modelo `videos/_shared/modelos/face_landmarker.task` (storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task).

## DECISIÓN FINAL (2026-10-12)
Ángel dijo «déjalo, al final en los vídeos miraré a la cámara»: **no hacer corrección de mirada** en los próximos vídeos (se saltan 09_mirada y la sesión local de GPU; `LOCAL_MIRADA.md` queda obsoleto, no ejecutarlo). El video1 se queda como está (v9, con la corrección clásica sutil). Solo retomar la corrección si Ángel la pide de nuevo en un vídeo concreto.
