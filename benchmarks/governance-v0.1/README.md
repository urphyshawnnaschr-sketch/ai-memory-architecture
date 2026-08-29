# Memory Governance Benchmark V0.1

This benchmark is a small, synthetic regression corpus for the deterministic structural-governance layer in AI Memory Architecture.

It answers a narrow question:

> Given an explicit governance manifest, does the checker reliably detect the structural failure mode that the case declares?

It does **not** claim to measure LLM reasoning quality, semantic truth, retrieval accuracy, or whether a model would recover the correct project state from ambiguous prose.

## Run

```bash
python tools/run_governance_benchmark.py
```

Expected result on the current implementation:

```text
SUMMARY: 16/16 benchmark cases passed
```

## Coverage

The V0.1 corpus contains one clean baseline, cases covering every current finding code, and invalid-manifest cases for unsupported or unsafe declarations.

Covered finding codes:

- `MISSING_CORE_MEMORY`
- `OVERSIZED_CORE_MEMORY`
- `DUPLICATE_AUTHORITY_DOMAIN`
- `AUTHORITY_PATH_REUSED`
- `MISSING_AUTHORITY_FILE`
- `MISSING_BOOKMARK_FILE`
- `ORPHAN_BOOKMARK`
- `BOOKMARK_TARGET_MISMATCH`
- `DUPLICATE_BOOKMARK`
- `MISSING_REFERENCE_SOURCE`
- `STALE_REFERENCE`
- `UNRESOLVED_CONTRADICTION`
- `DUPLICATE_CONTRADICTION_ID`

Invalid-manifest cases additionally verify that project-root escapes and unknown governance fields are rejected rather than silently accepted.

## Why synthetic cases?

V0.1 is deliberately synthetic so each case has an unambiguous expected result. That makes it useful as a regression suite and public specification example.

A future benchmark may add model-facing recovery tasks, but those should be reported separately because model behavior introduces non-determinism and requires a different evaluation protocol.

## Case format

Each case in `cases.json` declares:

- synthetic files to create;
- a `memory-integrity.json` manifest;
- the exact finding codes or manifest error expected.

The runner creates each case in an isolated temporary directory and compares observed results with the declared ground truth.
