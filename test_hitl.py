"""
test_hitl.py — Testes da fila HITL (Semana 5)

Testa sem LLM: criação de tarefas, listagem, prioridade, resolução.

Casos:
  1. Criar tarefa com red_flag alta → prioridade ALTA, status PENDENTE
  2. Criar tarefa com fraude → prioridade ALTA, motivo fraud_escalation
  3. Criar tarefa com vítima fatal → prioridade CRITICA
  4. Deduplicação: protocolo igual não cria segunda tarefa
  5. Listagem ordenada por prioridade
  6. Resolver: aprovar → mensagem ao segurado correta
  7. Resolver: solicitar_docs → mensagem com lista de documentos
  8. Resolver: recusar → mensagem com motivo
  9. Dupla resolução → erro
 10. Obter tarefa inexistente → retorna None

Rodar: python test_hitl.py
Esperado: 10/10 PASS (sem chamadas ao Claude)
"""

import sys
from datetime import date

from hitl_queue import (
    criar_tarefa, listar_tarefas, obter_tarefa, resolver_tarefa, resumo_fila,
    TarefaMotivo, TarefaPrioridade, TarefaStatus, DecisaoHumana,
    _FILA, _PROTOCOLO_IDX,
)


# ============================================================
# Helpers para montar state fake (sem rodar o agente)
# ============================================================

def _make_red_flag(severidade: str, descricao: str = "sinal suspeito"):
    class RF:
        pass
    rf = RF()
    rf.severidade = severidade
    rf.descricao = descricao
    rf.tipo = "detalhe_suspeito"
    return rf


def _make_extracao(
    tipo="DITA",
    plataforma="UBER",
    confianca=0.85,
    red_flags=None,
    ha_vitimas_fatais=False,
):
    class TS:
        def __init__(self, v): self.value = v
    class PL:
        def __init__(self, v): self.value = v
    class Ex:
        pass
    ex = Ex()
    ex.tipo_sinistro = TS(tipo)
    ex.plataforma_mencionada = PL(plataforma)
    ex.confianca = confianca
    ex.red_flags = red_flags or []
    ex.ha_vitimas_fatais = ha_vitimas_fatais
    return ex


def _make_state(
    protocolo: str,
    extracao=None,
    motivo_extra: str = "",
    fraud_score: int = 0,
    ha_fatais: bool = False,
):
    """Monta um state mínimo para testar a fila sem rodar o agente."""
    state = {
        "protocolo": protocolo,
        "segurado_id": "SEG-001",
        "narrativa_original": f"Narrativa de teste para protocolo {protocolo}",
        "extracao": extracao or _make_extracao(),
        "dados_apolice": None,
        "historico_sinistros": None,
        "veredicto_cobertura": None,
        "analise_documental": None,
        "log_execucao": [],
        "alerta_operacional": motivo_extra or None,
    }
    return state


# Limpa a fila antes dos testes
def _reset():
    _FILA.clear()
    _PROTOCOLO_IDX.clear()


# ============================================================
# Casos de teste
# ============================================================

def test_1_red_flag_alta():
    """Tarefa com red_flag alta → prioridade ALTA, motivo red_flag_alta."""
    _reset()
    state = _make_state(
        "88i-2026-TEST001",
        extracao=_make_extracao(red_flags=[_make_red_flag("alta", "ausência de BO em fratura")]),
    )
    tarefa = criar_tarefa(state)
    assert tarefa is not None, "criar_tarefa retornou None"
    assert tarefa.status == TarefaStatus.PENDENTE
    assert tarefa.prioridade == TarefaPrioridade.ALTA
    assert tarefa.motivo == TarefaMotivo.RED_FLAG_ALTA
    assert tarefa.protocolo == "88i-2026-TEST001"
    return True


def test_2_fraude():
    """Tarefa com fraud_escalation → prioridade ALTA, motivo fraude_escalation."""
    _reset()

    class FakeVeredicto:
        decision_status = "fraud_escalation"
        human_review_required = True
        fraud_score = 9
        key_findings = ["atestado anterior ao acidente"]

    class FakeAnalise:
        veredicto = FakeVeredicto()

    state = _make_state("88i-2026-TEST002")
    state["analise_documental"] = FakeAnalise()

    tarefa = criar_tarefa(state)
    assert tarefa is not None
    assert tarefa.motivo == TarefaMotivo.FRAUDE_ESCALATION
    assert tarefa.prioridade == TarefaPrioridade.ALTA
    assert tarefa.fraud_score == 9
    return True


def test_3_vitima_fatal():
    """Tarefa com vítima fatal → prioridade CRITICA."""
    _reset()
    state = _make_state(
        "88i-2026-TEST003",
        extracao=_make_extracao(ha_vitimas_fatais=True),
    )
    tarefa = criar_tarefa(state)
    assert tarefa is not None
    assert tarefa.prioridade == TarefaPrioridade.CRITICA
    assert tarefa.motivo == TarefaMotivo.VITIMA_FATAL
    return True


def test_4_deduplicacao():
    """Protocolo igual não cria segunda tarefa."""
    _reset()
    state = _make_state("88i-2026-TEST004")
    t1 = criar_tarefa(state)
    t2 = criar_tarefa(state)  # mesmo protocolo
    assert t1 is not None
    assert t2 is not None
    assert t1.id == t2.id, f"IDs diferentes: {t1.id} != {t2.id}"
    assert len(_FILA) == 1, f"Fila deveria ter 1 tarefa, tem {len(_FILA)}"
    return True


