# Prior Art and Project Positioning

AI Memory Architecture does not claim to have invented persistent AI memory, Markdown memory banks, cross-session context, or local-first agent knowledge.

Those ideas already exist in strong open-source projects. This document explains where this project overlaps with them and where it intentionally differs.

## The short version

Most agent-memory projects ask:

> How do we capture, store, retrieve, or inject useful memory?

AI Memory Architecture focuses on a narrower governance question:

> Once memory exists, how do we keep the active project state coherent, portable, and auditable so an agent does not follow stale, duplicated, or conflicting context?

The project therefore aims to be a **memory-governance and structural-integrity layer**, not another general-purpose memory backend.

## Related systems

| Project / pattern | Primary focus | Where it overlaps | Where this project differs |
|---|---|---|---|
| Cline Memory Bank | Structured Markdown project context across coding sessions | Project brief, active context, progress, durable files | AI Memory Architecture makes authority explicit: one authoritative progress source per domain, while checkpoints/bookmarks remain pointers rather than parallel status documents. It is also intended to work outside a single coding harness. |
| Roo Code Memory Bank | Persistent project context for Roo Code with structured files and mode rules | Markdown context, decisions, progress, cross-session continuity | Roo is tightly integrated with Roo Code modes and update behavior. This project treats the file structure as a portable method that can degrade down to manual copy/paste when no file-capable agent exists. |
| Basic Memory | Local-first Markdown knowledge graph with MCP, indexing, search, and human/AI co-editing | User-owned Markdown, cross-tool access, local-first philosophy | Basic Memory is a knowledge-management and retrieval system. This project does not require MCP, a database, indexing, or semantic search; it focuses on authority, references, checkpoints, contradiction state, and integrity checks. |
| Mem0 | Persistent personalized memory layer for AI applications | Cross-session memory and scoped context | Mem0 extracts, stores, and retrieves useful memories for applications. This project does not try to be a memory database or personalization layer; it focuses on the correctness of explicitly managed project context. |
| LangMem | LLM-assisted extraction, consolidation, and long-term memory management | Memory maintenance and consolidation | LangMem uses model-driven memory operations and application storage. This project keeps the core governance rules understandable without an LLM and provides deterministic structural checks. |
| Letta / MemGPT | Stateful agents with editable memory blocks and external memory | Core vs external memory, keeping always-loaded context lean, model portability | Letta provides a stateful agent runtime and memory filesystem. This project is runtime-independent and can be used as a lightweight governance convention even when no persistent agent runtime is available. |
| Graphiti / Zep | Temporal context graphs with provenance and changing facts | Contradiction/change over time, provenance concerns | Graphiti is a temporal graph and retrieval infrastructure layer. This project is deliberately much smaller: it validates explicit project-state relationships in ordinary files rather than building a temporal knowledge graph. |
| MemoryWiki | Local-first, Markdown-native agent memory with provenance, conflict history, and MCP recall | Inspectable local memory, conflict awareness, reversibility | MemoryWiki is a full memory/wiki system. AI Memory Architecture focuses on a minimal portable contract for authority topology and state integrity that can sit beside other storage/retrieval systems. |
| Markdown-only cross-agent memory systems | Shared files, Git history, no vector database | Portability, inspectability, cross-agent handoff | The differentiator here is not Markdown itself. It is the explicit separation of authoritative state from pointers/checkpoints plus deterministic validation of those relationships. |

## What is actually distinctive here?

### 1. Authority is a first-class concept

The project treats progress/state authority as something that should be declared and checked.

For one domain or project, there should be one authoritative progress source. If two files both claim that role, that is not merely "more context"; it is an integrity failure.

This is different from systems that mainly optimize recall or retrieval quality.

### 2. Checkpoints are pointers, not copies

A session bookmark should answer "where do I resume?" without becoming a second progress document.

This reduces one of the most common long-running AI workflow failures: a stale checkpoint contradicting a newer worklog.

### 3. Memory governance works at multiple capability levels

The method is intentionally usable in three environments:

- file-capable agents that can maintain the structure automatically;
- assistants with limited built-in memory where some maintenance is manual;
- stateless chat systems where a compact memory summary is copied into a new session.

The project does not require a specific runtime, MCP server, vector store, hosted service, or model provider.

### 4. Structural integrity is deterministic

Memory Integrity Check V1 does not ask a model whether memory "looks right."

It checks explicit invariants such as:

- one authority per domain;
- authority files exist;
- bookmarks point to the declared authority;
- references still resolve;
- contradictions are not left unresolved;
- core memory stays within a declared size bound;
- paths remain inside the project root.

This is **state-structure integrity**, not prompt-injection or credential scanning.

### 5. The project can complement existing memory systems

The long-term goal is not necessarily to replace Mem0, Basic Memory, Letta, MemoryWiki, or other storage/retrieval systems.

A stronger direction is to define a small, portable governance contract that those systems—or ordinary Markdown files—can satisfy and validate.

In that model:

- storage answers **where memory lives**;
- retrieval answers **which memory to fetch**;
- AI Memory Architecture answers **which state is authoritative and whether the structure is internally consistent**.

## Non-novel claims

The following ideas are explicitly **not** claimed as novel:

- persistent memory across AI sessions;
- Markdown as an AI-readable storage format;
- Git-tracked memory;
- memory tiers / core vs external memory;
- cross-agent handoff;
- MCP-based memory access;
- semantic or graph retrieval.

The project should be judged on whether its governance rules, portable contract, validation tooling, and examples are useful—not on a claim that no one else has worked on AI memory before.

## Direction

Near-term work should prioritize:

1. formalizing the Memory Integrity manifest as a portable schema;
2. strengthening deterministic checks around authority and reference normalization;
3. adding focused single-failure fixtures;
4. documenting adapters for other memory layouts rather than building another storage backend;
5. developing evaluation cases for stale state, duplicate authority, checkpoint drift, and cross-project context leakage.

That positioning keeps the project small enough to understand while giving it a clear role in a crowded memory ecosystem.
