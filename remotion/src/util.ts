import {Easing, interpolate} from 'remotion';
import marca from '../../marca/marca.json';

export const C = marca.colores;
export const FUENTE = `'${marca.tipografia.titulos}', sans-serif`;
export const MONO = `'${marca.tipografia.datos}', monospace`;
export const SERIF = `'Liberation Serif', 'Times New Roman', Georgia, serif`;

export const out5 = Easing.bezier(0.16, 1, 0.3, 1);
export const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
export const entra = (f: number, ini: number, dur = 10) => interpolate(f, [ini, ini + dur], [0, 1], {...clamp, easing: out5});
export const sale = (f: number, fin: number, dur = 6) => interpolate(f, [fin - dur, fin], [1, 0], clamp);
export const vis = (f: number, ini: number, fin: number, din = 10, dout = 6) => entra(f, ini, din) * sale(f, fin, dout);

export const sombraTexto = '0 4px 28px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.6)';
export const cristal: React.CSSProperties = {
  background: 'rgba(14,20,50,0.55)',
  backdropFilter: 'blur(26px) saturate(140%)',
  WebkitBackdropFilter: 'blur(26px) saturate(140%)',
  border: '2px solid rgba(255,255,255,0.30)',
  boxShadow: '0 30px 80px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.35)',
};
