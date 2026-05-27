"""
observability.py — Langfuse fail-open wrapper

Por que fail-open (e não fail-closed como no agente):
    Observabilidade é ortogonal à decisão de negócio. O agente já tem
    fail-closed pra compliance SUSEP (confiança < 0.6 → humano).
    Langfuse é pra debugar; se cair, não pode derrubar sinistro.

Comportamento:
    - Lê LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST do ambiente.
    - Se falta alguma das duas chaves → disabled; `observe` vira no-op.
    - Se o init do client falhar (chaves válidas mas Langfuse fora do ar,
      erro de rede, ou versão incompatível), o módulo vira disabled até
      o próximo restart do processo. Não há retry automático — reinicializar
      é responsabilidade do orquestrador (Inngest/Railway). Simples é melhor;
      circuit breaker seria overkill pra Semana 2.
    - NUNCA levanta exceção pra fora — princípio fail-open.

Contrato público:
    observe(name=None, as_type=None)  → decorator (delega ou no-op)
    flush()                            → force flush seguro em shutdown
    is_enabled()                       → bool pra healthcheck

Uso esperado (Commit 3):
    from observability import observe
    @observe(name="extrair_sinistro", as_type="generation")
    def no_extrair(state): ...
"""
from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# ============================================================
# Estado interno — inicializado uma vez no import
# ============================================================

_LANGFUSE_CLIENT: Any = None
_LANGFUSE_OBSERVE: Optional[Callable] = None
_ENABLED: bool = False


def _init_langfuse() -> None:
    """
    Tenta inicializar o client do Langfuse. Chamado uma única vez no import.
    Se falhar por qualquer motivo, deixa o módulo em modo disabled.
    """
    global _LANGFUSE_CLIENT, _LANGFUSE_OBSERVE, _ENABLED

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        logger.warning(
            "Langfuse desabilitado: LANGFUSE_PUBLIC_KEY e/ou "
            "LANGFUSE_SECRET_KEY ausentes. Observabilidade em modo no-op."
        )
        return

    try:
        from langfuse import Langfuse, observe as langfuse_observe

        _LANGFUSE_CLIENT = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        _LANGFUSE_OBSERVE = langfuse_observe
        _ENABLED = True
        logger.info("Langfuse habilitado (host=%s)", host)
    except Exception as exc:
        # Chaves presentes mas init falhou (rede, formato inválido,
        # versão incompatível). Fail-open: módulo continua utilizável,
        # apenas sem telemetria até o próximo restart do processo.
        logger.error(
            "Langfuse init falhou, seguindo sem telemetria: %s", exc
        )
        _LANGFUSE_CLIENT = None
        _LANGFUSE_OBSERVE = None
        _ENABLED = False


# ============================================================
# API pública
# ============================================================

def observe(
    name: Optional[str] = None,
    as_type: Optional[str] = None,
) -> Callable:
    """
    Decorator de observabilidade. Se Langfuse estiver habilitado, delega
    para `langfuse.observe`. Caso contrário, retorna a função original
    sem modificação (no-op transparente).

    Args:
        name: nome do span/generation no dashboard. Default: nome da função.
        as_type: "generation" (chamadas LLM) ou "span" (orquestração).
                 None → default do Langfuse (span).
    """
    def decorator(func: Callable) -> Callable:
        if _ENABLED and _LANGFUSE_OBSERVE is not None:
            kwargs: dict[str, Any] = {}
            if name is not None:
                kwargs["name"] = name
            if as_type is not None:
                kwargs["as_type"] = as_type
            try:
                return _LANGFUSE_OBSERVE(**kwargs)(func)
            except Exception as exc:
                logger.error(
                    "Langfuse observe() falhou ao decorar %s: %s — "
                    "usando no-op",
                    func.__name__, exc,
                )
                # cai no wrapper no-op abaixo

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper

    return decorator


def flush() -> None:
    """
    Força flush dos eventos pendentes. Safe em shutdown — nunca levanta.
    """
    if not _ENABLED or _LANGFUSE_CLIENT is None:
        return
    try:
        _LANGFUSE_CLIENT.flush()
        logger.info("Langfuse flush OK")
    except Exception as exc:
        logger.error("Langfuse flush falhou: %s", exc)


def is_enabled() -> bool:
    """True se Langfuse foi inicializado com sucesso."""
    return _ENABLED


# ============================================================
# Init eager no import
# ============================================================

_init_langfuse()
