import React from 'react';
import {Easing, interpolate, useCurrentFrame} from 'remotion';
import {FUENTE, clamp, out5} from './util';

/* ───────────────────────── Presets de rótulo clave ─────────────────────────
   Cada preset = relleno + borde + extrusión 3D + brillo (glow) + sombra de suelo + barrido de luz + animación por letras.
   Capas por letra: A (extrusión y sombra, define el hueco) · B (relleno con degradado y brillo) · C (barrido de luz). */
export type Preset = 'neon' | 'cromo' | 'ambar' | 'cristal' | 'foco' | 'hielo' | 'sombra';

type Cfg = {
  grad: string;
  borde?: string;
  bordePx?: number;
  extrusion?: {color: string; prof: number; ang: number};
  glow: string[]; // drop-shadow de la capa B
  sombra: string; // sombra de suelo
  barrido?: boolean;
  anim: 'subir' | 'enfoque' | 'parpadeo' | 'caer';
  rellenoPlano?: string; // color sólido (neón)
  textShadowB?: string;
  larga?: {color: string; largo: number; alfa: number; ang: number}; // sombra larga proyectada que se desvanece
};

export const PRESETS: Record<Preset, Cfg> = {
  neon: {
    grad: 'linear-gradient(180deg,#ffffff,#ffffff)',
    rellenoPlano: '#ffffff',
    borde: '#60a5fa',
    bordePx: 0,
    glow: ['0 0 6px #fff', '0 0 22px #60a5fa', '0 0 54px #3B82F6', '0 0 110px #3B82F6'],
    sombra: '0 30px 80px rgba(8,20,70,0.6)',
    larga: {color: '4,10,50', largo: 60, alfa: 0.45, ang: 120},
    anim: 'parpadeo',
  },
  cromo: {
    grad: 'linear-gradient(180deg,#ffffff 0%,#e9eef8 30%,#9aa7c0 50%,#f6f9ff 58%,#b9c5de 100%)',
    extrusion: {color: '#1e3a8a', prof: 16, ang: 118},
    glow: ['0 0 30px rgba(255,255,255,0.45)', '0 0 90px rgba(96,165,250,0.5)'],
    sombra: '0 40px 70px rgba(0,0,0,0.55)',
    barrido: true,
    larga: {color: '4,12,60', largo: 70, alfa: 0.5, ang: 118},
    anim: 'enfoque',
  },
  ambar: {
    grad: 'linear-gradient(180deg,#FFF6CF 0%,#FFD166 34%,#FF9A2E 64%,#C2410C 100%)',
    extrusion: {color: '#5a2406', prof: 13, ang: 125},
    glow: ['0 0 24px rgba(255,170,60,0.7)', '0 0 80px rgba(249,115,22,0.6)'],
    sombra: '0 36px 60px rgba(40,10,0,0.6)',
    larga: {color: '30,8,0', largo: 70, alfa: 0.5, ang: 125},
    barrido: true,
    anim: 'subir',
  },
  cristal: {
    grad: 'linear-gradient(135deg,rgba(255,255,255,0.78) 0%,rgba(190,220,255,0.28) 45%,rgba(255,255,255,0.12) 70%,rgba(255,255,255,0.5) 100%)',
    borde: 'rgba(255,255,255,0.92)',
    bordePx: 4,
    glow: ['0 0 18px rgba(255,255,255,0.35)', '0 0 70px rgba(96,165,250,0.55)'],
    sombra: '0 30px 60px rgba(10,20,60,0.5)',
    larga: {color: '6,14,50', largo: 70, alfa: 0.5, ang: 120},
    barrido: true,
    anim: 'enfoque',
  },
  foco: {
    grad: 'linear-gradient(180deg,#ffffff 0%,#fff6e0 55%,#ffe2a8 100%)',
    extrusion: {color: '#6b4a10', prof: 9, ang: 120},
    glow: ['0 0 40px rgba(255,236,190,0.7)', '0 0 120px rgba(255,214,120,0.45)'],
    sombra: '0 40px 80px rgba(0,0,0,0.65)',
    larga: {color: '10,6,0', largo: 70, alfa: 0.55, ang: 120},
    barrido: false,
    anim: 'caer',
  },
  sombra: {
    grad: 'linear-gradient(180deg,#ffffff 0%,#eaf2ff 100%)',
    glow: ['0 0 22px rgba(255,255,255,0.35)'],
    sombra: '0 20px 40px rgba(0,10,40,0.45)',
    larga: {color: '6,24,96', largo: 90, alfa: 0.62, ang: 122},
    anim: 'enfoque',
  },
  hielo: {
    grad: 'linear-gradient(180deg,#ffffff 0%,#d9f0ff 40%,#7dc4ff 75%,#3B82F6 100%)',
    extrusion: {color: '#0b2a6b', prof: 14, ang: 122},
    glow: ['0 0 30px rgba(125,196,255,0.6)', '0 0 90px rgba(59,130,246,0.6)'],
    sombra: '0 36px 70px rgba(0,10,50,0.6)',
    larga: {color: '2,12,60', largo: 70, alfa: 0.5, ang: 122},
    barrido: true,
    anim: 'subir',
  },
};

