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

from typing import TypedDict, Literal, Optional, Any
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()  # carrega .env antes de qualquer import que precise de chaves
from langgraph.graph import StateGraph, START, END
from baml_client.sync_client import b as baml
from baml_client.types import ExtracaoSinistro
from observability import observe
from tools import consultar_apolice, buscar_historico_sinistros, registrar_sinistro
from tools import DadosApolice, HistoricoSinistros
from rules_engine import avaliar_cobertura, VeredictoCobertura
from doc_pipeline import analisar_documentos, DocumentoInput, AnaliseDocumental
from hitl_queue import criar_tarefa


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

    # Contexto enriquecido pelas tools (Semana 2)
    dados_apolice: Optional[DadosApolice]
    historico_sinistros: Optional[HistoricoSinistros]

    # Veredicto de cobertura (Semana 3)
    veredicto_cobertura: Optional[VeredictoCobertura]

    # Pipeline documental (Semana 4)
    documentos_recebidos: Optional[list[DocumentoInput]]
    analise_documental: Optional[AnaliseDocumental]

    # HITL (Semana 5)
    hitl_tarefa_id: Optional[str]

    # Decisão de roteamento
    proxima_acao: Optional[Literal[
        "pronto_para_analise",
        "solicitar_esclarecimento",
        "escalar_humano"
    ]]

    # Mensagens de volta ao segurado ou ao time
    mensagem_ao_segurado: Optional[str]
    alerta_operacional: Optional[str]

    # Protocolo gerado após registro (Semana 2)
    protocolo: Optional[str]

    # Trilha de auditoria
    log_execucao: list[str]


# ============================================================
# 2. NÓS do grafo — cada um é uma função pura que recebe e
#    devolve uma atualização parcial do estado
# ============================================================

