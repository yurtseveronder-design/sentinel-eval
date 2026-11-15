# Results

Measured **2026-11-14** (rows with a classifier: **2026-11-15**) by the `benchmark` CI job against `main` of ai-sentinel (`a2d574c`), sentinel-semantic (`1312dd5`)
and sentinel-ui (`0346679`). Catch rate = attacks blocked; false-block rate = harmless prompts blocked.

| Configuration | Dev (88) catch / FP | Held-out (66) catch / FP | **Blind (55) catch / FP** |
|---|---|---|---|
| Rules + keyword semantic (default) | 89.6% / 0.0% | 69.4% / 0.0% | **10.0% / 4.0%** |
| Rules + embedding semantic, threshold 0.70 | 89.6% / 0.0% | 75.0% / 0.0% | **23.3% / 0.0%** |
| Rules + embedding semantic, threshold 0.60 | 91.7% / 2.5% | 80.6% / 6.7% | **46.7% / 4.0%** |
| Rules + embedding semantic, threshold 0.50 | 97.9% / 10.0% | 91.7% / 16.7% | **73.3% / 4.0%** |
| Rules + trained classifier (`protectai/deberta-v3-base-prompt-injection-v2`), threshold 0.50 or 0.90 | 97.9% / 5.0% | 97.2% / 10.0% | **73.3% / 8.0%** |
| Rules + classifier 0.50 + embedding 0.60 | 97.9% / 5.0% | 97.2% / 16.7% | **83.3% / 8.0%** |

Embedding runs use `paraphrase-multilingual-MiniLM-L12-v2`. Through sentinel-ui the default configuration gives the same
numbers as calling ai-sentinel directly (89.6% / 0.0% on the dev set).

## How to read this

* Only the **blind** column says how the system treats wording it has not seen. Dev and held-out were used while writing
  rules and anchors, so they are optimistic.
* There is a trade-off, not a free win: lowering the threshold catches more but also blocks more harmless prompts
  (10-17% on the harder sets at 0.50). At 0.60 roughly half of unseen attacks are caught at a cost of a few percent
  false blocks.
* The default (keyword) configuration catches about 1 in 10 unseen attacks. The pretrained classifier is the big step:
  73-83% of unseen attacks, including other languages, for 2 of 25 harmless blind prompts blocked (8%). Both of those are
  in the hard-negative groups (security discussion, instruction words). The classifier is a public pretrained model that
  sentinel-semantic loads; it was not trained or tuned here, and the threshold barely matters because it is very confident.
* 25 harmless blind prompts means one false block is 4 points; treat 8% as roughly 2-20%.
* 55-88 prompts per set is small; one prompt moves a rate by 1-4 points.

## Next steps that the numbers support

1. Fine-tune or distil a classifier on a larger labelled set with more hard negatives, evaluated on this blind set, to cut the false blocks that remain.
2. More hard negatives, because false blocks rise fastest as the threshold falls.
3. Re-run and update this file whenever ai-sentinel or sentinel-semantic changes detection.
