#!/bin/bash
# Headless shell de Remotion como root en contenedor: necesita --no-sandbox
exec /home/user/repo/remotion/node_modules/.remotion/chrome-headless-shell/linux64/chrome-headless-shell-linux64/chrome-headless-shell --no-sandbox "$@"
