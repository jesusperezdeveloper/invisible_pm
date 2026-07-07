#!/usr/bin/env node
/**
 * MCP Fireflies — El Project Manager invisible · Masterclass MCP
 * Servidor MCP mínimo que conecta Claude Code con tus reuniones de Fireflies.
 * 2 herramientas: listar_reuniones y leer_reunion.
 *
 * Uso:
 *   FIREFLIES_API_KEY=tu_clave node index.js
 *
 * Registro en Claude Code:
 *   claude mcp add fireflies -e FIREFLIES_API_KEY=tu_clave -- node /ruta/absoluta/fireflies-mcp/index.js
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API_URL = "https://api.fireflies.ai/graphql";
const API_KEY = process.env.FIREFLIES_API_KEY;

// ── Llamada genérica a la API GraphQL de Fireflies ──────────────────────
async function fireflies(query, variables = {}) {
  if (!API_KEY) {
    throw new Error(
      "Falta la clave de Fireflies. Arranca el servidor con FIREFLIES_API_KEY=tu_clave. " +
        "La clave se genera en Fireflies → Settings → Developer settings → API key."
    );
  }
  let res;
  try {
    res = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${API_KEY}`,
      },
      body: JSON.stringify({ query, variables }),
    });
  } catch {
    throw new Error("No se pudo conectar con Fireflies. Comprueba tu conexión a internet.");
  }
  if (res.status === 401 || res.status === 403) {
    throw new Error("Fireflies rechazó la clave (API key inválida o caducada). Genera una nueva en Settings → Developer settings.");
  }
  const json = await res.json().catch(() => null);
  if (!json) {
    throw new Error(`Fireflies devolvió una respuesta inesperada (HTTP ${res.status}).`);
  }
  if (json.errors?.length) {
    const detalle = json.errors.map((e) => e.message).join("; ");
    throw new Error("Fireflies respondió con error: " + detalle);
  }
  return json.data;
}

const fecha = (ms) =>
  ms ? new Date(Number(ms)).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" }) : "sin fecha";

// ── Servidor MCP ────────────────────────────────────────────────────────
const server = new McpServer({ name: "fireflies-invisible-pm", version: "1.0.0" });

server.tool(
  "listar_reuniones",
  "Lista las últimas reuniones grabadas en Fireflies con su id, título, fecha y duración.",
  { limite: z.number().int().min(1).max(25).default(5).describe("Cuántas reuniones devolver (1-25)") },
  async ({ limite }) => {
    const data = await fireflies(
      `query Transcripts($limit: Int) {
        transcripts(limit: $limit) { id title date duration }
      }`,
      { limit: limite }
    );
    const lista = (data.transcripts || []).map(
      (t) => `• [${t.id}] ${t.title} — ${fecha(t.date)} (${Math.round(t.duration || 0)} min)`
    );
    return {
      content: [
        {
          type: "text",
          text: lista.length ? lista.join("\n") : "No hay reuniones grabadas todavía en esta cuenta.",
        },
      ],
    };
  }
);

server.tool(
  "leer_reunion",
  "Devuelve el contenido de una reunión de Fireflies: resumen, puntos de acción y transcripción completa con quién dijo qué. Si no se indica id, devuelve la última reunión.",
  { id: z.string().optional().describe("Id de la reunión (de listar_reuniones). Vacío = la más reciente.") },
  async ({ id }) => {
    let transcriptId = id;
    if (!transcriptId) {
      const ultima = await fireflies(`query { transcripts(limit: 1) { id } }`);
      transcriptId = ultima.transcripts?.[0]?.id;
      if (!transcriptId) {
        return { content: [{ type: "text", text: "No hay ninguna reunión grabada en esta cuenta." }] };
      }
    }
    const data = await fireflies(
      `query Transcript($id: String!) {
        transcript(id: $id) {
          id title date duration
          summary { overview action_items }
          sentences { speaker_name text }
        }
      }`,
      { id: transcriptId }
    );
    const t = data.transcript;
    if (!t) {
      return { content: [{ type: "text", text: `No existe ninguna reunión con id ${transcriptId}.` }] };
    }
    const dialogo = (t.sentences || [])
      .map((s) => `${s.speaker_name || "Desconocido"}: ${s.text}`)
      .join("\n");
    const texto = [
      `REUNIÓN: ${t.title}`,
      `FECHA: ${fecha(t.date)} · DURACIÓN: ${Math.round(t.duration || 0)} min`,
      ``,
      `RESUMEN AUTOMÁTICO:`,
      t.summary?.overview || "(sin resumen)",
      ``,
      `PUNTOS DE ACCIÓN DETECTADOS:`,
      t.summary?.action_items || "(ninguno)",
      ``,
      `TRANSCRIPCIÓN:`,
      dialogo || "(vacía)",
    ].join("\n");
    return { content: [{ type: "text", text: texto }] };
  }
);

// ── Arranque ────────────────────────────────────────────────────────────
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("MCP Fireflies · invisible_pm en marcha ✓");
