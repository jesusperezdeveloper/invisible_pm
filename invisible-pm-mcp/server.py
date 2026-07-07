"""invisible-pm — El Project Manager invisible · Masterclass MCP.

UN solo MCP con todo el pipeline del martes post-reunión:

    Fireflies (los oídos)  →  Notion (el archivo)  →  Trello (el tablón)  →  Calendar (la agenda)

Herramientas:
    listar_reuniones / leer_reunion     — Fireflies (GraphQL)
    publicar_acta_notion                — crea la página del acta en Notion
    actualizar_trello                   — tarjetas nuevas con checklist + mover a Hecho
    agendar_reunion                     — evento en Google Calendar

Claude redacta el acta y decide; este MCP le da las acreditaciones para ejecutar.

Variables de entorno (.env / claude mcp add -e):
    FIREFLIES_API_KEY        — Fireflies → Settings → Developer settings
    NOTION_API_KEY           — https://www.notion.so/my-integrations (compartir la página con la integración)
    TRELLO_API_KEY, TRELLO_TOKEN — https://trello.com/power-ups/admin
    GOOGLE_CREDENTIALS_PATH  — credentials.json de Google Cloud (opcional, por defecto ./credentials.json)
    GOOGLE_TOKEN_PATH        — token.json generado por autorizar_google.py (por defecto ./token.json)

Registro en Claude Code (ruta absoluta al python del venv tras `uv sync`):
    claude mcp add invisible-pm \
      -e FIREFLIES_API_KEY=... -e NOTION_API_KEY=... -e TRELLO_API_KEY=... -e TRELLO_TOKEN=... \
      -- /ruta/absoluta/invisible-pm-mcp/.venv/bin/python /ruta/absoluta/invisible-pm-mcp/server.py
"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field

mcp = FastMCP("invisible-pm")

AQUI = Path(__file__).resolve().parent
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _fecha(ms) -> str:
    """Milisegundos epoch → '30 jun 2026, 17:00' (es-ES)."""
    if not ms:
        return "sin fecha"
    dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).astimezone()
    return f"{dt.day} {MESES[dt.month - 1]} {dt.year}, {dt:%H:%M}"


# ════════════════════════════════════════════════════════════════════════
# FIREFLIES — los oídos
# ════════════════════════════════════════════════════════════════════════

FIREFLIES_URL = "https://api.fireflies.ai/graphql"


def _fireflies(query: str, variables: dict | None = None) -> dict:
    api_key = os.environ.get("FIREFLIES_API_KEY")
    if not api_key:
        raise ToolError(
            "Falta la clave de Fireflies (FIREFLIES_API_KEY). "
            "Se genera en Fireflies → Settings → Developer settings → API key."
        )
    try:
        res = httpx.post(
            FIREFLIES_URL,
            json={"query": query, "variables": variables or {}},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
    except httpx.HTTPError:
        raise ToolError("No se pudo conectar con Fireflies. Comprueba tu conexión a internet.")
    if res.status_code in (401, 403):
        raise ToolError("Fireflies rechazó la clave (API key inválida o caducada).")
    try:
        payload = res.json()
    except ValueError:
        raise ToolError(f"Fireflies devolvió una respuesta inesperada (HTTP {res.status_code}).")
    if payload.get("errors"):
        detalle = "; ".join(e.get("message", "") for e in payload["errors"])
        raise ToolError(f"Fireflies respondió con error: {detalle}")
    return payload.get("data", {})


@mcp.tool
def listar_reuniones(
    limite: Annotated[int, Field(ge=1, le=25, description="Cuántas reuniones devolver (1-25)")] = 5,
) -> str:
    """Lista las últimas reuniones grabadas en Fireflies con su id, título, fecha y duración."""
    data = _fireflies(
        "query Transcripts($limit: Int) { transcripts(limit: $limit) { id title date duration } }",
        {"limit": limite},
    )
    reuniones = data.get("transcripts") or []
    if not reuniones:
        return "No hay reuniones grabadas todavía en esta cuenta."
    return "\n".join(
        f"• [{t['id']}] {t['title']} — {_fecha(t.get('date'))} ({round(t.get('duration') or 0)} min)"
        for t in reuniones
    )


@mcp.tool
def leer_reunion(
    id: Annotated[
        str | None,
        Field(description="Id de la reunión (de listar_reuniones). Vacío = la más reciente."),
    ] = None,
) -> str:
    """Devuelve el contenido de una reunión de Fireflies: resumen, puntos de acción y
    transcripción completa con quién dijo qué. Si no se indica id, devuelve la última reunión."""
    if not id:
        ultima = _fireflies("query { transcripts(limit: 1) { id } }")
        transcripts = ultima.get("transcripts") or []
        if not transcripts:
            return "No hay ninguna reunión grabada en esta cuenta."
        id = transcripts[0]["id"]
    data = _fireflies(
        """query Transcript($id: String!) {
          transcript(id: $id) {
            id title date duration
            summary { overview action_items }
            sentences { speaker_name text }
          }
        }""",
        {"id": id},
    )
    t = data.get("transcript")
    if not t:
        return f"No existe ninguna reunión con id {id}."
    dialogo = "\n".join(
        f"{s.get('speaker_name') or 'Desconocido'}: {s.get('text', '')}"
        for s in (t.get("sentences") or [])
    )
    resumen = (t.get("summary") or {}).get("overview") or "(sin resumen)"
    acciones = (t.get("summary") or {}).get("action_items") or "(ninguno)"
    return "\n".join(
        [
            f"REUNIÓN: {t['title']}",
            f"FECHA: {_fecha(t.get('date'))} · DURACIÓN: {round(t.get('duration') or 0)} min",
            "",
            "RESUMEN AUTOMÁTICO:",
            resumen,
            "",
            "PUNTOS DE ACCIÓN DETECTADOS:",
            acciones,
            "",
            "TRANSCRIPCIÓN:",
            dialogo or "(vacía)",
        ]
    )


# ════════════════════════════════════════════════════════════════════════
# NOTION — el archivo
# ════════════════════════════════════════════════════════════════════════

NOTION_URL = "https://api.notion.com/v1"


def _notion(method: str, path: str, body: dict | None = None) -> dict:
    api_key = os.environ.get("NOTION_API_KEY")
    if not api_key:
        raise ToolError(
            "Falta la clave de Notion (NOTION_API_KEY). Crea una integración interna en "
            "https://www.notion.so/my-integrations y comparte con ella la página destino "
            "(··· → Conexiones → tu integración)."
        )
    try:
        res = httpx.request(
            method,
            f"{NOTION_URL}{path}",
            json=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": "2022-06-28",
            },
            timeout=30,
        )
    except httpx.HTTPError:
        raise ToolError("No se pudo conectar con Notion. Comprueba tu conexión a internet.")
    payload = res.json()
    if res.status_code >= 400:
        msg = payload.get("message", f"HTTP {res.status_code}")
        if res.status_code == 401:
            msg = "clave inválida (NOTION_API_KEY). " + msg
        raise ToolError(f"Notion respondió con error: {msg}")
    return payload


def _rich_text(texto: str) -> list[dict]:
    """Texto plano con **negritas** → rich_text de Notion."""
    partes = []
    for trozo in re.split(r"(\*\*[^*]+\*\*)", texto):
        if not trozo:
            continue
        if trozo.startswith("**") and trozo.endswith("**"):
            partes.append(
                {"type": "text", "text": {"content": trozo[2:-2]}, "annotations": {"bold": True}}
            )
        else:
            partes.append({"type": "text", "text": {"content": trozo}})
    return partes or [{"type": "text", "text": {"content": ""}}]


def _markdown_a_bloques(md: str) -> list[dict]:
    """Markdown sencillo → bloques de Notion (h1-h3, bullets, numeradas, to-dos, divisores, párrafos)."""
    bloques = []
    for linea in md.splitlines():
        s = linea.strip()
        if not s:
            continue
        if s.startswith("### "):
            bloques.append({"heading_3": {"rich_text": _rich_text(s[4:])}})
        elif s.startswith("## "):
            bloques.append({"heading_2": {"rich_text": _rich_text(s[3:])}})
        elif s.startswith("# "):
            bloques.append({"heading_1": {"rich_text": _rich_text(s[2:])}})
        elif s in ("---", "***"):
            bloques.append({"divider": {}})
        elif s.startswith("- [ ] ") or s.startswith("- [x] "):
            bloques.append(
                {"to_do": {"rich_text": _rich_text(s[6:]), "checked": s.startswith("- [x] ")}}
            )
        elif s.startswith(("- ", "* ", "• ")):
            bloques.append({"bulleted_list_item": {"rich_text": _rich_text(s[2:])}})
        elif re.match(r"^\d+[.)] ", s):
            bloques.append(
                {"numbered_list_item": {"rich_text": _rich_text(re.sub(r"^\d+[.)] ", "", s))}}
            )
        else:
            bloques.append({"paragraph": {"rich_text": _rich_text(s)}})
    return [{"object": "block", **b} for b in bloques]


@mcp.tool
def publicar_acta_notion(
    titulo: Annotated[str, Field(description="Título de la página del acta, p. ej. 'Acta — ReservaFácil, 7 jul 2026'")],
    contenido_markdown: Annotated[str, Field(description="El acta en markdown: fecha, asistentes, decisiones, tareas con responsable, próximos pasos")],
    pagina_padre: Annotated[str, Field(description="Nombre de la página de Notion bajo la que crear el acta")] = "Proyectos",
) -> str:
    """Crea la página del acta en Notion debajo de la página indicada y devuelve su URL.
    La página padre debe estar compartida con la integración de Notion."""
    parent_id = os.environ.get("NOTION_PARENT_PAGE_ID")
    if not parent_id:
        resultado = _notion(
            "POST",
            "/search",
            {"query": pagina_padre, "filter": {"value": "page", "property": "object"}},
        )
        paginas = resultado.get("results") or []
        if not paginas:
            raise ToolError(
                f"No encuentro ninguna página '{pagina_padre}' en Notion. "
                "¿Está compartida con la integración? (··· → Conexiones → tu integración)"
            )
        parent_id = paginas[0]["id"]
    bloques = _markdown_a_bloques(contenido_markdown)
    pagina = _notion(
        "POST",
        "/pages",
        {
            "parent": {"page_id": parent_id},
            "properties": {"title": [{"type": "text", "text": {"content": titulo}}]},
            "children": bloques[:100],
        },
    )
    # Notion admite máx. 100 bloques por petición; el resto se añade en tandas
    restantes = bloques[100:]
    while restantes:
        _notion("PATCH", f"/blocks/{pagina['id']}/children", {"children": restantes[:100]})
        restantes = restantes[100:]
    return f"Acta creada en Notion: {pagina.get('url', pagina['id'])}"


# ════════════════════════════════════════════════════════════════════════
# TRELLO — el tablón
# ════════════════════════════════════════════════════════════════════════

TRELLO_URL = "https://api.trello.com/1"


def _trello(method: str, path: str, **params) -> dict | list:
    key = os.environ.get("TRELLO_API_KEY")
    token = os.environ.get("TRELLO_TOKEN")
    if not key or not token:
        raise ToolError(
            "Faltan las credenciales de Trello (TRELLO_API_KEY y TRELLO_TOKEN). "
            "Se generan en https://trello.com/power-ups/admin."
        )
    try:
        res = httpx.request(
            method, f"{TRELLO_URL}{path}", params={"key": key, "token": token, **params}, timeout=30
        )
    except httpx.HTTPError:
        raise ToolError("No se pudo conectar con Trello. Comprueba tu conexión a internet.")
    if res.status_code == 401:
        raise ToolError("Trello rechazó las credenciales (TRELLO_API_KEY/TRELLO_TOKEN inválidos).")
    if res.status_code >= 400:
        raise ToolError(f"Trello respondió con error: HTTP {res.status_code} — {res.text[:200]}")
    return res.json()


def _tablero_y_listas(nombre_tablero: str) -> tuple[dict, list]:
    tableros = _trello("GET", "/members/me/boards", fields="name,url", filter="open")
    tablero = next(
        (b for b in tableros if b["name"].strip().lower() == nombre_tablero.strip().lower()), None
    )
    if not tablero:
        disponibles = ", ".join(b["name"] for b in tableros[:10]) or "(ninguno)"
        raise ToolError(
            f"No encuentro el tablero '{nombre_tablero}' en Trello. Tableros disponibles: {disponibles}."
        )
    listas = _trello("GET", f"/boards/{tablero['id']}/lists", fields="name")
    return tablero, listas


def _lista_por_nombre(listas: list, nombre: str) -> dict:
    lista = next((l for l in listas if l["name"].strip().lower() == nombre.strip().lower()), None)
    if not lista:
        nombres = ", ".join(l["name"] for l in listas)
        raise ToolError(f"El tablero no tiene la lista '{nombre}'. Listas: {nombres}.")
    return lista


class TarjetaNueva(BaseModel):
    """Tarea nueva salida de la reunión."""

    titulo: str = Field(description="Qué hay que hacer")
    responsable: str = Field(default="", description="Quién lo hace (va al título de la tarjeta)")
    criterios: list[str] = Field(
        default_factory=list, description="Criterios de aceptación (checklist de la tarjeta)"
    )
    vencimiento: str = Field(
        default="", description="Fecha límite ISO (p. ej. 2026-07-11), vacío si no se dijo"
    )


@mcp.tool
def actualizar_trello(
    nuevas_tarjetas: Annotated[
        list[TarjetaNueva], Field(description="Tarjetas a crear en 'Por hacer', una por tarea nueva")
    ] = [],
    completadas: Annotated[
        list[str],
        Field(description="Títulos (o parte) de tarjetas existentes que se dieron por cerradas en la reunión → se mueven a 'Hecho'"),
    ] = [],
    tablero: Annotated[str, Field(description="Nombre del tablero de Trello")] = "ReservaFácil",
) -> str:
    """Actualiza el tablón de Trello tras la reunión: crea una tarjeta en 'Por hacer' por cada
    tarea nueva (responsable en el título, criterios de aceptación como checklist, vencimiento
    si se dijo) y mueve a 'Hecho' lo que se dio por cerrado."""
    board, listas = _tablero_y_listas(tablero)
    hechas: list[str] = []

    if nuevas_tarjetas:
        por_hacer = _lista_por_nombre(listas, "Por hacer")
        for t in nuevas_tarjetas:
            nombre = f"{t.responsable}: {t.titulo}" if t.responsable else t.titulo
            params = {"idList": por_hacer["id"], "name": nombre}
            if t.vencimiento:
                params["due"] = t.vencimiento
            tarjeta = _trello("POST", "/cards", **params)
            if t.criterios:
                checklist = _trello(
                    "POST", "/checklists", idCard=tarjeta["id"], name="Criterios de aceptación"
                )
                for criterio in t.criterios:
                    _trello("POST", f"/checklists/{checklist['id']}/checkItems", name=criterio)
            hechas.append(f"✚ '{nombre}' en Por hacer ({len(t.criterios)} criterios)")

    if completadas:
        hecho = _lista_por_nombre(listas, "Hecho")
        tarjetas_board = _trello("GET", f"/boards/{board['id']}/cards", fields="name")
        for buscada in completadas:
            tarjeta = next(
                (c for c in tarjetas_board if buscada.strip().lower() in c["name"].lower()), None
            )
            if tarjeta:
                _trello("PUT", f"/cards/{tarjeta['id']}", idList=hecho["id"])
                hechas.append(f"✔ '{tarjeta['name']}' movida a Hecho")
            else:
                hechas.append(f"⚠ No encontré ninguna tarjeta que contenga '{buscada}'")

    if not hechas:
        return f"Nada que hacer en el tablero {board['name']} (sin tarjetas nuevas ni completadas)."
    return f"Tablero {board['name']} actualizado:\n" + "\n".join(hechas) + f"\n{board['url']}"


# ════════════════════════════════════════════════════════════════════════
# GOOGLE CALENDAR — la agenda
# ════════════════════════════════════════════════════════════════════════


def _calendario():
    """Devuelve el servicio de Google Calendar autenticado con token.json."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    token_path = Path(os.environ.get("GOOGLE_TOKEN_PATH", AQUI / "token.json"))
    if not token_path.exists():
        raise ToolError(
            "Google Calendar no está autorizado todavía. Ejecuta una vez en la terminal:\n"
            f"  cd {AQUI} && uv run autorizar_google.py\n"
            "(necesita el credentials.json de un proyecto de Google Cloud con la API de "
            "Calendar habilitada — ver README)."
        )
    creds = Credentials.from_authorized_user_file(
        str(token_path), ["https://www.googleapis.com/auth/calendar.events"]
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


@mcp.tool
def agendar_reunion(
    titulo: Annotated[str, Field(description="Título del evento, p. ej. 'Seguimiento ReservaFácil'")],
    inicio: Annotated[str, Field(description="Fecha y hora de inicio ISO, p. ej. '2026-07-09T12:00'")],
    duracion_minutos: Annotated[int, Field(ge=15, le=480, description="Duración en minutos")] = 60,
    descripcion: Annotated[str, Field(description="Descripción del evento (p. ej. enlace al acta)")] = "",
    invitados: Annotated[list[str], Field(description="Emails de los asistentes (opcional)")] = [],
) -> str:
    """Crea la próxima reunión en Google Calendar y devuelve el enlace al evento."""
    try:
        dt_inicio = datetime.fromisoformat(inicio)
    except ValueError:
        raise ToolError(f"No entiendo la fecha '{inicio}'. Usa formato ISO: 2026-07-09T12:00.")
    dt_fin = dt_inicio + timedelta(minutes=duracion_minutos)
    evento = {
        "summary": titulo,
        "description": descripcion,
        "start": {"dateTime": dt_inicio.isoformat(), "timeZone": "Europe/Madrid"},
        "end": {"dateTime": dt_fin.isoformat(), "timeZone": "Europe/Madrid"},
    }
    if invitados:
        evento["attendees"] = [{"email": e} for e in invitados]
    try:
        creado = _calendario().events().insert(calendarId="primary", body=evento).execute()
    except ToolError:
        raise
    except Exception as e:  # errores de la API de Google con mensaje claro
        raise ToolError(f"Google Calendar respondió con error: {e}")
    return f"Reunión '{titulo}' agendada para el {dt_inicio:%d/%m/%Y a las %H:%M}: {creado.get('htmlLink')}"


# ════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("MCP invisible-pm (FastMCP) en marcha ✓ — Fireflies · Notion · Trello · Calendar", file=sys.stderr)
    mcp.run()
