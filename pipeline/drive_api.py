"""Google Drive por API (solo lectura): listar, ver info y descargar a raw/<id>/.

Credenciales: variables de entorno GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN.
Nunca se imprimen ni se guardan en archivos.

    drive_api.py info <fileId|enlace>
    drive_api.py ls   <folderId|enlace>
    drive_api.py get  <fileId|enlace> --dest raw/<id> [--nombre archivo.mp4]

La descarga es en trozos y reanudable (Range): si el archivo ya está completo no se vuelve a bajar.
Después comprueba tamaño y duración con ffprobe.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://www.googleapis.com/drive/v3"
CHUNK = 8 * 1024 * 1024
_tok = {"v": None, "exp": 0.0}


def token() -> str:
    if _tok["v"] and time.time() < _tok["exp"] - 60:
        return _tok["v"]
    try:
        data = urllib.parse.urlencode({
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        }).encode()
    except KeyError as e:
        sys.exit(f"Falta la variable de entorno {e.args[0]}")
    try:
        with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data)) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        msg = json.loads(e.read() or b"{}").get("error", e.code)
        sys.exit(f"Google rechazó el refresh token ({msg}). Repite drive_auth.py.")
    _tok.update(v=j["access_token"], exp=time.time() + j.get("expires_in", 3600))
    return _tok["v"]


def fid(x: str) -> str:
    m = re.search(r"/d/([\w-]+)|[?&]id=([\w-]+)|/folders/([\w-]+)", x)
    return next(g for g in m.groups() if g) if m else x


def call(url: str, headers: dict | None = None):
    h = {"Authorization": f"Bearer {token()}", **(headers or {})}
    return urllib.request.urlopen(urllib.request.Request(url, headers=h))


def meta(i: str) -> dict:
    q = urllib.parse.urlencode({"fields": "id,name,mimeType,size,md5Checksum,modifiedTime,videoMediaMetadata", "supportsAllDrives": "true"})
    with call(f"{API}/files/{i}?{q}") as r:
        return json.load(r)


def listar(folder: str) -> list[dict]:
    out, page = [], None
    while True:
        q = {"q": f"'{folder}' in parents and trashed = false", "fields": "nextPageToken,files(id,name,mimeType,size,modifiedTime)",
             "pageSize": "200", "supportsAllDrives": "true", "includeItemsFromAllDrives": "true", "orderBy": "name"}
        if page:
            q["pageToken"] = page
        with call(f"{API}/files?{urllib.parse.urlencode(q)}") as r:
            j = json.load(r)
        out += j["files"]
        page = j.get("nextPageToken")
        if not page:
            return out


def ffprobe(path: str) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate",
                        "-of", "json", path], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else {}


def descargar(i: str, dest: str, nombre: str | None) -> str:
    m = meta(i)
    total = int(m.get("size", 0))
    os.makedirs(dest, exist_ok=True)
    path = os.path.join(dest, nombre or m["name"])
    part = path + ".part"
    if os.path.exists(path) and os.path.getsize(path) == total:
        print(f"Ya descargado: {path}")
    else:
        if shutil.disk_usage(dest).free < total * 1.1:
            sys.exit("No hay espacio suficiente en disco.")
        done = os.path.getsize(part) if os.path.exists(part) else 0
        with open(part, "ab") as f:
            while done < total:
                end = min(done + CHUNK, total) - 1
                for intento in range(5):
                    try:
                        with call(f"{API}/files/{i}?alt=media&supportsAllDrives=true", {"Range": f"bytes={done}-{end}"}) as r:
                            buf = r.read()
                        break
                    except (urllib.error.URLError, ConnectionError, TimeoutError):
                        time.sleep(2 ** intento)
                else:
                    sys.exit(f"Descarga cortada en {done} bytes; vuelve a lanzarla para reanudar.")
                f.write(buf)
                done += len(buf)
                print(f"\r{done / 1e6:.0f}/{total / 1e6:.0f} MB", end="", flush=True)
        print()
        os.replace(part, path)
    if os.path.getsize(path) != total:
        sys.exit("El tamaño descargado no coincide con el de Drive.")
    info = ffprobe(path)
    if m["mimeType"].startswith("video/") and not info.get("format", {}).get("duration"):
        sys.exit("ffprobe no puede leer el vídeo: archivo dañado.")
    print(json.dumps({"archivo": path, "bytes": total, "ffprobe": info.get("format"), "streams": info.get("streams")}, ensure_ascii=False, indent=1))
    return path


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("info", "ls", "get"):
        p = sub.add_parser(c)
        p.add_argument("id")
    g = sub.choices["get"]
    g.add_argument("--dest", required=True)
    g.add_argument("--nombre")
    a = ap.parse_args()
    i = fid(a.id)
    try:
        if a.cmd == "info":
            print(json.dumps(meta(i), ensure_ascii=False, indent=1))
        elif a.cmd == "ls":
            for x in listar(i):
                print(f"{x['id']}\t{x['mimeType'].split('.')[-1]}\t{int(x.get('size', 0)) / 1e6:.1f} MB\t{x['name']}")
        else:
            descargar(i, a.dest, a.nombre)
    except urllib.error.HTTPError as e:
        sys.exit(f"Drive devolvió {e.code}: {e.reason}")


if __name__ == "__main__":
    main()
