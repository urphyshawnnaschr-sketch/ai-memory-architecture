# OpenAI Recovery Pilot Runner V0.1

This is the first provider-specific execution adapter for the provider-neutral [Authoritative-State Recovery Evaluation V0.1](09-authoritative-state-recovery-eval.md).

It uses the OpenAI **Responses API** to run the existing 8 tasks under both evaluation conditions:

- `ungoverned`
- `governed`

The underlying documents and deterministic scorer are unchanged.

## What this runner does

For a full run, the runner makes 16 independent API requests (8 tasks x 2 conditions). It saves evidence locally for every case:

- exact rendered prompt;
- request payload (never the API key);
- raw Responses API JSON;
- literal model output text;
- parsed model-output JSON when valid;
- deterministic score;
- aggregate governed/ungoverned results.

It also records:

- requested model;
- model identifier returned by the API when present;
- reasoning effort;
- corpus SHA-256;
- repository commit when available;
- deterministic shuffled order/seed;
- start/end timestamps;
- API and output-format failures.

## Security and evidence hygiene

Set the API key only through the environment:

```bash
export OPENAI_API_KEY="..."
```

On PowerShell:

```powershell
$env:OPENAI_API_KEY = "..."
```

The runner never writes the key to request, response, metadata, or score files.

Local run evidence is written under `eval-runs/` by default. That directory is gitignored so a pilot is **not published accidentally**.

Review the evidence before intentionally publishing any result.

## Dry run first

A dry run creates the exact shuffled run plan and all prompt/request files without making API calls:

```bash
python tools/openai_recovery_pilot.py --dry-run
```

For a small plumbing check:

```bash
python tools/openai_recovery_pilot.py --dry-run --limit 2
```

A limited run is never marked as a complete pilot.

## Full OpenAI pilot

Current default model in the runner:

```text
gpt-5.6-sol
```

Run all 16 cases:

```bash
python tools/openai_recovery_pilot.py --model gpt-5.6-sol
```

You can explicitly choose another model without changing the evaluation corpus or scorer:

```bash
python tools/openai_recovery_pilot.py --model <model-id>
```

The model identifier is recorded in the run evidence. A published result must always state the exact model used.

## No hidden retries

V0.1 deliberately performs **no automatic retry**.

Why: silently retrying an API/model failure until a valid answer appears would bias the pilot toward success and weaken reproducibility.

An API failure is saved as `api-error.json` and receives a zero-point case record for that attempted run. A researcher may run a new, separately recorded pilot later, but must not overwrite the failed evidence and describe the replacement as the same run.

## Strict output handling

The task asks the model for literal JSON only.

If a model returns a Markdown code fence, prose around the JSON, missing keys, or otherwise invalid output, the runner does **not** repair it. The raw text remains evidence and the case is recorded as an invalid model output.

This keeps V0.1 scoring deterministic.

## Result layout

Default path:

```text
eval-runs/openai/<timestamp>_<model>_seed<seed>/
```

Top-level files:

- `run.json` — pre-run metadata and protocol choices;
- `summary.json` — aggregate scores and all case records.

Each case directory contains the prompt, request, raw response (when available), model output, and score.

## Interpretation boundary

A successful API run is **not automatically evidence that governance helps**.

Before making that claim:

1. confirm all 16 cases were attempted under the same model/settings;
2. confirm `complete_full_pilot` is true;
3. inspect API/format failures rather than hiding them;
4. compare governed and ungoverned scores for the same corpus;
5. preserve per-task results, including tasks where governance had no effect or performed worse;
6. publish exact repository/corpus/model bindings and limitations.

Issue #6 remains the authority for the model-facing research question and publication acceptance criteria.

## CI boundary

Public GitHub Actions should only exercise `--dry-run` and unit tests.

The repository does not require, expect, or read an OpenAI API key in normal CI. A paid model pilot is an explicit maintainer action, not an automatic pull-request side effect.
