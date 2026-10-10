---
name: feedback_sonido
description: Reglas de sonido y voz de Ángel
metadata:
  type: feedback
---
- **Solo efectos REALES** (clics, teclado, papel, whoosh, golpes). NUNCA sonidos generados con IA: «se nota que la edición es muy IA». Librería: Mixkit + pack propio de Ángel.
- **Tienen que OÍRSE** pero sin molestar (pista de efectos ~7 dB LUFS bajo la voz, limitador a -6 dBFS). Antes estaban demasiado bajos y Ángel no los notó.
- **Riser desde el principio del hook** (acaba en el golpe de la 1.ª palabra clave) y antes de los momentos clave (pregunta, CTA). **Clic + golpe cuando aparece cada rótulo clave.** Un efecto específico por cada acción (grapadora, lápiz, rotulador, notificación, interruptor de luz, abrir interfaz, teclas, obturador, reloj).
- **Sincronía por TRANSITORIO** al fotograma exacto del evento (pista única a nivel de muestra: `08_sfx_bed.py`).
- **Voz:** EQ + de-esser + compresor suave; SIN reducción de ruido (su sala está a -77 dB). **Filtro de eco en apartes/paréntesis** o ideas dadas por hechas (ej. «y no necesitas convertir tu empresa en una multinacional»): `03c_apartes.py` propone, `04c_voz_fx.py` aplica (eco/reverb/telefono). Máx. 1-2 por vídeo.
- Música: la del pack son pistas comerciales → NO usar sin permiso. Si se pide música, libre de derechos, volumen bajo.
**How to apply:** ver «Sonido (reglas)» y «Voz FX» en CLAUDE.md.
