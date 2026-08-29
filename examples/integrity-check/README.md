# Integrity Check Examples

These fixtures make Memory Integrity Check V1 reproducible without private user data.

## Passing fixture

```bash
python tools/memory_integrity_check.py examples/integrity-check/pass/memory-integrity.json
```

Expected exit code: `0`.

Expected output:

```text
PASS: memory integrity checks passed
```

## Deliberately failing fixture

```bash
python tools/memory_integrity_check.py examples/integrity-check/fail/memory-integrity.json
```

Expected exit code: `1`.

The fixture intentionally contains several structural problems so reviewers can verify that the checker rejects them. It does not contain customer data, credentials, or copied conversation history.
