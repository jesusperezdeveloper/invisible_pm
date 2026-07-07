# Tracking FreeForm — invisible_pm

Backend spec-driven **FreeForm** del SpecBox Engine (board `ff-7c307a263348`).

- **Fuente de verdad:** `items.json` (1 US · 4 UC · 13 AC)
- `config.json` / `labels.json`: metadatos del board (estados y etiquetas)
- **Spec v2 (2026-07-07):** servidor reescrito en **Python + FastMCP** (la v1 era Node.js; la
  versión Node queda como respaldo en `doc/masterclass/fireflies-mcp/`)

## Estado (ensayo víspera masterclass, 2026-07-07)

| UC | Nombre | Estado | ACs |
|---|---|---|---|
| UC-001 | Scaffolding del servidor FastMCP en Python | ✅ done | 3/3 |
| UC-002 | Herramienta listar_reuniones | 🔍 review | 3/4 |
| UC-003 | Herramienta leer_reunion | ✅ done | 3/3 |
| UC-004 | Registro en Claude Code y documentación | ✅ done | 3/3 |

Único AC pendiente: **UC-002 AC-04** (cuenta sin reuniones → mensaje informativo). No
verificable con esta cuenta porque ya tiene reuniones; el camino de código existe y está
revisado. Verificable solo con una cuenta Fireflies vacía.

## Evidencias registradas (batería JSON-RPC stdio, API real)

- **UC-001:** `uv sync` sin errores (FastMCP 3.4.3, Python 3.12). `initialize` →
  `fireflies-invisible-pm`; `tools/list` → exactamente 2 herramientas. Confirmación por stderr,
  stdout limpio para el protocolo.
- **UC-002:** `listar_reuniones` devuelve las reuniones reales de la cuenta (id, título, fecha
  es-ES, duración en minutos). `limite=99` rechazado por pydantic (`less_than_equal 25`);
  default 5 aplicado. Sin API key → "Falta la clave de Fireflies… Settings → Developer settings".
- **UC-003:** Sin id devuelve la última reunión completa (resumen, puntos de acción,
  transcripción con hablantes); con id explícito devuelve esa reunión; id inexistente →
  "Transcript not found" limpio. **Bug cazado en el ensayo (v1 Node):** el esquema de Fireflies
  usa `transcript(id:)`, no `transcript(transcriptId:)` — corregido también en el respaldo Node.
- **UC-004:** README de `fireflies-mcp/` con `uv sync`, registro con ruta absoluta al python del
  venv y planes B (oficial remoto + respaldo Node).
- Con clave inválida, Fireflies responde HTTP 200 + `errors` GraphQL; el servidor lo convierte
  en mensaje claro (ToolError), sin stack trace.
