"""MCP Fireflies — El Project Manager invisible · Masterclass MCP.

Servidor MCP mínimo (FastMCP) que conecta Claude Code con tus reuniones de Fireflies.
2 herramientas: listar_reuniones y leer_reunion.

Uso:
    FIREFLIES_API_KEY=tu_clave uv run server.py

Registro en Claude Code (ruta absoluta al python del venv tras `uv sync`):
    claude mcp add fireflies -e FIREFLIES_API_KEY=tu_clave -- \
        /ruta/absoluta/fireflies-mcp/.venv/bin/python /ruta/absoluta/fireflies-mcp/server.py
"""

import os
import sys
from datetime import datetime, timezone
from typing import Annotated

import httpx
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

API_URL = "https://api.fireflies.ai/graphql"

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

mcp = FastMCP("fireflies-invisible-pm")


def _fireflies(query: str, variables: dict | None = None) -> dict:
    """Llamada genérica a la API GraphQL de Fireflies."""
    api_key = os.environ.get("FIREFLIES_API_KEY")
    if not api_key:
        raise ToolError(
            "Falta la clave de Fireflies. Arranca el servidor con FIREFLIES_API_KEY=tu_clave. "
            "La clave se genera en Fireflies → Settings → Developer settings → API key."
        )
    try:
        res = httpx.post(
            API_URL,
            json={"query": query, "variables": variables or {}},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )
    except httpx.HTTPError:
        raise ToolError("No se pudo conectar con Fireflies. Comprueba tu conexión a internet.")
    if res.status_code in (401, 403):
        raise ToolError(
            "Fireflies rechazó la clave (API key inválida o caducada). "
            "Genera una nueva en Settings → Developer settings."
        )
    try:
        payload = res.json()
    except ValueError:
        raise ToolError(f"Fireflies devolvió una respuesta inesperada (HTTP {res.status_code}).")
    if payload.get("errors"):
        detalle = "; ".join(e.get("message", "") for e in payload["errors"])
        raise ToolError(f"Fireflies respondió con error: {detalle}")
    return payload.get("data", {})


def _fecha(ms) -> str:
    """Milisegundos epoch → '30 jun 2026, 17:00' (es-ES)."""
    if not ms:
        return "sin fecha"
    dt = datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).astimezone()
    return f"{dt.day} {MESES[dt.month - 1]} {dt.year}, {dt:%H:%M}"


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


if __name__ == "__main__":
    print("MCP Fireflies · invisible_pm (FastMCP) en marcha ✓", file=sys.stderr)
    mcp.run()
