# AI Memory Architecture

> A practical, tool-agnostic methodology and governance layer for keeping long-running AI context coherent, portable, and auditable.

**Chinese documentation:** [README.md](README.md)

## What this project is

AI Memory Architecture is an open methodology, reusable template set, and small deterministic checker for organizing persistent context across AI assistants and coding agents.

It is intentionally **not a memory database, retrieval engine, agent runtime, or enterprise AI operating system**. The project focuses on a narrower problem: once memory exists, how do you keep active project state internally consistent?

It was derived from sustained real-world use of AI assistants across multiple projects and tools.

## The problem

Long-running AI work tends to fail in predictable ways:

- important context is scattered across conversations and files;
- stale notes compete with newer decisions;
- several projects leak context into one another;
- progress is duplicated in multiple places and becomes inconsistent;
- a checkpoint quietly turns into a second source of truth;
- switching AI tools means rebuilding context from scratch.

This repository treats those as **memory-governance and information-architecture problems**, not merely storage or retrieval problems.

## Where this fits

There are already strong open-source memory systems: Mem0, Letta/MemGPT, LangMem, Basic Memory, Cline/Roo memory-bank patterns, Graphiti/Zep, MemoryWiki, and other Markdown-based cross-agent memory projects.

This project does **not** claim to have invented persistent memory, Markdown memory banks, Git-tracked context, or cross-agent handoff.

Its narrower thesis is:

> Storage answers **where memory lives**. Retrieval answers **which memory to fetch**. AI Memory Architecture asks **which state is authoritative and whether the memory structure is internally consistent**.

See [Prior Art and Project Positioning](docs/07-prior-art-and-positioning.md) for the detailed comparison.

## Five core principles

1. **Single source of progress** — keep authoritative progress in one place; everything else points to it.
2. **Minimal core memory** — keep always-loaded context small and stable.
3. **Codename-triggered routing** — use a lightweight trigger table to select the relevant context domain.
4. **Linked checkpoints** — session bookmarks should point back to authoritative worklogs instead of duplicating them.
5. **Periodic pruning** — stale memory must be reviewed and removed before it becomes contradictory context.

## Deterministic structural checks

Memory Integrity Check V1 turns part of the methodology into machine-checkable invariants.

It currently checks for:

- duplicate authority domains;
- authority paths reused across domains;
- missing authority/core/bookmark/reference files;
- orphan or mismatched bookmarks;
- duplicate bookmarks;
- stale references;
- unresolved or duplicate contradiction IDs;
- oversized core memory;
- path aliases and project-root escapes;
- unknown manifest fields.

The checker is local, deterministic, uses only the Python standard library, and does not send memory contents to an external model.

- [Memory Integrity Check V1](docs/06-memory-integrity-check.md)
- [Manifest JSON Schema](spec/memory-integrity-manifest-v1.schema.json)
- [Reproducible pass/fail fixtures](examples/integrity-check/README.md)

## Benchmark and interoperability

The project now includes two additional pieces that test whether the governance layer is more than a repository-specific convention:

- [Memory Governance Benchmark V0.1](benchmarks/governance-v0.1/README.md) — 16 synthetic, deterministic cases covering every current finding code plus invalid-manifest behavior. It is a structural regression benchmark, not an LLM leaderboard.
- [Cline Memory Bank Governance Adapter](docs/08-cline-memory-bank-adapter.md) — generates the same governance manifest on top of Cline's existing six-file Memory Bank layout without replacing Cline's storage model.

The Cline adapter deliberately keeps `projectBrief.md` and `progress.md` as separate authority domains and does not mislabel Cline's richer `activeContext.md` as this project's pointer-only Session Bookmark.

## Reusable templates

The repository currently includes:

- [`templates/memory-core.md`](templates/memory-core.md) — compact core-memory template;
- [`templates/worklog.md`](templates/worklog.md) — authoritative project/domain worklog;
- [`templates/bookmark.md`](templates/bookmark.md) — lightweight session checkpoint;
- [`templates/trigger-table.md`](templates/trigger-table.md) — codename-to-context routing table;
- [`templates/health-check.md`](templates/health-check.md) — periodic memory integrity checklist;
- [`templates/lessons-learned.md`](templates/lessons-learned.md) — structured learning capture.

## Tool support

The method is vendor-neutral. It can be adapted to:

- file-capable coding agents that can maintain the structure automatically;
- project/workspace assistants with limited persistent memory;
- stateless chat systems where the user manually supplies a compact memory summary.

The repository currently documents examples for tools including ChatGPT, Claude, Cursor, Windsurf, Gemini, DeepSeek, Kimi, and similar assistants. Tool names are examples, not dependencies.

## Scope and non-goals

This project is about **memory governance and context integrity**.

It does not claim to provide:

- a general-purpose memory backend;
- vector or graph retrieval;
- a complete multi-agent runtime;
- autonomous agent orchestration;
- an enterprise AI operating system;
- semantic truth detection;
- a benchmark proving one model is superior to another.

Keeping this scope explicit makes the project easier to inspect, reuse, combine with other memory systems, and challenge.

## Contributing

Contributions are welcome, especially:

- English translation and terminology review;
- adapters for existing memory layouts;
- reproducible examples showing context-conflict failure modes;
- improvements to structural-integrity checks;
- field reports describing what did or did not work.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [ROADMAP.md](ROADMAP.md).

## License

MIT. See [LICENSE](LICENSE).
