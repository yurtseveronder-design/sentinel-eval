# Results

Measured **2026-11-14** by the `benchmark` CI job against `main` of ai-sentinel (`a2d574c`), sentinel-semantic (`1312dd5`)
and sentinel-ui (`0346679`). Catch rate = attacks blocked; false-block rate = harmless prompts blocked.

| Configuration | Dev (88) catch / FP | Held-out (66) catch / FP | **Blind (55) catch / FP** |
|---|---|---|---|
| Rules + keyword semantic (default) | 89.6% / 0.0% | 69.4% / 0.0% | **10.0% / 4.0%** |
| Rules + embedding semantic, threshold 0.70 | 89.6% / 0.0% | 75.0% / 0.0% | **23.3% / 0.0%** |
| Rules + embedding semantic, threshold 0.60 | 91.7% / 2.5% | 80.6% / 6.7% | **46.7% / 4.0%** |
| Rules + embedding semantic, threshold 0.50 | 97.9% / 10.0% | 91.7% / 16.7% | **73.3% / 4.0%** |

Embedding runs use `paraphrase-multilingual-MiniLM-L12-v2`. Through sentinel-ui the default configuration gives the same
numbers as calling ai-sentinel directly (89.6% / 0.0% on the dev set).

## How to read this

* Only the **blind** column says how the system treats wording it has not seen. Dev and held-out were used while writing
  rules and anchors, so they are optimistic.
* There is a trade-off, not a free win: lowering the threshold catches more but also blocks more harmless prompts
  (10-17% on the harder sets at 0.50). At 0.60 roughly half of unseen attacks are caught at a cost of a few percent
  false blocks.
* The default (keyword) configuration catches about 1 in 10 unseen attacks. Anyone relying on it for protection should
  turn on the embedding engine and choose a threshold from this table, or add a trained classifier.
* 55-88 prompts per set is small; one prompt moves a rate by 1-4 points.

## Next steps that the numbers support

1. A trained classifier on a larger labelled set (public prompt-injection datasets), evaluated on this blind set.
2. More hard negatives, because false blocks rise fastest as the threshold falls.
3. Re-run and update this file whenever ai-sentinel or sentinel-semantic changes detection.
