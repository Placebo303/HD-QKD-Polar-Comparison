# Route B M1 Acceptance — V18-B1 q=4 DE reproduction

Status: READY (awaiting M1 run completion)

## Commands

```bash
# Read reproduction verdict
python -c "import json; d=json.load(open(r'workspace\nbldpc_v18_b1_exec_q4\repro.json', encoding='utf-8')); print(json.dumps(d['reproduction'], indent=2)); print('best_lambda=', d['result']['best_lambda'])"

# Recompute verdict independently
python -c "import json; d=json.load(open(r'workspace\nbldpc_v18_b1_exec_q4\repro.json', encoding='utf-8')); tp=d['result']['threshold_proxy']; delta=None if tp is None else abs(float(tp)-0.069); v='NO_THRESHOLD' if tp is None else ('PASS' if delta<=0.012 else 'FAIL'); print('threshold_proxy=', tp); print('delta=', delta); print('recomputed verdict=', v)"
```

## Acceptance
- `de_search/run_complete.json` exists (strict replay marker).
- `repro.json` embedded `plan` equals `pre_run_plan.json` (seed `2026081602`).
- `PASS` iff `threshold_proxy` is not None and `|threshold_proxy - 0.069| <= 0.012`.

## M2 start (only after M1 PASS)
```bash
python -m comparison_bench.src.comparison_bench.cli.run_v18_b2_structured_de --out-dir workspace/nbldpc_v18_b2_plan
```
