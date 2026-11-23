# How we measured prompt-injection defences, and what went wrong first

This is the short story of building the Sentinel stack's benchmark, including the mistake that made the first numbers meaningless. It is written so anyone can reproduce the method with their own system.

## The mistake: scoring a system on the prompts it was written against

The first version of the rule shield scored about 100% on the benchmark prompts. It looked finished. An audit then showed that many rules and tests had been written by copying the benchmark's own wording, so the benchmark was measuring memory, not detection.

The fix was to split the data into three sets with different rules about use:

| Set | Size | How it may be used |
|---|---|---|
| Dev (`prompts.jsonl`) | 88 | Free to tune against. Optimistic by construction. |
| Held-out (`heldout.jsonl`) | 66 | Used once to check, then tuned against after the first look. Treat as optimistic too. |
| **Blind** (`blind.jsonl`) | 55 | **Was not tuned against when written, but is now used up** (it has been used to compare models). Indicative only; see the sealed set for unseen data. |

On the blind set the rules-only default caught **10%** of attacks. That was the figure on that set. The set is now used up, so treat it as a dated, indicative number, not a current result on unseen data; the READMEs quote it with its date.

## Rules that keep the numbers honest

1. **Report catch rate and false-block rate together.** A filter that blocks everything catches 100%. Harmless prompts (including hard ones: security discussions, quoted attack phrases, instruction-heavy but harmless requests) are half the benchmark.
2. **Date every number and name the commit.** Results change when code changes.
3. **Never choose a threshold on the set you report.** The training pipeline picks its threshold on a held-back validation split from the training data, then reports blind-set results at that threshold, and also at fixed thresholds so the choice can be checked.
4. **Remove overlap before training.** The dataset builder drops any training text that also appears in the eval files (after lower-casing and whitespace folding).
5. **Fail loudly.** A missing dataset, an unreachable service or a rate-limit response is an error, not a zero. One early run silently scored rate-limited requests as "allowed" and produced wrong figures; the benchmark now counts errors separately and fails if there are any.
6. **Say how small the sets are.** With 25 harmless blind prompts, one false block is 4 points. A difference of a few points between two systems is noise.

## What the numbers say (blind set, 2026-11)

| Configuration | Attacks caught | Harmless wrongly blocked |
|---|---|---|
| Rules + keyword semantic (default) | 10% | 4% |
| + embedding similarity, threshold 0.60 | 47% | 4% |
| + pretrained classifier (protectai v2) | 73% | 8% |
| + classifier + embeddings | 83% | 8% |
| Own fine-tune on public data (6,000 rows) | 73% | 4% |

Takeaways: pattern rules alone stop only classic phrasings; a trained classifier is the large step; and the public training data is easier than realistic traffic (the fine-tune scored 98% on its own validation split but 73% on blind), so further gains need data that looks like the deployment's own traffic.

## Reproduce it

```bash
pip install -e .
# with the stack running (see scripts/stack.sh):
sentinel-eval --target scan --dataset data/blind.jsonl --out reports/blind
# standalone public models on the same file:
python -m sentinel_eval.compare --model protectai/deberta-v3-base-prompt-injection-v2 --dataset data/blind.jsonl
```

Every run also writes an HTML report with latency, per-category results and the exact prompts missed.

## Limits

The sets are small and English-heavy with some other languages; the attack categories are the ones we thought of; and a benchmark can be gamed by anyone who sees it. Use these figures to compare configurations and catch regressions, not as a security guarantee.
