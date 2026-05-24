"""
inngest_functions.py — Funções Inngest para orquestração durável (Semana 2)

Cada função Inngest é um step durável com retry automático.
O webhook do Supabase Edge Function dispara o evento `sinistro/fnol.received`,
que aciona `fn_processar_sinistro`.

Em desenvolvimento local: o Inngest Dev Server intercepta e replay os eventos.
  inngest-cli dev  (requer inngest-cli instalado)

Integração com FastAPI:
  inngest.fast_api.serve(app, inngest_client, [fn_processar_sinistro])

Eventos definidos:
  sinistro/fnol.received  — payload: {narrativa, segurado_id, source}
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
load_dotenv()

import inngest
from agent import processar_narrativa


# ============================================================
# Client Inngest
# ============================================================

inngest_client = inngest.Inngest(
    app_id="88i-sinistro-agent",
    signing_key=os.getenv("INNGEST_SIGNING_KEY", ""),
    is_production=os.getenv("RAILWAY_ENVIRONMENT") == "production",
)


# ============================================================
# Função 1: processar sinistro FNOL
# ============================================================

@inngest_client.create_function(
    fn_id="processar-sinistro-fnol",
    trigger=inngest.TriggerEvent(event="sinistro/fnol.received"),
    retries=3,
)
async def fn_processar_sinistro(
    ctx: inngest.Context,
    step: inngest.Step,
) -> dict:
    """
    Step durável: executa o pipeline completo do agente.

    - step.run garante idempotência: se o step falhar e for reexecutado,
      o Inngest não re-envia o evento — ele retoma do ponto de falha.
    - Em produção: adicionar steps separados para
        - step "extrair" (BAML)
        - step "consultar_contexto" (tools Supabase)
        - step "registrar" (INSERT sinistros)
      Por enquanto, todo o pipeline é um único step (mais simples para Semana 2).

    Princípio: cada step deve ser retry-safe (idempotente).
    """
    data = ctx.event.data
    narrativa = data.get("narrativa", "")
    segurado_id = data.get("segurado_id")

    resultado = await step.run(
        "pipeline-fnol",
        lambda: processar_narrativa(narrativa=narrativa, segurado_id=segurado_id),
    )

    return {
        "proxima_acao": resultado.get("proxima_acao"),
        "protocolo": resultado.get("protocolo"),
        "mensagem_ao_segurado": resultado.get("mensagem_ao_segurado"),
    }
