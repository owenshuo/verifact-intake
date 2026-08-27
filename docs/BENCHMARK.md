# Trust benchmark

The checked-in benchmark measures the trust-policy layer after document extraction. It does
not claim to benchmark OCR quality or an LLM. Thirty deterministic evidence variations alter
the lower-authority method, approval, and retention claims and vary the extraction confidence
of the normative evidence.

Each variation passes through the real assertion compiler, conflict detector, promotion policy,
and evidence model. The comparison baseline chooses the highest-confidence assertion for every
fact key and does not stop when sources conflict.

Run it with:

```bash
python scripts/run_trust_benchmark.py
```

## Current result

| Measure | Confidence-only baseline | VeriFact |
|---|---:|---:|
| Evidence variations | 30 | 30 |
| Expected conflict decisions | 90 | 90 |
| Unreviewed choices on conflicting facts | 90 | 0 |
| Wrong values selected on conflicting facts | 60 | 0 after review |
| Conflict recall | Not applicable | 100% |
| Expected-fact accuracy after gated review | Not gated | 100% |
| Evidence coverage after gated review | Not guaranteed | 100% |

An “unsafe conflict choice” means selecting a value while incompatible source assertions are
still unresolved. It does not mean every selected value is factually wrong. The stricter metric
is deliberate: an operational agent must not silently choose between incompatible evidence even
when it happens to guess the correct value.

The golden expected values are an evaluation oracle only. Runtime API and compiler code do not
load the golden file. The benchmark uses it after compilation to score the deterministic cases.
