"""
olga_run_flow.py — fluxo FNOL + adaptação Olga em uma execução.

Exemplos:
  python olga_run_flow.py --narrativa "Bati minha moto ontem" --segurado-id SEG-001
  python olga_run_flow.py --narrativa "..." --segurado-id SEG-001 --save-harness-json out.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from olga_adapter import map_harness_to_olga, validate_olga_output
from olga_bootstrap import OlgaHarnessClient, DEFAULT_BASE_URL


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run FNOL flow and emit Olga output")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--timeout", type=int, default=45)
    p.add_argument("--narrativa", required=True)
    p.add_argument("--segurado-id")
    p.add_argument("--save-harness-json")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    client = OlgaHarnessClient(base_url=args.base_url, timeout=args.timeout)

    harness_output = client.submit_fnol(narrativa=args.narrativa, segurado_id=args.segurado_id)

    if args.save_harness_json:
        Path(args.save_harness_json).write_text(
            json.dumps(harness_output, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    olga_output = map_harness_to_olga(harness_output)
    validate_olga_output(olga_output)

    print(json.dumps(olga_output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
