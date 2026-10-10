import {AbsoluteFill, Audio, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import './fuentes';
import type {Edicion, Escena} from './types';
import {Subs} from './Subs';
import {Broll, Copiar, Cta, LowerThird, Notas, Periodico, Reloj} from './escenas';
import {C, FUENTE, clamp, entra, out5, sale} from './util';

type Clave = Extract<Escena, {tipo: 'claveDetras'}>;

/* Zoom por tramos (punch-in alterno) + deriva lenta */
const useZoom = (ed: Edicion) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  let k = 0;
  ed.zooms.forEach(([ti], i) => {
    if (t >= ti) k = i;
  });
  const [t0, esc] = ed.zooms[k];
  const t1 = ed.zooms[k + 1]?.[0] ?? ed.frames / fps;
  const deriva = interpolate(t, [t0, t1], [0, 0.025], clamp);
  return esc + deriva;
};

const Camara: React.FC<{ed: Edicion; zoom: number; mascara?: string}> = ({ed, zoom, mascara}) => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      transform: `scale(${zoom})`,
      transformOrigin: '56% 46%',
      ...(mascara ? {WebkitMaskImage: `url(${mascara})`, maskImage: `url(${mascara})`, WebkitMaskSize: '100% 100%', maskSize: '100% 100%'} : {}),
    }}
  >
    <OffthreadVideo src={staticFile(ed.camara)} muted={!!mascara} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
  </div>
);

/* Rótulo que va DETRÁS de la persona, en tres formatos distintos */
const TextoClave: React.FC<{e: Clave; dur: number}> = ({e, dur}) => {
  const frame = useCurrentFrame();
  const a = entra(frame, 0, 6) * sale(frame, dur, 7);
  const sube = interpolate(frame, [0, 9], [70, 0], {...clamp, easing: out5});
  const escala = interpolate(frame, [0, dur], [0.96, 1.05], clamp);
  const brillo = (c: string) => `0 10px 60px rgba(0,0,0,0.45), 0 0 90px ${c}66`;
  const ajusta = (l: string, max: number, ancho: number) => Math.min(max, Math.floor(ancho / (l.length * 0.64)));

  if (e.estilo === 'diagonal') {
    const deriva = interpolate(frame, [0, dur], [40, -40], clamp);
    const barra = entra(frame, 6, 12);
    return (
      <div style={{position: 'absolute', left: 50, top: 300, opacity: a, transform: `translate(${deriva}px, ${sube * 0.6}px) rotate(-7deg)`, transformOrigin: 'left top'}}>
        {e.lineas.map((l, i) => (
          <div key={i} style={{fontFamily: FUENTE, fontWeight: 800, fontSize: ajusta(l, 200, 900), lineHeight: 1, letterSpacing: -6, marginLeft: i * 150, marginTop: i ? 10 : 0, color: i ? C.acento2 : C.texto, textShadow: brillo(i ? C.acento2 : C.acento)}}>
            {l}
          </div>
        ))}
        <div style={{height: 12, width: 620 * barra, background: C.acento, borderRadius: 6, marginTop: 22, marginLeft: 150, boxShadow: `0 0 40px ${C.acento}`}} />
      </div>
    );
  }
  if (e.estilo === 'gigante') {
    const [pequena, grande] = e.lineas;
    return (
      <div style={{position: 'absolute', left: 0, right: 0, top: 150, opacity: a, transform: `translateY(${sube * 0.5}px) scale(${escala})`, textAlign: 'center'}}>
        <div style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 112, letterSpacing: 18, color: C.acento2, textShadow: brillo(C.acento2)}}>{pequena}</div>
        <div style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 760, lineHeight: 0.82, letterSpacing: -30, color: C.texto, textShadow: brillo(C.acento), marginTop: 150}}>{grande}</div>
      </div>
    );
  }
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 350, opacity: a, transform: `translateY(${sube}px) scale(${escala})`, textAlign: 'center'}}>
      {e.lineas.map((l, i) => (
        <div key={i} style={{fontFamily: FUENTE, fontWeight: 800, fontSize: ajusta(l, 250, 960), lineHeight: 0.98, letterSpacing: -6, marginTop: i ? 14 : 0, color: i % 2 ? C.acento2 : C.texto, textShadow: brillo(i % 2 ? C.acento2 : C.acento)}}>
          {l}
        </div>
      ))}
    </div>
  );
};

