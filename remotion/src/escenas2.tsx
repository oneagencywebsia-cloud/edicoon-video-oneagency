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
const Icono: React.FC<{tipo: 'chat' | 'obra' | 'tel'; s?: number}> = ({tipo, s = 76}) => {
  const bg = tipo === 'chat' ? '#25b866' : tipo === 'tel' ? '#34c759' : C.acento;
  return (
    <div style={{width: s, height: s, borderRadius: s * 0.26, background: bg, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>
      <svg width={s * 0.58} height={s * 0.58} viewBox="0 0 24 24" fill="#fff">
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
  return (
    <div style={{position: 'absolute', inset: 0, opacity: fuera}}>
      {e.avisos.map((a, i) => {
        const s = at(a.t);
        if (frame < s) return null;
        const p = spring({frame: frame - s, fps, config: {damping: 14, stiffness: 170}});
        const tiembla = a.tipo === 'tel' ? Math.sin((frame - s) * 1.6) * (frame - s < 22 ? 5 : 0) : 0;
        return (
          <div key={i} style={{position: 'absolute', left: i % 2 === 0 ? 28 : 726, top: 175 + Math.floor(i / 2) * 225, width: 326, height: 206, borderRadius: 34, background: 'rgba(250,251,255,0.94)', boxShadow: '0 24px 60px rgba(0,0,0,0.4)', padding: '16px 20px', boxSizing: 'border-box', fontFamily: FUENTE, transform: `translateY(${(1 - p) * -170}px) translateX(${tiembla}px) scale(${0.94 + 0.06 * p})`, opacity: Math.min(1, p * 1.6)}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <Icono tipo={a.tipo} s={50} />
              <div style={{flex: 1, fontWeight: 700, fontSize: 24, color: '#6b7185'}}>{a.app}</div>
              <div style={{fontWeight: 700, fontSize: 22, color: '#6b7185'}}>ahora</div>
            </div>
            <div style={{fontWeight: 800, fontSize: 33, color: '#12142a', marginTop: 8, lineHeight: 1.05}}>{a.titulo}</div>
            <div style={{fontWeight: 500, fontSize: 25, color: '#3b4058', marginTop: 4, lineHeight: 1.1}}>{a.texto}</div>
          </div>
        );
      })}
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
  const R = 62, W = 22, L = 2 * Math.PI * R;
  const lleno = interpolate(frame, [4, 26], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const partir = interpolate(frame, [at(e.partirT), at(e.partirT) + 12], [0, 1], {...clamp, easing: out5});
  const solo = e.soloTu; // 0..1 (visual, sin cifras)
  return (
    <div style={{position: 'absolute', inset: 0, opacity: a}}>
      <div style={{...cristal, position: 'absolute', left: 30, top: 175, width: 330, height: 330, borderRadius: 44}}>
        <svg width="250" height="250" viewBox="-85 -85 170 170" style={{position: 'absolute', left: 40, top: 40, transform: 'rotate(-90deg)'}}>
          <circle r={R} fill="none" stroke="rgba(255,255,255,0.14)" strokeWidth={W} />
          <circle r={R} fill="none" stroke="#9fb4e8" strokeWidth={W} strokeDasharray={`${L * lleno * (1 - solo)} ${L}`} strokeDashoffset={-L * solo * partir} strokeLinecap="butt" style={{filter: 'drop-shadow(0 0 10px #60a5fa88)'}} />
          <circle r={R} fill="none" stroke={C.acento} strokeWidth={W} strokeDasharray={`${L * lleno * solo * partir} ${L}`} strokeLinecap="butt" style={{filter: `drop-shadow(0 0 12px ${C.acento})`}} />
        </svg>
        <div style={{position: 'absolute', left: 40, top: 40, width: 250, height: 250, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FUENTE, fontWeight: 800, fontSize: 92, color: '#fff', textShadow: sombraTexto}}>
          {partir > 0.5 ? '¿?' : 'TÚ'}
        </div>
      </div>
      <div style={{position: 'absolute', left: 726, top: 175, width: 326, fontFamily: FUENTE}}>
        <div style={{...cristal, borderRadius: 34, padding: '18px 22px', opacity: partir, transform: `translateX(${(1 - partir) * 60}px)`, marginBottom: 18, display: 'flex', alignItems: 'center', gap: 14}}>
          <div style={{width: 22, height: 22, borderRadius: 11, background: C.acento, boxShadow: `0 0 18px ${C.acento}`, flexShrink: 0}} />
          <div style={{fontWeight: 800, fontSize: 38, color: '#fff', lineHeight: 1.08}}>Lo que solo puedes hacer tú</div>
        </div>
        <div style={{...cristal, borderRadius: 34, padding: '18px 22px', opacity: entra(frame, 18, 10), transform: `translateX(${(1 - entra(frame, 18, 10)) * 60}px)`, display: 'flex', alignItems: 'center', gap: 14}}>
          <div style={{width: 22, height: 22, borderRadius: 11, background: '#9fb4e8', flexShrink: 0}} />
          <div style={{fontWeight: 800, fontSize: 38, color: '#fff', lineHeight: 1.08}}>Lo que se repite cada día</div>
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

/* ───────── Agenda del día (turno 1) ───────── */
export const Agenda: React.FC<P<'agenda'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const at = useAt(f0);
  const a = vis(frame, 0, dur, 10, 8);
  return (
    <div style={{position: 'absolute', inset: 0, opacity: a}}>
      <div style={{position: 'absolute', left: 30, top: 150, display: 'inline-flex', alignItems: 'center', gap: 12, padding: '6px 22px', borderRadius: 34, ...cristal, transform: `translateY(${(1 - entra(frame, 0, 12)) * -30}px)`}}>
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={C.acento2} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="4.2" fill={C.acento2} /><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1" /></svg>
        <span style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 28, color: C.texto, letterSpacing: 3}}>{e.titulo}</span>
      </div>
      {e.items.map((it, i) => {
        const f = frame - at(it.t);
        const p = entra(f, 0, 14);
        const tick = interpolate(f, [10, 20], [0, 1], clamp);
        const izq = i % 2 === 0;
        return (
          <div key={i} style={{position: 'absolute', left: izq ? 30 : 718, top: 232 + Math.floor(i / 2) * 190, width: 330, padding: '14px 22px 18px', borderRadius: 30, ...cristal, opacity: p, transform: `translateX(${(1 - p) * (izq ? -160 : 160)}px)`}}>
            <div style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 32, color: C.acento, fontVariantNumeric: 'tabular-nums'}}>{it.hora}</div>
            <div style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 46, color: C.texto, textShadow: sombraTexto, lineHeight: 1.02, marginTop: 2}}>{it.texto}</div>
            <div style={{position: 'absolute', right: 14, top: 14, width: 40, height: 40, borderRadius: '50%', background: C.acento, opacity: tick, transform: `scale(${0.6 + 0.4 * tick})`, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12.5l4.5 4.5L19 7" /></svg>
            </div>
          </div>
        );
      })}
    </div>
  );
};

/* ───────── Comentario (CTA: «comenta la palabra…») ───────── */
export const Comentario: React.FC<P<'comentario'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = useAt(f0);
  const a = vis(frame, 0, dur, 12, 8);
  const ini = at(e.escribeT);
  const env = at(e.enviaT);
  const n = Math.floor(interpolate(frame, [ini, env - 8], [0, e.palabra.length], {...clamp}));
  const enviado = frame >= env;
  const prensa = frame >= env && frame < env + 5;
  const pop = spring({frame: frame - env - 6, fps, config: {damping: 9, stiffness: 220}});
  const cursor = !enviado && frame % 20 < 12;
  return (
    <div style={{position: 'absolute', left: 80, top: 150, width: 920, opacity: a, transform: `translateY(${(1 - entra(frame, 0, 14)) * -60}px)`}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 20, padding: '14px 26px', borderRadius: 44, ...cristal}}>
        <div style={{width: 70, height: 70, borderRadius: '50%', background: `linear-gradient(135deg,${C.acento},${C.acento2})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FUENTE, fontWeight: 800, fontSize: 34, color: '#fff', flexShrink: 0}}>Tú</div>
        <div style={{flex: 1, minHeight: 70, display: 'flex', alignItems: 'center'}}>
          {!enviado && n === 0 && <span style={{fontFamily: FUENTE, fontWeight: 600, fontSize: 38, color: 'rgba(255,255,255,0.45)'}}>Añade un comentario…{cursor ? '|' : ''}</span>}
          {(enviado || n > 0) && (
            <span style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 58, color: C.texto, textShadow: sombraTexto}}>
              {e.palabra.slice(0, enviado ? e.palabra.length : n)}
              {cursor && n > 0 ? <span style={{color: C.acento}}>|</span> : null}
            </span>
          )}
        </div>
        {!enviado || prensa ? (
          <div style={{width: 74, height: 74, borderRadius: '50%', background: n >= e.palabra.length ? C.acento : 'rgba(255,255,255,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${prensa ? 0.86 : 1})`, boxShadow: n >= e.palabra.length ? `0 12px 40px ${C.acento}99` : undefined}}>
            <svg width="38" height="38" viewBox="0 0 24 24" fill="#fff"><path d="M3 11.5L21 3l-6.5 18-3.2-7.3z" /></svg>
          </div>
        ) : (
          <div style={{display: 'flex', alignItems: 'center', gap: 10, fontFamily: FUENTE, fontWeight: 700, fontSize: 34, color: 'rgba(255,255,255,0.8)'}}>
            <svg width="54" height="54" viewBox="0 0 24 24" style={{transform: `scale(${0.5 + 0.6 * Math.min(1.2, pop)})`}}><path d="M12 21s-7.5-4.6-9.6-9.4C.9 8 3.2 4.5 6.6 4.5c2 0 3.5 1.1 4.4 2.5.9-1.4 2.4-2.5 4.4-2.5 3.4 0 5.7 3.5 4.2 7.1C19.5 16.4 12 21 12 21z" fill="#ef4467" /></svg>
          </div>
        )}
      </div>
      <div style={{fontFamily: FUENTE, fontWeight: 700, fontSize: 26, color: 'rgba(255,255,255,0.85)', marginTop: 8, marginLeft: 108, opacity: enviado ? 1 : 0, textShadow: sombraTexto}}>ahora · 1 me gusta</div>
    </div>
  );
};
