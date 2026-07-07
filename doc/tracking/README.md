# Tracking FreeForm — invisible_pm

Backend spec-driven **FreeForm** del SpecBox Engine (board `ff-7c307a263348`).

- **Fuente de verdad:** `items.json` (1 US · 4 UC · 13 AC)
- `config.json` / `labels.json`: metadatos del board (estados y etiquetas)

## Estado (ensayo víspera masterclass, 2026-07-07)

| UC | Nombre | Estado | ACs |
|---|---|---|---|
| UC-001 | Scaffolding del servidor MCP | ✅ done | 3/3 |
| UC-002 | Herramienta listar_reuniones | 🔍 review | 2/4 |
| UC-003 | Herramienta leer_reunion | 🔍 review | 1/3 |
| UC-004 | Registro en Claude Code y documentación | ✅ done | 3/3 |

Los UCs en **review** tienen pendientes solo los ACs que exigen una llamada real a la API de
Fireflies con `FIREFLIES_API_KEY` válida (UC-002: AC-01, AC-04 · UC-003: AC-01, AC-02).
Probar la víspera con la clave real y marcar con `mark_ac_batch`.

## Evidencias registradas

- **UC-001:** `npm install` 0 vulnerabilidades (Node v24). Handshake JSON-RPC stdio verificado:
  `initialize` → `fireflies-invisible-pm 1.0.0`; `tools/list` → exactamente 2 herramientas.
  Confirmación de arranque por stderr, stdout limpio.
- **UC-002:** `limite=99` rechazado por zod (error -32602, max 25); default 5 aplicado.
  Sin API key → "Falta la clave de Fireflies… Settings → Developer settings → API key" (isError).
- **UC-003:** Con clave inválida, Fireflies responde HTTP 200 + `errors` GraphQL; el servidor lo
  convierte en mensaje claro, sin stack trace.
- **UC-004:** README de `fireflies-mcp/` con instalación, registro (`claude mcp add … ruta absoluta`)
  y plan B con el MCP oficial remoto.
