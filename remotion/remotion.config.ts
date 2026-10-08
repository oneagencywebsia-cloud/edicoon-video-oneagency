import {Config} from '@remotion/cli/config';

// publicDir = videos/ : así se alcanza tanto _shared/ como cada <id>/ con staticFile('<id>/...')
Config.setPublicDir('../videos');
Config.setBrowserExecutable(process.env.REMOTION_BROWSER ?? null);
