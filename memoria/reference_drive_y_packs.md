---
name: reference_drive_y_packs
description: IDs, rutas y herramientas de acceso (sin secretos)
metadata:
  type: reference
---
- Repo: `oneagencywebsia-cloud/edicoon-video-oneagency`, rama `claude/wonderful-brown-uceebk` (sin `main`; PR pendiente).
- Drive: `python pipeline/drive_api.py info|ls|get <id|enlace> --dest raw/<video>` con variables de entorno GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET / GOOGLE_REFRESH_TOKEN (solo lectura; nunca imprimirlas). Si no existen en la sesión: repetir `pipeline/drive_auth.py` en el PC de Ángel y guardarlas como variables del entorno (ver docs del entorno).
- Pack de editor de Ángel: `PACKS FOR EDITORS.zip` id `1cpTu1-qJYjlcqQAE_ZbxURD8vNxiLV6d` (2,1 GB). Catálogo: `00_sfx_pack.py`. Procedencia/licencia SIN verificar.
- Vídeo de prueba: `raw/video1/` (IMG_1279.MOV cámara, IMG_1280.MOV b-roll de su web). Ids Drive en ESTADO.md.
- Contenedor efímero: 4 CPU, 15 GB, sin GPU; lo importante va a git (sin vídeos ni pack).
