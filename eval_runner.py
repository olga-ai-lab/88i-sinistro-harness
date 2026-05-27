"""
eval_runner.py — Runner de avaliação do pipeline 88i (Semana 6)

Executa o agente em cada caso do eval_dataset.json e compara com ground truth.

Métricas calculadas por dimensão:
  tipo_sinistro_accuracy  — LLM extraiu o tipo correto?
  plataforma_accuracy     — LLM identificou a plataforma correta?
  rota_accuracy           — agente tomou a rota correta (pronto/escalar/solicitar)?
  cobertura_accuracy      — rules engine mapeou a cobertura correta?
  elegibilidade_accuracy  — rules engine decidiu elegibilidade correta?

Score geral = média das dimensões aplicáveis por caso.

Uso:
  python eval_runner.py                      # roda todos os 20 casos
  python eval_runner.py --categoria uber_normal  # filtra por categoria
  python eval_runner.py --ids eval-uber-001,eval-uber-002  # casos específicos
  python eval_runner.py --dry-run            # sem chamadas ao LLM (testa framework)

Saída:
  - Console: resultado por caso + tabela de métricas
  - eval_results_<timestamp>.json: arquivo de resultados para histórico
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()


# ============================================================
# Tipos de dados
# ============================================================

@dataclass
class CasoEval:
    id: str
    categoria: str
    descricao: str
    narrativa: str
    ground_truth: dict


@dataclass
class ResultadoCaso:
    caso_id: str
    categoria: str
    # Predições do agente
    tipo_sinistro_pred: Optional[str]
    plataforma_pred: Optional[str]
    rota_pred: Optional[str]
    cobertura_pred: Optional[str]
    elegivel_pred: Optional[bool]
    confianca: Optional[float]
    # Ground truth
    tipo_sinistro_gt: Optional[str]
    plataforma_gt: Optional[str]
    rota_gt: Optional[str]
    cobertura_gt: Optional[str]
    elegivel_gt: Optional[bool]
    # Scores por dimensão (True/False/None se não aplicável)
    tipo_sinistro_ok: Optional[bool]
    plataforma_ok: Optional[bool]
    rota_ok: Optional[bool]
    cobertura_ok: Optional[bool]
    elegibilidade_ok: Optional[bool]
    # Score agregado do caso (0.0 - 1.0)
    score: float
    # Metadata
    latencia_ms: Optional[int]
    erro: Optional[str]


@dataclass
class ResultadoEval:
    timestamp: str
    git_commit: str
    total_casos: int
    casos_com_erro: int
    # Métricas agregadas
    tipo_sinistro_accuracy: float
    plataforma_accuracy: float
    rota_accuracy: float
    cobertura_accuracy: float
    elegibilidade_accuracy: float
    score_geral: float
    # Por categoria
    por_categoria: dict
    # Detalhes
    casos: list[dict]


# ============================================================
# Carregamento do dataset
# ============================================================

DATASET_PATH = Path(__file__).parent / "eval_dataset.json"


def carregar_dataset(
    categorias: Optional[list[str]] = None,
    ids: Optional[list[str]] = None,
) -> list[CasoEval]:
    with open(DATASET_PATH) as f:
        data = json.load(f)

    casos = [CasoEval(**c) for c in data]

    if categorias:
        casos = [c for c in casos if c.categoria in categorias]
    if ids:
        casos = [c for c in casos if c.id in ids]

    return casos


# ============================================================
# Execução de um caso (com o agente real)
# ============================================================

def _executar_caso(caso: CasoEval) -> ResultadoCaso:
    """Executa o pipeline completo para um caso e retorna o resultado."""
    from agent import processar_narrativa
    from rules_engine import avaliar_cobertura

    inicio = datetime.now()
    erro = None
    tipo_pred = plataforma_pred = rota_pred = cobertura_pred = None
    elegivel_pred = confianca = None

    try:
        resultado = processar_narrativa(caso.narrativa)
        latencia_ms = int((datetime.now() - inicio).total_seconds() * 1000)

        rota_pred = resultado.get("proxima_acao")

        extracao = resultado.get("extracao")
        if extracao:
            ts = getattr(extracao, "tipo_sinistro", None)
            tipo_pred = ts.value if ts and hasattr(ts, "value") else None

            pl = getattr(extracao, "plataforma_mencionada", None)
            plataforma_pred = pl.value if pl and hasattr(pl, "value") else None

            confianca = getattr(extracao, "confianca", None)

        veredicto = resultado.get("veredicto_cobertura")
        if veredicto:
            cobertura_pred = veredicto.cobertura
            elegivel_pred = veredicto.elegivel

    except Exception as e:
        latencia_ms = int((datetime.now() - inicio).total_seconds() * 1000)
        erro = f"{type(e).__name__}: {e}"

    # Ground truth
    gt = caso.ground_truth
    tipo_gt      = gt.get("tipo_sinistro")
    plataforma_gt = gt.get("plataforma")
    rota_gt      = gt.get("rota")
    cobertura_gt = gt.get("cobertura")
    elegivel_gt  = gt.get("elegivel")

    # Avaliações por dimensão
    def _match(pred, gt_val):
        if gt_val is None:
            return None  # não aplicável
        if pred is None:
            return False
        return str(pred).upper() == str(gt_val).upper()

    tipo_ok        = _match(tipo_pred, tipo_gt)
    plataforma_ok  = _match(plataforma_pred, plataforma_gt)
    rota_ok        = _match(rota_pred, rota_gt)
    cobertura_ok   = _match(cobertura_pred, cobertura_gt)
    elegivel_ok    = _match(elegivel_pred, elegivel_gt) if elegivel_gt is not None else None

    # Score do caso: média das dimensões aplicáveis com peso
    pesos = {
        "rota":        3,   # mais importante — determina fluxo operacional
        "tipo":        2,
        "plataforma":  2,
        "cobertura":   2,
        "elegivel":    1,
    }
    scores_pesos = []
    for dim, ok in [("rota", rota_ok), ("tipo", tipo_ok), ("plataforma", plataforma_ok),
                    ("cobertura", cobertura_ok), ("elegivel", elegivel_ok)]:
        if ok is not None:
            scores_pesos.append((1.0 if ok else 0.0, pesos[dim]))

    score = (
        sum(s * w for s, w in scores_pesos) / sum(w for _, w in scores_pesos)
        if scores_pesos else 0.0
    )

    return ResultadoCaso(
        caso_id=caso.id,
        categoria=caso.categoria,
        tipo_sinistro_pred=tipo_pred,
        plataforma_pred=plataforma_pred,
        rota_pred=rota_pred,
        cobertura_pred=cobertura_pred,
        elegivel_pred=elegivel_pred,
        confianca=confianca,
        tipo_sinistro_gt=tipo_gt,
        plataforma_gt=plataforma_gt,
        rota_gt=rota_gt,
        cobertura_gt=cobertura_gt,
        elegivel_gt=elegivel_gt,
        tipo_sinistro_ok=tipo_ok,
        plataforma_ok=plataforma_ok,
        rota_ok=rota_ok,
        cobertura_ok=cobertura_ok,
        elegibilidade_ok=elegivel_ok,
        score=score,
        latencia_ms=latencia_ms,
        erro=erro,
    )


def _executar_caso_dry_run(caso: CasoEval) -> ResultadoCaso:
    """Dry run: retorna resultado perfeito para testar o framework sem LLM."""
    gt = caso.ground_truth
    return ResultadoCaso(
        caso_id=caso.id,
        categoria=caso.categoria,
        tipo_sinistro_pred=gt.get("tipo_sinistro"),
        plataforma_pred=gt.get("plataforma"),
        rota_pred=gt.get("rota"),
        cobertura_pred=gt.get("cobertura"),
        elegivel_pred=gt.get("elegivel"),
        confianca=0.9,
        tipo_sinistro_gt=gt.get("tipo_sinistro"),
        plataforma_gt=gt.get("plataforma"),
        rota_gt=gt.get("rota"),
        cobertura_gt=gt.get("cobertura"),
        elegivel_gt=gt.get("elegivel"),
        tipo_sinistro_ok=True if gt.get("tipo_sinistro") else None,
        plataforma_ok=True if gt.get("plataforma") else None,
        rota_ok=True if gt.get("rota") else None,
        cobertura_ok=True if gt.get("cobertura") else None,
        elegibilidade_ok=True if gt.get("elegivel") is not None else None,
        score=1.0,
        latencia_ms=0,
        erro=None,
    )


# ============================================================
# Agregação de métricas
# ============================================================

def _agregar(resultados: list[ResultadoCaso]) -> ResultadoEval:
    def _acc(field_ok: str) -> float:
        vals = [getattr(r, field_ok) for r in resultados if getattr(r, field_ok) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    por_categoria: dict[str, dict] = {}
    for r in resultados:
        cat = r.categoria
        if cat not in por_categoria:
            por_categoria[cat] = {"total": 0, "score_sum": 0.0, "erros": 0}
        por_categoria[cat]["total"] += 1
        por_categoria[cat]["score_sum"] += r.score
        if r.erro:
            por_categoria[cat]["erros"] += 1

    for cat, vals in por_categoria.items():
        vals["score_medio"] = round(vals["score_sum"] / vals["total"], 3) if vals["total"] else 0.0

    # Git commit atual
    try:
        import subprocess
        git_commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        git_commit = "unknown"

    tipo_acc   = _acc("tipo_sinistro_ok")
    plat_acc   = _acc("plataforma_ok")
    rota_acc   = _acc("rota_ok")
    cob_acc    = _acc("cobertura_ok")
    eleg_acc   = _acc("elegibilidade_ok")

    # Score geral = média ponderada das dimensões com dados
    dims = [(rota_acc, 3), (tipo_acc, 2), (plat_acc, 2), (cob_acc, 2), (eleg_acc, 1)]
    score_geral = sum(s * w for s, w in dims) / sum(w for _, w in dims)

    return ResultadoEval(
        timestamp=datetime.now().isoformat(),
        git_commit=git_commit,
        total_casos=len(resultados),
        casos_com_erro=sum(1 for r in resultados if r.erro),
        tipo_sinistro_accuracy=round(tipo_acc, 3),
        plataforma_accuracy=round(plat_acc, 3),
        rota_accuracy=round(rota_acc, 3),
        cobertura_accuracy=round(cob_acc, 3),
        elegibilidade_accuracy=round(eleg_acc, 3),
        score_geral=round(score_geral, 3),
        por_categoria={k: {kk: vv for kk, vv in v.items() if kk != "score_sum"}
                       for k, v in por_categoria.items()},
        casos=[asdict(r) for r in resultados],
    )


# ============================================================
# Impressão de resultados
# ============================================================

def _imprimir(resultado: ResultadoEval, verbose: bool = False):
    print(f"\n{'='*70}")
    print(f"EVAL DATASET 88i — {resultado.timestamp[:19]}  commit={resultado.git_commit}")
    print(f"{'='*70}")
    print(f"\nCasos: {resultado.total_casos} | Erros: {resultado.casos_com_erro}")
    print(f"\nMétricas:")
    print(f"  rota_accuracy        {resultado.rota_accuracy:.1%}  (peso 3)")
    print(f"  tipo_sinistro_acc    {resultado.tipo_sinistro_accuracy:.1%}  (peso 2)")
    print(f"  plataforma_acc       {resultado.plataforma_accuracy:.1%}  (peso 2)")
    print(f"  cobertura_acc        {resultado.cobertura_accuracy:.1%}  (peso 2)")
    print(f"  elegibilidade_acc    {resultado.elegibilidade_accuracy:.1%}  (peso 1)")
    print(f"\n  SCORE GERAL          {resultado.score_geral:.1%}")

    print(f"\nPor categoria:")
    for cat, vals in resultado.por_categoria.items():
        print(f"  {cat:<22} score={vals['score_medio']:.1%}  n={vals['total']}  erros={vals['erros']}")

    if verbose:
        print(f"\nDetalhes por caso:")
        for r in resultado.casos:
            status = "✅" if r["score"] >= 0.8 else "⚠️" if r["score"] >= 0.5 else "❌"
            print(f"  {status} {r['caso_id']:<25} score={r['score']:.2f}")
            if r["erro"]:
                print(f"     ERRO: {r['erro']}")
            else:
                dim_status = []
                for dim, ok_field in [
                    ("rota", "rota_ok"),
                    ("tipo", "tipo_sinistro_ok"),
                    ("plat", "plataforma_ok"),
                    ("cob", "cobertura_ok"),
                ]:
                    ok = r[ok_field]
                    if ok is not None:
                        dim_status.append(f"{dim}={'✓' if ok else '✗'}")
                print(f"     {' | '.join(dim_status)}")
                print(f"     pred: tipo={r['tipo_sinistro_pred']} plat={r['plataforma_pred']} "
                      f"rota={r['rota_pred']}")

    # Gate de qualidade
    gate = resultado.score_geral >= 0.80
    print(f"\n{'─'*70}")
    print(f"QUALITY GATE (>= 80%): {'✅ PASSOU' if gate else '❌ FALHOU'} ({resultado.score_geral:.1%})")
    print(f"{'─'*70}\n")
    return gate


# ============================================================
# Persistência de resultados
# ============================================================

def _salvar(resultado: ResultadoEval) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(__file__).parent / f"eval_results_{ts}.json"
    with open(path, "w") as f:
        json.dump(asdict(resultado), f, indent=2, ensure_ascii=False)
    return path


# ============================================================
# Entrypoint
# ============================================================

def rodar(
    categorias: Optional[list[str]] = None,
    ids: Optional[list[str]] = None,
    dry_run: bool = False,
    verbose: bool = False,
    salvar: bool = True,
) -> ResultadoEval:
    casos = carregar_dataset(categorias=categorias, ids=ids)
    print(f"Carregados {len(casos)} caso(s) do dataset.")

    fn = _executar_caso_dry_run if dry_run else _executar_caso
    resultados: list[ResultadoCaso] = []

    for i, caso in enumerate(casos, 1):
        modo = "[DRY]" if dry_run else ""
        print(f"  [{i:02d}/{len(casos)}] {modo} {caso.id} — {caso.descricao[:50]}...", end=" ", flush=True)
        r = fn(caso)
        status = "✅" if r.score >= 0.8 else "⚠️" if r.score >= 0.5 else "❌"
        print(f"{status} score={r.score:.2f}" + (f" ERRO: {r.erro}" if r.erro else ""))
        resultados.append(r)

    resultado = _agregar(resultados)
    gate = _imprimir(resultado, verbose=verbose)

    if salvar:
        path = _salvar(resultado)
        print(f"Resultados salvos em: {path}")

    return resultado


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eval runner 88i")
    parser.add_argument("--categoria", help="Filtrar por categoria (csv)")
    parser.add_argument("--ids", help="Filtrar por IDs (csv)")
    parser.add_argument("--dry-run", action="store_true", help="Sem LLM — testa framework")
    parser.add_argument("--verbose", action="store_true", help="Detalhe por caso")
    parser.add_argument("--no-save", action="store_true", help="Não salva JSON de resultados")
    args = parser.parse_args()

    resultado = rodar(
        categorias=args.categoria.split(",") if args.categoria else None,
        ids=args.ids.split(",") if args.ids else None,
        dry_run=args.dry_run,
        verbose=args.verbose,
        salvar=not args.no_save,
    )
    gate = resultado.score_geral >= 0.80
    sys.exit(0 if gate else 1)
