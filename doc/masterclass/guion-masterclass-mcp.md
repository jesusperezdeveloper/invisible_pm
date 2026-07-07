# Masterclass · El Project Manager invisible
## Construye el MCP que gestiona tus proyectos

**Formato:** directo por Zoom · 120 min · Valen (guión compatible si Jesús se suma en Q&A)
**Objetivo de sesión (ocurre EN la clase, min ~105):** termina una reunión → un solo prompt en Claude Code → acta en Notion + tarjetas de Trello actualizadas con criterios de aceptación + próxima reunión en Calendar. Delante de todos.
**Contexto:** esta es la revancha de la 4.5. Allí los MCP se quedaron en abstracto. Hoy: cero teoría suelta, todo funcionando en vivo.

---

## Stack verificado (07/07/2026 — ensayo completo con API real)

**Arquitectura v2 (decisión 07/07): UN solo MCP propio — `invisible-pm` — con las cuatro acreditaciones dentro.** Las cuatro tarjetas del Bloque 2 (Fireflies = los oídos, Notion = el archivo, Trello = el tablón, Calendar = la agenda) son los servicios a los que el MCP habla por API; cada uno con su llave en el `.env`. Los MCPs oficial/comunidad siguen existiendo como alternativas y alimentan la tabla de decisión del B2.

| Pieza | Papel en invisible-pm | Llave | Estado ensayo 07/07 |
|---|---|---|---|
| **Plaud** (fuente por defecto) | `listar_reuniones` / `leer_reunion` via CLI — decenas de reuniones reales ya procesadas | `plaud login` (una vez; la CLI refresca sola) | ✅ probado con reuniones reales (11m y 3h13m) |
| **Fireflies** (fuente alternativa + camino de los alumnos) | Las mismas 2 herramientas via GraphQL — se conmuta con `FUENTE_REUNIONES=fireflies` | `FIREFLIES_API_KEY` | ✅ probado con API real |
| **Notion** | `publicar_acta_notion` (REST, markdown → bloques) | `NOTION_API_KEY` (integración interna + compartir página Proyectos) | 🟡 código listo, falta token |
| **Trello** | `actualizar_trello` (tarjetas + checklist + Hecho) | `TRELLO_API_KEY` + `TRELLO_TOKEN` | ✅ probado en vivo (tablero ReservaFácil creado) |
| **Google Calendar** | `agendar_reunion` (API v3, OAuth escritorio) | `credentials.json` + `uv run autorizar_google.py` (una vez) | 🟡 código listo, falta OAuth |
| **Zoom** | Fuera del circuito, a propósito | — | Fireflies ya escucha la reunión; simplificar también es diseñar |

Alternativas para la tabla de decisión del B2 (se mencionan, no se montan): Notion oficial remoto (`claude mcp add --transport http notion https://mcp.notion.com/mcp`), Trello comunidad (`GabrielRamirez/trello-mcp`), Calendar oficial de Google (proyecto Cloud + OAuth ~15 min), Fireflies oficial remoto (`https://api.fireflies.ai/mcp`, plan B del B3).

**Framing honesto obligatorio en B3:** Fireflies YA tiene MCP oficial. Construimos el nuestro igualmente por dos motivos que se dicen en voz alta: (1) abrir el capó — entender qué hay dentro de un MCP te permite evaluar cualquier otro; (2) control — el nuestro tiene 2 herramientas que hacen exactamente lo que queremos, el oficial trae de todo. Nadie sale de clase pensando que le hemos vendido trabajo innecesario.

---

## Checklist — HOY (víspera)

