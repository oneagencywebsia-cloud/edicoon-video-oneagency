# Estado del proyecto

Idioma de trabajo: español. Trabajar por fases y parar en cada punto de control hasta que Ángel conteste.
No publicar, no gastar créditos y no subir archivos a ningún servicio sin preguntar antes.

## Hecho
- Fase 0 completa: `marca/marca.json`, `marca/canal.json`, `marca/cliente.md`, `marca/avatar.png`.
- PC verificado: Windows 11 Pro, Ryzen 7 5800X, 32 GB, RTX 5060 (8 GB), driver 616.92, CUDA 13.4.
- Instalado y comprobado: Node 24.14.0, ffmpeg 8.1 (gyan full build), Python 3.12.10 (instalado con winget).
- Python del sistema es 3.14.3: NO usarlo (sin wheels para faster-whisper/ctranslate2). Usar `py -3.12 -m venv .venv`.

## Decisiones
- Canal O.N.E-Agency, @one-agency.es, español. Rótulos: Ángel Carrillo · CEO & FOUNDER.
- Formato: VERTICAL 1080x1920, 60 fps (graba el móvil en 4K 60). Parametrizar ancho/alto/fps; horizontal sigue disponible.
- Casi todo es solo cámara (20-60 s), sin grabación de pantalla. Sin palmada de sincronización.
- B-rolls: clips sin audio que se solapan sobre la cámara en la palabra exacta; no todos los vídeos llevan b-roll.
- Marca: fondo #0d0d1a, blanco, azul #3B82F6 (acento), naranja #F97316 (acento 2), cristal translúcido. Plus Jakarta Sans.
- Subtítulos: palabras clave grandes, semi detrás de la persona (recorte con rembg en GPU), aparición animada + SFX; el resto en posición fija con palabra activa en naranja.
- Animaciones con MUCHA variación (recorte de periódico/blog señalando el dato, captura de chat, post, nota, ficha de cristal, gráfico...). No repetir fondo ni formato seguidos.
- SFX: solo efectos reales de librería (clicks, teclado, whoosh, foley). Nada generado con IA. Preguntar antes de descargar.
- Objetivo editorial: concienciar sobre la IA con honestidad y empatizar con la audiencia (ver `marca/cliente.md`).
- Brutos en Google Drive vía API (nunca la app de escritorio): `O.N.E Agency / videos / contenido en vertical`,
  con `videos brutos/<video N>` y `videos finales/<video N>`. Ruta exacta por confirmar en fase 1b.
- Brutos y entregas, siempre procesados en local (`raw/<id>/`, `out/`).

## Siguiente: Fase 1 (instalación) ⏸
1. `py -3.12 --version` (debe dar 3.12.x) y crear `.venv`.
2. Instalar numpy y faster-whisper con CUDA; probar con un clip corto (large-v3 o turbo).
3. Proyecto Remotion en `remotion/` (1080x1920, 60 fps) y prueba de render de un still.
4. Anotar cada fallo en «Reglas técnicas» del CLAUDE.md.
Después: fase 1b (Drive API), fase 2 (estructura), fase 3 (pipeline de cámara), fase 4 (escenas), etc.

## ACTUALIZACIÓN: se trabaja TODO en la nube (decisión de Ángel)
- Fase 1 hecha en la nube: .venv (faster-whisper turbo CPU OK), Remotion 1080x1920@60 con still de prueba OK
  (`out/qa/prueba.png`), fuentes locales. Detalles y fallos en `CLAUDE.md`.
- El PC con Windows ya no se usa para procesar. Node/ffmpeg/Python del PC no hacen falta.
- Pendiente fase 1b: acceso a Drive. Probar primero el conector de Drive de la sesión (descarga de un vídeo corto);
  si no sirve para archivos grandes, OAuth «aplicación de escritorio» con `drive.readonly`.
  Las credenciales NO van al repo (`secrets/` ignorado); en la nube hay que guardarlas como secretos del entorno.
- Limitación: el contenedor es efímero. Lo que importa va a git (sin vídeos) y a Drive (entregas).