/* Rótulo DELANTE con marcador (sin recorte de persona) */
const ClaveMarcador: React.FC<{e: Extract<Escena, {tipo: 'claveFrente'}>; f0: number; dur: number}> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = entra(frame, 0, 7) * sale(frame, dur, 7);
  const sube = interpolate(frame, [0, 9], [50, 0], {...clamp, easing: out5});
  const ini = Math.round(e.resaltarT * fps) - f0;
  const barra = interpolate(frame, [ini, ini + 9], [0, 100], {...clamp, easing: out5});
  const [uno, dos] = e.lineas;
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 290, opacity: a, transform: `translateY(${sube}px)`, textAlign: 'center'}}>
      <div style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 124, letterSpacing: -3, color: C.texto, textShadow: '0 8px 40px rgba(0,0,0,0.6)'}}>{uno}</div>
      <div style={{display: 'inline-block', fontFamily: FUENTE, fontWeight: 800, fontSize: 250, lineHeight: 1, letterSpacing: -8, color: C.texto, marginTop: 6, padding: '0 34px', backgroundImage: `linear-gradient(transparent 50%, ${C.acento2} 50%, ${C.acento2} 94%, transparent 94%)`, backgroundRepeat: 'no-repeat', backgroundSize: `${barra}% 100%`, textShadow: '0 8px 40px rgba(0,0,0,0.55)', transform: 'rotate(-2deg)'}}>
        {dos}
      </div>
    </div>
  );
};

export const Vertical: React.FC<{ed: Edicion}> = ({ed}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const zoom = useZoom(ed);
  const fr = (t: number) => Math.round(t * fps);
  const claves = ed.escenas.filter((e): e is Clave => e.tipo === 'claveDetras');
  const claveActiva = claves.some((e) => frame >= fr(e.t0) && frame <= fr(e.t1));
  const todasClaves = ed.escenas.filter((e) => e.tipo === 'claveDetras' || e.tipo === 'claveFrente');
  const oscuro = todasClaves.reduce((m, e) => Math.max(m, entra(frame, fr(e.t0), 6) * sale(frame, fr(e.t1), 6) * (frame >= fr(e.t0) && frame <= fr(e.t1) ? 1 : 0)), 0);

  return (
    <AbsoluteFill style={{background: C.fondo}}>
      <Camara ed={ed} zoom={zoom} />
      <AbsoluteFill style={{background: `rgba(13,13,26,${0.38 * oscuro})`}} />

      {/* rótulos detrás de la persona */}
      {claves.map((e, i) => (
        <Sequence key={`c${i}`} from={fr(e.t0)} durationInFrames={fr(e.t1) - fr(e.t0) + 1}>
          <TextoClave e={e} dur={fr(e.t1) - fr(e.t0)} />
        </Sequence>
      ))}
      {claveActiva && (
        <>
          <Img src={staticFile(`${ed.id}/matte/m_${frame}.png`)} style={{position: 'absolute', width: 1, height: 1, opacity: 0}} />
          <Camara ed={ed} zoom={zoom} mascara={staticFile(`${ed.id}/matte/m_${frame}.png`)} />
        </>
      )}

      {/* degradado inferior para leer los subtítulos */}
      <AbsoluteFill style={{background: 'linear-gradient(180deg,rgba(0,0,0,0) 62%,rgba(0,0,0,0.42) 100%)', pointerEvents: 'none'}} />

      {/* escenas sobre la cámara */}
      {ed.escenas.map((e, i) => {
        const f0 = fr(e.t0);
        const dur = fr(e.t1) - f0;
        const comun = {f0, dur};
        let nodo: React.ReactNode = null;
        if (e.tipo === 'lowerThird') nodo = <LowerThird e={e} {...comun} />;
        if (e.tipo === 'reloj') nodo = <Reloj e={e} {...comun} />;
        if (e.tipo === 'notas') nodo = <Notas e={e} {...comun} />;
        if (e.tipo === 'copiar') nodo = <Copiar e={e} {...comun} />;
        if (e.tipo === 'periodico') nodo = <Periodico e={e} {...comun} />;
        if (e.tipo === 'broll') nodo = <Broll e={e} {...comun} />;
        if (e.tipo === 'cta') nodo = <Cta e={e} {...comun} />;
        if (e.tipo === 'claveFrente') nodo = <ClaveMarcador e={e} f0={f0} dur={dur} />;
        return nodo ? (
          <Sequence key={i} from={f0} durationInFrames={dur + 1}>
            {nodo}
          </Sequence>
        ) : null;
      })}

      <Subs chunks={ed.chunks} />

      {/* efectos de sonido: pista única mezclada con precisión de muestra (pipeline/08_sfx_bed.py) */}
      <Audio src={staticFile(`${ed.id}/sfx_bed.wav`)} />
    </AbsoluteFill>
  );
};
