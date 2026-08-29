# Roadmap

This roadmap describes the next public maintenance steps for AI Memory Architecture. It is intentionally focused on the repository's core scope: practical memory and context management for long-running AI work.

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

**Progress:** the first passing and deliberately failing fixtures are implemented under `examples/integrity-check/` as part of Memory Integrity Check V1. More single-failure examples can be added independently.

### 3. Memory integrity checks

Turn the existing health-check ideas into explicit, reviewable checks such as:

- duplicate-authority detection;
- stale-reference detection;
- orphan bookmark detection;
- oversized core-memory warnings;
- unresolved contradiction review.

**Progress:** V1 is implemented as a deterministic, standard-library Python checker with unit tests and CI. See `docs/06-memory-integrity-check.md`.

Future versions should keep automation narrow and reproducible rather than turning the repository into a full agent platform.

## Medium term

### 4. Tool adaptation notes

Document how the same methodology maps onto several classes of AI tools:

- file-capable coding agents;
- project/workspace assistants;
- chat assistants with built-in memory;
- stateless chat systems.

These are adaptations of one methodology, not separate product-specific forks.

### 5. Evaluation protocol

Define a lightweight evaluation protocol for questions such as:

- Can a fresh session recover the current project state from the documented memory structure?
- Can it distinguish authoritative state from a historical checkpoint?
- Can it avoid loading unrelated project context?
- Can a user identify and remove stale information without reconstructing the entire history?

The goal is reproducibility and falsifiability, not model rankings.

## Community goals

- Accept field reports, including negative results.
- Add contribution templates for tool adaptations and failure-mode reports.
- Track terminology changes in the changelog.
- Keep examples free of private customer data, credentials, and personal conversation history.

## Non-goals

The roadmap does not include building a general-purpose multi-agent runtime, enterprise AI operating system, proprietary hosted memory service, or autonomous orchestration framework. Those remain outside this repository's scope.