- [ ] Enviar el pre-work a los alumnos (documento aparte). **Antes de las 18:00.**
- [ ] Crear en Notion la página **Proyectos → ReservaFácil** con un acta antigua de ejemplo (para que el acta nueva no caiga en vacío).
- [x] Registrar `invisible-pm` en TU Claude Code con las llaves del `.env` y verificar `claude mcp list` → ✓ Connected. **Hecho 07/07.**
- [x] Generar tu API key de Fireflies y probar el MCP: batería completa en verde contra la API real (Fireflies + Trello). **Hecho 07/07 (repo invisible_pm).**
- [ ] **Notion:** crear la integración interna en https://www.notion.so/my-integrations, compartir la página **Proyectos** con ella, añadir `NOTION_API_KEY` al `.env` y re-registrar el MCP (o pasarla con `-e`).
- [ ] **Google Calendar:** descargar `credentials.json` del proyecto de Google Cloud a `invisible-pm-mcp/` y ejecutar `uv run autorizar_google.py` (una vez, abre navegador).
- [x] Tablero Trello **ReservaFácil** con listas *Por hacer / En curso / Hecho* y 4 tarjetas creíbles. **Hecho 07/07 (via API).**
- [ ] **Grabar la reunión pregrabada del gancho:** reunión Zoom de 3 min contigo mismo (o con Jesús) sobre ReservaFácil, con Fireflies invitado. Confirmar que el transcript está procesado.
- [ ] Elegir voluntario para la reunión simulada en vivo (avisarle por privado, pasarle su papel del guion de reunión de abajo).
- [ ] Exportar a .txt el transcript de la pregrabada → **plan B nuclear** si la API de Fireflies cae en directo.

## Checklist — 1h antes

- [ ] `plaud me` → sesión viva (si no: `plaud login`, 30 segundos). El token caduca: comprobarlo SIEMPRE.
- [ ] `claude mcp list` → `invisible-pm ✓ Connected`.
- [ ] Prompt mágico copiado en un bloc de notas (no escribirlo en vivo).
- [ ] Trello, Notion y Calendar abiertos en pestañas separadas y con zoom de pantalla al 125% mínimo.
- [ ] Fireflies dashboard abierto (para enseñar el transcript cuando procese).
- [ ] Terminal con fuente grande, tema claro u oscuro con buen contraste en Zoom.

---

## B0 · El gancho + sembrar la reunión (0–12 min)

**Min 0-2 — Encuadre.** Frase de apertura sugerida:
> "La última vez que hablamos de MCPs os conté qué eran. Hoy no os voy a contar nada: lo vais a ver trabajar. Y al final de la clase, una reunión que hagamos aquí, en directo, se va a convertir sola en acta, tareas y calendario."

Anunciar las reglas: **preguntas al final de cada bloque** (apuntadlas, habrá espacio). Decir explícitamente cuándo estamos en Zoom, cuándo en la terminal y cuándo en el navegador — cada cambio de pantalla se anuncia: *"Ahora me veis la terminal"*.

**Min 2-8 — El truco de magia (con la reunión PREGRABADA de la víspera).**
Enseñar 10 segundos el dolor: Fireflies con el transcript, Trello desactualizado, Notion sin acta. *"Esto es un martes cualquiera."* Lanzar el prompt mágico (versión corta) sobre la reunión pregrabada y dejar que trabaje mientras hablas. Cuando termine: enseñar acta, tarjetas, evento. *"Esto que acabáis de ver, en dos horas lo sabréis montar. Rebobinamos."*

**Min 8-12 — Sembrar la reunión en vivo.** Traer al voluntario, leer el guion de reunión (abajo, 3-4 min) con Fireflies invitado a la llamada. Colgar esa "sub-reunión". *"Mientras Fireflies digiere esto, nosotros aprendemos. Volveremos a esta reunión al final."* — Esto compra ~75 min de procesamiento. **Checkpoint:** transcript en cola en Fireflies.

### Guion de la reunión simulada (leer con naturalidad, no recitar)

*Proyecto: ReservaFácil — app de reserva de clases prácticas para autoescuelas.*

- VALEN: repasa estado: la pantalla de login está terminada, la integración de pagos está atascada.
- VOLUNTARIO: propone sacar el MVP **sin pagos online** (se paga en la autoescuela) y dejarlos para fase 2. → **Decisión 1: aprobada.**
- VALEN: los recordatorios de clase irán por **WhatsApp, no SMS** (coste y tasa de lectura). → **Decisión 2: aprobada.**
- Tareas nuevas, en voz alta y con nombre:
  - **Ana** (mencionarla aunque no esté): maqueta de la pantalla de reserva. Criterios de aceptación: se ve el hueco libre de cada profesor, máximo 3 toques para reservar. **Para el viernes.**
  - **Valen:** redactar criterios de aceptación del calendario de profesores.
  - **Voluntario:** validar el flujo con 2 autoescuelas piloto antes de fin de mes.
- Cerrar: **próxima reunión jueves a las 12:00.** Despedirse con naturalidad (Fireflies corta mejor así).

