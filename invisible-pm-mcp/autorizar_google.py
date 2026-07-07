"""Autorización de Google Calendar para invisible-pm (ejecutar UNA vez en la terminal).

1. En Google Cloud Console: crea un proyecto, habilita la API de Google Calendar,
   crea credenciales OAuth de tipo "Escritorio" y descarga el credentials.json
   a esta carpeta (o exporta GOOGLE_CREDENTIALS_PATH con su ruta).
2. Ejecuta:  uv run autorizar_google.py
3. Se abre el navegador → inicia sesión → acepta. Se guarda token.json y el MCP
   ya puede agendar reuniones sin volver a preguntar.
"""

import os
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

AQUI = Path(__file__).resolve().parent
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

credentials_path = Path(os.environ.get("GOOGLE_CREDENTIALS_PATH", AQUI / "credentials.json"))
token_path = Path(os.environ.get("GOOGLE_TOKEN_PATH", AQUI / "token.json"))

if not credentials_path.exists():
    print(
        f"No encuentro {credentials_path}.\n"
        "Descarga el credentials.json de tu proyecto de Google Cloud "
        "(APIs y servicios → Credenciales → ID de cliente OAuth tipo 'Escritorio') "
        "y colócalo en esta carpeta.",
        file=sys.stderr,
    )
    sys.exit(1)

flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
creds = flow.run_local_server(port=0)
token_path.write_text(creds.to_json())
print(f"✓ Autorizado. Token guardado en {token_path}. El MCP invisible-pm ya puede agendar reuniones.")
