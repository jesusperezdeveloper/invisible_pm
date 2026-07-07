# MCP Fireflies · PotenzIA

Servidor MCP mínimo (2 herramientas) que conecta Claude Code con Fireflies.
Versión de respaldo probada — la que Claude Code construirá en directo debería salir equivalente.

## Uso
1. `npm install`
2. API key: Fireflies → Settings → Developer settings
3. Registrar en Claude Code:
   `claude mcp add fireflies -e FIREFLIES_API_KEY=tu_clave -- node /ruta/absoluta/index.js`
4. Probar dentro de Claude Code: "Lista mis últimas reuniones de Fireflies"

## Herramientas
- `listar_reuniones(limite)` — últimas reuniones: id, título, fecha, duración
- `leer_reunion(id?)` — resumen, puntos de acción y transcripción con hablantes. Sin id = la última.

## Estado de pruebas (06/07/2026)
✔ Protocolo MCP (initialize + tools/list) — verificado
✔ Manejo de error sin API key — mensaje claro en español
⚠ Llamada real a la API de Fireflies — pendiente de probar con API key real (hazlo la víspera)

## Plan B — MCP oficial de Fireflies
`claude mcp add fireflies-oficial -- npx mcp-remote https://api.fireflies.ai/mcp --header "Authorization: Bearer TU_KEY"`