@observe(name="extrair_sinistro", as_type="generation")
def no_extrair(state: SinistroState) -> dict:
    """
    Chama BAML para extrair estrutura da narrativa.
    BAML garante schema válido ou levanta exceção explícita.

    Instrumentado com @observe(as_type="generation") — cada chamada
    aparece no Langfuse como generation filha do trace da request.
    Fail-open: se Langfuse cair, decorator vira no-op.
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


def no_consultar_contexto(state: SinistroState) -> dict:
    """
    Semana 2: enriquece o state com dados de apólice e histórico.

    Chama as tools de forma sequencial (não bloqueia em falha).
    Resultados ficam em state["dados_apolice"] e state["historico_sinistros"]
    para uso no no_decidir_rota e nos nós terminais.

    ZERO LLM — código determinístico.
    Fail-safe: se qualquer tool falhar, o sinistro continua sem travar.
    """
    log = state.get("log_execucao", [])
    segurado_id = state.get("segurado_id")
    extracao = state.get("extracao")

    # Consulta apólice
    apolice = None
    if segurado_id:
        apolice = consultar_apolice(segurado_id)
        if apolice.encontrada:
            status_vig = "vigente" if apolice.vigente_hoje else "VENCIDA"
            log.append(
                f"[contexto] apólice {status_vig} — produto={apolice.produto} "
                f"coberturas={apolice.coberturas} carência={apolice.carencia_ativa}"
            )
        else:
            log.append(f"[contexto] apólice não encontrada: {apolice.observacao}")
    else:
        log.append("[contexto] segurado_id ausente — consulta de apólice pulada")

    # Consulta histórico
    historico = None
    if segurado_id:
        tipo = extracao.tipo_sinistro.value if extracao and hasattr(extracao.tipo_sinistro, "value") else None
        historico = buscar_historico_sinistros(segurado_id, tipo_sinistro=tipo)
        if historico.encontrado:
            log.append(
                f"[contexto] histórico — total={historico.total_sinistros} "
                f"12m={historico.sinistros_12_meses} alerta_freq={historico.alerta_frequencia}"
            )
            if historico.alerta_frequencia:
                log.append("[contexto] ALERTA: >= 3 sinistros em 12 meses")
        else:
            log.append(f"[contexto] histórico não encontrado: {historico.observacao}")

    return {
        "dados_apolice": apolice,
        "historico_sinistros": historico,
        "log_execucao": log,
    }


def no_decidir_rota(state: SinistroState) -> dict:
    """
    Decisão determinística (ZERO LLM) sobre para onde encaminhar.
    Baseada em thresholds explícitos e auditáveis.

    Semana 2: incorpora sinais das tools (apólice vencida, alerta frequência).
    """
    log = state.get("log_execucao", [])
    extracao = state.get("extracao")
    apolice = state.get("dados_apolice")
    historico = state.get("historico_sinistros")

    if extracao is None:
        log.append("roteamento: extração vazia → escalar_humano")
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # --- Regras determinísticas de roteamento ---

    # Regra 1: red flags de alta severidade → humano sempre
    red_flags_altas = [rf for rf in extracao.red_flags if rf.severidade == "alta"]
    if red_flags_altas:
        log.append(f"roteamento: {len(red_flags_altas)} red_flag(s) alta → escalar_humano")
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # Regra 1b: acumulação de red_flags media (>= 3) → humano
    # Robustez contra não-determinismo do LLM na classificação alta vs media
    red_flags_medias = [rf for rf in extracao.red_flags if rf.severidade == "media"]
    if len(red_flags_medias) >= 3:
        log.append(f"roteamento: {len(red_flags_medias)} red_flag(s) media → escalar_humano")
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # Regra 2: vítima fatal → humano sempre (política da seguradora)
    if extracao.ha_vitimas_fatais:
        log.append("roteamento: vítima fatal → escalar_humano")
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # Regra 3 (Semana 2): alerta de frequência → humano
    if historico and historico.alerta_frequencia:
        log.append(
            f"roteamento: alerta frequência ({historico.sinistros_12_meses} sinistros/12m) "
            f"→ escalar_humano"
        )
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # Regra 4 (Semana 2): apólice vencida → humano (pode haver regularização)
    if apolice and apolice.encontrada and not apolice.vigente_hoje:
        log.append("roteamento: apólice VENCIDA → escalar_humano")
        return {"proxima_acao": "escalar_humano", "log_execucao": log}

    # Regra 5: narrativa insuficiente para classificar o evento → perguntar
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

    # Regra 6: evento classificado → segue para análise (bloqueantes viram pendências)
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
    Semana 3: chama rules engine para decidir elegibilidade/cobertura.
    Semana 2: registra o sinistro via tool e retorna protocolo ao segurado.
    Em produção: aciona a próxima Activity Inngest (Cobertura + Docs + Fraude).
    """
    log = state.get("log_execucao", [])
    extracao = state["extracao"]
    tipo_label = extracao.tipo_sinistro.value if hasattr(extracao.tipo_sinistro, "value") else str(extracao.tipo_sinistro)

    log.append(
        f"PRONTO PARA ANÁLISE — tipo={extracao.tipo_sinistro} "
        f"urgência={extracao.urgencia}"
    )

    # --- Semana 3: avaliação de cobertura ---
    # Plataforma vem da extração BAML — dinâmica, não hardcoded
    plataforma_str = (
        extracao.plataforma_mencionada.value
        if hasattr(extracao.plataforma_mencionada, "value")
        else str(extracao.plataforma_mencionada)
    ) if hasattr(extracao, "plataforma_mencionada") else "NAO_MENCIONADA"

    veredicto = avaliar_cobertura(
        tipo_sinistro=tipo_label,
        dados_apolice=state.get("dados_apolice"),
        historico_sinistros=state.get("historico_sinistros"),
        extracao=extracao,
        plataforma=plataforma_str,
    )
    log.append(
        f"cobertura: plataforma={plataforma_str} status={veredicto.status} "
        f"cobertura={veredicto.cobertura} docs_pendentes={len(veredicto.docs_pendentes)}"
    )

    # Registra sinistro e gera protocolo
    registro = registrar_sinistro(
        segurado_id=state.get("segurado_id"),
        narrativa_original=state["narrativa_original"],
        tipo_sinistro=tipo_label,
        proxima_acao="pronto_para_analise",
        extracao_json=extracao.model_dump_json(),
        timestamp_recebimento=state["timestamp_recebimento"],
    )

    protocolo_txt = f"\nProtocolo: {registro.protocolo}" if registro.sucesso else ""
    log.append(f"registro: sucesso={registro.sucesso} protocolo={registro.protocolo}")

    # Monta mensagem ao segurado baseada no veredicto
    if not veredicto.elegivel:
        mensagem = (
            f"Analisamos sua comunicação de sinistro.{protocolo_txt}\n"
            f"Infelizmente, identificamos que o evento não está coberto pela sua apólice.\n"
            f"Motivo: {veredicto.motivo_recusa}\n"
            f"Entre em contato com a 88i: 0800 718 7813"
        )
    elif veredicto.docs_pendentes:
        pendencias_txt = "\n".join(f"  • {d}" for d in veredicto.docs_pendentes[:5])
        mensagem = (
            f"Sinistro registrado.{protocolo_txt}\n"
            f"Cobertura identificada: {veredicto.descricao_cobertura or veredicto.cobertura}\n"
            f"Para prosseguir, precisamos dos seguintes documentos:\n{pendencias_txt}"
        )
    else:
        mensagem = (
            f"Sinistro registrado.{protocolo_txt}\n"
            f"Cobertura: {veredicto.descricao_cobertura or veredicto.cobertura}\n"
            f"Documentação completa. Vamos analisar e retornamos em breve."
        )

    bloqueantes = [c for c in extracao.campos_faltantes if c.criticidade == "bloqueante"]
    if bloqueantes:
        log.append(f"PENDÊNCIAS DOCUMENTAIS: {len(bloqueantes)} bloqueantes para análise posterior")

    return {
        "mensagem_ao_segurado": mensagem,
        "protocolo": registro.protocolo,
        "veredicto_cobertura": veredicto,
        "log_execucao": log,
    }


