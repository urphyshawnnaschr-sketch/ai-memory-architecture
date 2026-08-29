# AI Memory Architecture

> A practical, tool-agnostic methodology for managing long-running AI collaboration without turning memory into an uncontrolled pile of context.

**Chinese documentation:** [README.md](README.md)

## What this project is

AI Memory Architecture is an open methodology and reusable template set for organizing persistent context across AI assistants and coding agents. It is intentionally **not a platform, agent framework, or enterprise operating system**. The project focuses on a narrower problem: keeping long-running AI work understandable, portable, and maintainable.

It was derived from sustained real-world use of AI assistants across multiple projects and tools.

## The problem

Long-running AI work tends to fail in predictable ways:

- important context is scattered across conversations and files;
- stale notes compete with newer decisions;
- several projects leak context into one another;
- progress is duplicated in multiple places and becomes inconsistent;
- switching AI tools means rebuilding context from scratch.

This repository treats those as information-architecture problems rather than model-capability problems.

## Five core principles

1. **Single source of progress** — keep authoritative progress in one place; everything else points to it.
2. **Minimal core memory** — keep always-loaded context small and stable.
3. **Codename-triggered routing** — use a lightweight trigger table to select the relevant context domain.
4. **Linked checkpoints** — session bookmarks should point back to authoritative worklogs instead of duplicating them.
5. **Periodic pruning** — stale memory must be reviewed and removed before it becomes contradictory context.

## Reusable templates

The repository currently includes:

- [`templates/memory-core.md`](templates/memory-core.md) — compact core-memory template;
- [`templates/worklog.md`](templates/worklog.md) — authoritative project/domain worklog;
- [`templates/bookmark.md`](templates/bookmark.md) — lightweight session checkpoint;
- [`templates/trigger-table.md`](templates/trigger-table.md) — codename-to-context routing table;
- [`templates/health-check.md`](templates/health-check.md) — periodic memory integrity checklist;
- [`templates/lessons-learned.md`](templates/lessons-learned.md) — structured learning capture.

## Tool support

The method is vendor-neutral. It can be adapted to AI coding tools that can read/write local files, project-oriented assistants with limited persistent memory, or plain chat systems where the user manually supplies a compact memory summary.

The repository currently documents examples for tools including ChatGPT, Claude, Cursor, Windsurf, Gemini, DeepSeek, Kimi, and similar assistants. Tool names are examples, not dependencies.

## Scope and non-goals

This project is about **memory and context management methodology**.

It does not claim to provide:

- a complete multi-agent runtime;
- autonomous agent orchestration;
- an enterprise AI operating system;
- a proprietary memory backend;
- a benchmark proving one model is superior to another.

Keeping this scope explicit makes the methodology easier to inspect, reuse, and challenge.

## Contributing

Contributions are welcome, especially:

- English translation and terminology review;
- adaptations for additional AI tools;
- reproducible examples showing context-conflict failure modes;
- improvements to templates and memory-health checks;
- field reports describing what did or did not work.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [ROADMAP.md](ROADMAP.md).

## License

MIT. See [LICENSE](LICENSE).