> **OBSOLETO (2026-10-12):** Ángel canceló este encargo; no ejecutar.

# Encargo para la sesión LOCAL (PC de Ángel, Windows 11, RTX 5060): mirada a cámara con IA

Eres la sesión local de Claude Code en el PC de Ángel (con GPU). Lee primero `memoria/MEMORY.md` y `memoria/feedback_mirada.md`, y `CLAUDE.md`.
Habla en español, conciso. NO subas nada a ningún servicio ni gastes créditos sin preguntar a Ángel.

## Objetivo
Ángel mira ABAJO (a la pantalla del móvil) en ~90 % de su vídeo. Quiere que parezca que mira al objetivo. En la nube lo intentamos con un método clásico
(`pipeline/09_mirada.py`: deformación del iris con MediaPipe) y solo corrige lo horizontal (0,21 -> 0,12); lo vertical casi no mejora (0,35 -> 0,32) y subir la
fuerza deja los ojos entrecerrados. Hace falta un modelo NEURONAL de redirección de mirada, que en la nube no hay (sin GPU).

## Entrada y salida
- Entrada: el bruto vertical del móvil `IMG_1279.MOV` (4K HEVC, 30 fps, rotación -90 guardada, con audio). Está en su Drive:
  `O.N.E Agency / videos / contenido en vertical / videos brutos / video 1` (id de archivo 1RumzQzxZU977aXJv4MO8PIz_dfveStgZ). Probablemente ya lo tiene en el PC.
- Salida: `IMG_1279_mirada.mp4`, MISMA duración, MISMOS fps (30) y MISMO número de fotogramas, misma resolución/orientación (respeta la rotación), audio copiado SIN tocar,
  vídeo en H.264 de alta calidad (>= 40 Mbps o crf <= 14). Los tiempos deben coincidir fotograma a fotograma con el original (la nube reutiliza los mismos cortes).
- Ángel lo subirá a Drive (misma carpeta); no lo subas tú. Al acabar, dile el nombre del archivo para que lo use la sesión de la nube.

## Cómo conseguirlo (probar en este orden; parar en el primero que dé buen resultado)
1. **NVIDIA Maxine / «Eye Contact» (Gaze Redirection)**: es el estado del arte para esto. NVIDIA Broadcast solo actúa sobre la cámara en directo; para ARCHIVOS hay que usar el
   **Maxine AR SDK (Gaze Redirection)** o el Video Effects SDK, con su ejemplo de línea de comandos que procesa un vídeo. Comprueba si está disponible para Windows y si soporta la
   RTX 5060 (Blackwell, sm_120: puede exigir una versión reciente del SDK/driver). Si hace falta cuenta/licencia de NVIDIA o descarga manual, PREGUNTA a Ángel.
2. **LivePortrait (KwaiVGI) con control de pupila** (p. ej. el nodo «Advanced LivePortrait» de ComfyUI, parámetros pupil_x / pupil_y y apertura de ojos). Es neuronal y corre en GPU.
   OJO: RTX 5060 = Blackwell -> necesita PyTorch >= 2.7 con CUDA 12.8 (índice `cu128`). Procesa por fotograma con suavizado temporal; vigila las GAFAS (reflejos azules),
   el parpadeo y el parpadeo temporal (flicker). Pega el resultado solo en la zona de los ojos para no degradar el resto de la cara.
3. Otra herramienta/modelo de gaze redirection que encuentres y que funcione en local (investiga; no inventes comandos).
4. Último recurso: `pipeline/09_mirada.py` (horizontal) tal cual.

## Cómo medir que funciona (obligatorio, con números y con ojos)
- `pip install mediapipe opencv-python-headless` (Python 3.12 en Windows) y el modelo `videos/_shared/modelos/face_landmarker.task`
  (https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task).
- `python pipeline/09b_medir_mirada.py original.mp4 corregido.mp4` -> objetivo: mirada hacia ABAJO media < 0,15, lateral < 0,10, «desvío > 0,4» < 5 %.
  Referencia actual (original): abajo 0,35, derecha 0,21, desvío > 0,4: 36 %.
- Revisa a mano hojas de contacto de los ojos a 3x (antes/después) en fotogramas repartidos y con parpadeos: sin ojos entrecerrados, sin «ojos de muñeco», sin saltos entre fotogramas,
  sin deformar las gafas ni los párpados. Si se ve artificial, NO lo des por bueno: enséñaselo a Ángel con las opciones.

## Guardar lo aprendido
Cuando funcione, documenta en `memoria/feedback_mirada.md` (qué herramienta, parámetros, tiempo de proceso, límites) y deja el script en `pipeline/` (p. ej. `09_mirada_gpu.py`)
con commit en la rama `claude/wonderful-brown-uceebk` (sin vídeos ni modelos pesados en git).

## Recomendaciones de grabación para Ángel (ya dadas; repítelas si el resultado no convence)
Mirar al objetivo, apagar la previsualización, móvil a la altura de los ojos, marca junto a la lente o teleprompter pegado al objetivo.
