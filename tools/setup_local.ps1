# Preparación del editor en el PC de Ángel (Windows 11). Ejecutar desde la raíz del repo:
#   powershell -ExecutionPolicy Bypass -File tools\setup_local.ps1
# No sube nada ni usa cuentas. Todo queda dentro de la carpeta del repo (.venv, remotion\node_modules).
$ErrorActionPreference = "Stop"
function Need($cmd, $msg) { if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "Falta $cmd. $msg" } }
Need node   "Instala Node 20+ (winget install OpenJS.NodeJS.LTS)."
Need ffmpeg "Instala ffmpeg (winget install Gyan.FFmpeg) y abre una terminal nueva."
Need py     "Instala Python 3.12 (winget install Python.Python.3.12)."
py -3.12 --version
if (-not (Test-Path .venv)) { py -3.12 -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-local.txt
Push-Location remotion
npm install
npx remotion browser ensure
Pop-Location
New-Item -ItemType Directory -Force raw, out\final, out\qa | Out-Null
# Comprobación rápida
& .\.venv\Scripts\python.exe -c "import faster_whisper, rembg, cv2; print('Python OK')"
Push-Location remotion; npx tsc --noEmit; Pop-Location
Write-Host "Listo. Activa el entorno con:  .\.venv\Scripts\Activate.ps1"
