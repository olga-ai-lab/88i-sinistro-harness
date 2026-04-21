"""
============================================================
88i Seguradora Digital - Agente de Ingestão de Sinistro
Semana 1: LangGraph + BAML

Fluxo:
  recebe_narrativa → extrai (BAML) → valida → decide_rota → saida
                                                   │
                                                   ├─ solicita_esclarecimento (se confiança baixa)
                                                   ├─ escala_humano (se red flags críticas)
                                                   └─ pronto_para_analise (caminho feliz)
============================================================
"""

from typing import TypedDict, Literal, Optional
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from baml_client.sync_client import b as baml
from baml_client.types import ExtracaoSinistro


# ============================================================
# 1. Definição do ESTADO (a memória que flui entre os nós)
# ============================================================

class SinistroState(TypedDict):
    """
    Estado compartilhado entre todos os nós do grafo.
    Cada nó pode ler e escrever aqui.
    """
    # Entrada
    narrativa_original: str
    segurado_id: Optional[str]
    timestamp_recebimento: str

    # Saída do BAML
    extracao: Optional[ExtracaoSinistro]

    # Decisão de roteamento
    proxima_acao: Optional[Literal[
        "pronto_para_analise",
        "solicitar_esclarecimento",
        "escalar_humano"
    ]]

    # Mensagens de volta ao segurado ou ao time
    mensagem_ao_segurado: Optional[str]
    alerta_operacional: Optional[str]

    # Trilha de auditoria
    log_execucao: list[str]


# ============================================================
# 2. NÓS do grafo — cada um é uma função pura que recebe e
#    devolve uma atualização parcial do estado
# ============================================================

def no_extrair(state: SinistroState) -> dict:
    """
    Chama BAML para extrair estrutura da narrativa.
    BAML garante schema válido ou levanta exceção explícita.
    """
    log = state.get("log_execucao", [])
    log.append(f"[{datetime.now().isoformat()}] extraindo narrativa ({len(state['narrativa_original'])} chars)")

    try:
        extracao = baml.ExtrairSinistro(narrativa=state["narrativa_original"])
        log.append(
            f"[{datetime.now().isoformat()}] extração OK — tipo={extracao.tipo_sinistro} "
            f"confiança={extracao.confianca:.2f} red_flags={len(extracao.red_flags)}"
        )
        return {"extracao": extracao, "log_execucao": log}
    except Exception as e:
        log.append(f"[{datetime.now().isoformat()}] ERRO extração: {e}")
        return {"extracao": None, "log_execucao": log, "proxima_acao": "escalar_humano"}


def no_decidir_rota(state: SinistroState) -> dict:
    """
    Decisão determinística (ZERO LLM) sobre para onde encaminhar.
    Baseada em thresholds explícitos e auditáveis.
    """
    log = state.get("log_execucao", [])
    extracao = state.get("extracao")

    if extracao is None:
        log.append("roteamento: extração vazia → escalar_humano")
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # --- Regras determinísticas de roteamento ---

    # Regra 1: red flags de alta severidade → humano sempre
    red_flags_altas = [rf for rf in extracao.red_flags if rf.severidade == "alta"]
    if red_flags_altas:
        log.append(f"roteamento: {len(red_flags_altas)} red_flag(s) alta → escalar_humano")
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # Regra 2: vítima fatal → humano sempre (política da seguradora)
    if extracao.ha_vitimas_fatais:
        log.append("roteamento: vítima fatal → escalar_humano")
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # Regra 3: narrativa insuficiente para classificar o evento → perguntar
    # NOTA: campos_faltantes bloqueantes NÃO disparam aqui. Documentos pendentes
    # são responsabilidade da camada de análise documental (Semana 3-4), não da
    # ingestão. Aqui só barramos se o LLM não entendeu o EVENTO.
    if extracao.confianca < 0.6 or extracao.requer_esclarecimento:
        log.append(
            f"roteamento: confiança={extracao.confianca:.2f} "
            f"requer_esclarecimento={extracao.requer_esclarecimento} "
            f"→ solicitar_esclarecimento"
        )
        return {"proxima_acao": "solicitar_esclarecimento", "log_execucao": log}

    # Regra 4: evento classificado → segue para análise (bloqueantes viram pendências)
    bloqueantes = [c for c in extracao.campos_faltantes if c.criticidade == "bloqueante"]
    log.append(
        f"roteamento: confiança={extracao.confianca:.2f} bloqueantes={len(bloqueantes)} "
        f"→ pronto_para_analise"
    )
    return {"proxima_acao": "pronto_para_analise", "log_execucao": log}


def no_solicitar_esclarecimento(state: SinistroState) -> dict:
    """
    Monta mensagem para o segurado com as perguntas sugeridas pelo LLM.
    Em produção: envia via Evolution API.
    """
    log = state.get("log_execucao", [])
    extracao = state["extracao"]

    perguntas = extracao.perguntas_sugeridas or [
        "Pode me contar mais detalhes sobre o que aconteceu?"
    ]
    bloqueantes_txt = ""
    bloqueantes = [c for c in extracao.campos_faltantes if c.criticidade == "bloqueante"]
    if bloqueantes:
        bloqueantes_txt = "\n\nPrecisamos das seguintes informações:\n" + "\n".join(
            f"  • {c.campo}: {c.justificativa}" for c in bloqueantes
        )

    mensagem = (
        "Olá! Recebemos sua comunicação de sinistro. Para prosseguir, preciso "
        "esclarecer alguns pontos:\n\n"
        + "\n".join(f"  {i+1}. {p}" for i, p in enumerate(perguntas))
        + bloqueantes_txt
    )

    log.append("mensagem de esclarecimento montada")
    return {"mensagem_ao_segurado": mensagem, "log_execucao": log}


