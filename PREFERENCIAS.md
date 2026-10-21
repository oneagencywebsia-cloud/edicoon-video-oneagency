# Cómo edita Ángel — todas sus preferencias (resumen, 2026-10-21)
Fuente completa: `memoria/*.md` y `CLAUDE.md`. Esto es el resumen para leer de un tirón.

## 1. Formato y calidad
- Vertical **1080×1920**, 20–60 s, **60 fps constantes** (el móvil graba 4K VFR ~55–60). Salida H.264, CRF 18 (`out/final/<v>.mp4`) y copias de envío (ligera ~23 MB, alta ~28 MB por el límite de 30 MB del chat).
- Sonido final **−14 LUFS** (voz −16 LUFS antes de mezclar), limitador, AAC 256 kbps.
- Color: LUT **Oceano_oscuro al 0,55** (los otros 11 ensucian la piel). Sin corrección de mirada (graba mirando a cámara).
- Vídeo con **audio del micro** (archivo aparte): se silencia el del vídeo y se sincroniza el del micro (correlación, error < 1 ms).

## 2. Corte
- Cortes secos y dinámicos; pausa máxima ~0,25 s; se queda la **ÚLTIMA toma buena**; fuera «gracias», claquetas y frases abandonadas.
- Se decide por islas de voz y se **verifica transcribiendo el corte**.
- Si la última palabra es el CTA, se alarga 0,95 s el final (fotograma congelado) para que se vea la animación.

## 3. Posición y composición
- **La cara siempre a la vista.** Ninguna animación la tapa: todo lo que no sea pantalla completa va **DETRÁS de la persona** (recorte con matte) y bien legible.
- **Zona segura:** nada pegado al borde de arriba (empezar hacia y≈150 px). Escenas compactas en **columnas laterales** (≈330 px) junto a la cabeza; rótulos clave en una sola línea arriba (top≈138). Subtítulos abajo (y 1400–1590).
- Animación a pantalla completa solo si es b-roll.

## 4. Subtítulos
- Palabra a palabra abajo; la palabra activa en **píldora de UN solo color (azul de marca)**; no cambiar de color.
- Máx. 4 palabras / 26 letras por bloque; no acabar en partícula («y», «de», «me»…).
- **No repetir lo que dice el rótulo clave** mientras está en pantalla.
- Corrección de nombres propios y errores de Whisper.

## 5. Rótulos clave (presets)
- Presets animados con luz, sombras largas y extrusión: neón, cromo, ámbar, cristal, foco, hielo, sombra. **No todos naranjas ni del mismo formato** seguidos; no siempre centrados/enormes.
- Van detrás de la persona; el fondo **no cambia de color ni brillo** cuando salen.

## 6. Animaciones
- **Mucha variedad**: nunca el mismo formato/fondo dos veces seguidas.
- Deben **conectar con el cliente ideal** (pymes: comercio, clínica, despacho, obra, transporte): papeleo, «segundo turno», llamadas sin contestar, copiar de un sitio a otro, CTA de comentario.
- Datos = recorte de periódico/blog; tarjetas de **cristal oscuro**; nada de cifras inventadas; negar = desvanecer, nunca tachones rojos.
- Escenas disponibles: nombre (lower third), sectores, reloj, notas, copiar-pegar, periódico, móvil con avisos, anillo «solo tú», agenda, lista lateral, sello, comentario, b-roll.
- **B-roll solo si tiene sentido con lo que se dice**, sin audio; no todos los vídeos llevan.

## 7. Zoom
- Zoom in/out suave (≈0,09–0,11, tope 1,18) en rótulos y momentos importantes, **nunca brusco**, siempre con su efecto de sonido sincronizado. Una sola curva por fotograma; los saltos de corte se disimulan con escalones suaves.

## 8. Sonido
- **Solo efectos REALES** (Mixkit + pack propio); nunca generados con IA. **Audibles sin molestar** (efectos ≈7 dB por debajo de la voz).
- **Riser desde el inicio del gancho** y antes de los momentos clave; **clic + golpe** cuando sale cada rótulo; un efecto por cada acción (teclas, grapadora, lápiz, notificación…); sincronía al fotograma por transitorio.
- Voz: EQ + de-esser + compresión suave, **sin reducción de ruido**. **Eco SUTIL** solo en apartes (máx. 1–2 por vídeo); el fuerte le molestó.
- Nada de música comercial sin permiso.

## 9. Descripción de cada vídeo (se entrega sin pedirla)
- Basada en **lo que se dice** (transcripción), profesional, con **neuromarketing sutil** y **nada forzado ni robótico**: tuteo, frases como habla Ángel, 3 títulos con ángulos distintos, hashtags útiles, nota de estrategia y CTA de diagnóstico gratuito (one-agency.es) al final y suave. Sin promesas de ahorro ni cifras inventadas.

## 10. Trabajo
- Edición semi-automática: Ángel sube brutos a Drive y dice «edita el vídeo N». Español, directo, conciso.
- **Nunca sin preguntar:** publicar, gastar créditos, subir archivos a servicios (Drive incluido).
- Preferencia: trabajar en **local con su RTX 5060** por velocidad.
