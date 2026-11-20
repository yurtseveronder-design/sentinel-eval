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
| `data/blind.jsonl` | 55 | **Blind set.** Not used to write rules, but since used to compare models, so it is **used up**: indicative, no longer a result on unseen data. |

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

See [RESULTS.md](RESULTS.md) for the latest dated numbers by configuration (blind-set catch rates from 10% to 97%, depending on engine, model and threshold; the blind set is used up).

## For agents and scripts

Everything an AI needs to re-check a change is a file or one command:

| Need | Where |
|---|---|
| Latest numbers, machine-readable | [`results/latest.json`](results/latest.json): every configuration on dev, held-out, blind, plus sealed runs. Says which sets are spent |
| Re-evaluate after a rule or model change | `sentinel-eval-local` (in-process, no server, JSON on stdout) |
| Known boundaries | [`data/known_gaps.jsonl`](data/known_gaps.jsonl): attacks the default stack misses and harmless prompts it blocks, each with `expect: "miss"` or `"false_block"` |

```bash
pip install "git+https://github.com/yurtseveronder-design/ai-sentinel.git" \
            "git+https://github.com/yurtseveronder-design/sentinel-semantic.git" \
            "git+https://github.com/yurtseveronder-design/sentinel-eval.git"

sentinel-eval-local --compare results/latest.json --config default --known-gaps data/known_gaps.jsonl
sentinel-eval-local --url http://localhost:8000 --api-key demo --compare results/latest.json   # a RUNNING gateway; needs no other install
sentinel-eval-local --classifier deepset/deberta-v3-base-injection        # try a model (needs the semantic [classifier] extra)
sentinel-eval-local --sealed /private/sealed.jsonl                         # aggregate numbers only, never which prompts missed
```

Exit code `0` means no regression beyond the tolerance (default 2 points) and no stale known gap. Exit `1` means either a rate got worse, or a known gap now passes: that is good news, but the list is **strict** (like an expected-failure test), so remove the fixed entries and update `results/latest.json`. Exit `2` means setup error (including a wrong key or an unreachable gateway with `--url`: those abort the run and are never scored as "allowed"). With `--url` the gateway's own configuration decides what is measured, so the numbers describe that instance.

Rules for agents: tune against dev and held-out only; the blind set is spent and the sealed set must never be tuned against ([docs/SEALED_SET.md](docs/SEALED_SET.md)).

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
