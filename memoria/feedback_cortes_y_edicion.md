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
- **(2026-10-22) Tres defectos que Ángel detectó y quedan resueltos en el pipeline:** (1) «un milisegundo de errores» -> se descartan los tramos sin ninguna palabra (restos de tropiezos) y el relleno de tramos cortos se limita a 0,08 s por lado; (2) **volumen irregular** -> nivelación por tramo al nivel mediano de la voz (±8 dB) en `01_cut_silences.py` + `dynaudnorm` y compresor 2,2:1 en `04_voz.py`; (3) **palabras alargadas cortadas al final** -> la cola de cada palabra/tramo se extiende mientras haya voz > voz−28/30 dB (hasta 0,30/0,25 s). Si re-cortas: `01c_remapear_guion.py` traslada los tiempos del guion al corte nuevo y `05_matte.py` es reanudable.
- Subtítulos: Whisper cambia palabras entre pasadas; tras cada re-corte REVISAR la lista de bloques que imprime 06_edicion.py y corregir con `correcciones` (usar tokens exactos con puntuación).
