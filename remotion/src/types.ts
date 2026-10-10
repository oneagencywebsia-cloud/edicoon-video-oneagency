export type Palabra = {w: string; t0: number; t1: number};
export type Chunk = {t0: number; t1: number; palabras: Palabra[]};
export type Sfx = {f: string; ini: number; archivo: string; vol: number; desde: number; dur: number; en: number};

type Base = {t0: number; t1: number};
export type Escena =
  | (Base & {tipo: 'lowerThird'; nombre: string; cargo: string})
  | (Base & {tipo: 'reloj'; desde: string; hasta: string; etiqueta: string})
  | (Base & {tipo: 'claveDetras'; estilo?: 'centro' | 'diagonal' | 'gigante'; lineas: string[]})
  | (Base & {tipo: 'claveFrente'; estilo: 'marcador'; lineas: string[]; resaltar: string; resaltarT: number})
  | (Base & {tipo: 'notas'; items: {texto: string; t: number}[]})
  | (Base & {tipo: 'copiar'; origen: string; destino: string})
  | (Base & {tipo: 'periodico'; cabecera: string; titular: string[]; resaltar: string; resaltarT: number})
  | (Base & {tipo: 'broll'; src: string; desde: number; etiqueta?: string})
  | (Base & {tipo: 'cta'; boton: string; clicT: number});

export type Edicion = {
  id: string;
  fps: number;
  frames: number;
  camara: string;
  chunks: Chunk[];
  escenas: Escena[];
  sfx: Sfx[];
  zooms: [number, number][];
};

export type Props = {id: string; ed?: Edicion};