def no_analisar_documentos(state: SinistroState) -> dict:
    """
    Semana 4: executa o pipeline documental nos documentos recebidos.
    Chama as 3 skills: classifier → forensics → adjudicator.

    Só é chamado quando state["documentos_recebidos"] está preenchido.
    Em produção: disparado por webhook quando segurado envia documentos via WhatsApp.

    ZERO decisão de negócio aqui — adjudicator retorna decisão,
    que pode promover o sinistro ou escalar para humano.
    """
    log = state.get("log_execucao", [])
    docs = state.get("documentos_recebidos") or []

    if not docs:
        log.append("[docs] nenhum documento recebido — pulando análise documental")
        return {"analise_documental": None, "log_execucao": log}

    log.append(f"[docs] iniciando pipeline documental: {len(docs)} documento(s)")

    extracao = state.get("extracao")
    veredicto_cob = state.get("veredicto_cobertura")
    tipo_label = (
        extracao.tipo_sinistro.value
        if extracao and hasattr(extracao.tipo_sinistro, "value")
        else "INDEFINIDO"
    )
    plataforma_label = (
        extracao.plataforma_mencionada.value
        if extracao and hasattr(extracao, "plataforma_mencionada") and hasattr(extracao.plataforma_mencionada, "value")
        else "NAO_MENCIONADA"
    )
    cobertura_label = veredicto_cob.cobertura if veredicto_cob else "desconhecida"
    protocolo = state.get("protocolo") or "sem-protocolo"

    contexto = (
        f"Protocolo: {protocolo}\n"
        f"Tipo de sinistro: {tipo_label}\n"
        f"Plataforma: {plataforma_label}\n"
        f"Cobertura identificada: {cobertura_label}\n"
        f"Narrativa original: {state['narrativa_original'][:300]}\n"
    )

    try:
        analise = analisar_documentos(docs, contexto_sinistro=contexto)
        veredicto = analise.veredicto
        log.append(
            f"[docs] pipeline concluído: decision={veredicto.decision_status if veredicto else 'erro'} "
            f"fraud_score={veredicto.fraud_score if veredicto else 0} "
            f"human_review={analise.needs_human_review}"
        )
        if analise.resumo_fraude:
            log.append(f"[docs] FRAUDE: {analise.resumo_fraude}")
    except Exception as e:
        log.append(f"[docs] ERRO no pipeline: {e}")
        analise = None

    return {"analise_documental": analise, "log_execucao": log}


