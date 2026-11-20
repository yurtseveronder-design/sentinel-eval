# Comparison with public prompt-injection models

Measured 2026-11-16 with `sentinel_eval.compare` (workflow `compare`) and the `benchmark` CI job, on the same three files. Threshold 0.5. CPU, GitHub-hosted runner.
Blind = 30 attacks + 25 harmless prompts, not tuned against when written but now used up (used to compare these models).

## The detector alone (public model, no Sentinel rules)

| Model | Blind catch / FP | Held-out catch / FP | Dev catch / FP | Median latency |
|---|---|---|---|---|
| `protectai/deberta-v3-base-prompt-injection` (v1) | 56.7% / 0.0% | 80.6% / 16.7% | 85.4% / 5.0% | ~124 ms |
| `protectai/deberta-v3-base-prompt-injection-v2` | 73.3% / 4.0% | 97.2% / 10.0% | 93.8% / 5.0% | ~128 ms |
| `deepset/deberta-v3-base-injection` | 93.3% / 8.0% | 97.2% / 16.7% | 91.7% / 15.0% | ~110 ms |

## The whole Sentinel stack (rules + semantic layer with that classifier)

| Configuration | Blind catch / FP | Held-out catch / FP | Dev catch / FP | Median latency |
|---|---|---|---|---|
| Default (rules + keyword, no classifier) | 10.0% / 4.0% | 69.4% / 0.0% | 89.6% / 0.0% | ~3 ms |
| + protectai v2 | 73.3% / 8.0% | 97.2% / 10.0% | 97.9% / 5.0% | ~130 ms |
| + deepset | 93.3% / 12.0% | 100% / 16.7% | 97.9% / 15.0% | ~131 ms |
| + deepset + embeddings 0.60 | 96.7% / 12.0% | 100% / 23.3% | 97.9% / 15.0% | ~167 ms |

## How to read it

* The two models trade off differently: deepset catches far more unseen attacks but blocks more harmless prompts (8-17% on these sets); protectai v2 blocks fewer harmless prompts but misses more attacks. Which is better depends on whether a missed attack or a blocked user costs more.
* **Caution about deepset:** it was trained on the public `deepset/prompt-injections` dataset. We found no exact overlap with our files, but near-paraphrases cannot be ruled out, so its blind-set score may be flattering.
* Adding the Sentinel rules on top of a classifier mostly adds false blocks here (one or two harmless prompts) rather than catches, because the classifier already catches nearly everything the rules do. The rules still matter when the classifier is off, and they are fast and explainable.
* Latency is client-side including HTTP, on a shared 2-core CPU. A classifier adds roughly 100-130 ms per request; the rules-only default is about 3 ms.
* Sets are small: one prompt moves a figure by 2-4 points.
