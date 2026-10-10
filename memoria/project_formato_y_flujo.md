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
