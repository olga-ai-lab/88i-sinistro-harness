"""
olga_bootstrap.py — cliente inicial para integrar Hermes/Olga ao 88i harness.

Uso rápido:
  python olga_bootstrap.py health
  python olga_bootstrap.py fnol --narrativa "Bati minha moto ontem" --segurado-id SEG-001
  python olga_bootstrap.py docs --protocolo 88i-2026-00000001 --file /tmp/bo.pdf
"""

from __future__ import annotations

import argparse
import json
import mimetypes
from pathlib import Path
from typing import Any

import requests


DEFAULT_BASE_URL = "https://88i-sinistro-harness.railway.app"


class OlgaHarnessClient:
    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: int = 45):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> dict[str, Any]:
        r = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def submit_fnol(self, narrativa: str, segurado_id: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"narrativa": narrativa}
        if segurado_id:
            payload["segurado_id"] = segurado_id

        r = requests.post(f"{self.base_url}/sinistro", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def submit_documents(
        self,
        protocolo: str,
        file_paths: list[Path],
        tipo_sinistro: str = "DITA",
        cobertura: str = "B_DITA",
        narrativa_resumo: str = "",
    ) -> dict[str, Any]:
        data = {
            "tipo_sinistro": tipo_sinistro,
            "cobertura": cobertura,
            "narrativa_resumo": narrativa_resumo,
        }

        files = []
        opened = []
        try:
            for p in file_paths:
                fh = p.open("rb")
                opened.append(fh)
                mime, _ = mimetypes.guess_type(str(p))
                files.append(("arquivos", (p.name, fh, mime or "application/octet-stream")))

            r = requests.post(
                f"{self.base_url}/sinistro/{protocolo}/documentos",
                data=data,
                files=files,
                timeout=max(self.timeout, 120),
            )
            r.raise_for_status()
            return r.json()
        finally:
            for fh in opened:
                fh.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Olga bootstrap client")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=45)

    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("health")

    p_fnol = sub.add_parser("fnol")
    p_fnol.add_argument("--narrativa", required=True)
    p_fnol.add_argument("--segurado-id")

    p_docs = sub.add_parser("docs")
    p_docs.add_argument("--protocolo", required=True)
    p_docs.add_argument("--file", dest="files", action="append", required=True)
    p_docs.add_argument("--tipo-sinistro", default="DITA")
    p_docs.add_argument("--cobertura", default="B_DITA")
    p_docs.add_argument("--narrativa-resumo", default="")

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    client = OlgaHarnessClient(base_url=args.base_url, timeout=args.timeout)

    if args.cmd == "health":
        out = client.health()
    elif args.cmd == "fnol":
        out = client.submit_fnol(narrativa=args.narrativa, segurado_id=args.segurado_id)
    elif args.cmd == "docs":
        out = client.submit_documents(
            protocolo=args.protocolo,
            file_paths=[Path(p) for p in args.files],
            tipo_sinistro=args.tipo_sinistro,
            cobertura=args.cobertura,
            narrativa_resumo=args.narrativa_resumo,
        )
    else:
        raise ValueError(f"Comando não suportado: {args.cmd}")

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
