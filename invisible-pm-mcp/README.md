# invisible-pm · El Project Manager invisible

**Un solo MCP** (Python + FastMCP) con todo el pipeline del martes post-reunión:

```
Fireflies (los oídos) → Notion (el archivo) → Trello (el tablón) → Calendar (la agenda)
```

Claude Code redacta el acta y decide; este MCP le da las acreditaciones para ejecutar.

## Herramientas

| Herramienta | Servicio | Qué hace |
|---|---|---|
| `listar_reuniones(limite)` | Fireflies | Últimas reuniones: id, título, fecha, duración |
| `leer_reunion(id?)` | Fireflies | Resumen, puntos de acción y transcripción con hablantes. Sin `id` = la última |
| `publicar_acta_notion(titulo, contenido_markdown, pagina_padre?)` | Notion | Crea la página del acta (markdown → bloques) y devuelve su URL |
| `actualizar_trello(nuevas_tarjetas, completadas?, tablero?)` | Trello | Tarjetas en "Por hacer" con responsable + checklist de criterios + vencimiento; mueve a "Hecho" lo cerrado |
| `agendar_reunion(titulo, inicio, duracion_minutos?, descripcion?, invitados?)` | Calendar | Crea el evento y devuelve el enlace |

## Instalación

1. [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. `uv sync` (crea `.venv/` con Python 3.12 + FastMCP)

## Credenciales (las 4 acreditaciones)

| Variable | Dónde se consigue |
|---|---|
| `FIREFLIES_API_KEY` | Fireflies → Settings → Developer settings → API key |
| `NOTION_API_KEY` | https://www.notion.so/my-integrations (integración interna) + compartir la página **Proyectos** con ella (··· → Conexiones) |
| `TRELLO_API_KEY` / `TRELLO_TOKEN` | https://trello.com/power-ups/admin |
| Google Calendar | `credentials.json` de Google Cloud (OAuth "Escritorio", API Calendar habilitada) en esta carpeta → `uv run autorizar_google.py` una vez (abre navegador, guarda `token.json`) |

Ninguna clave se sube a Git: viven en el `.env` del root (gitignorado) y en `token.json` (gitignorado).

## Registro en Claude Code

```
claude mcp add invisible-pm \
  -e FIREFLIES_API_KEY=... -e NOTION_API_KEY=... \
  -e TRELLO_API_KEY=... -e TRELLO_TOKEN=... \
  -- /ruta/absoluta/invisible-pm-mcp/.venv/bin/python /ruta/absoluta/invisible-pm-mcp/server.py
```

> Ruta **absoluta** al python del venv, y **reinicia la sesión** de Claude Code tras registrar.

## Gotchas cazados en el ensayo (07/07/2026)

- El esquema GraphQL de Fireflies usa `transcript(id:)` — **no** `transcript(transcriptId:)`.
- Con clave inválida, Fireflies responde HTTP 200 + array `errors`, no un 401.
- Cada tool sin su credencial devuelve un error en español con los pasos exactos de configuración
  (probado): así la demo degrada con elegancia en vez de romperse.

## Plan B

Versión Node.js solo-Fireflies (probada contra la API real): `doc/masterclass/fireflies-mcp/`.
MCP oficial de Fireflies: `claude mcp add fireflies-oficial -- npx mcp-remote https://api.fireflies.ai/mcp --header "Authorization: Bearer TU_KEY"`.