def no_pronto_para_analise(state: SinistroState) -> dict:
    """
    Caminho feliz: narrativa extraída com confiança, sem red flags.
    Em produção: grava em Supabase e aciona a próxima Activity Temporal
    (Cobertura + Documentação + Fraude em paralelo).
    """
    log = state.get("log_execucao", [])
    extracao = state["extracao"]

    bloqueantes = [c for c in extracao.campos_faltantes if c.criticidade == "bloqueante"]

    log.append(
        f"PRONTO PARA ANÁLISE — tipo={extracao.tipo_sinistro} "
        f"urgência={extracao.urgencia}"
    )

    if bloqueantes:
        log.append(
            f"PENDÊNCIAS DOCUMENTAIS registradas: "
            f"{len(bloqueantes)} bloqueantes para análise posterior"
        )
        mensagem = (
            f"Sinistro registrado. Protocolo em geração.\n"
            f"Tipo identificado: {extracao.tipo_sinistro}\n"
            f"Em breve solicitaremos os documentos necessários para "
            f"prosseguir com a análise."
        )
    else:
        mensagem = (
            f"Sinistro registrado. Protocolo em geração.\n"
            f"Tipo identificado: {extracao.tipo_sinistro}\n"
            f"Vamos analisar sua documentação e retornamos em breve."
        )
    return {"mensagem_ao_segurado": mensagem, "log_execucao": log}


def no_escalar_humano(state: SinistroState) -> dict:
    """
    Casos sensíveis ou de baixa confiança vão para fila humana priorizada.
    Em produção: cria card no painel da Rosi/time.
    """
    log = state.get("log_execucao", [])
    extracao = state.get("extracao")

    motivos = []
    if extracao is None:
        motivos.append("falha na extração automática")
    else:
        if extracao.ha_vitimas_fatais:
            motivos.append("vítima fatal")
        for rf in extracao.red_flags:
            if rf.severidade == "alta":
                motivos.append(f"red flag: {rf.descricao}")

    alerta = f"ESCALAR: {' | '.join(motivos) if motivos else 'análise manual requerida'}"
    log.append(alerta)

    mensagem = (
        "Recebemos sua comunicação de sinistro. Dada a natureza do caso, "
        "um especialista da 88i vai entrar em contato em breve."
    )
    return {
        "mensagem_ao_segurado": mensagem,
        "alerta_operacional": alerta,
        "log_execucao": log,
    }


# ============================================================
# 3. Função de roteamento condicional
#    (lê state["proxima_acao"] e direciona)
# ============================================================

def rotear(state: SinistroState) -> str:
    return state["proxima_acao"] or "escalar_humano"


# ============================================================
# 4. Construção do GRAFO
# ============================================================

def construir_agente():
    """
    Monta o StateGraph. Em produção isso rodaria dentro de uma
    Activity do Temporal (semana 5), mas aqui roda local/sync.
    """
    workflow = StateGraph(SinistroState)

    # Adiciona os nós
    workflow.add_node("extrair", no_extrair)
    workflow.add_node("decidir_rota", no_decidir_rota)
    workflow.add_node("solicitar_esclarecimento", no_solicitar_esclarecimento)
    workflow.add_node("pronto_para_analise", no_pronto_para_analise)
    workflow.add_node("escalar_humano", no_escalar_humano)

    # Arestas lineares
    workflow.add_edge(START, "extrair")
    workflow.add_edge("extrair", "decidir_rota")

    # Aresta condicional: a saída de `decidir_rota` determina o caminho
    workflow.add_conditional_edges(
        "decidir_rota",
        rotear,
        {
            "solicitar_esclarecimento": "solicitar_esclarecimento",
            "pronto_para_analise": "pronto_para_analise",
            "escalar_humano": "escalar_humano",
        },
    )

    # Terminais
    workflow.add_edge("solicitar_esclarecimento", END)
    workflow.add_edge("pronto_para_analise", END)
    workflow.add_edge("escalar_humano", END)

    return workflow.compile()


# ============================================================
# 5. API pública simples
# ============================================================

def processar_narrativa(narrativa: str, segurado_id: Optional[str] = None) -> SinistroState:
    """
    Ponto de entrada. Em produção seria chamado pelo webhook Evolution API.
    """
    agente = construir_agente()
    estado_inicial: SinistroState = {
        "narrativa_original": narrativa,
        "segurado_id": segurado_id,
        "timestamp_recebimento": datetime.now().isoformat(),
        "extracao": None,
        "proxima_acao": None,
        "mensagem_ao_segurado": None,
        "alerta_operacional": None,
        "log_execucao": [],
    }
    resultado = agente.invoke(estado_inicial)
    return resultado


if __name__ == "__main__":
    # Teste rápido ao rodar o módulo direto
    import sys
    narrativa_exemplo = sys.argv[1] if len(sys.argv) > 1 else (
        "oi, bati minha moto ontem a noite na paulista, to com perna quebrada, "
        "tenho BO, preciso abrir sinistro pra receber a diaria"
    )
    resultado = processar_narrativa(narrativa_exemplo)
    print("\n" + "=" * 60)
    print("RESULTADO DO AGENTE")
    print("=" * 60)
    print(f"\nPróxima ação: {resultado['proxima_acao']}")
    print(f"\nMensagem ao segurado:\n{resultado['mensagem_ao_segurado']}")
    if resultado.get("alerta_operacional"):
        print(f"\nAlerta operacional: {resultado['alerta_operacional']}")
    print(f"\nLog de execução:")
    for linha in resultado["log_execucao"]:
        print(f"  {linha}")
    if resultado.get("extracao"):
        print(f"\nExtração completa (JSON):")
        print(resultado["extracao"].model_dump_json(indent=2))
