# Authoritative-State Recovery Evaluation V0.1

This evaluation is the first **model-facing** layer in AI Memory Architecture.

It is separate from Memory Governance Benchmark V0.1:

- **Governance Benchmark V0.1** tests deterministic checker behavior against known structural failures.
- **Recovery Evaluation V0.1** prepares controlled prompts for an AI model and measures whether it recovers the currently authoritative state from conflicting project context.

No model results are included yet. This repository does not claim an improvement until a reproducible pilot run is completed and published.

## Research question

Given the same conflicting project documents, does adding an explicit governance contract improve recovery of the current authoritative state?

Each underlying task is rendered in two conditions:

1. `ungoverned` — the model receives the documents but no explicit authority contract;
2. `governed` — the model receives the same documents plus the declared authority domain/path and non-authoritative paths.

The documents do not change between conditions.

## Corpus

`eval/recovery-v0.1/tasks.json` contains 8 synthetic tasks covering failure patterns such as:

- stale bookmarks after a plan change;
- historical progress copies;
- cross-project context leakage;
- superseded architecture decisions;
- checkpoints that became a second status source;
- old handoffs after scope reduction;
- blockers that have already been resolved;
- archived migration plans that are no longer current.

All ground truth is declared before a model is run.

Machine-readable corpus schema:

`spec/recovery-eval-v0.1.schema.json`

## Required model output

Models are instructed to return JSON only:

```json
{
  "current_state": "...",
  "authority_path": "...",
  "current_evidence_paths": ["..."],
  "stale_or_non_authoritative_paths": ["..."]
}
```

The scorer rejects missing or unknown keys.

## Metrics

Each task/condition receives four binary points:

1. **State accuracy** — `current_state` matches the pre-declared ground truth after whitespace normalization.
2. **Authority citation accuracy** — `authority_path` matches the authoritative path.
3. **Safe evidence selection** — the authority is used as current evidence and no known stale/non-authoritative path is used as current evidence.
4. **Stale-path identification** — the returned stale/non-authoritative path set exactly matches the declared set.

Maximum score: `4` points per task-condition.

The initial scorer is deliberately strict. If a future revision needs semantic-equivalence judging, that must be versioned separately instead of silently changing V0.1 scoring.

## Generate prompts

List tasks:

```bash
python tools/recovery_eval.py list
```

Render one prompt:

```bash
python tools/recovery_eval.py prompt stale_bookmark_after_plan_change governed
```

Generate all 16 prompts:

```bash
python tools/recovery_eval.py bundle /tmp/recovery-prompts
```

The bundle includes a `manifest.json` mapping task IDs and conditions to prompt files.

## Score a model output

Save a model response as JSON, then run:

```bash
python tools/recovery_eval.py score stale_bookmark_after_plan_change governed output.json
```

The scorer prints structured metric results.

## Self-test

```bash
python tools/recovery_eval.py selftest
```

The self-test verifies that:

- pre-declared oracle outputs receive perfect scores for all 8 tasks in both conditions;
- a deliberately wrong output does not receive a perfect score.

This validates the corpus/scorer plumbing. It is **not** evidence that any AI model performs well.

## Pilot-run requirements

A real model-facing result should not be published until the run records at least:

- exact corpus version/commit;
- exact model identifier;
- condition (`governed` or `ungoverned`);
- raw prompts;
- raw structured outputs where licensing/privacy permits;
- scorer version/commit;
- aggregate and per-task results;
- limitations and failures, including null or negative results.

The same model should be tested on both conditions before interpreting the governance effect.

## Non-goals

V0.1 does not:

- call any model provider automatically;
- rank model vendors;
- claim semantic truth detection;
- prove production safety;
- prove that governance improves every model;
- process private user or customer memory.

The provider-neutral design is intentional: the corpus and scorer should remain usable with Codex, Claude, local models, or future systems without changing the benchmark definition.
