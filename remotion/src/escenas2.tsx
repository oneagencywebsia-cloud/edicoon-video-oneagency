import React from 'react';
import {Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Escena} from './types';
import {C, FUENTE, clamp, cristal, entra, out5, sale, sombraTexto, vis} from './util';

type P<T extends Escena['tipo']> = {e: Extract<Escena, {tipo: T}>; f0: number; dur: number};
const useAt = (f0: number) => {
  const {fps} = useVideoConfig();
  return (t: number) => Math.round(t * fps) - f0;
};

/* ───────── Tu sector (conecta con el cliente ideal) ───────── */
const ICONOS: Record<string, React.ReactNode> = {
  comercio: <path d="M4 9l2-5h12l2 5v2a3 3 0 0 1-6 0 3 3 0 0 1-6 0 3 3 0 0 1-6 0V9zM5 14v6h14v-6" />,
  clinica: <path d="M10 3h4v7h7v4h-7v7h-4v-7H3v-4h7z" />,
  despacho: (
    <>
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M3 13h18" />
    </>
  ),
  obra: <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-3 3-2.4-.6-.6-2.4z" />,
  transporte: (
    <>
      <path d="M2 6h11v9H2zM13 9h4l3 3v3h-7z" />
      <circle cx="7" cy="17" r="2" />
      <circle cx="17" cy="17" r="2" />
    </>
  ),
};
export const Sectores: React.FC<P<'sectores'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const at = useAt(f0);
  const fuera = sale(frame, dur, 8);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 400, opacity: fuera}}>
      <div style={{display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 18, padding: '0 36px'}}>
        {e.items.map((it, i) => {
          const s = at(it.t);
          const p = interpolate(frame, [s, s + 9], [0, 1], {...clamp, easing: out5});
          const col = [C.acento, '#60a5fa', '#ffffff', C.acento2, '#93c5fd'][i % 5];
          return (
            <div key={i} style={{...cristal, opacity: p, transform: `translateY(${(1 - p) * 50}px) scale(${0.85 + 0.15 * p})`, height: 112, borderRadius: 56, padding: '0 38px 0 28px', display: 'flex', alignItems: 'center', gap: 16}}>
              <svg width="54" height="54" viewBox="0 0 24 24" fill="none" stroke={col} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" style={{filter: `drop-shadow(0 0 10px ${col}99)`}}>
                {ICONOS[it.icono]}
              </svg>
              <span style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 46, color: '#fff', textShadow: sombraTexto}}>{it.texto}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/* ───────── Móvil: avisos sin contestar ───────── */
const Icono: React.FC<{tipo: 'chat' | 'obra' | 'tel'}> = ({tipo}) => {
  const bg = tipo === 'chat' ? '#25b866' : tipo === 'tel' ? '#34c759' : C.acento;
  return (
    <div style={{width: 76, height: 76, borderRadius: 20, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>
      <svg width="44" height="44" viewBox="0 0 24 24" fill="#fff">
        {tipo === 'chat' && <path d="M12 3C6.5 3 2 6.7 2 11.3c0 2.5 1.3 4.7 3.4 6.2L4.5 21l3.8-1.9c1.2.4 2.4.6 3.7.6 5.5 0 10-3.7 10-8.4S17.500 3 12 3z" />}
        {tipo === 'tel' && <path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25 11.400 11.400 0 0 0 3.600.6 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.500a1 1 0 0 1 1 1c0 1.300.2 2.500.6 3.600a1 1 0 0 1-.25 1z" />}
        {tipo === 'obra' && <path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm-9 14l-4-4 1.400-1.400L10 14.200l6.600-6.600L18 9z" />}
      </svg>
    </div>
  );
};
export const Movil: React.FC<P<'movil'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = useAt(f0);
  const fuera = sale(frame, dur, 8);
  const vistos = e.avisos.filter((a) => frame >= at(a.t)).length;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: fuera}}>
      {e.avisos.map((a, i) => {
        const s = at(a.t);
        if (frame < s) return null;
        const p = spring({frame: frame - s, fps, config: {damping: 14, stiffness: 170}});
        const tiembla = a.tipo === 'tel' ? Math.sin((frame - s) * 1.6) * (frame - s < 22 ? 5 : 0) : 0;
        return (
          <div key={i} style={{position: 'absolute', left: 60, right: 60, top: 150 + i * 172, height: 150, borderRadius: 38, background: 'rgba(250,251,255,0.93)', boxShadow: '0 24px 60px rgba(0,0,0,0.4)', display: 'flex', alignItems: 'center', gap: 22, padding: '0 26px', transform: `translateY(${(1 - p) * -170}px) translateX(${tiembla}px) scale(${0.94 + 0.06 * p})`, opacity: Math.min(1, p * 1.6)}}>
            <Icono tipo={a.tipo} />
            <div style={{flex: 1, fontFamily: FUENTE}}>
              <div style={{display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: 28, color: '#6b7185'}}>
                <span>{a.app}</span>
                <span>ahora</span>
              </div>
              <div style={{fontWeight: 800, fontSize: 42, color: '#12142a', marginTop: 2}}>{a.titulo}</div>
              <div style={{fontWeight: 500, fontSize: 34, color: '#3b4058'}}>{a.texto}</div>
            </div>
            {a.tipo === 'tel' && (
              <div style={{width: 64, height: 64, borderRadius: '50%', background: '#34c759', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 34, color: '#fff', fontWeight: 800}}>✓</div>
            )}
          </div>
        );
      })}
      {vistos > 0 && (
        <div style={{position: 'absolute', right: 40, top: 100, minWidth: 120, height: 60, borderRadius: 30, padding: '0 22px', background: C.acento2, color: '#fff', fontFamily: FUENTE, fontWeight: 800, fontSize: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: `0 10px 30px ${C.acento2}88`, transform: `scale(${1 + Math.max(0, 1 - ((frame - at(e.avisos[vistos - 1].t)) / 6)) * 0.25})`}}>
          {vistos} sin contestar
        </div>
      )}
    </div>
  );
};

/* ───────── Noche: la luz cambia (conecta con «segundo turno») ───────── */
export const Noche: React.FC<P<'noche'>> = ({dur}) => {
  const frame = useCurrentFrame();
  const a = entra(frame, 0, 14) * sale(frame, dur, 14);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: a, pointerEvents: 'none'}}>
      <div style={{position: 'absolute', inset: 0, background: 'rgba(8,16,52,0.34)'}} />
      <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0) 30%, rgba(3,6,28,0.72) 100%)'}} />
    </div>
  );
};

