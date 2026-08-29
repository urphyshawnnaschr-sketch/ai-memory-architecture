# Memory Integrity Check V1

Memory Integrity Check V1 turns several AI Memory Architecture principles into deterministic, local **structural-governance checks**.

It does **not** ask an AI model to decide whether memory "looks healthy." Instead, a small JSON manifest declares the files and relationships that should be true, and the checker verifies those invariants.

The manifest is also published as a machine-readable JSON Schema:

[`spec/memory-integrity-manifest-v1.schema.json`](../spec/memory-integrity-manifest-v1.schema.json)

## What V1 checks

- **Core-memory size bound** — warns when always-loaded memory exceeds the configured byte limit.
- **Single authority per domain** — detects duplicate authoritative progress sources.
- **Authority path reuse** — detects one canonical file being assigned as authority for multiple domains.
- **Authority file existence** — detects declared worklogs that no longer exist.
- **Bookmark linkage** — detects bookmarks that point to an unknown domain or a path different from that domain's authority.
- **Duplicate bookmarks** — detects the same bookmark file declared more than once, including path aliases such as `bookmark.md` and `./bookmark.md`.
- **Reference freshness** — detects references whose target file has disappeared.
- **Contradiction status** — fails when an explicitly tracked contradiction remains unresolved.
- **Duplicate contradiction IDs** — prevents two manifest entries from silently representing the same named conflict.
- **Path normalization** — compares canonical project-relative paths so spelling aliases cannot bypass authority checks.
- **Path containment** — rejects manifest paths that escape the project directory.
- **Closed manifest fields** — rejects unknown fields instead of silently accepting a misspelled or unsupported governance claim.

## Run it

Requires Python 3.9+ and uses only the Python standard library.

```bash
python tools/memory_integrity_check.py path/to/memory-integrity.json
```

Exit codes:

- `0` — all checks pass;
- `1` — the manifest is valid but one or more integrity findings exist;
- `2` — the manifest itself is invalid.

## Manifest format

```json
{
  "version": 1,
  "core_memory": {
    "path": "memory-core.md",
    "max_bytes": 5000
  },
  "authorities": [
    {"domain": "project-alpha", "path": "worklog.md"}
  ],
  "bookmarks": [
    {
      "path": "bookmark.md",
      "target_domain": "project-alpha",
      "target_path": "worklog.md"
    }
  ],
  "references": [
    {"source": "memory-core.md", "target": "worklog.md"}
  ],
  "contradictions": [
    {"id": "deployment-mode", "status": "resolved"}
  ]
}
```

All paths are relative to the manifest's directory. Before comparing relationships, the checker resolves paths to one canonical project-relative representation. This means `worklog.md` and `./worklog.md` are treated as the same file.

## Why a manifest?

The manifest is deliberately small. It is not another memory store.

It expresses a portable governance contract:

- which file is core memory;
- which file is authoritative for each domain;
- which bookmarks are allowed to point to those authorities;
- which explicit references must continue to resolve;
- which named contradictions have or have not been resolved.

A future adapter could generate the same manifest from a Cline Memory Bank, a local Markdown wiki, or another memory backend. That lets the integrity rules remain independent of how memory is stored or retrieved.

## Reproducible examples

A passing fixture lives at:

`examples/integrity-check/pass/memory-integrity.json`

Run:

```bash
python tools/memory_integrity_check.py examples/integrity-check/pass/memory-integrity.json
```

Expected result:

```text
PASS: memory integrity checks passed
```

A deliberately broken fixture lives at:

`examples/integrity-check/fail/memory-integrity.json`

It demonstrates several common failure modes at once. Running it should return exit code `1` and findings including `OVERSIZED_CORE_MEMORY`, `DUPLICATE_AUTHORITY_DOMAIN`, `ORPHAN_BOOKMARK`, `STALE_REFERENCE`, and `UNRESOLVED_CONTRADICTION`.

## Design boundary

V1 checks explicit structural claims. It does not attempt:

- semantic truth detection;
- prompt-injection or credential scanning;
- automatic memory rewriting;
- vector or graph retrieval;
- model ranking;
- autonomous agent orchestration.

That boundary is deliberate. Other projects already solve storage, retrieval, provenance, temporal graphs, or memory security. This checker focuses on **state-structure integrity**: authority, references, checkpoints, contradictions, and containment.

See [Prior Art and Project Positioning](07-prior-art-and-positioning.md) for the broader ecosystem comparison.