---

## B1 · Qué es un MCP de verdad (12–30 min)

**Analogía antes de definición (no negociable):**
> "Claude Code es un empleado nuevo brillante. El primer día sabe de todo… pero está encerrado en una sala sin llaves. No puede entrar al departamento de tareas (Trello), ni al archivo (Notion), ni a la agenda (Calendar), ni a la sala donde se toman notas de las reuniones (Fireflies). Un MCP es la acreditación que le da acceso a un departamento. Cada acreditación trae escrito qué puede hacer ahí dentro: leer tarjetas, crear páginas, agendar reuniones."

Refuerzo con la analogía del estándar: antes cada aparato tenía su cargador; ahora todo es USB-C. MCP es el USB-C de las aplicaciones: **un solo tipo de enchufe** para que cualquier IA se conecte a cualquier herramienta.

**Anatomía mínima (2 conceptos, cero más):**
1. **Herramientas (tools):** las acciones concretas que la acreditación permite. "Listar tarjetas", "crear evento". Ni una más.
2. **La llave (credencial):** API key o inicio de sesión. Sin llave no hay acceso — y eso es una característica de seguridad, no un fastidio.

**Micro-glosario al vuelo** (20 segundos cada término la primera vez que salga): *servidor* = programa que espera peticiones; *API key* = contraseña para programas; *OAuth* = "iniciar sesión con Google" de toda la vida; *terminal* = la ventana negra donde se escribe a Claude Code.

**Demo del dolor (5 min):** hacer A MANO lo que luego hará el MCP — abrir Fireflies, copiar un trozo de transcript, pegarlo en Notion, abrir Trello, crear una tarjeta a mano. Cronometrarlo en voz alta. *"Tres minutos para UNA tarea. Y os he ahorrado los errores de copia-pega."*

**Q&A bloque 1 (3 min).**

---

## B2 · Conectar MCPs existentes + la tabla de decisión (30–55 min)

*"Ahora me veis la terminal."*

**Notion (oficial, en directo, min 30-38):**
```
claude mcp add --transport http notion https://mcp.notion.com/mcp
```
Dentro de Claude Code: `/mcp` → autorizar en el navegador (anunciar el salto: *"ahora estamos en el navegador"*). Primera orden en lenguaje natural:
> "¿Qué páginas hay dentro de Proyectos en mi Notion?"

**Trello (comunidad, min 38-46):** NO montarlo desde cero en directo (el wizard pide claves y come tiempo) — lo llevas conectado y enseñas 90 segundos de grabación de pantalla o capturas del `npm run setup` de anoche. Honestidad: *"esto anoche me llevó 6 minutos; el paso a paso lo tenéis en el material"*. En vivo, la parte jugosa:
> "Mira el tablero ReservaFácil de Trello y dime qué está en curso y qué huele a atascado."

**Calendar (oficial con fricción, min 46-49):** enseñar `claude mcp list` con calendar en verde y explicar en 60 segundos por qué no se monta en directo: la configuración oficial de Google pide crear un proyecto en Google Cloud y pasar pantallas de permisos (~15 min de clics). *"Os dejo la guía en el material. Que exista un MCP oficial no significa que sea el más cómodo de instalar — apuntad esto, que ahora lo usamos."*

**La tabla de decisión (min 49-53) — el momento "criterio":** dibujarla en pantalla compartida con los 4 casos REALES que acaban de ver.

| Criterio | Oficial | Comunidad | Propio |
|---|---|---|---|
| Quién lo mantiene | La empresa (Notion, Google) | Un voluntario de internet | Tú |
| Confianza / seguridad | Alta | **Leer el código o el repo antes** — le estás dando tus llaves | Total: sabes qué hay dentro |
| Funciones | Todas las que la empresa decida | Las que el autor necesitó | **Exactamente** las que tú necesitas |
| Coste de arranque | De 1 comando (Notion) a 15 min de pantallas (Google) | Variable: wizard fácil o README críptico | El más alto… hasta hoy |
| Cuándo elegirlo | Existe y cubre tu caso | No hay oficial (Trello) | Necesitas control fino o no existe nada |

Regla que se llevan: **oficial si existe y te vale → comunidad revisada si no → propio cuando necesitas control.** Y la pregunta de seguridad que un profesional hace SIEMPRE antes de instalar uno de comunidad: *¿a quién le estoy dando las llaves de mi Trello?*

