"""Autoriza el acceso de SOLO LECTURA a Google Drive y muestra el refresh token.

Se ejecuta UNA vez, en el ordenador de Ángel (Python 3.8+, sin dependencias):
    py -3.12 pipeline/drive_auth.py "RUTA\\client_secret.json"

El token se imprime en la terminal. NO se guarda en ningún archivo y NO se pega en el chat:
se copia a mano en las variables del entorno de la nube (ver CLAUDE.md).
"""
import http.server
import json
import secrets
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser

SCOPE = "https://www.googleapis.com/auth/drive.readonly"
PORT = 8765


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Uso: drive_auth.py <client_secret.json>")
    with open(sys.argv[1], encoding="utf-8") as f:
        cfg = json.load(f)
    cfg = cfg.get("installed") or cfg.get("web")
    client_id, client_secret = cfg["client_id"], cfg["client_secret"]
    redirect = f"http://localhost:{PORT}"
    state = secrets.token_urlsafe(16)
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": state,
    })
    result: dict = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state and "code" in q:
                result["code"] = q["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("Listo. Puedes cerrar esta pestaña y volver a la terminal.".encode())

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("localhost", PORT), H)
    t = threading.Thread(target=srv.handle_request)
    t.start()
    print("Abriendo el navegador para autorizar (solo lectura)…")
    webbrowser.open(url)
    t.join()
    if "code" not in result:
        sys.exit("No se recibió el código de autorización.")
    data = urllib.parse.urlencode({
        "code": result["code"], "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect, "grant_type": "authorization_code",
    }).encode()
    with urllib.request.urlopen(urllib.request.Request("https://oauth2.googleapis.com/token", data=data)) as r:
        tok = json.load(r)
    if "refresh_token" not in tok:
        sys.exit("Google no devolvió refresh_token. Repite y acepta todos los permisos.")
    print("\nCopia estos 3 valores en las variables del entorno de la nube (NO en el chat):\n")
    print(f"GOOGLE_CLIENT_ID={client_id}")
    print(f"GOOGLE_CLIENT_SECRET={client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN={tok['refresh_token']}")


if __name__ == "__main__":
    main()
