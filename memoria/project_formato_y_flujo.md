---
name: project_formato_y_flujo
description: Formato de vídeo, estructura en Drive, entregables y flujo de trabajo
metadata:
  type: project
---
- **Formato:** VERTICAL 1080×1920, 20–60 s. fps de salida = fps de la cámara (30 o 60, depende del vídeo). Casi todo solo cámara; sin palmada de sincronización; a veces b-rolls sin audio. Horizontal sigue soportado (cambiar ancho/alto/fps en marca.json).
- **Drive:** `O.N.E Agency / videos / contenido en vertical / videos brutos / <video N>` (brutos) y `videos finales / <video N>` (entregas). Lectura por API con `drive_api.py` (variables GOOGLE_*). Solo lectura: NO subir a Drive sin permiso nuevo y sin preguntar.
- **Entregables por vídeo:** vídeo final (-14 LUFS) + `descripcion.txt` con título x3, descripción, ESTRATEGIA y CTAs inteligentes ligados al tema (CTA de venta último y suave).
- **Sin Blotato:** Ángel publica a mano. No hay script de publicación.
- **Flujo:** semi-automático: Ángel sube brutos y dice «edita el vídeo N». Se hace TODO en la nube. Ángel revisa el borrador y pide ajustes.
**How to apply:** seguir «Procedimiento de edición completa» de CLAUDE.md; ver [[reference_drive_y_packs]].
- **Entrega de brutos (desde 2026-10-14):** en Drive `Vídeos Brutos/Vídeo N/` hay un `IMG_xxxx.MOV` (4K, 60 fps, VFR) y un `WhatsApp Audio ….mp4` con el audio del MICRO. Se SILENCIA el audio del vídeo y se pone el del micro sincronizado (`00b_sync_audio.py`, error < 1 ms). Cortar a 60 fps constantes (`--fps 60`) aunque el móvil grabe a ~55 de media.
- **Cola final:** si la última palabra es la del CTA, `01b_cola.py` congela 0,95 s para que la animación final (comentario) se vea.
- **No mirar el documento de guiones** de Drive: Ángel cambia cosas al grabar; se edita solo lo que dice en el vídeo (transcripción).
- **Entorno:** Ángel quiere LOCAL (GPU RTX 5060) por velocidad; en la nube (4 CPU, sin GPU) un vídeo tarda ~45-60 min.
