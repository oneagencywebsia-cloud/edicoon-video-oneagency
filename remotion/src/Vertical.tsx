import {AbsoluteFill, Audio, Easing, Img, OffthreadVideo, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import './fuentes';
import type {Edicion, Escena} from './types';
import {Subs} from './Subs';
import {Broll, Copiar, Cta, LowerThird, Notas, Periodico, Reloj} from './escenas';
import {Agenda, Comentario, Donut, Movil, Noche, Sectores, Sello} from './escenas2';
import {Linea} from './presets';
import {C, clamp, entra, out5, sale} from './util';

type ClaveE = Extract<Escena, {tipo: 'clave'}>;

/* Zoom por tramos (punch-in alterno) + deriva lenta */
const useZoom = (ed: Edicion) => {
  const frame = useCurrentFrame();
  if (ed.zoomCurva) return ed.zoomCurva[Math.min(frame, ed.zoomCurva.length - 1)];
  const {fps} = useVideoConfig();
  const t = frame / fps;
  let k = 0;
  ed.zooms.forEach(([ti], i) => {
    if (t >= ti) k = i;
  });
  const [t0, esc] = ed.zooms[k];
  const t1 = ed.zooms[k + 1]?.[0] ?? ed.frames / fps;
  // zoom de énfasis: in = golpe rápido y vuelta suave; out = arranca cerca y se abre
  let extra = 0;
  (ed.enfasis ?? []).forEach((e) => {
    const f0 = Math.round(e.t0 * fps);
    const f1 = Math.round(e.t1 * fps);
    let v: number;
    if (e.modo === 'out') v = interpolate(frame, [f0, f0 + 4, f0 + 20], [0, 1, 0], {...clamp, easing: Easing.out(Easing.cubic)});
    else if (frame < f1) v = interpolate(frame, [f0, f0 + 5], [0, 1], {...clamp, easing: out5});
    else v = interpolate(frame, [f1, f1 + 10], [1, 0], {...clamp, easing: Easing.inOut(Easing.cubic)});
    extra += e.escala * v;
  });
  return Math.min(esc + interpolate(t, [t0, t1], [0, 0.025], clamp) + extra, 1.16);
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

/* Rótulo clave con preset (luz, sombras, extrusión) en tres composiciones */
const Clave: React.FC<{e: ClaveE; dur: number}> = ({e, dur}) => {
  const ajusta = (l: string, max: number, ancho: number) => Math.min(max, Math.floor(ancho / (l.length * 0.64)));
  const luz = null; // el fondo NO cambia de color al salir un rótulo (Ángel, 2026-10-10)
  if (e.layout === 'diagonal') {
    return (
      <>
        {luz}
        <div style={{position: 'absolute', left: 50, top: 170, transform: 'rotate(-7deg)', transformOrigin: 'left top'}}>
          {e.lineas.map((l, i) => (
            <div key={i} style={{marginLeft: i * 150, marginTop: i ? 10 : 0}}>
              <Linea texto={l} preset={e.preset} size={ajusta(l, 200, 900)} ls={-5} inicio={i * 4} dur={dur} />
            </div>
          ))}
        </div>
      </>
    );
  }
  if (e.layout === 'gigante') {
    const [pequena, grande] = e.lineas;
    return (
      <>
        {luz}
        <div style={{position: 'absolute', left: 0, right: 0, top: 150, textAlign: 'center'}}>
          <Linea texto={pequena} preset={e.preset} size={112} ls={18} dur={dur} />
          <div style={{marginTop: 150}}>
            <Linea texto={grande} preset={e.preset} size={760} ls={-30} inicio={5} dur={dur} />
          </div>
        </div>
      </>
    );
  }
  return (
    <>
      {luz}
      <div style={{position: 'absolute', left: 0, right: 0, top: 50, textAlign: 'center'}}>
        {e.lineas.map((l, i) => (
          <div key={i} style={{marginTop: i ? 14 : 0}}>
            <Linea texto={l} preset={e.preset} size={ajusta(l, 250, 960)} ls={-6} inicio={i * 4} dur={dur} />
          </div>
        ))}
      </div>
    </>
  );
};

export const Vertical: React.FC<{ed: Edicion}> = ({ed}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const zoom = useZoom(ed);
  const fr = (t: number) => Math.round(t * fps);
  const claves = ed.escenas.filter((e): e is ClaveE => e.tipo === 'clave');
  // TODO lo que no es pantalla completa va DETRÁS de la persona (Ángel, 2026-10-14: nada tapa la cara)
  const FRENTE = new Set(['broll', 'cta', 'sello']);
  const detrasEsc = ed.escenas.filter((e) => !FRENTE.has(e.tipo));
  const detrasActiva = detrasEsc.some((e) => frame >= fr(e.t0) && frame <= fr(e.t1));
  const paso = ed.mattePaso ?? 1;
  const matte = staticFile(`${ed.id}/matte/m_${frame - (frame % paso)}.png`);
  const nodoEscena = (e: Escena, f0: number, dur: number): React.ReactNode => {
    const comun = {f0, dur};
    if (e.tipo === 'lowerThird') return <LowerThird e={e} {...comun} />;
    if (e.tipo === 'reloj') return <Reloj e={e} {...comun} />;
    if (e.tipo === 'notas') return <Notas e={e} {...comun} />;
    if (e.tipo === 'copiar') return <Copiar e={e} {...comun} />;
    if (e.tipo === 'periodico') return <Periodico e={e} {...comun} />;
    if (e.tipo === 'broll') return <Broll e={e} {...comun} />;
    if (e.tipo === 'cta') return <Cta e={e} {...comun} />;
    if (e.tipo === 'sectores') return <Sectores e={e} {...comun} />;
    if (e.tipo === 'movil') return <Movil e={e} {...comun} />;
    if (e.tipo === 'noche') return <Noche e={e} {...comun} />;
    if (e.tipo === 'donut') return <Donut e={e} {...comun} />;
    if (e.tipo === 'sello') return <Sello e={e} {...comun} />;
    if (e.tipo === 'agenda') return <Agenda e={e} {...comun} />;
    if (e.tipo === 'comentario') return <Comentario e={e} {...comun} />;
    if (e.tipo === 'clave') return <Clave e={e} dur={dur} />;
    return null;
  };
  const capa = (lista: Escena[], k: string) =>
    lista.map((e, i) => {
      const f0 = fr(e.t0);
      const dur = fr(e.t1) - f0;
      const nodo = nodoEscena(e, f0, dur);
      return nodo ? (
        <Sequence key={`${k}${i}`} from={f0} durationInFrames={dur + 1}>
          {nodo}
        </Sequence>
      ) : null;
    });

  return (
    <AbsoluteFill style={{background: C.fondo}}>
      <Camara ed={ed} zoom={zoom} />

      {/* escenas y rótulos DETRÁS de la persona */}
      {capa(detrasEsc, 'd')}
      {detrasActiva && (
        <>
          <Img src={matte} style={{position: 'absolute', width: 1, height: 1, opacity: 0}} />
          <Camara ed={ed} zoom={zoom} mascara={matte} />
        </>
      )}

      <AbsoluteFill style={{background: 'linear-gradient(180deg,rgba(0,0,0,0) 62%,rgba(0,0,0,0.42) 100%)', pointerEvents: 'none'}} />

      {/* pantalla completa / botón: delante */}
      {capa(ed.escenas.filter((e) => FRENTE.has(e.tipo)), 'f')}

      <Subs chunks={ed.chunks} vozFx={ed.vozFx} ocultar={claves.map((e) => ({t0: e.t0, t1: e.t1, tokens: e.lineas.join(' ').split(/\s+/).map((x) => x.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]/g, '')).filter(Boolean)}))} />

      {/* efectos de sonido: pista única (pipeline/08_sfx_bed.py) */}
      <Audio src={staticFile(`${ed.id}/sfx_bed.wav`)} />
    </AbsoluteFill>
  );
};
