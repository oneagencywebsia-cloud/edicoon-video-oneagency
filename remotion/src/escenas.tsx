import {Img, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing} from 'remotion';
import type {Escena} from './types';
import {C, FUENTE, MONO, SERIF, clamp, cristal, entra, out5, sale, sombraTexto, vis} from './util';

type P<T extends Escena['tipo']> = {e: Extract<Escena, {tipo: T}>; f0: number; dur: number};
const useAt = (f0: number) => {
  const {fps} = useVideoConfig();
  return (t: number) => Math.round(t * fps) - f0;
};

/* ───────── Nombre y cargo ───────── */
export const LowerThird: React.FC<P<'lowerThird'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const a = vis(frame, 0, dur, 12, 8);
  const w = entra(frame, 0, 16);
  return (
    <div style={{position: 'absolute', left: 60, top: 190, opacity: a, display: 'flex', alignItems: 'center', gap: 24, transform: `translateX(${(1 - w) * -70}px)`}}>
      <Img src={staticFile('_shared/logos/avatar.png')} style={{width: 112, height: 112, borderRadius: '50%', border: `4px solid ${C.acento}`, boxShadow: `0 0 40px ${C.acento}88`}} />
      <div>
        <div style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 60, color: C.texto, lineHeight: 1.05, textShadow: sombraTexto}}>{e.nombre}</div>
        <div style={{fontFamily: FUENTE, fontWeight: 700, fontSize: 31, color: C.acento2, letterSpacing: 6, marginTop: 8, textShadow: sombraTexto}}>{e.cargo}</div>
        <div style={{height: 6, width: 380 * w, background: C.acento, marginTop: 12, borderRadius: 3}} />
      </div>
    </div>
  );
};

/* ───────── Reloj de cristal ───────── */
const minutos = (s: string) => {
  const [h, m] = s.split(':').map(Number);
  return h * 60 + m;
};
export const Reloj: React.FC<P<'reloj'>> = ({e, dur}) => {
  const frame = useCurrentFrame();
  const a = vis(frame, 0, dur, 10, 7);
  const p = interpolate(frame, [4, dur - 10], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const m = Math.round(minutos(e.desde) + (minutos(e.hasta) - minutos(e.desde)) * p);
  const hh = String(Math.floor(m / 60)).padStart(2, '0');
  const mm = String(m % 60).padStart(2, '0');
  return (
    <div style={{position: 'absolute', left: 190, top: 250, width: 700, height: 300, borderRadius: 52, ...cristal, opacity: a, transform: `translateY(${(1 - a) * 40}px) scale(${0.94 + 0.06 * a})`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'}}>
      <div style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 170, color: C.texto, fontVariantNumeric: 'tabular-nums', letterSpacing: -4, lineHeight: 1, textShadow: `0 0 50px ${C.acento}99`}}>
        {hh}
        <span style={{color: C.acento2, opacity: frame % 20 < 12 ? 1 : 0.25}}>:</span>
        {mm}
      </div>
      <div style={{fontFamily: FUENTE, fontWeight: 700, fontSize: 34, color: C.acento2, letterSpacing: 5, textTransform: 'uppercase', marginTop: 8}}>{e.etiqueta}</div>
    </div>
  );
};

/* ───────── Notas de papel ───────── */
export const Notas: React.FC<P<'notas'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = useAt(f0);
  const fuera = sale(frame, dur, 8);
  const rot = [-3, 2.5, -2, 3];
  return (
    <>
      {e.items.map((it, i) => {
        const s = at(it.t);
        const p = spring({frame: frame - s, fps, config: {damping: 13, stiffness: 150}});
        if (frame < s) return null;
        return (
          <div key={i} style={{position: 'absolute', left: 40 + (i % 2) * 34, top: 175 + i * 132, width: 500, height: 112, opacity: fuera, transform: `translateX(${(1 - p) * -560}px) rotate(${rot[i % 4] * p}deg)`, background: 'linear-gradient(180deg,#FFFBEA,#F7EFD0)', borderRadius: 10, boxShadow: '0 22px 50px rgba(0,0,0,0.38), 0 2px 0 rgba(0,0,0,0.08)', display: 'flex', alignItems: 'center', paddingLeft: 40, borderLeft: `14px solid ${i % 2 ? C.acento2 : C.acento}`}}>
            <span style={{fontFamily: FUENTE, fontWeight: 800, fontSize: 46, color: '#17172b', letterSpacing: -0.5}}>{it.texto}</span>
          </div>
        );
      })}
    </>
  );
};

