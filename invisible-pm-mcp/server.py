"""invisible-pm — El Project Manager invisible · Masterclass MCP.

UN solo MCP con todo el pipeline del martes post-reunión:

    Fireflies (los oídos)  →  Notion (el archivo)  →  Trello (el tablón)  →  Calendar (la agenda)

Herramientas:
    listar_reuniones / leer_reunion     — los oídos: Plaud (CLI) o Fireflies (GraphQL)
    publicar_acta_notion                — crea la página del acta en Notion
    actualizar_trello                   — tarjetas nuevas con checklist + mover a Hecho
    agendar_reunion                     — evento en Google Calendar

Claude redacta el acta y decide; este MCP le da las acreditaciones para ejecutar.

Variables de entorno (.env / claude mcp add -e):
    FUENTE_REUNIONES         — "plaud" (por defecto) o "fireflies". Cambiar los oídos
                               no toca el resto del pipeline: esa es la gracia.
    (Plaud)                  — sin API key: usa la CLI `plaud` autenticada (`plaud login`)
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
import shutil
import subprocess
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
MAX_TRANSCRIPCION = 20000  # caracteres; una reunión de 3h no debe inundar el contexto de Claude


def _cargar_env() -> None:
    """Carga las llaves del .env del root del repo, sin pisar las ya definidas.
    Así el registro en Claude Code no necesita repetir cada -e cuando se añade una llave."""
    env_path = AQUI.parent / ".env"
    if not env_path.exists():
        return
    for linea in env_path.read_text().splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        if clave.strip() and valor.strip():
            os.environ.setdefault(clave.strip(), valor.strip())


_cargar_env()


def _fecha(ms) -> str:
    """Milisegundos epoch → '30 jun 2026, 17:00' (es-ES)."""
    if not ms:
        return "sin fecha"
    dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).astimezone()
    return f"{dt.day} {MESES[dt.month - 1]} {dt.year}, {dt:%H:%M}"


# ════════════════════════════════════════════════════════════════════════
# LOS OÍDOS — fuente conmutable: Plaud (por defecto) o Fireflies
# ════════════════════════════════════════════════════════════════════════

FUENTE_REUNIONES = os.environ.get("FUENTE_REUNIONES", "plaud").strip().lower()

# ── Plaud (via CLI autenticada: `plaud login`) ──────────────────────────

PLAUD_CLI = shutil.which("plaud") or "/opt/homebrew/bin/plaud"


def _plaud_cli(*args: str) -> str:
    if not Path(PLAUD_CLI).exists():
        raise ToolError(
            "No encuentro la CLI de Plaud. Instálala (brew install plaud o "
            "https://support.plaud.ai → Plaud CLI) y ejecuta `plaud login`."
        )
    try:
        res = subprocess.run(
            [PLAUD_CLI, *args], capture_output=True, text=True, timeout=90
        )
    except subprocess.TimeoutExpired:
        raise ToolError("Plaud no respondió en 90 segundos. Comprueba tu conexión a internet.")
    salida = (res.stdout or "") + (res.stderr or "")
    if res.returncode != 0 or "✗ [" in salida:
        if "AUTH_FAILED" in salida:
            raise ToolError("La sesión de Plaud ha caducado. Ejecuta `plaud login` en la terminal y reintenta.")
        if any(c in salida for c in ("NOT_FOUND", "[404", "[500", "FETCH_FAILED")):
            raise ToolError(
                "Plaud no pudo recuperar esa reunión: lo más probable es que el id no exista "
                "(cópialo tal cual de listar_reuniones)."
            )
        raise ToolError(f"Plaud respondió con error: {salida.strip()[:300]}")
    return res.stdout


def _plaud_limpiar(texto: str, *cabeceras: str) -> str:
    """Quita las líneas de spinner/cabecera de la salida de la CLI."""
    lineas = []
    for linea in texto.splitlines():
        s = linea.strip()
        if not s or s.startswith("- Fetching") or any(s.startswith(c) for c in cabeceras):
            continue
        lineas.append(linea.rstrip())
    return "\n".join(lineas).strip()


FILA_PLAUD = re.compile(r"^\s{2}([0-9a-f]{32})\s+(.+?)\s{2,}(\d{4}-\d{2}-\d{2})\s+(\S+)\s*$")


def _plaud_filas(pagina_texto: str) -> list[tuple[str, str, str, str]]:
    return [m.groups() for l in pagina_texto.splitlines() if (m := FILA_PLAUD.match(l))]


def _plaud_listar(limite: int) -> str:
    salida = _plaud_cli("files", "-s", str(max(10, limite)))
    filas = _plaud_filas(salida)[:limite]
    if not filas:
        return "No hay reuniones grabadas todavía en esta cuenta de Plaud."
    return "\n".join(f"• [{fid}] {nombre} — {fecha} ({dur})" for fid, nombre, fecha, dur in filas)


def _plaud_leer(id: str | None) -> str:
    if not id:
        filas = _plaud_filas(_plaud_cli("files", "-s", "10"))
        if not filas:
            return "No hay ninguna reunión grabada en esta cuenta de Plaud."
        id = filas[0][0]
    detalle = _plaud_limpiar(_plaud_cli("file", id), "File Details:")
    campos = dict(
        (k.strip(), v.strip())
        for k, _, v in (l.partition(":") for l in detalle.splitlines())
        if _
    )
    resumen = _plaud_limpiar(_plaud_cli("summary", id), "Summary:") or "(sin resumen)"
    transcripcion = _plaud_limpiar(_plaud_cli("transcript", id), "Transcript:") or "(vacía)"
    if len(transcripcion) > MAX_TRANSCRIPCION:
        omitidos = len(transcripcion) - MAX_TRANSCRIPCION
        transcripcion = transcripcion[:MAX_TRANSCRIPCION] + f"\n… (transcripción truncada: {omitidos} caracteres omitidos)"
    return "\n".join(
        [
            f"REUNIÓN: {campos.get('name', id)}",
            f"FECHA: {campos.get('start_at', campos.get('created_at', 'sin fecha'))} · DURACIÓN: {campos.get('duration', '?')}",
            "",
            "RESUMEN AUTOMÁTICO:",
            resumen,
            "",
            "TRANSCRIPCIÓN:",
            transcripcion,
        ]
    )


# ── Fireflies (GraphQL) ─────────────────────────────────────────────────

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


def _fireflies_listar(limite: int) -> str:
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


def _fireflies_leer(id: str | None) -> str:
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
    if len(dialogo) > MAX_TRANSCRIPCION:
        omitidos = len(dialogo) - MAX_TRANSCRIPCION
        dialogo = dialogo[:MAX_TRANSCRIPCION] + f"\n… (transcripción truncada: {omitidos} caracteres omitidos)"
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


# ── Las dos herramientas de los oídos (despachan según FUENTE_REUNIONES) ─


@mcp.tool
def listar_reuniones(
    limite: Annotated[int, Field(ge=1, le=25, description="Cuántas reuniones devolver (1-25)")] = 5,
) -> str:
    """Lista las últimas reuniones grabadas con su id, título, fecha y duración.
    La fuente (Plaud o Fireflies) la decide la variable de entorno FUENTE_REUNIONES."""
    if FUENTE_REUNIONES == "fireflies":
        return _fireflies_listar(limite)
    return _plaud_listar(limite)


@mcp.tool
def leer_reunion(
    id: Annotated[
        str | None,
        Field(description="Id de la reunión (de listar_reuniones). Vacío = la más reciente."),
    ] = None,
) -> str:
    """Devuelve el contenido de una reunión: resumen automático y transcripción completa
    con quién dijo qué. Si no se indica id, devuelve la última reunión. La fuente
    (Plaud o Fireflies) la decide la variable de entorno FUENTE_REUNIONES."""
    if FUENTE_REUNIONES == "fireflies":
        return _fireflies_leer(id)
    return _plaud_leer(id)


# ════════════════════════════════════════════════════════════════════════
# GUIAR PROPUESTA — de la reunión al borrador comercial
# ════════════════════════════════════════════════════════════════════════


def _leer_fuente(id: str | None) -> str:
    """Contenido de la reunión según la fuente activa (mismo texto que leer_reunion)."""
    if FUENTE_REUNIONES == "fireflies":
        return _fireflies_leer(id)
    return _plaud_leer(id)


def _participantes(contenido: str) -> list[str]:
    """Nombres únicos de quien habla, extraídos de la transcripción."""
    # solo el bloque de diálogo — las cabeceras (REUNIÓN:, FECHA:) también llevan dos puntos
    _, _, dialogo = contenido.partition("TRANSCRIPCIÓN:")
    vistos: list[str] = []
    for linea in (dialogo or contenido).splitlines():
        # Plaud: "[MM:SS - MM:SS] Nombre: texto" · Fireflies: "Nombre: texto"
        m = re.match(r"^(?:\[[\d:]+\s*-\s*[\d:]+\]\s*)?([A-ZÁÉÍÓÚÑ][\w .áéíóúñÁÉÍÓÚÑ-]{1,40}?):\s", linea)
        if m and m.group(1) not in vistos:
            vistos.append(m.group(1))
    return vistos


PLANTILLA_PROPUESTA = """\
== INSTRUCCIONES PARA REDACTAR EL BORRADOR ==
Redacta AHORA un borrador completo de propuesta de {tipo} en markdown, siguiendo las
secciones de abajo. Reglas innegociables:
- Todo lo que afirmes del cliente debe salir de la reunión; cita literalmente los dolores.
- Lo que la reunión NO diga se marca como [TBD: qué falta] — NUNCA lo inventes
  (presupuestos, plazos, nombres, alcances no discutidos).
