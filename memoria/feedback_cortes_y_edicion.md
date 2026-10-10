---
name: feedback_cortes_y_edicion
description: Cómo cortar y editar el bruto (criterio profesional)
metadata:
  type: feedback
---
- Editar «profesionalmente», haciendo lo necesario sin preguntar cada paso; si se equivoca 60 veces, cortar con inteligencia y quedarse con la ÚLTIMA toma buena.
- Cortes secos y dinámicos; cualquier pausa que se note sobra (máx. ~0,25 s entre frases). Quitar coletillas finales («gracias»), claquetas, marcadores («no, no») y frases abandonadas.
- Whisper estira palabras sobre tomas fallidas: decidir por ISLAS de voz (`02b_islas.py`) y VERIFICAR siempre transcribiendo el corte.
**Why:** el bruto de Ángel tiene muchas tomas repetidas y tropiezos; Whisper normal no las ve.
**How to apply:** pasos 1-5 de «Procedimiento de cámara» en CLAUDE.md.
