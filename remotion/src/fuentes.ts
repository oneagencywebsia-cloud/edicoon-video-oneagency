import {continueRender, delayRender, staticFile} from 'remotion';

const archivos: [string, string, string, string][] = [
  ['Plus Jakarta Sans', '200 800', 'PlusJakartaSans-latin.woff2', 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+20AC,U+2122'],
  ['Plus Jakarta Sans', '200 800', 'PlusJakartaSans-latin-ext.woff2', 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+1E00-1E9F,U+1EF2-1EFF'],
  ['JetBrains Mono', '400 500', 'JetBrainsMono-latin.woff2', 'U+0000-00FF,U+0131,U+0152-0153,U+2000-206F,U+20AC,U+2122'],
];

// Las familias vienen de marca/marca.json; los archivos, de videos/_shared/fonts.
const handle = delayRender('fuentes');
Promise.all(
  archivos.map(async ([familia, peso, archivo, rango]) => {
    const f = new FontFace(familia, `url(${staticFile('_shared/fonts/' + archivo)}) format('woff2')`, {weight: peso, unicodeRange: rango});
    document.fonts.add(await f.load());
  }),
).then(() => continueRender(handle));
