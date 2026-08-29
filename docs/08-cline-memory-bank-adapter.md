# Cline Memory Bank Governance Adapter

This adapter generates an AI Memory Architecture `memory-integrity.json` overlay for the documented Cline Memory Bank layout.

It is intentionally conservative. It does **not** rewrite Cline files, replace Cline's own workflow, or claim that Cline officially uses AI Memory Architecture terminology.

## Source layout

Cline's documented Memory Bank uses six required Markdown files:

- `projectBrief.md`
- `productContext.md`
- `activeContext.md`
- `systemPatterns.md`
- `techContext.md`
- `progress.md`

Cline documents `projectBrief.md` as the source of truth for project scope. `activeContext.md` carries current work focus and recent changes, while `progress.md` tracks current status, remaining work, known issues, and decision evolution.

## Governance interpretation

The adapter makes two explicit authority assignments:

- `project-scope` → `projectBrief.md`
- `project-progress` → `progress.md`

It does **not** map `activeContext.md` to AI Memory Architecture's pointer-only Session Bookmark concept. Cline gives `activeContext.md` richer state semantics, so treating it as a bookmark would distort the source system.

The other Cline core files are represented as structural dependency references following Cline's published hierarchy.

This is a governance overlay, not a claim that Cline itself enforces these authority rules.

## Generate the manifest

```bash
python tools/adapters/cline_memory_bank.py path/to/memory-bank
```

By default this creates:

```text
path/to/memory-bank/memory-integrity.json
```

The command refuses to overwrite an existing manifest unless `--force` is supplied.

Then run:

```bash
python tools/memory_integrity_check.py path/to/memory-bank/memory-integrity.json
```

## What this proves

A passing result proves only that the declared structural overlay is internally consistent and that required files/dependency paths exist.

It does not prove that the prose inside `activeContext.md` and `progress.md` is semantically consistent. Semantic contradiction detection remains outside V1's deterministic scope.

## Why this adapter matters

The adapter demonstrates that AI Memory Architecture does not need to own the memory storage format. A pre-existing memory system can keep its own files and workflow while adding an independent governance contract on top.

Future adapters can target other file-based memory layouts without requiring those projects to adopt this repository's storage model.
