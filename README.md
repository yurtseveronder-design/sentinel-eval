# sentinel-eval

Measures how well the Sentinel stack ([ai-sentinel](https://github.com/yurtseveronder-design/ai-sentinel) +
[sentinel-semantic](https://github.com/yurtseveronder-design/sentinel-semantic) +
[sentinel-ui](https://github.com/yurtseveronder-design/sentinel-ui)) separates attacks from normal prompts.

Two numbers matter:

| Metric | Meaning | Want |
|---|---|---|
| **Catch rate** | share of attack prompts that were blocked | high |
| **False-block rate** | share of harmless prompts that were blocked | low |

## Datasets

| File | Prompts | Purpose |
|---|---|---|
| `data/prompts.jsonl` | 88 | **Dev set.** Rules are tuned against it, and it gates CI via `baseline.json`. |
| `data/heldout.jsonl` | 66 | Held-out when first written, but later tuned against, so treat it as a second dev set. |
| `data/blind.jsonl` | 55 | **Blind set.** Never tuned against. This is the honest generalisation number; do not fit rules to it. |

Dev-set scores are optimistic by construction. Quote the blind-set number when you describe detection quality.

### Dev set layout (88 prompts, 8 per category)

- Attacks: `direct_injection`, `prompt_leak`, `jailbreak_roleplay`, `obfuscated`, `multilingual`, `indirect_injection`
- Benign: `general`, `business`, `code`, plus two hard-negative groups, `security_talk` and `instruction_words`, which use words like "ignore", "password" and "override" innocently

Add a line per prompt (`id`, `label`, `category`, `text`). Ids must be unique.

## Run

```bash
pip install -e .
sentinel-eval --target scan      # ai-sentinel /v1/scan   (SENTINEL_URL, SENTINEL_API_KEY)
sentinel-eval --target gateway   # whole stack via sentinel-ui (UI_URL, UI_API_KEY)
```

Writes `reports/<target>.json` and `.md`, and lists every missed attack and wrongly blocked prompt by id.

## Results

See [RESULTS.md](RESULTS.md) for the latest dated numbers by configuration (blind-set catch rates from 10% to 73%, depending on engine and threshold).

## Regression gate

`baseline.json` holds the accepted catch and false-block rates. CI fails if the catch rate drops, or the
false-block rate rises, by more than 2 points. After an intended improvement, refresh it:

```bash
sentinel-eval --write-baseline baseline.json
```

If `baseline.json` is absent, CI only reports. Commit one after the first green run.

## CI

`unit` tests the harness against a stub server. `benchmark` checks out the three services, starts them with
`scripts/stack.sh`, runs both targets and uploads the reports and service logs.

## Limits

The dataset is small and hand-written, so treat results as a regression signal rather than a security guarantee.
A request that errors (service down, bad key) is counted as an error and fails the run, never as a pass.
