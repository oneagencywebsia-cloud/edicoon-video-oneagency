# Cómo edito tus vídeos, de principio a fin (detalle completo)

## A. Entrada
1. En Drive (`Vídeos Brutos/Vídeo N/`): `IMG_xxxx.MOV` (4K HEVC, 60 fps variable, rotación −90) y `WhatsApp Audio….mp4` (micro).
2. **Audio:** se SILENCIA el del vídeo y se pone el del micro (`00b_sync_audio.py`): correlación cruzada para el desfase, medición de deriva al inicio/final (atempo si > 200 ppm), el vídeo no se recodifica. Se comprueba el error residual (< 1 ms).
3. **No uso el documento de guiones**: solo lo que dices (transcripción).

## B. Corte
- `02b_islas.py`: Whisper turbo por islas de voz (porque Whisper estira palabras sobre tomas fallidas). `03_tomas.py`: se queda la ÚLTIMA toma buena de cada frase y quita claquetas, «gracias», ruidos y frases abandonadas (`--prep` para forzar decisiones).
- `01_cut_silences.py`: corte seco palabra a palabra, exacto a fotograma; aire 60 ms entre palabras (90 ms tras coma/punto); quita silencios internos ≥ 0,12 s; **tramo mínimo 0,30 s** (sin destellos); salida a **60 fps constantes**, 1080×1920; verifica transcribiendo el corte.
- `01b_cola.py`: si lo último es el CTA, congela 0,5–0,95 s para que se vea la animación final.

## C. Audio de la voz
`04_voz.py`: EQ + de-esser + compresor suave 1,8:1, **sin reducción de ruido**, −16 LUFS (loudnorm 2 pasadas). `04c_voz_fx.py`: eco/reverb solo en apartes (máx. 1–2 por vídeo, eco sutil: 1 rebote a 210 ms, decay 0,26).
Después `04b_color.py`: LUT **Oceano_oscuro al 0,55**.

## D. Subtítulos
**Normales (abajo, y 1400–1590):** Plus Jakarta Sans 800, 78 px, blancos con sombra; bloques de máx. 4 palabras/26 letras, nunca acaban en «y, de, tu, me, lo…»; cortan tras coma/punto. La palabra que suena va en **píldora azul `#3B82F6`** (texto blanco, ligero giro y escala 1,04). UN solo color. Entrada con spring (8 fotogramas). Si hay eco, dos copias fantasma azules claras.
**Destacados (rótulos clave, presets):** palabra(s) clave en grande y animadas por letras con luz y sombras: neón, cromo, ámbar, cristal, foco, hielo, sombra. Todos con extrusión + sombra larga + sombra de contacto; **van DETRÁS de ti** (recorte rembg) y subidos (top ≈138–150). Layouts: centro (una línea), diagonal (−5°), gigante (línea pequeña + palabra enorme). El subtítulo normal no repite lo que dice el rótulo mientras está en pantalla. El fondo nunca cambia de color.

## E. Animaciones (siempre DETRÁS de ti, nunca tapan la cara, zona segura arriba, columnas laterales ~330 px)
nombre (lower third), lista lateral, agenda, notas de papel, móvil con avisos, anillo «solo tú», copiar-pegar, recorte de periódico, reloj, sello, comentario (CTA «comenta la palabra…»), sectores, b-roll (pantalla completa, sin audio, solo si encaja). Tarjetas de cristal oscuro. Variedad: nunca el mismo formato seguidas. Cada una ilustra lo que dices en ese instante; sin cifras inventadas.

## F. Zoom
Una curva por fotograma (`zoomCurva`): zoom-in 12 fotogramas (seno), zoom-out 18 (smoothstep), amplitud 0,09–0,11, tope 1,18, paso máx. < 0,02; alterna in/out en cada rótulo y se añaden énfasis manuales en frases importantes. Escalones base (1,0↔1,06) en los saltos de corte, suaves y fuera de los énfasis. Cada zoom lleva su efecto: `loud_whip` (in) y `vs_short_whoosh_6` (out), con el pico a mitad de la rampa.

## G. Sonido (solo efectos REALES: Mixkit + tu pack; nunca IA)
Pista única a nivel de muestra (`08_sfx_bed.py`), sincronía por transitorio al fotograma, `sfx_gain` 1,7, ducking suave bajo la voz, limitador −6 dBFS; objetivo ≈ 7 dB por debajo de la voz.
- **Riser** (`p/02_riser`, `p/01_riser`, `p/riser`, `p/riser_1`) desde el inicio del gancho: acaba en el golpe del primer rótulo; también antes de los rótulos clave y del CTA.
- **En cada rótulo clave:** golpe grave (`p/deep_bass_hit_1` o `p/cinematic_bass_3`) + sub (`p/sub_bass_drop_2/4`, `p/sub_bass_hit`) + clic (`p/mouse_click_03/04`) + whoosh (`p/woosh_effect_6/12`).
- **Entradas de escena:** `p/vs_short_whoosh_1/4/5`, `interfaz_abre`/`interfaz_cierra`.
- **Avisos/listas:** `p/pop_up_sfx`, `mensaje_alerta`, `p/lighter_double_click_01`, teclas `p/mechanical_keyboard_click_05/07/09/19`.
- **Papel/oficina:** `papel_desliza`, `grapadora`, `lapiz_escribe`, `papel_periodico`, `periodico_cae`, `p/06572_marker_drawing_on_paper_full`, `p/camera_shutter`.
- **Reloj/contador:** `p/reloj`, `p/106_counter_9`. **Luz:** `interruptor_luz`. **Confirmación:** `tono_confirmacion`. **Eco:** `p/woosh_effect_5` al entrar. **Zooms:** `loud_whip`, `vs_short_whoosh_6`.
- Descartados: «among us», «Windows_error», «CENSORED». Música comercial: nunca sin permiso.

## H. Salida
Remotion (React) 1080×1920, 60 fps, H.264 CRF 18, audio 256 kbps → `07_final.py` normaliza a **−14 LUFS**. Copias de envío ≤ 30 MB. + `descripcion` (3 títulos, descripción natural con neuromarketing sutil, estrategia, CTA suave).

## I. Marca
Fondo `#0d0d1a`, texto `#ffffff`, azul `#3B82F6`, naranja `#F97316`, cristal `rgba(14,20,50,0.55)`; Plus Jakarta Sans 400–800 + JetBrains Mono; @one-agency.es; «Ángel Carrillo · CEO & FOUNDER».