const extrusion = (c: Cfg) => {
  const capas: string[] = [];
  let prof = 0;
  if (c.extrusion) {
    const {color, ang} = c.extrusion;
    prof = c.extrusion.prof;
    const dx = Math.cos((ang * Math.PI) / 180);
    const dy = Math.sin((ang * Math.PI) / 180);
    for (let i = 1; i <= prof; i++) capas.push(`${(dx * i).toFixed(1)}px ${(dy * i).toFixed(1)}px 0 ${color}`);
  }
  if (c.larga) {
    // sombra larga proyectada (luz desde arriba-izquierda): capas que se desvanecen con la distancia
    const {color, largo, alfa, ang} = c.larga;
    const dx = Math.cos((ang * Math.PI) / 180);
    const dy = Math.sin((ang * Math.PI) / 180);
    for (let i = prof + 1; i <= prof + largo; i += 2) {
      const k = (i - prof) / largo;
      capas.push(`${(dx * i).toFixed(1)}px ${(dy * i).toFixed(1)}px ${(1 + k * 5).toFixed(1)}px rgba(${color},${(alfa * (1 - k) ** 1.4).toFixed(3)})`);
    }
  }
  // sombra de contacto / ambiente
  const m = c.sombra.match(/^(-?[\d.]+)px (-?[\d.]+)px (-?[\d.]+)px (.+)$/);
  if (m) {
    const [, x, y, bl, col] = m;
    capas.push(`${parseFloat(x)}px ${parseFloat(y) + prof}px ${bl}px ${col}`);
  }
  return capas.join(',');
};

