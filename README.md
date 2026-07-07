# invisible_pm — El Project Manager invisible

**Un solo MCP que se come el martes post-reunión**: termina la reunión → un prompt en Claude Code → acta en Notion + tarjetas de Trello con criterios de aceptación + próxima reunión en Calendar.

```
                         ┌──────────────── invisible-pm (MCP propio, FastMCP) ────────────────┐
Claude Code ── prompt ──▶│  Fireflies        Notion           Trello           Calendar       │
                         │  (los oídos)      (el archivo)     (el tablón)      (la agenda)    │
                         │  listar/leer      publicar_acta    actualizar       agendar        │
                         └──────────────────────────────────────────────────────────────────┘
```

## Contenido

| Carpeta | Qué es |
|---|---|
| [`invisible-pm-mcp/`](invisible-pm-mcp/) | **El MCP completo** (Python + FastMCP): 5 herramientas sobre Fireflies, Notion, Trello y Google Calendar |
| [`doc/masterclass/`](doc/masterclass/) | Guion, pre-work, slides y versión Node.js solo-Fireflies de respaldo |
| [`doc/tracking/`](doc/tracking/) | Tracking spec-driven FreeForm (SpecBox Engine — US/UC/AC) |

## El prompt mágico

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

Una sola acreditación: Claude resuelve los 3 pasos llamando a las herramientas de `invisible-pm`.

## Puesta en marcha

```
cd invisible-pm-mcp
uv sync
claude mcp add invisible-pm \
  -e FIREFLIES_API_KEY=... -e NOTION_API_KEY=... \
  -e TRELLO_API_KEY=... -e TRELLO_TOKEN=... \
  -- $(pwd)/.venv/bin/python $(pwd)/server.py
```

Credenciales, autorización de Google Calendar y gotchas: [`invisible-pm-mcp/README.md`](invisible-pm-mcp/README.md).
