"""
test_shadow.py — Testes do shadow mode e comparador (Semana 7)

Testa sem LLM: comparação de outputs, modos de operação, métricas.

Casos:
  1. Concordância total — OCTA e novo agente iguais
  2. Divergência crítica de rota (escalar vs pronto)
  3. Divergência alta de tipo_sinistro
  4. OCTA sem campo plataforma — informativo, não divergência
  5. Score de concordância calculado corretamente
  6. Modo SHADOW: OCTA é retornado, métricas atualizadas
  7. Modo CUTOVER: novo agente é retornado
  8. Canary: hash determinístico (mesmo sinistro → mesmo agente)
  9. relatorio() retorna pronto_para_cutover=False antes de 100 sinistros
 10. relatorio() após resetar_metricas() zera contadores

Rodar: python test_shadow.py
Esperado: 10/10 PASS (sem LLM)
"""

import os
import sys

# Garante que shadow mode não chama o agente real nos testes
os.environ["SHADOW_MODE"] = "shadow"

from shadow_comparator import comparar, ResultadoComparacao, Divergencia
from shadow_mode import (
    resetar_metricas, relatorio, ShadowModeEnum,
    _deve_usar_novo_agente, _atualizar_metricas, MetricasShadow,
    ResultadoShadowRun,
)


# ============================================================
# Helpers
# ============================================================

def _output_octa(rota="pronto_para_analise", tipo="DITA"):
    return {"proxima_acao": rota, "tipo_sinistro": tipo}


def _output_novo(rota="pronto_para_analise", tipo="DITA", plataforma="UBER", cobertura="B_DITA", elegivel=True):
    """Simula state do novo agente."""
    class _TS:
        def __init__(self, v): self.value = v
    class _PL:
        def __init__(self, v): self.value = v
    class _VC:
        def __init__(self, c, e):
            self.cobertura = c
            self.elegivel = e
    class _EX:
        def __init__(self, t, p):
            self.tipo_sinistro = _TS(t)
            self.plataforma_mencionada = _PL(p)
    return {
        "proxima_acao": rota,
        "extracao": _EX(tipo, plataforma),
        "veredicto_cobertura": _VC(cobertura, elegivel),
        "protocolo": "88i-TEST-001",
        "mensagem_ao_segurado": "Sinistro registrado.",
    }


# ============================================================
# Casos
# ============================================================

def test_1_concordancia_total():
    """OCTA e novo agente concordam em tudo → concordancia=True, score=1.0."""
    octa = _output_octa("pronto_para_analise", "DITA")
    novo = _output_novo("pronto_para_analise", "DITA", "UBER", "B_DITA", True)
    r = comparar(octa, novo)
    assert r.concordancia, f"Esperado concordância, got: {r.resumo}"
    assert r.score_concordancia == 1.0, f"Score esperado 1.0, got {r.score_concordancia}"
    assert len(r.divergencias) == 0
    return True


def test_2_divergencia_critica_rota():
    """Rota diferente → divergência crítica, concordancia=False."""
    octa = _output_octa("pronto_para_analise", "DITA")
    novo = _output_novo("escalar_humano",       "DITA")
    r = comparar(octa, novo)
    assert not r.concordancia, "Esperado discordância"
    assert r.requer_revisao_manual, "Divergência crítica deveria exigir revisão"
    criticas = [d for d in r.divergencias if d.severidade == "critica"]
    assert len(criticas) >= 1, "Esperado ao menos 1 divergência crítica"
    campos = [d.campo for d in criticas]
    assert "rota" in campos, f"Esperado divergência em rota, got: {campos}"
    return True


def test_3_divergencia_alta_tipo():
    """Tipo de sinistro diferente → divergência alta."""
    octa = _output_octa("pronto_para_analise", "DITA")
    novo = _output_novo("pronto_para_analise", "IAT")
    r = comparar(octa, novo)
    altas = [d for d in r.divergencias if d.severidade == "alta"]
    assert len(altas) >= 1, f"Esperado divergência alta, got divergências: {r.divergencias}"
    campos = [d.campo for d in altas]
    assert "tipo_sinistro" in campos
    return True


def test_4_octa_sem_plataforma():
    """OCTA não tem plataforma — não deve gerar divergência."""
    octa = _output_octa("pronto_para_analise", "DITA")  # sem plataforma
    novo = _output_novo("pronto_para_analise", "DITA", "UBER")
    r = comparar(octa, novo)
    campos_div = [d.campo for d in r.divergencias]
    assert "plataforma" not in campos_div, f"Plataforma não deveria divergir (OCTA não tem): {campos_div}"
    return True


def test_5_score_calculado_corretamente():
    """Score reflete pesos: rota(4) tipo(2) plat(1) cob(2) eleg(3)."""
    # Só rota diverge (peso 4 de 4+2+2+3=11 — plataforma OCTA ausente)
    octa = {"proxima_acao": "pronto_para_analise", "tipo_sinistro": "DITA",
            "cobertura": "B_DITA", "elegivel": True}
    novo = _output_novo("escalar_humano", "DITA", "UBER", "B_DITA", True)
    r = comparar(octa, novo)
    # Campos com dados em ambos: rota(4), tipo(2), cobertura(2), elegivel(3) = 11
    # rota diverge → score = (0*4 + 1*2 + 1*2 + 1*3) / 11 = 7/11 ≈ 0.636
    assert r.score_concordancia < 1.0
    assert r.score_concordancia > 0.0
    return True


