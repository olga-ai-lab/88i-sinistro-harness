import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from olga_adapter import map_harness_to_olga, validate_olga_output

samples = json.loads((ROOT / 'tests_olga_adapter_samples.json').read_text())
for i, case in enumerate(samples, start=1):
    out = map_harness_to_olga(case['input'])
    validate_olga_output(out)
    print(f"case {i}: ok -> {out['intent']} / {out['next_action']}")
