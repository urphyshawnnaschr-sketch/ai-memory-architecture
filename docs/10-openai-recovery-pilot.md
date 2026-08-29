# OpenAI Recovery Pilot Runner V0.1

This is the first provider-specific execution adapter for the provider-neutral [Authoritative-State Recovery Evaluation V0.1](09-authoritative-state-recovery-eval.md).

It uses the OpenAI **Responses API** to run the existing 8 tasks under both evaluation conditions:

- `ungoverned`
- `governed`

The underlying documents and deterministic scorer are unchanged.

## What this runner does

For a full run, the runner makes 16 independent API requests (8 tasks x 2 conditions). It saves evidence for every case:

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

The API key must be provided only through `OPENAI_API_KEY`.

Local shell example:

```bash
export OPENAI_API_KEY="..."
```

PowerShell:

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

## Full OpenAI pilot — local execution

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

## Full OpenAI pilot — manual GitHub Actions execution

The repository also provides a separate workflow:

```text
openai-recovery-pilot
```

It is **manual only** (`workflow_dispatch`). Normal pushes and pull requests do not start paid API calls.

To use it:

1. Configure the repository Actions secret named `OPENAI_API_KEY`.
2. Open GitHub Actions and select `openai-recovery-pilot`.
3. Choose **Run workflow**.
4. Confirm the exact model and reasoning effort.
5. Explicitly enable the paid-run confirmation checkbox.
6. After completion, download the `openai-recovery-pilot-<run-id>` artifact and inspect `summary.json` plus per-case evidence.

The workflow refuses to run the pilot job unless the explicit paid-run confirmation is true. It also checks that the repository secret exists before invoking the runner.

Evidence is uploaded even when the runner reports an API or invalid-output failure, so a failed attempt is not silently lost. The artifact is retained for 14 days by default.

Because the corpus is synthetic/public, the workflow does not require private customer or personal memory. Do not modify it to place private memory, credentials, or customer data into evaluation artifacts.

## No hidden retries

V0.1 deliberately performs **no automatic retry**.

Why: silently retrying an API/model failure until a valid answer appears would bias the pilot toward success and weaken reproducibility.

An API failure is saved as `api-error.json` and receives a zero-point case record for that attempted run. A researcher may run a new, separately recorded pilot later, but must not overwrite the failed evidence and describe the replacement as the same run.

## Strict output handling

The task asks the model for literal JSON only.

If a model returns a Markdown code fence, prose around the JSON, missing keys, or otherwise invalid output, the runner does **not** repair it. The raw text remains evidence and the case is recorded as an invalid model output.

This keeps V0.1 scoring deterministic.

## Result layout

Default local path:

```text
eval-runs/openai/<timestamp>_<model>_seed<seed>/
```

Top-level files:

- `run.json` — pre-run metadata and protocol choices;
- `summary.json` — aggregate scores and all case records.

Each case directory contains the prompt, request, raw response (when available), model output, and score.

The manual GitHub Actions path writes the same evidence layout into the uploaded artifact.

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

Normal public CI exercises only `--dry-run` and unit tests.

The separate credentialed workflow is manual-only and requires both a repository secret and an explicit paid-run confirmation. A model pilot is therefore a deliberate maintainer action, not an automatic pull-request side effect.