def test_5_listagem_por_prioridade():
    """Listagem ordena por prioridade: critica antes de alta antes de baixa."""
    _reset()
    # Cria em ordem inversa
    criar_tarefa(_make_state("P-BAIXA"))  # → revisao_manual → baixa
    criar_tarefa(_make_state("P-ALTA",
        extracao=_make_extracao(red_flags=[_make_red_flag("alta")])))  # → alta
    criar_tarefa(_make_state("P-CRITICA",
        extracao=_make_extracao(ha_vitimas_fatais=True)))  # → critica

    lista = listar_tarefas(TarefaStatus.PENDENTE)
    assert len(lista) == 3
    prioridades = [t.prioridade for t in lista]
    assert prioridades[0] == TarefaPrioridade.CRITICA, f"Primeira deveria ser critica, é {prioridades[0]}"
    assert prioridades[1] == TarefaPrioridade.ALTA,    f"Segunda deveria ser alta, é {prioridades[1]}"
    assert prioridades[2] == TarefaPrioridade.BAIXA,   f"Terceira deveria ser baixa, é {prioridades[2]}"
    return True


def test_6_resolver_aprovar():
    """Resolução APROVAR → mensagem positiva ao segurado."""
    _reset()
    state = _make_state("88i-2026-APROVAR")
    tarefa = criar_tarefa(state)
    assert tarefa is not None

    resultado = resolver_tarefa(
        tarefa_id=tarefa.id,
        decisao=DecisaoHumana.APROVAR,
        analista="Rosi",
        justificativa="Documentação válida, aprovado",
    )
    assert resultado.sucesso
    assert resultado.decisao == DecisaoHumana.APROVAR
    assert "aprovado" in resultado.mensagem_ao_segurado.lower()

    # Verifica estado da tarefa
    t = obter_tarefa(tarefa.id)
    assert t.status == TarefaStatus.RESOLVIDA
    assert t.analista == "Rosi"
    assert t.resolvida_em is not None
    return True


def test_7_resolver_solicitar_docs():
    """Resolução SOLICITAR_DOCS → mensagem com lista de documentos."""
    _reset()
    state = _make_state("88i-2026-DOCS")
    tarefa = criar_tarefa(state)

    resultado = resolver_tarefa(
        tarefa_id=tarefa.id,
        decisao=DecisaoHumana.SOLICITAR_DOCS,
        analista="Rosi",
        justificativa="Laudo médico insuficiente",
        docs_solicitados=["Laudo médico com CRM", "Atestado de 30 dias"],
    )
    assert resultado.sucesso
    assert "Laudo médico com CRM" in resultado.mensagem_ao_segurado
    assert "Atestado de 30 dias" in resultado.mensagem_ao_segurado
    return True


def test_8_resolver_recusar():
    """Resolução RECUSAR → mensagem com motivo."""
    _reset()
    state = _make_state("88i-2026-RECUSA")
    tarefa = criar_tarefa(state)

    resultado = resolver_tarefa(
        tarefa_id=tarefa.id,
        decisao=DecisaoHumana.RECUSAR,
        analista="Rosi",
        justificativa="Apólice vencida antes do sinistro",
    )
    assert resultado.sucesso
    assert "Apólice vencida" in resultado.mensagem_ao_segurado
    return True


def test_9_dupla_resolucao():
    """Segunda tentativa de resolver tarefa já resolvida → erro."""
    _reset()
    state = _make_state("88i-2026-DUPLA")
    tarefa = criar_tarefa(state)

    resolver_tarefa(tarefa.id, DecisaoHumana.APROVAR, "Rosi")
    resultado2 = resolver_tarefa(tarefa.id, DecisaoHumana.RECUSAR, "Outro")

    assert not resultado2.sucesso
    assert resultado2.erro is not None
    return True


def test_10_tarefa_inexistente():
    """Obter tarefa com ID inválido → retorna None."""
    _reset()
    t = obter_tarefa("id-que-nao-existe")
    assert t is None
    return True


# ============================================================
# Runner
# ============================================================

TESTES = [
    ("1. red_flag alta → prioridade ALTA",         test_1_red_flag_alta),
    ("2. fraud_escalation → FRAUDE_ESCALATION",    test_2_fraude),
    ("3. vítima fatal → prioridade CRITICA",        test_3_vitima_fatal),
    ("4. deduplicação por protocolo",               test_4_deduplicacao),
    ("5. listagem ordenada por prioridade",         test_5_listagem_por_prioridade),
    ("6. resolver APROVAR → mensagem positiva",     test_6_resolver_aprovar),
    ("7. resolver SOLICITAR_DOCS → lista de docs",  test_7_resolver_solicitar_docs),
    ("8. resolver RECUSAR → mensagem com motivo",   test_8_resolver_recusar),
    ("9. dupla resolução → erro",                   test_9_dupla_resolucao),
    ("10. tarefa inexistente → None",               test_10_tarefa_inexistente),
]


def executar():
    total = len(TESTES)
    passes = 0

    for nome, fn in TESTES:
        try:
            fn()
            print(f"✅ PASS — {nome}")
            passes += 1
        except AssertionError as e:
            print(f"❌ FAIL — {nome}: {e}")
        except Exception as e:
            print(f"❌ ERRO — {nome}: {type(e).__name__}: {e}")

    print(f"\n{'='*60}")
    print(f"RESULTADO: {passes}/{total} PASS")
    print(f"{'='*60}")
    return passes == total


if __name__ == "__main__":
    ok = executar()
    sys.exit(0 if ok else 1)
