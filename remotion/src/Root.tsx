import {Composition, staticFile} from 'remotion';
import {Prueba} from './Prueba';
import {Vertical} from './Vertical';
import type {Edicion, Props} from './types';
import marca from '../../marca/marca.json';

const Envoltorio: React.FC<Props> = ({ed}) => (ed ? <Vertical ed={ed} /> : null);

export const Root: React.FC = () => (
  <>
    <Composition
      id="Vertical"
      component={Envoltorio}
      durationInFrames={300}
      fps={marca.formato.fps}
      width={marca.formato.ancho}
      height={marca.formato.alto}
      defaultProps={{id: 'video1'} as Props}
      calculateMetadata={async ({props}) => {
        const ed: Edicion = await (await fetch(staticFile(`${props.id}/edicion.json`))).json();
        return {durationInFrames: ed.frames, fps: ed.fps, props: {...props, ed}};
      }}
    />
    <Composition id="Prueba" component={Prueba} durationInFrames={marca.formato.fps * 2} fps={marca.formato.fps} width={marca.formato.ancho} height={marca.formato.alto} />
  </>
);