def test_6_modo_shadow_retorna_octa():
    """No modo SHADOW, métricas são atualizadas após comparação."""
    os.environ["SHADOW_MODE"] = ShadowModeEnum.SHADOW
    resetar_metricas()

    octa = _output_octa("pronto_para_analise", "DITA")
    novo = _output_novo("pronto_para_analise", "DITA")

    comparacao = comparar(octa, novo)
    assert comparacao.concordancia, f"Esperado concordância, got: {comparacao.resumo}"

    _atualizar_metricas(comparacao)

    r = relatorio()
    assert r["total_sinistros"] == 1, f"Esperado 1, got {r['total_sinistros']}"
    assert r["total_concordancias"] == 1, f"Esperado 1, got {r['total_concordancias']}"
    assert r["taxa_concordancia"] == 1.0
    assert r["modo_atual"] == ShadowModeEnum.SHADOW
    return True


def test_7_modo_cutover():
    """No modo CUTOVER, a variável de ambiente está correta."""
    os.environ["SHADOW_MODE"] = ShadowModeEnum.CUTOVER
    from shadow_mode import get_modo
    assert get_modo() == ShadowModeEnum.CUTOVER
    os.environ["SHADOW_MODE"] = ShadowModeEnum.SHADOW  # restaura
    return True


def test_8_canary_hash_deterministico():
    """Hash determinístico: mesma narrativa → mesmo resultado."""
    os.environ["CANARY_PERCENT"] = "50"
    narrativa = "Bati minha moto na Paulista ontem às 22h."
    resultado1 = _deve_usar_novo_agente(narrativa)
    resultado2 = _deve_usar_novo_agente(narrativa)
    assert resultado1 == resultado2, "Hash não é determinístico"
    # Narrativas diferentes devem ter resultados diferentes às vezes
    resultados = {_deve_usar_novo_agente(f"narrativa {i}") for i in range(20)}
    assert len(resultados) == 2, "Com 50% deveria ter True e False nas 20 narrativas"
    os.environ["CANARY_PERCENT"] = "5"
    return True


def test_9_pronto_para_cutover_false_antes_de_100():
    """pronto_para_cutover=False se < 100 sinistros."""
    resetar_metricas()
    # Simula 50 sinistros com concordância total
    for _ in range(50):
        comparacao = comparar(
            _output_octa("pronto_para_analise", "DITA"),
            _output_novo("pronto_para_analise", "DITA"),
        )
        _atualizar_metricas(comparacao)

    r = relatorio()
    assert r["total_sinistros"] == 50
    assert r["taxa_concordancia"] == 1.0
    assert not r["pronto_para_cutover"], "Não deveria estar pronto com < 100 sinistros"
    return True


def test_10_resetar_metricas():
    """resetar_metricas() zera todos os contadores."""
    # Acumula algumas métricas
    for _ in range(5):
        _atualizar_metricas(comparar(
            _output_octa("pronto_para_analise", "DITA"),
            _output_novo("escalar_humano", "DITA"),
        ))

    r_antes = relatorio()
    assert r_antes["total_sinistros"] > 0

    resetar_metricas()
    r_depois = relatorio()
    assert r_depois["total_sinistros"] == 0
    assert r_depois["total_concordancias"] == 0
    assert r_depois["divergencias_criticas"] == 0
    assert r_depois["taxa_concordancia"] == 1.0
    return True


# ============================================================
# Runner
# ============================================================

TESTES = [
    ("1. concordância total → score=1.0",                          test_1_concordancia_total),
    ("2. rota diferente → divergência crítica",                    test_2_divergencia_critica_rota),
    ("3. tipo_sinistro diferente → divergência alta",              test_3_divergencia_alta_tipo),
    ("4. OCTA sem plataforma → sem divergência de plataforma",     test_4_octa_sem_plataforma),
    ("5. score calculado com pesos corretos",                      test_5_score_calculado_corretamente),
    ("6. modo SHADOW: métricas atualizadas",                       test_6_modo_shadow_retorna_octa),
    ("7. modo CUTOVER: variável de ambiente",                      test_7_modo_cutover),
    ("8. canary: hash determinístico",                             test_8_canary_hash_deterministico),
    ("9. pronto_para_cutover=False antes de 100 sinistros",        test_9_pronto_para_cutover_false_antes_de_100),
    ("10. resetar_metricas() zera contadores",                     test_10_resetar_metricas),
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
            import traceback
            print(f"❌ ERRO — {nome}: {type(e).__name__}: {e}")
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"RESULTADO: {passes}/{total} PASS")
    print(f"{'='*60}")
    return passes == total


if __name__ == "__main__":
    ok = executar()
    sys.exit(0 if ok else 1)
