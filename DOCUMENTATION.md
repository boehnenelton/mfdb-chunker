# MFDB Chunker — Full Documentation
**Version 6.0.0 · MFDB Spec v1.31 · BEJSON Library Family v2.0.1 OFFICIAL**
Author: Elton Boehnen · boehnenelton2024.pages.dev · github.com/boehnenelton · boehnenelton2024@gmail.com

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Installation](#3-installation)
4. [Configuration Reference](#4-configuration-reference)
5. [CLI Reference](#5-cli-reference)
6. [Flask UI Reference](#6-flask-ui-reference)
7. [Manifest Schema](#7-manifest-schema)
8. [Entity File Schema](#8-entity-file-schema)
9. [Library Compatibility](#9-library-compatibility)
10. [Public API Reference](#10-public-api-reference)
11. [Error Reference](#11-error-reference)
12. [Changelog](#12-changelog)
13. [Suggested Features Roadmap](#13-suggested-features-roadmap)

---

## 1. Overview

MFDB Chunker is a version-archiving tool built on the BEJSON MFDB 1.31 specification. It packs a project directory into a persistent MFDB (Multi-File Database), tracking every version as rows inside a single project entity file. Any version can be restored to disk at any time.

It ships as two entry points:

- **`mfdb_chunker.py`** — command-line interface. Also importable as a Python module.
- **`mfdb_chunker_app.py`** — Flask web UI with project mode, changelog, tagging, prune, export, and import.

### Key properties

- **One entity file per project** — all versions stored as rows in `data/<project>.bejson`, differentiated by a `version` field. No per-version files, no null-padding.
- **Manifest is the registry** — `104a.mfdb.bejson` holds one row per version with metadata.
- **Optional binary encoding** — images and other binary files can be base64-encoded and fully restored on unchunk.
- **Self-describing** — every entity file carries `Parent_Hierarchy` pointing back to its manifest.
- **Export/import** — any version can be exported as a portable `.mfdb.zip` and imported into another MFDB.

---

## 2. Architecture

### On-disk layout

```
output/
└── MyProject_MFDB/
    ├── 104a.mfdb.bejson          ← Manifest (BEJSON 104a, MFDB 1.31)
    └── data/
        └── myproject.bejson      ← ALL versions as rows (BEJSON 104)

unchunked/
└── MyProject_v1_2_0_<ts>/        ← Restored project files

exports/
└── MyProject-1.2.0.mfdb.zip      ← Self-contained export packages

projects.json                     ← Flask UI project registry
chunker_config.json               ← Per-project config (lives in project dir)
```

### Data flow

```
Project directory
      │
      ▼ --chunk
  [scan files] ──► [base64-encode binaries?] ──► [append rows to entity file]
                                                          │
                                               [append row to manifest]

104a.mfdb.bejson
      │
      ▼ --unchunk
  [read manifest] ──► [filter entity rows by version] ──► [write files to disk]
                                                           (base64 decoded if is_base64=true)
```

### MFDB 1.31 compliance

| Requirement | Implementation |
|---|---|
| `MFDB_Version: "1.31"` | Set in `init_manifest()` |
| `Records_Type: ["mfdb"]` in manifest | Set in `init_manifest()` |
| Custom headers before `Records_Type` | Dict key insertion order enforced |
| Entity `Records_Type` matches manifest `entity_name` | Both derived from `sanitize_name(project_name)` |
| `Parent_Hierarchy` relative path in every entity file | `os.path.relpath(manifest, data_dir)` |
| Entity filename lowercase | `sanitize_name()` enforced |
| Atomic writes | `bejson_core_atomic_write()` v2.0.1 (temp+rename+fsync) |
| Dense entity records, no null-padding | One entity type per file |

---

## 3. Installation

### Requirements

- Python 3.10+
- `flask` — for the UI only: `pip install flask`
- All BEJSON libraries included in `lib/` — no other pip dependencies

### Package structure

```
mfdb_chunker/
├── mfdb_chunker.py
├── mfdb_chunker_app.py
├── README.md
├── DOCUMENTATION.md
└── lib/
    ├── lib_bejson_core.py           v2.0.1 — Atomic I/O, document factories, lock management
    ├── lib_bejson_validator.py      v2.0.1 — Structural integrity checker
    ├── lib_bejson_parse.py          v2.0.1 — Rapid indexing and retrieval engine
    ├── lib_bejson_errors.py         v2.0.1 — Unified error code registry (codes 1–289)
    ├── lib_bejson_env.py            v2.0.1 — Path resolution for {SC_ROOT}, {HOME}, etc.
    ├── lib_bejson_schema.py         v2.0.1 — Schema management and enforcement
    ├── lib_bejson_state_management.py v2.0.1 — BEJSON 104db state persistence
    ├── lib_bejson_provider.py       v2.0.1 — Data provider interface
    ├── lib_bejson_server.py         v2.0.1 — Flask server port management
    ├── lib_bejson_static_backend.py v2.0.1 — Flat-file persistence layer
    ├── lib_be_core.py               v2.0.1 — BE system abstractions
    ├── lib_mfdb_core.py             v2.0.1 — MFDB orchestrator, MFDBArchive, recovery
    ├── lib_mfdb_validator.py        v2.0.1 — Manifest/entity bidirectional validator
    └── lib_mfdb_extensions.py       v2.0.1 — Migrations, integrity checks, transforms
```

No install step. Run from the `mfdb_chunker/` directory.

### Android / Termux note

The Flask UI uses `use_reloader=False` and auto-selects a free port (5100–5120), avoiding port conflicts and the recursive-server-spawn issue. `bejson_core_acquire_lock` in v2.0.1 has a stale-lock override — locks older than 60 seconds are automatically cleared.

---

## 4. Configuration Reference

`chunker_config.json` lives in your **project directory**. Auto-created with the directory name as `project_name` on first run.

```json
{
  "project_name":           "BEChat",
  "version":                "1.0.0",
  "extensions": [
    ".py", ".js", ".ts", ".html", ".css",
    ".md", ".json", ".sh", ".txt", ".bejson",
    ".png", ".jpg", ".gif", ".ico", ".webp", ".svg"
  ],
  "exclude_dirs": [
    ".git", "__pycache__", "node_modules",
    "lib", "output", ".mfdb_lock"
  ],
  "output_base":            "./output",
  "include_binary_base64":  false
}
```

| Field | Type | Default | Description |
|---|---|---|---|
| `project_name` | string | Directory name | `DB_Name` and MFDB directory name. Auto-set from folder on first run. |
| `version` | string | `"1.0.0"` | Current version. Bump before each chunk. |
| `extensions` | array | See above | File suffixes to include. Case-insensitive. |
| `exclude_dirs` | array | See above | Directory names to skip. |
| `output_base` | string | `./output` | Where to create `<project_name>_MFDB/`. |
| `include_binary_base64` | boolean | `false` | Encode binary files as base64. Decoded on unchunk. |

---

## 5. CLI Reference

### --chunk

```bash
python mfdb_chunker.py --chunk ./BEChat
python mfdb_chunker.py --chunk ./BEChat --changelog "Fixed auth bug" --tags "stable,release"
```

### --chunk-template

```bash
python mfdb_chunker.py --chunk-template ./BEChat --template-name baseline_ui
```

Creates a reusable template zip under:
`output/BEChat_MFDB/templates/`

### --unchunk-template

```bash
python mfdb_chunker.py --unchunk-template ./BEChat --template-name baseline_ui
python mfdb_chunker.py --unchunk-template ./BEChat --template-out ./restore_from_template
```

Restores a template zip to disk. If `--template-name` is omitted, the latest template zip is restored.

### --bump

```bash
python mfdb_chunker.py --bump ./BEChat
python mfdb_chunker.py --bump ./BEChat --bump-part minor   # patch | minor | major
```

### --list

```bash
python mfdb_chunker.py --list ./output/BEChat_MFDB/104a.mfdb.bejson
```

### --unchunk

```bash
python mfdb_chunker.py --unchunk ./output/BEChat_MFDB/104a.mfdb.bejson --version 1.2.0
```

### --prune

```bash
python mfdb_chunker.py --prune ./output/BEChat_MFDB/104a.mfdb.bejson --version 1.0.0
```

### --export

```bash
python mfdb_chunker.py --export ./output/BEChat_MFDB/104a.mfdb.bejson --version 1.2.0 --out ./v1.2.0.mfdb.zip
```

### --import

```bash
python mfdb_chunker.py --import ./output/BEChat_MFDB/104a.mfdb.bejson --zip ./v1.2.0.mfdb.zip
python mfdb_chunker.py --import ./output/BEChat_MFDB/104a.mfdb.bejson --zip ./v1.2.0.mfdb.zip --on-conflict prefix
```

### Full flag reference

| Flag | Arg | Description |
|---|---|---|
| `--chunk` | `DIR` | Pack project as new version |
| `--chunk-template` | `DIR` | Create reusable template zip in project MFDB `templates/` subdir |
| `--bump` | `DIR` | Bump version in config |
| `--list` | `MANIFEST` | List all versions |
| `--unchunk` | `MANIFEST` | Restore a version |
| `--unchunk-template` | `DIR` | Restore from template zip (latest or named) |
| `--prune` | `MANIFEST` | Delete a version permanently |
| `--export` | `MANIFEST` | Export a version as zip |
| `--import` | `MANIFEST` | Import from a zip |
| `--version` | `VER` | Target version |
| `--template-name` | `NAME` | Template name for template chunk/restore |
| `--template-out` | `PATH` | Restore output directory for `--unchunk-template` |
| `--changelog` | `TEXT` | Release notes (for `--chunk`) |
| `--tags` | `TAGS` | Comma-separated tags |
| `--bump-part` | `PART` | `patch` / `minor` / `major` |
| `--out` | `PATH` | Output zip path |
| `--zip` | `PATH` | Source zip path |
| `--on-conflict` | `MODE` | `reject` or `prefix` |

---

## 6. Flask UI Reference

### Starting

```bash
python mfdb_chunker_app.py
```

Port auto-selected 5100–5120. `use_reloader=False`.

### Sidebar — Project Mode

Add any number of project directories by absolute path. Each entry shows name, path, and current version. Click to switch.

### Bump Version

PATCH / MINOR / MAJOR buttons. Writes to `chunker_config.json` immediately.

### Chunk

- Changelog textarea and tags field
- **INCLUDE BINARY AS BASE64** checkbox — encodes images/binaries into the chunk; decoded automatically on unchunk
- CHUNK button — shows result in status log; table reloads after 1.2s

### Version History Table

Columns: VERSION · FILES · CHUNKED AT · CHANGELOG · TAGS · actions

- **Changelog** — click to edit inline. Enter saves, Escape cancels.
- **Tags** — ✎ button opens tag modal. Color-coded: `stable`=green, `release`=blue, `hotfix`=orange.
- **Tag filter** — filter row appears when any tags exist.
- **RESTORE** — unchunk to disk. Output path in status log.
- **EXPORT** — export as `.mfdb.zip`. Triggers browser download.
- **PRUNE** — confirmation modal. Deletes permanently on confirm.

### Import

Drag-and-drop zone. Accepts `.mfdb.zip` exports. Reject or prefix conflict resolution.

### Status Log

ALL CAPS messages at page bottom. Green = success. Red = error.

---

## 7. Manifest Schema

`104a.mfdb.bejson` — BEJSON 104a. One row per version.

### Headers (in spec order)

```json
{
  "Format":         "BEJSON",
  "Format_Version": "104a",
  "Format_Creator": "Elton Boehnen",
  "MFDB_Version":   "1.31",
  "DB_Name":        "BEChat",
  "DB_Description": "Version archive for project: BEChat",
  "Schema_Version": "1.0.0",
  "Author":         "Elton Boehnen",
  "Created_At":     "2026-05-21T12:00:00Z",
  "Records_Type":   ["mfdb"],
  "Fields":         [...],
  "Values":         [...]
}
```

### Fields

| # | Field | Type | Description |
|---|---|---|---|
| 0 | `entity_name` | string | e.g. `v1_2_0` |
| 1 | `file_path` | string | e.g. `data/bechat.bejson` |
| 2 | `description` | string | Human-readable |
| 3 | `record_count` | integer | Advisory file count |
| 4 | `schema_version` | string | Semver, e.g. `1.2.0` |
| 5 | `primary_key` | string | `"file_path"` |
| 6 | `changelog` | string | Release notes (editable after chunk) |
| 7 | `chunked_at` | string | ISO 8601 UTC timestamp |
| 8 | `tags` | string | Comma-separated tag labels |

---

## 8. Entity File Schema

`data/bechat.bejson` — BEJSON 104. One row per (version, file) pair.

### Headers

```json
{
  "Format":           "BEJSON",
  "Format_Version":   "104",
  "Format_Creator":   "Elton Boehnen",
  "Parent_Hierarchy": "../104a.mfdb.bejson",
  "Records_Type":     ["bechat"],
  "Fields":           [...],
  "Values":           [...]
}
```

### Fields

| # | Field | Type | Description |
|---|---|---|---|
| 0 | `version` | string | Entity name, e.g. `v1_2_0` |
| 1 | `file_path` | string | Relative path from project root |
| 2 | `file_name` | string | Filename only |
| 3 | `content` | string | UTF-8 text, base64 string, or `""` |
| 4 | `is_binary` | boolean | True if file could not be read as UTF-8 |
| 5 | `is_base64` | boolean | True if `content` is base64-encoded binary |

### Binary handling

| `is_binary` | `is_base64` | `content` | Unchunk behavior |
|---|---|---|---|
| `false` | `false` | UTF-8 text | Write as text |
| `true` | `false` | `""` | Create empty placeholder |
| `true` | `true` | Base64 string | Decode and write raw bytes |

---

## 9. Library Compatibility

### v5.0.0 Breaking Changes from v4.x

**`bejson_core_atomic_write` signature changed:**

```python
# v4.x (OLD — no longer works)
BEJSONCore.bejson_core_atomic_write(path, doc, create_backup=False)

# v5.0.0 (NEW — official v2.0.1 API)
BEJSONCore.bejson_core_atomic_write(path, doc)
```

The `create_backup` parameter was removed in v2.0.1. The function always writes atomically (temp file + rename + fsync) without creating a backup file.

**New lock API in lib_bejson_core.py v2.0.1:**

```python
bejson_core_acquire_lock(file_path, timeout=10, stale_age=60)  # returns bool
bejson_core_release_lock(file_path)
```

Stale locks (older than `stale_age` seconds) are automatically cleared. This eliminates the Android/Termux freeze caused by orphaned locks.

**New error code registry:**

All error codes are now defined in `lib_bejson_errors.py`. Import pattern:

```python
from lib_bejson_errors import E_INVALID_JSON, E_MFDB_CORE_ENTITY_NOT_FOUND
# etc.
```

Error code ranges:
- `1–19`: BEJSON Core/Validator
- `20–29`: BEJSON Core operations
- `30–49`: MFDB Validator
- `50–69`: MFDB Core
- `70–71`: MFDB Archive
- `270–289`: Cognition

**New validator API:**

`validate_bejson()` is now the canonical entry point, returning a `ValidationResult` dataclass. Compatibility wrappers `bejson_validator_validate_string()` and `bejson_validator_validate_file()` still exist and raise `BEJSONValidationError` on failure.

---

## 10. Public API Reference

All functions are in `mfdb_chunker.py` and are importable.

### `do_chunk(target_dir, changelog="", tags="")`

Chunk a project. Reads `include_binary_base64` from config.

```python
result = do_chunk("/path/to/BEChat", changelog="Fixed auth", tags="stable")
# {"ok": True, "message": "VERSION 1.2.0 CHUNKED SUCCESSFULLY",
#  "detail": {"version": "1.2.0", "entity_name": "v1_2_0",
#             "file_count": 12, "skipped": [], ...}}
```

### `do_bump(target_dir, part="patch")` → `dict`

```python
do_bump("/path/to/BEChat", "minor")
# {"ok": True, "message": "1.2.0 → 1.3.0", "new_version": "1.3.0"}
```

### `do_unchunk(manifest_path, version)` → `dict`

```python
do_unchunk("...104a.mfdb.bejson", "1.2.0")
# {"ok": True, "message": "VERSION 1.2.0 RESTORED TO DISK",
#  "out_dir": "...", "file_count": 12}
```

### `do_update_changelog(manifest_path, version, new_changelog)` → `dict`

Edit changelog of an existing version. Does not touch entity file.

### `do_update_tags(manifest_path, version, tags)` → `dict`

Set comma-separated tags on a version in the manifest.

### `do_prune(manifest_path, version)` → `dict`

Atomically remove a version from manifest and entity file.

```python
do_prune("...104a.mfdb.bejson", "1.0.0")
# {"ok": True, "message": "VERSION 1.0.0 PRUNED", "rows_removed": 10}
```

### `do_export(manifest_path, version, out_path)` → `dict`

Export a version as a portable `.mfdb.zip`.

### `do_import(manifest_path, zip_path, on_conflict="reject")` → `dict`

Import versions from an export zip. `on_conflict`: `"reject"` or `"prefix"`.

### `list_versions(manifest_path)` → `list[dict]`

All version rows as field-name-keyed dicts. Empty list on error.

### `get_manifest_meta(manifest_path)` → `dict`

Top-level manifest headers.

### `bump_version(version, part="patch")` → `str`

Pure function. `bump_version("1.2.3", "minor")` → `"1.3.0"`.

### `version_to_entity_name(version)` → `str`

`version_to_entity_name("1.2.3")` → `"v1_2_3"`

---

## 11. Error Reference

### CLI

| Message | Fix |
|---|---|
| `Version 'x' already exists` | Bump version first |
| `Manifest not found` | Point to `104a.mfdb.bejson` |
| `Version 'x' not found in manifest` | Run `--list` to see valid versions |
| `Entity file missing on disk` | Entity was moved/deleted |
| `--unchunk requires --version` | Add `--version 1.2.0` |
| `Zip missing 104a.mfdb.bejson` | Not a valid MFDB export |
| `CRITICAL: Local libraries not found in lib/` | Keep `lib/` beside `mfdb_chunker.py` |

### Flask UI

| Status | Meaning |
|---|---|
| `READY` | No action yet |
| `VERSION x CHUNKED SUCCESSFULLY` | Chunk complete |
| `VERSION x RESTORED TO DISK` | Unchunk complete |
| `VERSION BUMPED: x → y` | Config updated |
| `VERSION x EXPORTED` | Export zip created |
| `IMPORT COMPLETE: N imported, N skipped` | Import done |
| `VERSION x PRUNED` | Delete complete |
| `ERROR: Version 'x' already exists` | Bump first |

---

## 12. Changelog

| Version | Summary |
|---|---|
| **5.0.0** | Official BEJSON Library v2.0.1. Removed `create_backup` kwarg. Added `lib_bejson_errors.py`, `lib_bejson_env.py`, `lib_bejson_schema.py`, `lib_bejson_state_management.py`, `lib_mfdb_extensions.py`. Stale-lock override in core. |
| **4.1.0** | Renamed package folder, documentation updated. |
| **4.0.0** | Optional base64 binary encoding. `is_base64` field. UI checkbox. |
| **3.0.0** | `project_name` auto-set from target directory name. |
| **2.0.0** | Single entity file per project. Version tagging, inline changelog edit, prune, export/import zip. |
| **1.2.0** | Flask UI, project mode, changelog field, bump/restore buttons. |
| **1.1.0** | MFDB Spec 1.31 compliance. |
| **1.0.2** | `create_backup=False` on all atomic writes (pre-v2 API). |
| **1.0.0** | Initial release. |

---

## 13. Suggested Features Roadmap

### Tier 1 — Low effort

**DB Integrity Check (`--validate`)**
Walk the manifest, verify every `file_path` exists, verify `Parent_Hierarchy` resolves correctly, check row counts against `record_count`. CLI: `--validate <MANIFEST>`. UI: VALIDATE button. Backed by `mfdb_core_deep_verify()` and `mfdb_core_self_heal()` already in `lib_mfdb_core.py` v2.0.1.

**Remove Project from UI**
Remove button in the sidebar. Deletes from `projects.json` only — does not touch the MFDB on disk.

**File Tree Preview**
Before restoring, show a collapsible tree of all files in that version with file path, character count, binary flag. No disk writes. Computed by filtering entity rows.

### Tier 2 — Medium effort

**Diff View**
Compare two versions side-by-side. Show files added, removed, changed (by content hash). Line-level diff is a stretch goal; file-level is straightforward.

**MFDB Snapshot Backups (Coming Soon)**
Point-in-time snapshot packs for fast rollback safety and archival checkpoints.

**Selective Restore**
Pick specific files from the tree preview to restore. Useful for cherry-picking one file from an older version without overwriting the rest.

**Stats Dashboard**
Per-project panel: total versions, total files, total content size, most-changed files, average time between chunks.

**Auto-Chunk Watcher**
Poll project directory (Termux-compatible). Trigger automatic chunk after debounce delay. Auto-generate changelog like `Auto-chunk: 3 files changed`.

### Tier 3 — Higher effort

**DB Integrity Validation via `lib_mfdb_extensions.py`**
`mfdb_ext_verify_referential_integrity()` is already implemented in the v2.0.1 lib. Wire it up to a `--validate-fk <MANIFEST>` CLI flag and a UI button to report unresolved `_fk` fields.

**Search Across Versions**
Given a search string, scan `content` field across all entity rows. Return matches with version, file path, and line number.

**Time Machine Restoration (Coming Soon)**
Restore the MFDB to a selected historical checkpoint from snapshot history.

**Federation / Master-Slave**
Implement MFDB 1.31 `Network_Role` header (already in `mfdb_core_create_database` in v2.0.1). Master node tracks Slave MFDBs. Master UI shows unified version history across nodes.

**Self-Healing Import**
On import, if entity rows fail positional validation, call `mfdb_core_self_heal()` from the v2.0.1 lib to auto-repair before writing.

---

*MFDB Chunker is a project by Elton Boehnen.*
*boehnenelton2024.pages.dev · github.com/boehnenelton · boehnenelton2024@gmail.com*
