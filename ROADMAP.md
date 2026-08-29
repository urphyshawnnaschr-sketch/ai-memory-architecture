# Roadmap

This roadmap describes the next public maintenance steps for AI Memory Architecture. It is intentionally focused on the repository's core scope: practical memory governance and context integrity for long-running AI work.

## Near term

### 1. English documentation baseline

- Maintain an English project overview.
- Translate the five core principles with terminology notes.
- Translate the quick-start path.
- Keep Chinese and English terminology aligned.

### 2. Reproducible examples

Add small, public examples for common failure modes:

- stale memory conflicting with a newer decision;
- duplicated progress sources drifting apart;
- context leakage between projects;
- oversized always-loaded memory reducing useful context;
- a session bookmark accidentally becoming a second source of truth.

Each example should include the initial state, failure mode, corrective pattern, and expected result.

**Progress:** pass/fail fixtures exist under `examples/integrity-check/`, and Memory Governance Benchmark V0.1 adds 16 isolated synthetic cases covering every current finding code plus invalid-manifest behavior.

### 3. Memory integrity checks

Turn the existing health-check ideas into explicit, reviewable checks such as:

- duplicate-authority detection;
- stale-reference detection;
- orphan bookmark detection;
- oversized core-memory warnings;
- unresolved contradiction review.

**Progress:** V1 is implemented as a deterministic, standard-library Python checker with unit tests, CI, a JSON Schema, and a structural regression benchmark. See `docs/06-memory-integrity-check.md` and `benchmarks/governance-v0.1/`.

Future versions should keep automation narrow and reproducible rather than turning the repository into a full agent platform.

## Medium term

### 4. Memory-layout adapters

Demonstrate that the governance contract can sit on top of existing memory systems instead of requiring a new storage backend.

- publish conservative adapters for file-based memory layouts;
- keep source-system semantics explicit rather than forcing every file into AI Memory Architecture roles;
- document which authority assignments are source-system facts and which are governance-overlay choices.

**Progress:** the first adapter targets Cline Memory Bank. It maps `projectBrief.md` to project-scope authority and `progress.md` to project-progress authority while leaving Cline's richer `activeContext.md` semantics intact.

### 5. Evaluation protocol

Define evaluation layers separately so deterministic structural checks are not confused with model behavior.

Current layer:

- Can explicit governance invariants be checked reproducibly against known-good and known-bad structures?

Future model-facing layer:

- Can a fresh session recover the current project state from the documented memory structure?
- Can it distinguish authoritative state from a historical checkpoint?
- Can it avoid loading unrelated project context?
- Can it identify stale information without reconstructing the entire history?

The goal is reproducibility and falsifiability, not model rankings. Model-facing evaluations must be reported separately from the deterministic benchmark because they introduce non-determinism.

## Community goals

- Accept field reports, including negative results.
- Add contribution templates for tool adaptations and failure-mode reports.
- Track terminology changes in the changelog.
- Keep examples free of private customer data, credentials, and personal conversation history.

## Non-goals

The roadmap does not include building a general-purpose multi-agent runtime, enterprise AI operating system, proprietary hosted memory service, autonomous orchestration framework, or another general-purpose memory database. Those remain outside this repository's scope.