- Después del borrador, lista en un bloque final las preguntas abiertas que el usuario
  debe responder para cerrar cada [TBD].
- Tono profesional y cercano, en español.

== SECCIONES DEL BORRADOR ==
1. Contexto y objetivo — quién es el cliente y qué busca (apóyate en el resumen).
2. Necesidades detectadas — cada dolor con su cita literal de la transcripción.
3. Solución propuesta — SOLO lo que se discutió en la reunión; no añadas alcance nuevo.
4. Alcance por fases — divide la solución en fases entregables.
5. Cronograma — [TBD si no se hablaron fechas].
6. Inversión — [TBD: presupuesto no mencionado en la reunión] salvo que se dijera cifra.
7. Supuestos y fuera de alcance — lo que explícitamente quedó fuera o se pospuso.
8. Próximos pasos — incluye la próxima reunión si se acordó.

== HUECOS TÍPICOS A PREGUNTAR TRAS EL BORRADOR ==
- ¿Presupuesto orientativo u horquilla? · ¿Plazo o fecha objetivo? · ¿Quién decide/firma?
- ¿Formato de entrega de la propuesta (PDF, página de Notion, email)?
"""


@mcp.tool
def guiar_propuesta(
    id: Annotated[
        str | None,
        Field(description="Id de la reunión (de listar_reuniones). Vacío = la más reciente."),
    ] = None,
    tipo: Annotated[
        str,
        Field(description="Tipo de propuesta: 'servicios' (por defecto), 'producto', 'formación'…"),
    ] = "servicios",
) -> str:
    """Prepara el expediente para redactar un BORRADOR de propuesta comercial a partir de una
    reunión: contenido de la reunión + participantes detectados + plantilla con instrucciones
    de extracción por sección y reglas anti-invención. Úsala cuando el usuario pida una
    propuesta, presupuesto u oferta basada en una reunión."""
    contenido = _leer_fuente(id)
    participantes = _participantes(contenido)
    cabecera = [
        "EXPEDIENTE DE PROPUESTA — generado desde la reunión",
        f"PARTICIPANTES DETECTADOS: {', '.join(participantes) if participantes else '(no identificados — pregunta al usuario)'}",
        "",
        PLANTILLA_PROPUESTA.format(tipo=tipo),
        "== CONTENIDO DE LA REUNIÓN ==",
        contenido,
    ]
    return "\n".join(cabecera)


@mcp.prompt
def propuesta(id_reunion: str = "") -> str:
    """Receta: borrador de propuesta comercial a partir de una reunión."""
    objetivo = f"la reunión con id {id_reunion}" if id_reunion else "la última reunión"
    return (
        f"Llama a la herramienta guiar_propuesta de invisible-pm sobre {objetivo} y sigue sus "
        "instrucciones al pie de la letra: redacta el borrador completo de propuesta en markdown, "
        "marca como [TBD] todo lo que la reunión no diga, y termina con las preguntas abiertas "
        "que necesito responder para cerrar la propuesta."
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
