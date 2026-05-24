// supabase/functions/sinistro-webhook/index.ts
// Edge Function: recebe webhook da Evolution API, grava raw_inbox, dispara Inngest
//
// Deploy:
//   supabase functions deploy sinistro-webhook
//   supabase secrets set INNGEST_EVENT_KEY=...

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const INNGEST_EVENT_KEY = Deno.env.get("INNGEST_EVENT_KEY") ?? "";
const INNGEST_API_URL   = Deno.env.get("INNGEST_API_URL") ?? "https://inn.gs/e";
const SUPABASE_URL      = Deno.env.get("SUPABASE_URL")    ?? "";
const SUPABASE_SERVICE  = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

serve(async (req: Request) => {
  // Aceita apenas POST
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  // Extrai narrativa e segurado do payload Evolution API
  // Formato: { data: { key: { remoteJid: "5511..." }, message: { conversation: "texto" } } }
  const mensagem = (
    body?.data as Record<string, unknown>
  )?.message as Record<string, unknown>;

  const narrativa = (
    mensagem?.conversation ??
    (mensagem?.extendedTextMessage as Record<string, unknown>)?.text ??
    ""
  ) as string;

  const remoteJid = (
    (body?.data as Record<string, unknown>)?.key as Record<string, unknown>
  )?.remoteJid as string ?? "";

  // Extrai número do telefone como segurado_id provisório
  const segurado_id = remoteJid.split("@")[0] ?? null;

  if (!narrativa || narrativa.trim().length < 3) {
    return new Response(
      JSON.stringify({ ok: false, error: "narrativa vazia ou muito curta" }),
      { status: 200, headers: { "Content-Type": "application/json" } }
    );
  }

  // 1. Grava em raw_inbox (auditoria SUSEP — ANTES de processar)
  const sb = createClient(SUPABASE_URL, SUPABASE_SERVICE);
  const { data: inbox, error: dbError } = await sb
    .from("raw_inbox")
    .insert({
      source:      "whatsapp",
      payload:     body,
      narrativa:   narrativa.trim(),
      segurado_id: segurado_id,
      processed:   false,
    })
    .select("id")
    .single();

  if (dbError) {
    console.error("raw_inbox insert error:", dbError.message);
    // Não bloqueia — continua para o Inngest mesmo se Supabase falhar
  }

  // 2. Dispara evento Inngest
  const inngestPayload = {
    name: "sinistro/fnol.received",
    data: {
      narrativa:    narrativa.trim(),
      segurado_id:  segurado_id,
      raw_inbox_id: inbox?.id ?? null,
      source:       "whatsapp",
      timestamp:    new Date().toISOString(),
    },
  };

  let inngestOk = false;
  try {
    const inngestResp = await fetch(`${INNGEST_API_URL}/${INNGEST_EVENT_KEY}`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(inngestPayload),
    });
    inngestOk = inngestResp.ok;
    if (!inngestOk) {
      const txt = await inngestResp.text();
      console.error("Inngest error:", inngestResp.status, txt);
    }
  } catch (e) {
    console.error("Inngest fetch error:", e);
  }

  return new Response(
    JSON.stringify({
      ok:           true,
      raw_inbox_id: inbox?.id ?? null,
      inngest_ok:   inngestOk,
    }),
    { status: 200, headers: { "Content-Type": "application/json" } }
  );
});