/* ───────── Tu día: lo que solo tú puedes hacer vs. lo que se repite ───────── */
export const Donut: React.FC<P<'donut'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const at = useAt(f0);
  const a = vis(frame, 0, dur, 10, 8);
  const R = 170, W = 46, L = 2 * Math.PI * R;
  const lleno = interpolate(frame, [4, 26], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const partir = interpolate(frame, [at(e.partirT), at(e.partirT) + 12], [0, 1], {...clamp, easing: out5});
  const solo = e.soloTu; // 0..1 (visual, sin cifras)
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: 130, height: 600, opacity: a}}>
      <div style={{...cristal, position: 'absolute', left: 46, right: 46, top: 0, bottom: 0, borderRadius: 54}} />
      <svg width="440" height="440" viewBox="-220 -220 440 440" style={{position: 'absolute', left: 80, top: 80, transform: 'rotate(-90deg)'}}>
        <circle r={R} fill="none" stroke="rgba(255,255,255,0.14)" strokeWidth={W} />
        <circle r={R} fill="none" stroke="#9fb4e8" strokeWidth={W} strokeDasharray={`${L * lleno * (1 - solo)} ${L}`} strokeDashoffset={-L * solo * partir} strokeLinecap="butt" style={{filter: 'drop-shadow(0 0 14px #60a5fa88)'}} />
        <circle r={R} fill="none" stroke={C.acento} strokeWidth={W} strokeDasharray={`${L * lleno * solo * partir} ${L}`} strokeLinecap="butt" style={{filter: `drop-shadow(0 0 18px ${C.acento})`}} />
      </svg>
      <div style={{position: 'absolute', left: 80, top: 80, width: 440, height: 440, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FUENTE, fontWeight: 800, fontSize: 150, color: '#fff', textShadow: sombraTexto}}>
        {partir > 0.5 ? '¿?' : 'TÚ'}
      </div>
      <div style={{position: 'absolute', left: 560, top: 150, right: 90, fontFamily: FUENTE}}>
        <div style={{opacity: partir, transform: `translateX(${(1 - partir) * 40}px)`, marginBottom: 56}}>
          <div style={{width: 44, height: 12, borderRadius: 6, background: C.acento, boxShadow: `0 0 20px ${C.acento}`, marginBottom: 12}} />
          <div style={{fontWeight: 800, fontSize: 46, color: '#fff', lineHeight: 1.1}}>Lo que solo puedes hacer tú</div>
        </div>
        <div style={{opacity: entra(frame, 18, 10), transform: `translateX(${(1 - entra(frame, 18, 10)) * 40}px)`}}>
          <div style={{width: 44, height: 12, borderRadius: 6, background: '#9fb4e8', marginBottom: 12}} />
          <div style={{fontWeight: 800, fontSize: 46, color: '#fff', lineHeight: 1.1}}>Lo que se repite cada día</div>
        </div>
      </div>
    </div>
  );
};

/* ───────── Sello (pegatina) ───────── */
export const Sello: React.FC<P<'sello'>> = ({e, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame, fps, config: {damping: 9, stiffness: 190, mass: 0.8}});
  const sacude = frame < 8 ? Math.sin(frame * 3) * (8 - frame) * 0.6 : 0;
  const a = sale(frame, dur, 7);
  return (
    <div style={{position: 'absolute', left: e.x, top: e.y, opacity: a, transform: `translate(${sacude}px, ${-sacude}px) rotate(${e.giro}deg) scale(${1 + (1 - p) * 1.8})`, transformOrigin: 'center'}}>
      <div style={{padding: '14px 44px', borderRadius: 28, background: `linear-gradient(135deg,${C.acento},#1d4ed8)`, border: '6px solid #fff', boxShadow: `0 26px 60px rgba(0,0,0,0.5), 0 0 60px ${C.acento}99`, fontFamily: FUENTE, fontWeight: 800, fontSize: 92, color: '#fff', letterSpacing: 4, textShadow: '0 4px 0 rgba(0,0,40,0.5)'}}>
        {e.texto}
      </div>
    </div>
  );
};
