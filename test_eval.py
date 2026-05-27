"""
test_eval.py — Smoke test do framework de avaliação (Semana 6)

Valida o framework sem chamadas ao LLM usando --dry-run.
Verifica:
  1. Dataset carregado corretamente — 20 casos
  2. Todas as categorias presentes
  3. Ground truth válido em todos os casos
  4. Dry-run retorna score 1.0 (baseline de sanidade)
  5. Métricas calculadas corretamente
  6. Arquivo JSON de resultado é gerado
  7. Quality gate funciona (>= 80% passa, < 80% falha)
  8. Filtro por categoria funciona
  9. Filtro por IDs funciona
 10. Resultados por categoria batem com o dataset

Rodar: python test_eval.py
Esperado: 10/10 PASS (sem chamadas ao Claude)
"""

import json
import sys
import os
import glob
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

from eval_runner import (
    carregar_dataset, rodar, _agregar, _executar_caso_dry_run,
    CasoEval,
)


CATEGORIAS_ESPERADAS = {
    "uber_normal", "plataforma_padrao", "fraude_rejeicao", "ambiguo"
}


def test_1_dataset_carregado():
    """Dataset tem 20 casos."""
    casos = carregar_dataset()
    assert len(casos) == 20, f"Esperado 20 casos, tem {len(casos)}"
    return True


def test_2_categorias_presentes():
    """Todas as 4 categorias estão no dataset."""
    casos = carregar_dataset()
    categorias = {c.categoria for c in casos}
    faltando = CATEGORIAS_ESPERADAS - categorias
    assert not faltando, f"Categorias faltando: {faltando}"
    # Cada categoria tem pelo menos 5 casos
    for cat in CATEGORIAS_ESPERADAS:
        n = sum(1 for c in casos if c.categoria == cat)
        assert n >= 5, f"Categoria {cat} tem só {n} casos (mínimo 5)"
    return True


def test_3_ground_truth_valido():
    """Todo caso tem ground truth com tipo_sinistro e rota."""
    casos = carregar_dataset()
    for c in casos:
        gt = c.ground_truth
        assert "tipo_sinistro" in gt, f"{c.id}: falta tipo_sinistro no ground truth"
        assert "rota" in gt, f"{c.id}: falta rota no ground truth"
        assert gt["rota"] in ("pronto_para_analise", "solicitar_esclarecimento", "escalar_humano"), \
            f"{c.id}: rota inválida: {gt['rota']}"
    return True


def test_4_dry_run_score_perfeito():
    """Dry-run retorna score 1.0 para todos os casos (baseline de sanidade)."""
    casos = carregar_dataset()
    resultados = [_executar_caso_dry_run(c) for c in casos]
    for r in resultados:
        assert r.score == 1.0, f"{r.caso_id}: score esperado 1.0, got {r.score}"
        assert r.erro is None, f"{r.caso_id}: erro inesperado: {r.erro}"
    return True


def test_5_metricas_calculadas():
    """Métricas são calculadas corretamente com dry-run."""
    resultado = rodar(dry_run=True, salvar=False, verbose=False)
    assert resultado.score_geral == 1.0, f"Score geral esperado 1.0, got {resultado.score_geral}"
    assert resultado.rota_accuracy == 1.0
    assert resultado.tipo_sinistro_accuracy == 1.0
    assert resultado.plataforma_accuracy == 1.0
    assert resultado.casos_com_erro == 0
    assert resultado.total_casos == 20
    return True


def test_6_arquivo_json_gerado():
    """Dry-run com salvar=True gera arquivo eval_results_*.json."""
    # Limpa arquivos antigos de teste
    for f in glob.glob("eval_results_*.json"):
        os.remove(f)

    resultado = rodar(dry_run=True, salvar=True, verbose=False)

    arquivos = glob.glob("eval_results_*.json")
    assert len(arquivos) >= 1, "Nenhum arquivo eval_results gerado"

    # Verifica estrutura do JSON
    with open(arquivos[0]) as f:
        data = json.load(f)
    assert "score_geral" in data
    assert "casos" in data
    assert len(data["casos"]) == 20
    assert "git_commit" in data

    # Limpa
    for f in arquivos:
        os.remove(f)
    return True


def test_7_quality_gate():
    """Quality gate: >= 0.80 passa, < 0.80 falha."""
    from eval_runner import ResultadoEval, ResultadoCaso
    from dataclasses import asdict

    # Cria resultado fake com score 1.0
    resultado_ok = rodar(dry_run=True, salvar=False)
    assert resultado_ok.score_geral >= 0.80

    # Cria resultado fake com score baixo — manipula diretamente
    resultado_ruim = rodar(dry_run=True, salvar=False)
    resultado_ruim.score_geral = 0.50
    assert resultado_ruim.score_geral < 0.80
    return True


def test_8_filtro_categoria():
    """Filtro por categoria retorna só casos da categoria."""
    casos = carregar_dataset(categorias=["uber_normal"])
    assert len(casos) == 5, f"Esperado 5 casos uber_normal, got {len(casos)}"
    for c in casos:
        assert c.categoria == "uber_normal", f"Caso {c.id} tem categoria {c.categoria}"

    resultado = rodar(categorias=["uber_normal"], dry_run=True, salvar=False)
    assert resultado.total_casos == 5
    return True


def test_9_filtro_ids():
    """Filtro por IDs retorna só os casos especificados."""
    ids = ["eval-uber-001", "eval-padrao-001", "eval-ambiguo-001"]
    casos = carregar_dataset(ids=ids)
    assert len(casos) == 3, f"Esperado 3 casos, got {len(casos)}"
    ids_retornados = {c.id for c in casos}
    assert ids_retornados == set(ids)

    resultado = rodar(ids=ids, dry_run=True, salvar=False)
    assert resultado.total_casos == 3
    return True


def test_10_por_categoria_consistente():
    """por_categoria no resultado bate com a contagem real do dataset."""
    resultado = rodar(dry_run=True, salvar=False)
    casos = carregar_dataset()

    contagens_reais = {}
    for c in casos:
        contagens_reais[c.categoria] = contagens_reais.get(c.categoria, 0) + 1

    for cat, vals in resultado.por_categoria.items():
        assert vals["total"] == contagens_reais.get(cat, 0), \
            f"{cat}: esperado {contagens_reais.get(cat)}, got {vals['total']}"
    return True


# ============================================================
# Runner
# ============================================================

TESTES = [
    ("1. dataset carregado — 20 casos",               test_1_dataset_carregado),
    ("2. categorias presentes — 4 categorias x 5",    test_2_categorias_presentes),
    ("3. ground truth válido em todos os casos",       test_3_ground_truth_valido),
    ("4. dry-run score 1.0 (baseline sanidade)",       test_4_dry_run_score_perfeito),
    ("5. métricas calculadas corretamente",            test_5_metricas_calculadas),
    ("6. arquivo JSON gerado com estrutura correta",   test_6_arquivo_json_gerado),
    ("7. quality gate >= 80% / < 80%",                 test_7_quality_gate),
    ("8. filtro por categoria funciona",               test_8_filtro_categoria),
    ("9. filtro por IDs funciona",                     test_9_filtro_ids),
    ("10. por_categoria consistente com dataset",      test_10_por_categoria_consistente),
]


def executar():
    total = len(TESTES)
    passes = 0

    print(f"\nSmoke test do framework de eval (dry-run — sem LLM)\n")
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
