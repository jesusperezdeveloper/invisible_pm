# Pre-work · Masterclass "El Project Manager invisible"

**Tiempo estimado: 25 minutos. Hazlo HOY.** Mañana construimos en directo un sistema que convierte tus reuniones en actas, tareas y calendario de forma automática. Si llegas con esto hecho, saldrás de clase con él funcionando en tu ordenador. Si no, solo podrás mirar.

---

## 1. Claude Code instalado y funcionando (10 min)

Claude Code es la herramienta de terminal con la que trabajaremos toda la clase. Guía oficial de instalación: https://docs.claude.com/en/docs/claude-code/overview

Comprueba que funciona: abre una terminal, escribe `claude` y verifica que arranca y tienes sesión iniciada. Necesitas también Node.js 18 o superior (compruébalo con `node -v`; si no lo tienes: https://nodejs.org).

**Opcional para construir el MCP propio en tu máquina:** instala `uv`, el gestor de Python que usaremos (un comando, no necesitas tener Python instalado):

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Tu tablero de Trello (5 min)

1. Cuenta gratuita en https://trello.com si no la tienes.
2. Crea un tablero llamado **Mi proyecto** con tres listas: **Por hacer**, **En curso**, **Hecho**.
3. Añade 3 tarjetas de un proyecto real tuyo (aunque sea pequeño). Mañana Claude las leerá y las moverá.

## 3. Tu espacio de Notion (3 min)

1. Cuenta gratuita en https://notion.so si no la tienes.
2. Crea una página llamada **Proyectos**. Vacía vale. Ahí aterrizarán las actas.

## 4. Tu cuenta de Fireflies (5 min)

Fireflies es el "tomador de notas" que se une a tus reuniones de Zoom y las transcribe.

1. Cuenta gratuita en https://fireflies.ai (regístrate con tu cuenta de Google).
2. Ve a **Settings → Developer settings** y genera tu **API key**. Guárdala en un sitio seguro — es la llave de tus reuniones, no la compartas.
3. Si tu plan no te deja generar la API key, no pasa nada: en clase verás la alternativa con el conector oficial de Fireflies.

## 5. Opcional para valientes (2 min)

Conecta ya tu primer MCP. En la terminal:

```
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

Luego abre Claude Code, escribe `/mcp` y autoriza Notion en el navegador. Si te funciona, mañana vas un paso por delante. Si no, lo hacemos juntos en clase.

---

**Checklist final:** ☐ Claude Code arranca · ☐ Tablero Trello con 3 tarjetas · ☐ Página Proyectos en Notion · ☐ Cuenta Fireflies (+ API key si tu plan lo permite)

Nos vemos mañana. Trae una reunión real de tu semana en la cabeza: la vas a querer automatizar.
