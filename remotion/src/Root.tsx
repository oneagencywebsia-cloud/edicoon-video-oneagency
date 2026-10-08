import {Composition} from 'remotion';
import {Prueba} from './Prueba';
import marca from '../../marca/marca.json';

export const Root: React.FC = () => (
  <Composition
    id="Prueba"
    component={Prueba}
    durationInFrames={marca.formato.fps * 2}
    fps={marca.formato.fps}
    width={marca.formato.ancho}
    height={marca.formato.alto}
  />
);
