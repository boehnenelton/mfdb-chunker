# MFDB Chunker v6.0.0
**MFDB Spec v1.31 · BEJSON Library Family v2.0.1 OFFICIAL**
Author: Elton Boehnen · boehnenelton2024.pages.dev · [github.com/boehnenelton/mfdb-chunker](https://github.com/boehnenelton/mfdb-chunker)

---

## 🚀 Overview
The **MFDB Chunker** is the authoritative system for converting codebases into AI-optimized, tabular **BEJSON (104/104db)** and **MFDB** formats. Version 6.0.0 represents a major leap in reliability and usability, introducing integrated snapshots, point-in-time recovery, and an interactive dashboard with a visual file selector.

### Key Capabilities:
- **Relational Archiving:** Store unlimited versions of a codebase as rows in a single, high-performance BEJSON entity file.
- **Lostless Binary Storage:** Optional Base64 encoding for binaries (images, zips) ensuring 100% data fidelity during serialization.
- **Snapshot Backups (v6):** Create full ZIP snapshots of the entire MFDB project for secondary archival safety.
- **Integrity Validation (v6):** Automated cross-checking between manifest records and actual entity data to detect corruption or missing files.
- **Web UI Dashboard (v6):** Interactive Flask-based GUI with mobile optimization and real-time activity feedback.
- **Interactive File Selector (v6):** Visual browser for internal storage and SD cards to select project directories effortlessly.

---

## 🛠️ Quick Start

### 1. Installation
Ensure you have Python 3.10+ and Flask installed:
```bash
pip install flask
```

### 2. Launch the Dashboard
Run the Flask application to manage your projects visually:
```bash
python3 mfdb_chunker_app.py
```
Visit `http://localhost:5100` (or the port displayed in your terminal) to begin.

### 3. CLI Basic Usage
For terminal-centric workflows, use `mfdb_chunker.py`:
```bash
# Chunk a directory into a new version
python3 mfdb_chunker.py --chunk /path/to/project --changelog "Initial commit"

# Restore a specific version to disk
python3 mfdb_chunker.py --unchunk /path/to/manifest.bejson --version "1.0.0"

# Create a snapshot zip
python3 mfdb_chunker.py --snapshot /path/to/project

# Validate MFDB integrity
python3 mfdb_chunker.py --validate /path/to/manifest.bejson
```

---

## 📜 Compliance
- **MFDB Spec:** v1.31
- **BEJSON Standards:** 104, 104a, 104db
- **Library Jurisdiction:** `BEJSON_LIBRARIES`

For exhaustive technical details, schema examples, and API references, please see [DOCUMENTATION.md](./DOCUMENTATION.md).

---
*MFDB Chunker is a project by Elton Boehnen.*
*boehnenelton2024.pages.dev · github.com/boehnenelton · boehnenelton2024@gmail.com*