/* ───────── Copiar y pegar ───────── */
const Ventana: React.FC<{x: number; titulo: string; children: React.ReactNode; rot?: number}> = ({x, titulo, children, rot = 0}) => (
  <div style={{position: 'absolute', left: x, top: 190, width: 470, height: 350, borderRadius: 26, overflow: 'hidden', background: '#F5F6FA', boxShadow: '0 30px 70px rgba(0,0,0,0.42)', transform: `rotate(${rot}deg)`}}>
    <div style={{height: 52, background: '#E1E4EE', display: 'flex', alignItems: 'center', padding: '0 18px', gap: 9}}>
      {['#FF5F57', '#FEBC2E', '#28C840'].map((c) => <div key={c} style={{width: 15, height: 15, borderRadius: '50%', background: c}} />)}
      <span style={{fontFamily: FUENTE, fontWeight: 700, fontSize: 22, color: '#4a4f66', marginLeft: 14}}>{titulo}</span>
    </div>
    <div style={{padding: 22}}>{children}</div>
  </div>
);
export const Copiar: React.FC<P<'copiar'>> = ({e, dur}) => {
  const frame = useCurrentFrame();
  const a = vis(frame, 0, dur, 10, 8);
  const ciclo = 46;
  const k = Math.min(2, Math.floor(Math.max(frame - 8, 0) / ciclo));
  const l = (Math.max(frame - 8, 0)) % ciclo;
  const vuelo = interpolate(l, [14, 30], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const ctrlC = l >= 8 && l < 18;
  const ctrlV = l >= 30 && l < 40;
  const filas = ['Cliente: M. García', 'Importe: 1.250 €', 'Pedido: nº 4821'];
  const pegadas = vuelo >= 1 ? k + 1 : k;
  return (
    <div style={{position: 'absolute', inset: 0, opacity: a, transform: `translateY(${(1 - a) * -30}px)`}}>
      <Ventana x={40} titulo={e.origen} rot={-1.5}>
        {filas.map((f, i) => (
          <div key={i} style={{height: 54, borderRadius: 12, marginBottom: 12, display: 'flex', alignItems: 'center', padding: '0 16px', fontFamily: FUENTE, fontWeight: 700, fontSize: 25, color: '#23263a', background: i === k % 3 && l < 30 ? `${C.acento}33` : '#fff', border: i === k % 3 && l < 30 ? `2px solid ${C.acento}` : '2px solid #E3E6F0'}}>{f}</div>
        ))}
      </Ventana>
      <Ventana x={570} titulo={e.destino} rot={1.5}>
        {[0, 1, 2].map((i) => (
          <div key={i} style={{height: 54, borderRadius: 12, marginBottom: 12, display: 'flex', alignItems: 'center', padding: '0 16px', fontFamily: MONO, fontWeight: 500, fontSize: 24, color: '#23263a', background: i < pegadas ? '#E7F8EE' : '#fff', border: `2px solid ${i < pegadas ? '#34C77B' : '#E3E6F0'}`}}>{i < pegadas ? filas[i] : ''}</div>
        ))}
      </Ventana>
      {vuelo > 0 && vuelo < 1 && (
        <div style={{position: 'absolute', left: 280 + vuelo * 560, top: 330 - Math.sin(vuelo * Math.PI) * 120, padding: '12px 22px', borderRadius: 14, background: C.acento, color: '#fff', fontFamily: FUENTE, fontWeight: 800, fontSize: 26, boxShadow: `0 16px 40px ${C.acento}88`, transform: `rotate(${(vuelo - 0.5) * 14}deg)`}}>{filas[k % 3]}</div>
      )}
      {[['Ctrl + C', 190, ctrlC], ['Ctrl + V', 700, ctrlV]].map(([t, x, on]) => (
        <div key={t as string} style={{position: 'absolute', left: x as number, top: 590, width: 190, height: 74, borderRadius: 16, ...cristal, display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: MONO, fontWeight: 500, fontSize: 30, color: on ? '#fff' : 'rgba(255,255,255,0.8)', background: on ? C.acento : 'rgba(255,255,255,0.13)', transform: `scale(${on ? 0.93 : 1}) translateY(${on ? 4 : 0}px)`}}>{t as string}</div>
      ))}
    </div>
  );
};

/* ───────── Recorte de periódico ───────── */
export const Periodico: React.FC<P<'periodico'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const at = useAt(f0);
  const a = vis(frame, 0, dur, 12, 8);
  const p = spring({frame, fps: 30, config: {damping: 15, stiffness: 120}});
  const hl = interpolate(frame, [at(e.resaltarT), at(e.resaltarT) + 10], [0, 100], {...clamp, easing: out5});
  const [a1, a2, a3] = e.titular;
  const palabra = (t: string) => {
    const i = t.indexOf(e.resaltar);
    if (i < 0) return <>{t}</>;
    return (
      <>
        {t.slice(0, i)}
        <span style={{backgroundImage: `linear-gradient(transparent 52%, ${C.acento2}CC 52%, ${C.acento2}CC 92%, transparent 92%)`, backgroundRepeat: 'no-repeat', backgroundSize: `${hl}% 100%`}}>{e.resaltar}</span>
        {t.slice(i + e.resaltar.length)}
      </>
    );
  };
  return (
    <div style={{position: 'absolute', left: 70, top: 150, width: 940, height: 540, opacity: a, transform: `translate(${(1 - p) * 300}px, ${(1 - p) * -120}px) rotate(${-2.2 - (1 - p) * 8}deg)`, background: '#F2EDDF', boxShadow: '0 40px 90px rgba(0,0,0,0.5)', padding: '26px 40px', overflow: 'hidden'}}>
      <svg width="100%" height="100%" style={{position: 'absolute', inset: 0, opacity: 0.1, mixBlendMode: 'multiply'}}>
        <filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" /></filter>
        <rect width="100%" height="100%" filter="url(#n)" />
      </svg>
      <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 30, letterSpacing: 7, textAlign: 'center', color: '#222', borderBottom: '3px double #222', paddingBottom: 12}}>{e.cabecera}</div>
      <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 70, lineHeight: 1.06, color: '#141414', marginTop: 26, letterSpacing: -1}}>
        <div>{a1}</div>
        <div>{a2}</div>
        <div>{palabra(a3)}</div>
      </div>
      <div style={{display: 'flex', gap: 22, marginTop: 24}}>
        {[0, 1, 2].map((c) => (
          <div key={c} style={{flex: 1}}>
            {[0, 1, 2].map((r) => <div key={r} style={{height: 11, borderRadius: 3, background: '#7d7a70', opacity: 0.45, marginBottom: 12, width: `${r === 2 ? 60 : 100}%`}} />)}
          </div>
        ))}
      </div>
    </div>
  );
};

