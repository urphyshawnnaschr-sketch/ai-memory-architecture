# Memory Integrity Check V1

Memory Integrity Check V1 turns several AI Memory Architecture principles into deterministic, local checks.

It does **not** ask an AI model to decide whether memory "looks healthy." Instead, a small JSON manifest declares the files and relationships that should be true, and the checker verifies those invariants.

## What V1 checks

- **Core-memory size bound** — warns when always-loaded memory exceeds the configured byte limit.
- **Single authority per domain** — detects duplicate authoritative progress sources.
- **Authority file existence** — detects declared worklogs that no longer exist.
- **Bookmark linkage** — detects bookmarks that point to an unknown domain or a path different from that domain's authority.
- **Reference freshness** — detects references whose target file has disappeared.
- **Contradiction status** — fails when an explicitly tracked contradiction remains unresolved.
- **Path containment** — rejects manifest paths that escape the project directory.

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

All paths are relative to the manifest's directory.

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

V1 checks explicit structural claims. It does not attempt semantic truth detection, automatic memory rewriting, model ranking, or autonomous agent orchestration.

That boundary is deliberate: deterministic structural checks are reproducible, reviewable, and usable without sending private memory contents to an external service.