def no_escalar_humano(state: SinistroState) -> dict:
    """
    Casos sensíveis ou de baixa confiança vão para fila humana priorizada.
    Semana 5: cria tarefa na fila HITL para a Rosi.
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

    # Cria tarefa na fila HITL (fail-open: não bloqueia se falhar)
    tarefa = criar_tarefa(dict(state))
    tarefa_id = tarefa.id if tarefa else None
    if tarefa_id:
        log.append(f"[hitl] tarefa criada: {tarefa_id} prioridade={tarefa.prioridade}")
    else:
        log.append("[hitl] falha ao criar tarefa — continuando sem HITL")

    mensagem = (
        "Recebemos sua comunicação de sinistro. Dada a natureza do caso, "
        "um especialista da 88i vai entrar em contato em breve."
    )
    return {
        "mensagem_ao_segurado": mensagem,
        "alerta_operacional": alerta,
        "hitl_tarefa_id": tarefa_id,
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
    Activity do Inngest, mas aqui roda local/sync.

    Semana 2: adicionado nó consultar_contexto entre extrair e decidir_rota.
    """
    workflow = StateGraph(SinistroState)

    # Adiciona os nós
    workflow.add_node("extrair", no_extrair)
    workflow.add_node("consultar_contexto", no_consultar_contexto)
    workflow.add_node("decidir_rota", no_decidir_rota)
    workflow.add_node("solicitar_esclarecimento", no_solicitar_esclarecimento)
    workflow.add_node("pronto_para_analise", no_pronto_para_analise)
    workflow.add_node("analisar_documentos", no_analisar_documentos)
    workflow.add_node("escalar_humano", no_escalar_humano)

    # Arestas lineares
    workflow.add_edge(START, "extrair")
    workflow.add_edge("extrair", "consultar_contexto")
    workflow.add_edge("consultar_contexto", "decidir_rota")

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
    workflow.add_edge("pronto_para_analise", "analisar_documentos")
    workflow.add_edge("analisar_documentos", END)
    workflow.add_edge("escalar_humano", END)

    return workflow.compile()


# ============================================================
# 5. API pública simples
# ============================================================

@observe(name="processar_narrativa", as_type="span")
def processar_narrativa(narrativa: str, segurado_id: Optional[str] = None) -> SinistroState:
    """
    Ponto de entrada. Em produção seria chamado pelo webhook Evolution API.

    Instrumentado com @observe(as_type="span") — cria o trace top-level
    no Langfuse; a `extrair_sinistro` fica aninhada dentro deste span.
    """
    agente = construir_agente()
    estado_inicial: SinistroState = {
        "narrativa_original": narrativa,
        "segurado_id": segurado_id,
        "timestamp_recebimento": datetime.now().isoformat(),
        "extracao": None,
        "dados_apolice": None,
        "historico_sinistros": None,
        "veredicto_cobertura": None,
        "documentos_recebidos": None,
        "analise_documental": None,
        "hitl_tarefa_id": None,
        "proxima_acao": None,
        "mensagem_ao_segurado": None,
        "alerta_operacional": None,
        "protocolo": None,
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
