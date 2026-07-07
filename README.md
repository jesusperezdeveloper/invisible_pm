# invisible_pm — El Project Manager invisible

Proyecto de la masterclass MCP (PotenzIA): una reunión termina → un solo prompt en Claude Code → acta en Notion + tarjetas de Trello con criterios de aceptación + próxima reunión en Calendar.

## Contenido

| Carpeta | Qué es |
|---|---|
| [`fireflies-mcp/`](fireflies-mcp/) | Servidor MCP propio de Fireflies en **Python + FastMCP** (`listar_reuniones`, `leer_reunion`) |
| [`doc/masterclass/`](doc/masterclass/) | Guion, pre-work, slides y versión Node.js de respaldo del MCP |
| [`doc/tracking/`](doc/tracking/) | Tracking spec-driven FreeForm (SpecBox Engine — US/UC/AC) |

## El flujo completo (prompt mágico)

```
Lee la última reunión de Fireflies. Después:
1. Crea el acta en Notion dentro de Proyectos/ReservaFácil: fecha, asistentes,
   decisiones tomadas, tareas con responsable y fecha, y próximos pasos.
2. En el tablero Trello ReservaFácil: crea una tarjeta en "Por hacer" por cada
   tarea nueva, con el responsable en el título y los criterios de aceptación
   como checklist. Si algo se dio por cerrado en la reunión, muévelo a "Hecho".
3. Crea en Google Calendar la reunión acordada para el jueves a las 12:00
   con el enlace al acta en la descripción.
Cuando termines, resume todo lo que has hecho.
```

## Conexiones MCP usadas en la clase

| Pieza | Tipo | Registro |
|---|---|---|
| Notion | Oficial remoto | `claude mcp add --transport http notion https://mcp.notion.com/mcp` (+ autorizar con `/mcp`) |
| Trello | Comunidad | `GabrielRamirez/trello-mcp` (clone → `npm install` → `npm run setup`) |
| Google Calendar | Oficial con fricción | Requiere proyecto Google Cloud + OAuth (~15 min) |
| Fireflies | **Propio** (este repo) | `claude mcp add fireflies -e FIREFLIES_API_KEY=clave -- <repo>/fireflies-mcp/.venv/bin/python <repo>/fireflies-mcp/server.py` |

## Construcción del MCP propio

```
cd fireflies-mcp
uv sync          # crea .venv con Python 3.12 + FastMCP
FIREFLIES_API_KEY=tu_clave uv run server.py   # prueba manual
```

Detalles, gotchas y planes B en [`fireflies-mcp/README.md`](fireflies-mcp/README.md).
