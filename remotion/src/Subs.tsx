import {useCurrentFrame, useVideoConfig, spring} from 'remotion';
import type {Chunk} from './types';
import {C, FUENTE} from './util';

export const Subs: React.FC<{chunks: Chunk[]; vozFx?: {t0: number; t1: number; fx: string}[]}> = ({chunks, vozFx = []}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const i = chunks.findIndex((c, k) => {
    const sig = chunks[k + 1];
    const fin = sig && sig.t0 - c.t1 < 0.5 ? sig.t0 : c.t1 + 0.18;
    return t >= c.t0 - 0.03 && t < fin;
  });
  if (i < 0) return null;
  const c = chunks[i];
  const pill = [{fondo: C.acento, texto: '#fff'}, {fondo: '#ffffff', texto: '#0d0d1a'}, {fondo: C.acento2, texto: '#fff'}][i % 3];
  const eco = vozFx.some((v) => t >= v.t0 && t <= v.t1 + 0.2 && (v.fx === 'eco' || v.fx === 'reverb'));
  const pop = spring({frame: frame - Math.round((c.t0 - 0.03) * fps), fps, config: {damping: 16, stiffness: 260}, durationInFrames: 8});
  return (
    <div style={{position: 'absolute', left: 50, right: 50, top: 1400, height: 190, display: 'flex', justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
      {eco && [2, 1].map((k) => (
        <div key={k} style={{position: 'absolute', fontFamily: FUENTE, fontWeight: 800, fontSize: 78, lineHeight: 1.1, letterSpacing: -1.5, color: '#9fc4ff', opacity: 0.2 * k * (0.7 + 0.3 * Math.sin(frame / 3 + k)), transform: `scale(${1 + k * 0.07}) translateY(${-k * 16}px)`, filter: `blur(${k * 3}px)`, whiteSpace: 'pre'}}>
          {c.palabras.map((w) => w.w).join('  ')}
        </div>
      ))}
      <div style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 78, lineHeight: 1.1, letterSpacing: -1.5, transform: `scale(${0.9 + 0.1 * pop})`, opacity: Math.min(1, pop * 1.4)}}>
        {c.palabras.map((w, k) => {
          const sig = c.palabras[k + 1];
          const activa = t >= w.t0 - 0.02 && (!sig || t < sig.t0 - 0.02);
          return (
            <span key={k} style={{color: activa ? pill.texto : C.texto, background: activa ? pill.fondo : 'transparent', borderRadius: 22, padding: '0 16px', boxShadow: activa ? `0 10px 30px ${pill.fondo}88` : undefined, textShadow: activa && pill.fondo !== '#ffffff' ? '0 3px 0 rgba(0,0,0,0.25)' : '0 5px 26px rgba(0,0,0,0.7), 0 2px 4px rgba(0,0,0,0.7)', display: 'inline-block', margin: '0 6px', transform: activa ? 'scale(1.04) rotate(-1.2deg)' : 'none'}}>
              {w.w}
            </span>
          );
        })}
      </div>
    </div>
  );
};
