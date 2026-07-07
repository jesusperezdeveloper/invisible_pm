# MCP Fireflies · El Project Manager invisible

Servidor MCP mínimo (2 herramientas) que conecta Claude Code con Fireflies.
Construido en la masterclass "El Project Manager invisible" (PotenzIA).

## Instalación

1. Requiere Node.js 18 o superior (`node -v`).
2. Instala dependencias:
   ```
   npm install
   ```
3. Genera tu API key: Fireflies → **Settings → Developer settings → API key**.
   Es la llave de tus reuniones — no la compartas ni la subas a Git.

## Registro en Claude Code

```
claude mcp add fireflies -e FIREFLIES_API_KEY=tu_clave -- node /ruta/absoluta/fireflies-mcp/index.js
```

> Usa la **ruta absoluta** al `index.js` (obtenla con `pwd` dentro de la carpeta).
> Tras registrar, **reinicia la sesión de Claude Code** para que cargue el servidor.

Probar dentro de Claude Code:

> "Lista mis últimas reuniones de Fireflies."

## Herramientas

| Herramienta | Qué hace |
|---|---|
| `listar_reuniones(limite)` | Últimas reuniones: id, título, fecha y duración. `limite` 1-25, por defecto 5. |
| `leer_reunion(id?)` | Resumen, puntos de acción y transcripción con hablantes. Sin `id` = la última. |

## Plan B — MCP oficial de Fireflies

Si el servidor propio falla en directo, el conector oficial remoto:

```
claude mcp add fireflies-oficial -- npx mcp-remote https://api.fireflies.ai/mcp --header "Authorization: Bearer TU_KEY"
```
