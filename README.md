# MFDB Chunker v5.0.0
**MFDB Spec v1.31 · BEJSON Library Family v2.0.1 OFFICIAL**
Author: Elton Boehnen · boehnenelton2024.pages.dev · github.com/boehnenelton · boehnenelton2024@gmail.com

---

## What's New in v5.0.0

- **Official BEJSON Library v2.0.1** — all Core libs upgraded to the remediated 2026-05-21 release
- **`bejson_core_atomic_write` API change** — `create_backup` parameter removed in v2.0.1; all call sites updated
- **New libs included:** `lib_bejson_errors.py`, `lib_bejson_env.py`, `lib_bejson_schema.py`, `lib_bejson_state_management.py`, `lib_mfdb_extensions.py`
- **Stale-lock override** — `bejson_core_acquire_lock` now auto-clears locks older than 60s (remediated in v2.0.1)
- **Unified error code registry** — all error codes now come from `lib_bejson_errors.py` (codes 1–289)

---

## Usage

### Flask UI
```bash
python mfdb_chunker_app.py
```
Auto-selects a free port (5100–5120). `use_reloader=False` — no Inception loop.

### CLI
```bash
python mfdb_chunker.py --chunk  ./MyProject
python mfdb_chunker.py --chunk  ./MyProject --changelog "Fix" --tags "stable,release"
python mfdb_chunker.py --bump   ./MyProject --bump-part minor
python mfdb_chunker.py --list   ./output/MyProject_MFDB/104a.mfdb.bejson
python mfdb_chunker.py --unchunk ./output/MyProject_MFDB/104a.mfdb.bejson --version 1.0.0
python mfdb_chunker.py --prune  ./output/MyProject_MFDB/104a.mfdb.bejson --version 1.0.0
python mfdb_chunker.py --export ./output/MyProject_MFDB/104a.mfdb.bejson --version 1.0.0 --out ./v1.mfdb.zip
python mfdb_chunker.py --import ./output/MyProject_MFDB/104a.mfdb.bejson --zip ./v1.mfdb.zip
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

Python 3.10+ · `pip install flask` for the UI.