export const Linea: React.FC<{
  texto: string;
  preset: Preset;
  size: number;
  ls?: number; // letter-spacing (px)
  inicio?: number; // fotograma de arranque dentro de la escena
  dur: number;
}> = ({texto, preset, size, ls = -6, inicio = 0, dur}) => {
  const frame = useCurrentFrame() - inicio;
  const c = PRESETS[preset];
  const sombraA = extrusion(c);
  const letras = Array.from(texto);
  const salida = interpolate(frame, [dur - 7, dur], [1, 0], clamp);
  const base: React.CSSProperties = {fontFamily: FUENTE, fontWeight: 800, fontSize: size, lineHeight: 1, letterSpacing: ls, display: 'inline-block', whiteSpace: 'pre'};
  const pulso = 0.85 + 0.15 * Math.sin(frame / 5);
  return (
    <span style={{display: 'inline-block', opacity: salida, whiteSpace: 'pre'}}>
      {letras.map((ch, i) => {
        const p = interpolate(frame - i * 1, [0, 8], [0, 1], {...clamp, easing: out5});
        let transform = '';
        let blur = 0;
        let op = p;
        if (c.anim === 'subir') transform = `translateY(${(1 - p) * 90}px) scale(${1 + (1 - p) * 0.25})`;
        if (c.anim === 'enfoque') {
          transform = `scale(${1 + (1 - p) * 0.5})`;
          blur = (1 - p) * 18;
        }
        if (c.anim === 'caer') transform = `translateY(${(1 - p) * -140}px) rotate(${(1 - p) * (i % 2 ? 14 : -14)}deg)`;
        if (c.anim === 'parpadeo') {
          const t = frame - i * 1.5;
          const pat = [0, 0.9, 0.2, 1, 0.35, 1, 0.7, 1];
          op = t < 0 ? 0 : t < pat.length * 2 ? pat[Math.floor(t / 2)] : 1;
          transform = `scale(${1 + (1 - Math.min(t / 14, 1)) * 0.08})`;
        }
        if (ch === ' ') return <span key={i} style={{...base, width: size * 0.28}}>{' '}</span>;
        const sweepX = interpolate(frame - i * 1.5, [10, 34], [160, -60], clamp);
        return (
          <span key={i} style={{position: 'relative', display: 'inline-block', transform, filter: blur ? `blur(${blur}px)` : undefined, opacity: op}}>
            <span style={{...base, color: c.extrusion ? c.extrusion.color : 'transparent', textShadow: sombraA}}>{ch}</span>
            <span
              style={{
                ...base,
                position: 'absolute',
                left: 0,
                top: 0,
                color: c.rellenoPlano ?? 'transparent',
                backgroundImage: c.rellenoPlano ? undefined : c.grad,
                WebkitBackgroundClip: c.rellenoPlano ? undefined : 'text',
                backgroundClip: c.rellenoPlano ? undefined : 'text',
                WebkitTextStroke: c.borde && c.bordePx ? `${c.bordePx}px ${c.borde}` : undefined,
                textShadow: c.rellenoPlano ? c.glow.map((g) => g.replace(/^0 0 /, '0 0 ')).join(',') : undefined,
                filter: c.rellenoPlano ? undefined : c.glow.map((g) => `drop-shadow(${g})`).join(' '),
                opacity: preset === 'neon' ? pulso : 1,
              }}
            >
              {ch}
            </span>
            {c.barrido && (
              <span
                style={{
                  ...base,
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  color: 'transparent',
                  backgroundImage: 'linear-gradient(105deg,transparent 38%,rgba(255,255,255,0.95) 50%,transparent 62%)',
                  backgroundSize: '300% 100%',
                  backgroundPosition: `${sweepX}% 0`,
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  mixBlendMode: 'screen',
                }}
              >
                {ch}
              </span>
            )}
          </span>
        );
      })}
    </span>
  );
};

/* Haz de luz de foco (para el preset «foco») */
export const HazFoco: React.FC<{dur: number}> = ({dur}) => {
  const frame = useCurrentFrame();
  const a = interpolate(frame, [0, 10, dur - 8, dur], [0, 1, 1, 0], clamp);
  const giro = Math.sin(frame / 14) * 6;
  return (
    <div style={{position: 'absolute', left: '50%', top: -40, width: 1400, height: 1500, marginLeft: -700, opacity: a * 0.55, transform: `rotate(${giro}deg)`, transformOrigin: '50% 0', background: 'conic-gradient(from 168deg at 50% 0%, transparent 0deg, rgba(255,246,214,0.0) 2deg, rgba(255,246,214,0.55) 12deg, rgba(255,246,214,0.0) 24deg, transparent 26deg)', mixBlendMode: 'screen', filter: 'blur(14px)'}} />
  );
};

/* Resplandor de fondo (neón / hielo) */
export const Bloom: React.FC<{color: string; dur: number}> = ({color, dur}) => {
  const frame = useCurrentFrame();
  const a = interpolate(frame, [0, 8, dur - 8, dur], [0, 1, 1, 0], clamp);
  return <div style={{position: 'absolute', left: 0, right: 0, top: 120, height: 900, opacity: a * (0.7 + 0.3 * Math.sin(frame / 6)), background: `radial-gradient(ellipse at 50% 45%, ${color}88 0%, ${color}22 45%, transparent 72%)`, mixBlendMode: 'screen'}} />;
};