**Q&A bloque 2 (min 53-55).**

---

## B3 · Construir NUESTRO MCP de Fireflies (55–85 min)

**Framing honesto de apertura (obligatorio):**
> "Fireflies tiene MCP oficial desde 2025. Podríamos usarlo y acabar antes. Pero hoy construimos el nuestro por dos razones: para abrir el capó — cuando entiendes qué hay dentro de un MCP puedes evaluar cualquiera — y por control: el nuestro tendrá 2 herramientas que hacen exactamente lo que este flujo necesita. Ni una más."

**El giro épico (min 57):** *"¿Y quién lo va a programar? Claude Code. La IA fabricándose su propia acreditación."*

**Prompt de construcción (copiado, no escrito en vivo):**
```
Crea un servidor MCP en Python con FastMCP en la carpeta invisible-pm-mcp:
el "Project Manager invisible". Herramientas:
1. listar_reuniones(limite) y leer_reunion(id opcional): API GraphQL de
   Fireflies (https://api.fireflies.ai/graphql, Bearer FIREFLIES_API_KEY).
   leer_reunion devuelve resumen, puntos de acción y transcripción con
   el nombre de quien habla; sin id, la última reunión.
2. publicar_acta_notion(titulo, contenido_markdown, pagina_padre): crea la
   página del acta en Notion (API REST, NOTION_API_KEY) y devuelve su URL.
3. actualizar_trello(nuevas_tarjetas, completadas, tablero): tarjetas en
   "Por hacer" con responsable en el título y criterios como checklist;
   mueve a "Hecho" lo cerrado (TRELLO_API_KEY + TRELLO_TOKEN).
4. agendar_reunion(titulo, inicio, duracion_minutos, descripcion): evento
   en Google Calendar (OAuth con token.json).
Usa FastMCP con dependencias gestionadas por uv (pyproject.toml).
Mensajes de error claros en español que digan cómo conseguir cada llave.
Dime al final el comando exacto de claude mcp add para registrarlo.
```

**Gestión del tiempo en B3:** el MCP completo es demasiado para construirlo entero en directo.
En clase se lanza este prompt y se narra mientras trabaja; la versión probada de la víspera
(repo `invisible_pm`, carpeta `invisible-pm-mcp/`) es la que se registra si el directo se alarga.

**Nota para el instructor (bug real cazado en el ensayo del 07/07):** el esquema GraphQL de
Fireflies usa `transcript(id:)`, **no** `transcript(transcriptId:)`. Si Claude Code genera
`transcriptId` en directo, la primera llamada real a `leer_reunion` falla con *"Unknown argument
transcriptId"* — son 2 minutos de depuración didáctica en vivo (el error dice exactamente qué
argumento espera). Y con clave inválida Fireflies devuelve HTTP 200 + `errors`, no un 401.

**Mientras Claude Code trabaja (min 58-70):** narrar lo que va haciendo en lenguaje llano — "está escribiendo la herramienta de listar", "está definiendo qué parámetros acepta". Aquí es donde el público no técnico ve que *construir* un MCP es describir bien lo que quieres.

**Registro y prueba (min 70-80):**
```
cd invisible-pm-mcp && uv sync
claude mcp add invisible-pm \
  -e FIREFLIES_API_KEY=... -e NOTION_API_KEY=... \
  -e TRELLO_API_KEY=... -e TRELLO_TOKEN=... \
  -- /ruta/absoluta/invisible-pm-mcp/.venv/bin/python /ruta/absoluta/invisible-pm-mcp/server.py
```
Reiniciar sesión de Claude Code y probar:
> "Lista mis últimas reuniones de Fireflies."

Debe aparecer **la reunión simulada del B0, ya procesada.** Momento de aplauso natural.

**El ejercicio del cambio de oídos (remate del B3, ~3 min):** el MCP arranca escuchando por Plaud
(tus reuniones reales). Se re-registra con `-e FUENTE_REUNIONES=fireflies`, se reinicia la sesión, y
el mismo prompt funciona contra Fireflies — *"he cambiado los oídos sin tocar el archivo, el tablón
ni la agenda; eso es lo que compra una arquitectura de herramientas bien diseñada"*. Los alumnos
replican el camino Fireflies (no tienen Plaud, es hardware).

