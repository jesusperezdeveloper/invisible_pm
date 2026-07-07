# Tracking FreeForm — invisible_pm

Backend spec-driven **FreeForm** del SpecBox Engine (board `ff-7c307a263348`).

- **Fuente de verdad:** `items.json` (1 US · 4 UC · 13 AC)
- `config.json` / `labels.json`: metadatos del board (estados y etiquetas)

## Estado (ensayo víspera masterclass, 2026-07-07)

| UC | Nombre | Estado | ACs |
|---|---|---|---|
| UC-001 | Scaffolding del servidor MCP | ✅ done | 3/3 |
| UC-002 | Herramienta listar_reuniones | 🔍 review | 3/4 |
| UC-003 | Herramienta leer_reunion | ✅ done | 3/3 |
| UC-004 | Registro en Claude Code y documentación | ✅ done | 3/3 |

Único AC pendiente: **UC-002 AC-04** (cuenta sin reuniones → mensaje informativo). No
verificable con esta cuenta porque ya tiene reuniones; el camino de código existe y está
revisado. Verificable solo con una cuenta Fireflies vacía.

## Evidencias registradas

- **UC-001:** `npm install` 0 vulnerabilidades (Node v24). Handshake JSON-RPC stdio verificado:
  `initialize` → `fireflies-invisible-pm 1.0.0`; `tools/list` → exactamente 2 herramientas.
  Confirmación de arranque por stderr, stdout limpio.
- **UC-002:** `limite=99` rechazado por zod (error -32602, max 25); default 5 aplicado.
  Sin API key → "Falta la clave de Fireflies… Settings → Developer settings → API key" (isError).
- **UC-002 (API real, 2026-07-07):** `listar_reuniones` devuelve las reuniones reales de la
  cuenta con id, título, fecha es-ES y duración en minutos.
- **UC-003 (API real, 2026-07-07):** `leer_reunion` sin id devuelve la última reunión completa
  (resumen, puntos de acción, transcripción con hablantes); con id explícito devuelve esa misma
  reunión; con id inexistente devuelve "Transcript not found" limpio. **Bug corregido en el
  ensayo:** el esquema de Fireflies usa `transcript(id:)`, no `transcript(transcriptId:)` — la
  versión de respaldo también lo tenía y habría fallado en directo.
- Con clave inválida, Fireflies responde HTTP 200 + `errors` GraphQL; el servidor lo
  convierte en mensaje claro, sin stack trace.
- **UC-004:** README de `fireflies-mcp/` con instalación, registro (`claude mcp add … ruta absoluta`)
  y plan B con el MCP oficial remoto.
