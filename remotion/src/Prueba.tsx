import {AbsoluteFill} from 'remotion';
import './fuentes';
import marca from '../../marca/marca.json';

export const Prueba: React.FC = () => (
  <AbsoluteFill style={{fontFamily: marca.tipografia.texto, background: marca.colores.fondo, color: marca.colores.texto, justifyContent: 'center', alignItems: 'center'}}>
    <div style={{fontFamily: marca.tipografia.titulos, fontSize: 90, fontWeight: 800}}>{marca.nombre}</div>
    <div style={{color: marca.colores.acento, fontSize: 48}}>{marca.persona.nombre} · {marca.persona.cargo}</div>
  </AbsoluteFill>
);