/* ───────── B-roll en panel de cristal ───────── */
export const Broll: React.FC<P<'broll'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const a = vis(frame, 0, dur, 10, 8);
  const p = entra(frame, 0, 14);
  const W = 980, H = 620, s = W / 1080, yOff = 0.365 * 1920;
  return (
    <div style={{position: 'absolute', left: 50, top: 110, width: W, height: H, opacity: a, transform: `perspective(1600px) rotateX(${(1 - p) * 10}deg) translateY(${(1 - p) * 60}px) scale(${0.94 + 0.06 * p}) rotate(${-1.2 * p}deg)`, borderRadius: 38, overflow: 'hidden', border: '3px solid rgba(255,255,255,0.45)', boxShadow: `0 40px 100px rgba(0,0,0,0.55), 0 0 60px ${C.acento}55`, background: '#0d0d1a'}}>
      <div style={{position: 'absolute', left: 0, top: -yOff * s, width: 1080, height: 1920, transform: `scale(${s})`, transformOrigin: 'top left'}}>
        <OffthreadVideo src={staticFile(e.src)} startFrom={Math.round(e.desde * fps)} muted style={{width: 1080, height: 1920}} />
      </div>
      <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(180deg,rgba(13,13,26,0) 70%,rgba(13,13,26,0.55))'}} />
      {e.etiqueta && (
        <div style={{position: 'absolute', left: 26, bottom: 24, padding: '10px 22px', borderRadius: 999, background: 'rgba(13,13,26,0.7)', border: `2px solid ${C.acento}`, fontFamily: FUENTE, fontWeight: 700, fontSize: 28, color: '#fff'}}>{e.etiqueta}</div>
      )}
    </div>
  );
};

/* ───────── Botón con clic ───────── */
export const Cta: React.FC<P<'cta'>> = ({e, f0, dur}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const at = useAt(f0);
  const a = vis(frame, 0, dur, 10, 4);
  const p = spring({frame, fps, config: {damping: 14, stiffness: 150}});
  const c = at(e.clicT);
  const mov = interpolate(frame, [4, c - 3], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const prensa = frame >= c && frame < c + 6;
  const onda = interpolate(frame, [c, c + 16], [0, 1], clamp);
  const hecho = frame >= c + 2;
  return (
    <div style={{position: 'absolute', left: 130, top: 1130, width: 820, height: 160, opacity: a, transform: `scale(${(0.9 + 0.1 * p) * (prensa ? 0.96 : 1)})`}}>
      <div style={{width: '100%', height: '100%', borderRadius: 80, background: hecho ? `linear-gradient(90deg,${C.acento2},#fb923c)` : `linear-gradient(90deg,${C.acento},#60a5fa)`, boxShadow: `0 30px 80px ${hecho ? C.acento2 : C.acento}88`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 22, fontFamily: FUENTE, fontWeight: 800, fontSize: 58, color: '#fff'}}>
        {hecho && <span style={{fontSize: 64}}>✓</span>}
        {e.boton}
      </div>
      {frame >= c && <div style={{position: 'absolute', left: 560, top: 70, width: 40, height: 40, marginLeft: -20 - 140 * onda, marginTop: -20 - 140 * onda, padding: 0, width2: 0, borderRadius: '50%', border: '4px solid #fff', opacity: 1 - onda, transform: `scale(${1 + onda * 5})`, boxSizing: 'border-box'} as React.CSSProperties} />}
      <svg width="64" height="64" viewBox="0 0 24 24" style={{position: 'absolute', left: 560 + (1 - mov) * 280, top: 70 + (1 - mov) * 260, filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.55))', transform: `scale(${prensa ? 0.88 : 1})`}}>
        <path d="M5 2l14 10-6 1 3.5 7-2.5 1.2-3.5-7-5 4z" fill="#fff" stroke="#111" strokeWidth="1.2" />
      </svg>
    </div>
  );
};
