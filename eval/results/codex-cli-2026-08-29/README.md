# Codex CLI Recovery Pilot — 2026-08-29

Status: **first real model-facing pilot for Authoritative-State Recovery Evaluation V0.1**.

This result is intentionally reported as an initial synthetic pilot, not as a general claim that memory governance improves every model or workload.

## Run identity

| Field | Value |
|---|---|
| Pilot type | ChatGPT-authenticated Codex CLI pilot |
| Evaluation | `authoritative-state-recovery-v0.1` |
| Repository HEAD | `54f017bd0060074cf3b8331a9737bc7b8b2cb293` |
| Corpus SHA-256 | `d540524fb5c1e95a94889b45b87f9715ea8f98e3ccae6e96948a3debc967f80d` |
| Model reported by Codex CLI | `gpt-5.6-sol` |
| Reasoning effort | `medium` |
| Codex version | `codex-cli 0.150.0-alpha.12.2` |
| Cases | 8 tasks × 2 conditions = 16 executions |
| Distinct thread IDs | 16 |
| Orchestration retries | 0 |
| Codex execution failures | 0 |
| Invalid model outputs | 0 |
| Sandbox | read-only |
| CLI mode | ephemeral; no resume |
| API key inherited | false |

This was **not** an OpenAI Responses API pilot. The run used the maintainer's ChatGPT-authenticated Codex CLI session, so there is no API-returned model snapshot identifier. The model name above is the model recorded by Codex CLI.

## Aggregate result

| Condition | Score | Rate |
|---|---:|---:|
| Governed | **31 / 32** | **96.875%** |
| Ungoverned | **24 / 32** | **75.0%** |
| Difference | **+7 points** | **+21.875 percentage points** |

Four tasks improved under the governed condition, four were unchanged, and none received a lower total score.

## Per-task scores

| Task | Ungoverned | Governed | Delta |
|---|---:|---:|---:|
| `stale_bookmark_after_plan_change` | 3 / 4 | 4 / 4 | +1 |
| `historical_progress_copy` | 4 / 4 | 4 / 4 | 0 |
| `cross_project_leakage` | 4 / 4 | 4 / 4 | 0 |
| `superseded_architecture_decision` | 3 / 4 | 3 / 4 | 0 |
| `checkpoint_became_second_status` | 2 / 4 | 4 / 4 | +2 |
| `old_handoff_after_scope_reduction` | 4 / 4 | 4 / 4 | 0 |
| `completed_blocker_still_in_notes` | 2 / 4 | 4 / 4 | +2 |
| `archived_migration_plan` | 2 / 4 | 4 / 4 | +2 |

## Metric-level difference

The 7-point aggregate difference is not evenly distributed across the four metrics:

| Metric | Ungoverned | Governed | Delta |
|---|---:|---:|---:|
| State accuracy | 6 / 8 | 7 / 8 | +1 |
| Authority citation accuracy | 8 / 8 | 8 / 8 | 0 |
| Safe evidence selection | 5 / 8 | 8 / 8 | +3 |
| Stale/non-authoritative path identification | 5 / 8 | 8 / 8 | +3 |

The clearest observed effect in this pilot was therefore **not simply getting the headline state right**. It was avoiding stale/supporting documents as current evidence and correctly classifying non-authoritative context.

Three tasks show this pattern directly:

- `checkpoint_became_second_status`
- `completed_blocker_still_in_notes`
- `archived_migration_plan`

In all three, the ungoverned run identified the current state and authority path correctly but also treated a non-authoritative supporting file as current evidence and failed to classify it as stale/non-authoritative. The governed condition scored all four metrics correctly.

## Scorer caveat: exact state-text matching

Recovery Evaluation V0.1 deliberately uses a strict deterministic scorer. `state_accuracy` requires the returned `current_state` to equal the pre-declared ground-truth text after whitespace normalization. It does **not** perform semantic-equivalence judging.

That matters when interpreting the +1 state-accuracy difference:

- For `stale_bookmark_after_plan_change`, the ungoverned output selected Plan C correctly but added the true explanatory clause `Plan B was superseded after load testing.` The strict V0.1 scorer therefore assigned `state_accuracy = 0` because the full string did not exactly match the ground truth.
- For `superseded_architecture_decision`, both conditions returned `PostgreSQL`, while the pre-declared state was a fuller sentence. Both conditions therefore received `state_accuracy = 0`; this did not affect the governed-vs-ungoverned difference.

For that reason, the strongest result from this pilot is the **+6 combined points in evidence selection and stale-path classification**, not a claim of a universal 21.875% improvement in semantic state understanding.

The V0.1 scorer is left unchanged after the pilot. Any semantic-equivalence scorer must be introduced as a separately versioned evaluation rather than changing the scoring rule after seeing results.

## Evidence audit

The retained local run archive was audited before publication of this summary.

Observed execution properties:

- 16 generated prompt files for 16 executions;
- 16 distinct Codex thread IDs;
- ephemeral CLI execution with no resume;
- no orchestration retries;
- read-only sandbox;
- no inherited `OPENAI_API_KEY`;
- every saved raw output was valid JSON;
- saved raw-output SHA-256 values matched the recorded summary;
- final model output recorded in the execution event stream matched the saved `raw-output.txt` for each case;
- each governed/ungoverned task pair used the same question, project documents, and output schema;
- the intended experimental variable was the governance section: the governed condition explicitly declared authority/non-authority, while the ungoverned condition required the model to infer authority from the documents.

The checked-in `run.json` and `summary.json` are copied from the retained run evidence without changing the recorded scores. The full local evidence archive also contains prompts, raw outputs, event streams, commands, scorer outputs, and exit records.

## What this pilot supports

A careful interpretation is:

> In this initial 8-task synthetic Codex CLI pilot, an explicit memory-governance contract was associated with better deterministic recovery scores, with the clearest difference in safe evidence selection and stale/non-authoritative context classification.

This is consistent with the project's narrower thesis: an AI can often infer the correct current state without governance, yet still mix historical or supporting context into the evidence it treats as current.

## What this pilot does not prove

This result does **not** establish:

- a general 21.875% model-performance improvement;
- statistical significance across repeated samples;
- improvement across other models, providers, temperatures, reasoning settings, or real customer workloads;
- semantic truth detection;
- production safety;
- superiority over Mem0, Letta, Cline, Basic Memory, or other memory systems.

The corpus contains only 8 synthetic tasks, the pilot uses one model/configuration, and each condition was executed once per task.

## Public evidence in this directory

- [`run.json`](run.json) — run identity and execution settings.
- [`summary.json`](summary.json) — aggregate/per-case deterministic scores, output hashes, thread IDs, and failure counts.

The underlying task corpus, prompt generator, and deterministic scorer remain versioned in the repository, so the 16 prompts can be regenerated from the recorded repository HEAD and corpus.