**Plan B por capas (tenerlo interiorizado, no leerlo):**
- Si el código generado en vivo falla → cambiar a tu versión probada del repo `invisible_pm` (el MCP completo en `invisible-pm-mcp/server.py`, y de reserva la versión Node solo-Fireflies en `doc/masterclass/fireflies-mcp/index.js` — **ambas probadas contra la API real el 07/07**): *"esto le pasa a cualquiera en directo; por eso un profesional siempre prueba la víspera — os enseño la mía"*. La depuración en vivo de 2-3 min también es oro didáctico; más de 5 min, corta y cambia.
- Si Fireflies cae → `FUENTE_REUNIONES=plaud` y siguen ahí TODAS tus reuniones reales (y al revés: si Plaud caduca en directo, `fireflies`). Dos proveedores de oídos = doble red.
- Si la API de Fireflies cae y quieres enseñar el oficial → MCP remoto: `claude mcp add fireflies-oficial -- npx mcp-remote https://api.fireflies.ai/mcp --header "Authorization: Bearer TU_KEY"`.
- Si TODO lo que escucha cae → el .txt exportado anoche: "leed este archivo como si fuera el transcript" y el flujo del B4 sigue intacto.

**Q&A bloque 3 (min 80-85).**

---

## B4 · El flujo completo — el momento épico (85–110 min)

*"¿Os acordáis de la reunión del principio? Fireflies ya la ha digerido. Ahora, el prompt."*

**El prompt mágico (min 87, pegado del bloc de notas, leerlo en voz alta ANTES de lanzarlo):**
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

**Min 88-100 — Verlo trabajar.** Narrar cada llamada a herramienta que aparece en pantalla: *"acaba de pedir el transcript… ahora está escribiendo en Notion… fijaos: acreditación por acreditación"*. Cuando termine, **verificación en vivo con navegación anunciada**: *"vamos al navegador"* → Notion (acta), Trello (tarjetas con checklist), Calendar (evento del jueves). Pedir al voluntario que confirme que SUS tareas están bien recogidas.

**Min 100-108 — Aterrizarlo a negocio (30 segundos de cifra, sin humo):** una reunión semanal de proyecto genera 20-30 min de trabajo administrativo posterior. Por equipo y por semana. *"Haced la cuenta con vuestros proyectos — y ahora sabéis montar la máquina que se lo come."* Matiz profesional obligatorio: **la primera semana se revisa todo lo que escribe** — actas y tarjetas las valida un humano hasta ganar confianza. Control humano no es opcional, es parte del diseño.

**Min 108-110 — Micro-Q&A del flujo.**

---

## B5 · Ejercicio de cierre + Q&A final (110–120 min)

**Ejercicio (al final, nunca intercalado):** cada alumno, en 5 minutos y con la tabla de decisión delante, escribe en el chat de Zoom su **stack de proyecto**:
1. Dos MCPs existentes que conectaría esta semana (¿oficial o comunidad? ¿por qué?).
2. Un MCP propio que le falta: nombre + las 2-3 herramientas exactas que tendría.

Leer 3-4 respuestas en voz alta y afinarlas en directo con la tabla. **Pregunta de reflexión de cierre:** *"¿Qué proceso de tu semana desaparecería si tu IA tuviera las acreditaciones adecuadas?"*

**Despedida:** el material incluye el paso a paso de las 4 conexiones, el código del MCP de Fireflies y el prompt mágico para adaptar. *"La 4.5 os conté qué era un MCP. Hoy habéis visto para qué existe."*

---

## Anti-fuegos rápidos

- **Fireflies no ha procesado la reunión del B0 al llegar a B4** → usar la pregrabada de anoche (ya procesada) para el flujo, y decir que la de clase llegará en minutos: *"os la enseño al final si da tiempo"*.
- **OAuth de Notion falla en directo** → tienes la sesión ya autorizada de anoche; el add en vivo es demostrativo, no crítico.
- **Un alumno pregunta por precios/planes de Fireflies o Trello** → no improvisar cifras: "en el material os dejo los enlaces oficiales; los planes cambian".
- **Pregunta trampa "¿y esto no lo hace ya n8n?"** → respuesta puente hacia MC4: "n8n orquesta pasos fijos; esto interpreta una conversación humana y decide. En la masterclass de automatización enfrentamos los dos mundos en directo."
