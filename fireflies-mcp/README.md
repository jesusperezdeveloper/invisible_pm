# MCP Fireflies · El Project Manager invisible

Servidor MCP mínimo (2 herramientas) en **Python + FastMCP** que conecta Claude Code con Fireflies.
Construido en la masterclass "El Project Manager invisible" (PotenzIA).

## Instalación

1. Requiere [uv](https://docs.astral.sh/uv/) (gestiona Python y dependencias automáticamente):
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
2. Instala dependencias (crea `.venv/` con Python 3.12 + FastMCP):
   ```
   uv sync
   ```
3. Genera tu API key: Fireflies → **Settings → Developer settings → API key**.
   Es la llave de tus reuniones — no la compartas ni la subas a Git.

## Registro en Claude Code

Con la **ruta absoluta** al python del venv (obtenla con `pwd` dentro de la carpeta):

```
claude mcp add fireflies -e FIREFLIES_API_KEY=tu_clave -- \
  /ruta/absoluta/fireflies-mcp/.venv/bin/python /ruta/absoluta/fireflies-mcp/server.py
```

> Tras registrar, **reinicia la sesión de Claude Code** para que cargue el servidor.

Probar dentro de Claude Code:

> "Lista mis últimas reuniones de Fireflies."

## Herramientas

| Herramienta | Qué hace |
|---|---|
| `listar_reuniones(limite)` | Últimas reuniones: id, título, fecha y duración. `limite` 1-25, por defecto 5. |
| `leer_reunion(id?)` | Resumen, puntos de acción y transcripción con hablantes. Sin `id` = la última. |

## Gotcha aprendido en el ensayo

El esquema GraphQL de Fireflies usa `transcript(id: String!)` — **no** `transcript(transcriptId:)`.
Con una clave inválida la API responde HTTP 200 con un array `errors`, no un 401.

## Planes B

1. **MCP oficial de Fireflies** (remoto):
   ```
   claude mcp add fireflies-oficial -- npx mcp-remote https://api.fireflies.ai/mcp --header "Authorization: Bearer TU_KEY"
   ```
2. **Versión Node.js de respaldo** (probada contra la API real): `doc/masterclass/fireflies-mcp/`
   ```
   claude mcp add fireflies -e FIREFLIES_API_KEY=tu_clave -- node /ruta/absoluta/doc/masterclass/fireflies-mcp/index.js
   ```
