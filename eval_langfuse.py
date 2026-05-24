"""
eval_langfuse.py — Integração do eval dataset com Langfuse (Semana 6)

Envia resultados de cada run de avaliação para o Langfuse como:
  - Dataset: eval_dataset_88i (criado uma vez, atualizado com novos casos)
  - Experiment: eval_run_<commit>_<timestamp> (um por execução)

Permite comparar performance entre commits no dashboard Langfuse:
  - Qual versão tem maior rota_accuracy?
  - O commit X quebrou a detecção de plataforma?
  - Como evoluiu o score_geral ao longo das semanas?

Requer: LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY no .env

Uso:
  python eval_langfuse.py                   # roda eval + envia para Langfuse
  python eval_langfuse.py --dry-run         # framework dry-run + envia
  python eval_langfuse.py --from-file eval_results_20260524.json  # envia resultado salvo
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()


def _langfuse_disponivel() -> bool:
    return bool(
        os.getenv("LANGFUSE_PUBLIC_KEY")
        and os.getenv("LANGFUSE_SECRET_KEY")
    )


def _get_langfuse():
    from langfuse import Langfuse
    return Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
    )


def sincronizar_dataset(casos_raw: list[dict]) -> str:
    """
    Cria ou atualiza o dataset eval_dataset_88i no Langfuse.
    Retorna o nome do dataset.
    """
    lf = _get_langfuse()
    dataset_name = "eval_dataset_88i"

    # Cria dataset (ignora erro se já existe)
    try:
        lf.create_dataset(
            name=dataset_name,
            description="Casos de avaliação do pipeline 88i — Last Mile Delivery sinistros",
        )
        print(f"Dataset criado/atualizado: {dataset_name}")
    except Exception:
        print(f"Dataset já existe: {dataset_name}")

    # Upsert de cada caso como DatasetItem
    for caso in casos_raw:
        try:
            lf.create_dataset_item(
                dataset_name=dataset_name,
                id=caso["id"],
                input={"narrativa": caso["narrativa"]},
                expected_output=caso["ground_truth"],
                metadata={
                    "categoria": caso["categoria"],
                    "descricao": caso["descricao"],
                },
            )
        except Exception:
            pass  # item pode já existir

    lf.flush()
    return dataset_name


def enviar_experiment(resultado_eval: dict) -> str:
    """
    Envia um resultado de eval como scores por trace no Langfuse.
    Cria uma trace por caso com scores das dimensões.
    Retorna o nome do experiment.
    """
    lf = _get_langfuse()
    commit = resultado_eval.get("git_commit", "unknown")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiment_name = f"eval_{commit}_{ts}"

    print(f"Enviando experiment: {experiment_name}")
    print(f"  {len(resultado_eval.get('casos', []))} casos...")

    for caso in resultado_eval.get("casos", []):
        # Cria trace_id determinístico por caso + experiment
        trace_id = lf.create_trace_id()

        # Envia scores das dimensões
        dims = [
            ("rota_accuracy",       caso["rota_ok"]),
            ("tipo_sinistro_acc",   caso["tipo_sinistro_ok"]),
            ("plataforma_acc",      caso["plataforma_ok"]),
            ("cobertura_acc",       caso["cobertura_ok"]),
            ("elegibilidade_acc",   caso["elegibilidade_ok"]),
            ("score_caso",          caso["score"]),
        ]
        for nome, valor in dims:
            if valor is not None:
                try:
                    lf.create_score(
                        trace_id=trace_id,
                        name=nome,
                        value=float(valor),
                        comment=f"gt={caso.get('rota_gt')} pred={caso.get('rota_pred')} exp={experiment_name}",
                    )
                except Exception:
                    pass

        # Link com dataset item (run de avaliação)
        try:
            dataset = lf.get_dataset("eval_dataset_88i")
            item = dataset.items.get(caso["caso_id"])
            if item:
                item.link(
                    trace_or_observation=None,
                    run_name=experiment_name,
                    trace_id=trace_id,
                    run_metadata={"score": caso["score"]},
                )
        except Exception:
            pass

    lf.flush()
    print(f"Experiment enviado: {experiment_name}")
    return experiment_name


def rodar_e_enviar(dry_run: bool = False) -> int:
    """Roda o eval runner e envia para Langfuse. Retorna exit code."""
    from eval_runner import rodar, carregar_dataset

    if not _langfuse_disponivel():
        print("LANGFUSE_PUBLIC_KEY/SECRET_KEY não configurados.")
        print("Rodando eval local sem envio para Langfuse.")
        resultado = rodar(dry_run=dry_run, salvar=True, verbose=True)
        return 0 if resultado.score_geral >= 0.80 else 1

    # Sincroniza dataset
    casos_raw = json.loads(Path("eval_dataset.json").read_text())
    sincronizar_dataset(casos_raw)

    # Roda eval
    resultado = rodar(dry_run=dry_run, salvar=True, verbose=True)

    # Envia para Langfuse
    from dataclasses import asdict
    enviar_experiment(asdict(resultado))

    return 0 if resultado.score_geral >= 0.80 else 1


def enviar_de_arquivo(path: str) -> int:
    """Envia resultado já salvo em JSON para o Langfuse."""
    if not _langfuse_disponivel():
        print("Langfuse não configurado. Nada enviado.")
        return 1
    with open(path) as f:
        resultado = json.load(f)
    experiment = enviar_experiment(resultado)
    print(f"Enviado: {experiment}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eval Langfuse 88i")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--from-file", help="Envia resultado de arquivo JSON existente")
    args = parser.parse_args()

    if args.from_file:
        sys.exit(enviar_de_arquivo(args.from_file))
    else:
        sys.exit(rodar_e_enviar(dry_run=args.dry_run))
