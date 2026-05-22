# MFDB Chunker v5.0.0
**MFDB Spec v1.31 · BEJSON Library Family v2.0.1 OFFICIAL**
Author: Elton Boehnen · boehnenelton2024.pages.dev · [github.com/boehnenelton/mfdb-chunker](https://github.com/boehnenelton/mfdb-chunker) · boehnenelton2024@gmail.com

---

## Overview
The **MFDB Chunker** is the authoritative system for converting codebases into AI-optimized, tabular **BEJSON (104/104db)** and **MFDB** formats. Version 5 represents the complete remediation of the BEJSON ecosystem, integrating unified error registries, environment management, and authoritative schema enforcement.

---

## What's New in v5.0.0

- **Authoritative Repository** — Moved to [boehnenelton/mfdb-chunker](https://github.com/boehnenelton/mfdb-chunker).
- **Official BEJSON Library v2.0.1** — All Core libs upgraded to the remediated 2026-05-21 release.
- **Unified Schema Registry** — Integrated `lib_bejson_schema.py` for rigid validation of Chunker v5 entities and manifests.
- **Environment Awareness** — Uses `lib_bejson_env.py` to resolve paths via the MFDB Layer Registry.
- **Stale-lock Override** — `bejson_core_acquire_lock` now auto-clears locks older than 60s.
- **Unified Error Codes** — All system events mapped to the BEJSON Unified Error Registry (codes 1–289).

---

## Usage

### Flask UI (Desktop/Mobile)
```bash
python mfdb_chunker_app.py
```
Auto-selects a free port (5100–5120). UI provides a dashboard for visual project selection, version bumping, and chunking operations.

### CLI
```bash
# Chunk a project
python mfdb_chunker.py --chunk  ./MyProject

# Chunk with metadata
python mfdb_chunker.py --chunk  ./MyProject --changelog "Fix" --tags "stable,release"

# Versioning
python mfdb_chunker.py --bump   ./MyProject --bump-part minor

# Operations
python mfdb_chunker.py --list   ./output/MyProject_MFDB/104a.mfdb.bejson
python mfdb_chunker.py --unchunk ./output/MyProject_MFDB/104a.mfdb.bejson --version 1.0.0
python mfdb_chunker.py --export ./output/MyProject_MFDB/104a.mfdb.bejson --version 1.0.0 --out ./v1.mfdb.zip
```

---

## Package Structure

```
mfdb_chunker/
├── mfdb_chunker.py
├── mfdb_chunker_app.py
├── README.md
├── DOCUMENTATION.md
└── lib/
    ├── lib_bejson_core.py           v2.0.1 OFFICIAL
    ├── lib_bejson_validator.py      v2.0.1 OFFICIAL
    ├── lib_bejson_parse.py          v2.0.1 OFFICIAL
    ├── lib_bejson_errors.py         v2.0.1 OFFICIAL  ← NEW
    ├── lib_bejson_env.py            v2.0.1 OFFICIAL  ← NEW
    ├── lib_bejson_schema.py         v2.0.1 OFFICIAL  ← NEW
    ├── lib_bejson_state_management.py v2.0.1 OFFICIAL ← NEW
    ├── lib_bejson_provider.py       v2.0.1 OFFICIAL
    ├── lib_bejson_server.py         v2.0.1 OFFICIAL
    ├── lib_bejson_static_backend.py v2.0.1 OFFICIAL
    ├── lib_be_core.py               v2.0.1 OFFICIAL
    ├── lib_mfdb_core.py             v2.0.1 OFFICIAL
    ├── lib_mfdb_validator.py        v2.0.1 OFFICIAL
    └── lib_mfdb_extensions.py       v2.0.1 OFFICIAL  ← NEW
```

---
*Created by Elton Boehnen | 2026-05-21*
