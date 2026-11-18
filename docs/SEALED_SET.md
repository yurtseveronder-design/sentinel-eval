# Sealed set

The 55-prompt blind set was used to compare and rank models, so it no longer counts as unseen data. A new set of 60 prompts (30 attacks, 30 harmless) was written on 2026-11-18 to replace it for reporting.

**The prompts are not in this repository.** Publishing them would let anyone, including us, tune against them. Only a fingerprint is published, so a later claim can be checked against the same file:

```
sealed.jsonl  SHA-256  c98d60af8f2aa469bc96105917fa5cc18af341840543b1343d0da00dfbca4083
```

Check a copy with `sha256sum sealed.jsonl`. The file is kept privately by the repository owner.

## Rules

1. Never tune rules, thresholds or model choice against it, and never read which prompts were missed. Look at aggregate rates only.
2. Run it only to report a result for a finished configuration, and note each run here.
3. If it is ever used to choose between options, it is spent: write a new one and publish the new hash.
4. To run it: `sentinel-eval --dataset /path/to/sealed.jsonl --out reports`.

## Honest limits

- **Author:** it was written by Claude (the assistant that also helped write the rules), not by an independent person. Blind spots can be shared. A set written by someone else would be stronger.
- It has 60 prompts, so one prompt moves a rate by about 3 points. Treat results as indicative.
- Exact-text overlap with the dev, held-out and blind sets was checked: none. Near-paraphrases were not checked.
- Categories: direct injection, prompt leak, role-play jailbreak, multilingual (French, German, Portuguese, Italian, Japanese), obfuscated, indirect; harmless business, code, instruction-words, security talk, general, multilingual.

## Runs

| Date | Configuration | Attacks blocked | Harmless wrongly blocked |
|---|---|---|---|
| 2026-11-18 | Default (rules + keyword semantic) | 30% (9 of 30) | 3% (1 of 30) |

The classifier configurations have not been run on it yet.
