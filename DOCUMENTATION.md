# MFDB Chunker v6.0.0 Technical Documentation
**Relational Archiving & Versioning for the BEJSON Ecosystem**
**MFDB Spec v1.31 · BEJSON Formats: 104 | 104a | 104db**
**Author:** Elton Boehnen
**Status:** OFFICIAL v6.0.0

---

## 1. Executive Summary
The **MFDB Chunker** is a high-performance serialization and archiving engine designed to convert complex file systems and codebases into tabular, AI-optimized data formats. Unlike traditional compression tools, the MFDB Chunker prioritizes **relational data integrity**, allowing multiple versions of a codebase to exist as indexed records within a single database file.

Version 6.0.0 represents the definitive release for enterprise-grade maintenance. It introduces point-in-time **Snapshot Backups**, automated **Integrity Validation**, and a refined **Web Dashboard** featuring a professional interactive file selector. This documentation serves as the authoritative guide for developers and system administrators working within the BEJSON ecosystem.

---

## 2. Core Capabilities

### 2.1 Chunking (Serialization)
Chunking is the process of scanning a target directory and serializing its contents into a BEJSON 104 entity file. 
- **Recursive Scanning:** Automatically traverses subdirectories while obeying strict exclusion rules defined in `chunker_config.json`.
- **Lostless Binary Management:** Optional Base64 encoding transforms binary files (images, compiled assets) into text strings, ensuring 100% data fidelity during BEJSON transport.
- **Positional Integrity:** Every file is mapped to a specific schema index, making it instantly searchable and retrievable by AI agents and relational parsers.
- **Incremental Appending:** New versions are appended as fresh rows, preserving previous history without file duplication.
- **Metadata Tagging:** Supports custom tags (e.g., `stable`, `release-candidate`) per version.

### 2.2 Unchunking (Restoration)
Unchunking reverses the serialization process, rebuilding the directory structure on disk from a specific version row in the database.
- **Point-in-Time Recovery:** Instantly restore any version (e.g., v1.2.4) by querying its semver identifier.
- **Binary Decoding:** Automatically detects and decodes Base64 strings back into their original binary form.
- **Surgical Extraction:** The system ensures that only files belonging to the requested version are written, preventing cross-version contamination.
- **Clean Restores:** The unchunking process ensures that existing files are overwritten or replaced accurately to match the archived state.

### 2.3 Snapshot Backups (v6 Feature)
The snapshot system creates a self-contained ZIP archive of the entire MFDB project directory (manifest + data). 
- **Atomic Archives:** Captures the state of the database and its versions at a specific timestamp.
- **Secondary Safety:** Provides a traditional backup layer on top of the relational archiving system.
- **Portability:** Snapshots can be moved between machines and re-imported into the Chunker UI.
- **Timestamped Naming:** Snapshots are automatically named with the current date and time for easy retrieval.

### 2.4 Integrity Validation (v6 Feature)
The validation engine performs a deep semantic scan of the MFDB:
- **Manifest-to-Entity Mapping:** Ensures every record in the manifest has a corresponding entity file path.
- **Row Count Verification:** Cross-checks the `record_count` field in the manifest against the actual rows present in the entity file for that version.
- **Structure Audit:** Verifies that all required BEJSON headers (Format, Format_Version, Records_Type) are intact.
- **Corruption Detection:** Flags missing files or malformed JSON structures before they cause runtime errors.
- **Detailed Error Reporting:** Provides specific version and file path info when validation fails.

---

## 3. Schema Architecture (MFDB Spec v1.31)

The MFDB (Multifile Database) architecture separates metadata (Manifest) from payload (Entity).

### 3.1 The Manifest (`104a.mfdb.bejson`)
The manifest is a BEJSON 104a document that acts as the relational index for the project. It tracks version metadata but does not store actual file content.

#### Schema Definition:
- **entity_name:** Semantic version prefixed with 'v' and underscores (e.g., `v1_2_0`).
- **file_path:** Path to the entity file relative to the manifest (e.g., `data/myproject.bejson`).
- **description:** A brief summary of the version.
- **record_count:** Number of files captured in this version.
- **schema_version:** The standard semver string (e.g., `1.2.0`).
- **primary_key:** The field used for indexing (usually `file_path`).
- **changelog:** User-provided description of changes.
- **chunked_at:** ISO 8601 timestamp.
- **tags:** Comma-separated strings for filtering.

#### Example:
```json
{
  "Format": "BEJSON",
  "Format_Version": "104a",
  "Format_Creator": "Elton Boehnen",
  "MFDB_Version": "1.31",
  "DB_Name": "MyProject_Manifest",
  "Network_Role": "Master",
  "Records_Type": ["mfdb"],
  "Fields": [
    {"name": "entity_name",    "type": "string"},
    {"name": "file_path",      "type": "string"},
    {"name": "description",    "type": "string"},
    {"name": "record_count",   "type": "integer"},
    {"name": "schema_version", "type": "string"},
    {"name": "primary_key",    "type": "string"},
    {"name": "changelog",      "type": "string"},
    {"name": "chunked_at",     "type": "string"},
    {"name": "tags",           "type": "string"}
  ],
  "Values": [
    [
      "v1_0_0",
      "data/myproject.bejson",
      "Project version 1.0.0",
      42,
      "1.0.0",
      "file_path",
      "Initial production release",
      "2026-05-24T12:00:00Z",
      "stable,release"
    ],
    [
      "v1_1_0",
      "data/myproject.bejson",
      "Project version 1.1.0",
      55,
      "1.1.0",
      "file_path",
      "Added new module x",
      "2026-05-25T09:30:00Z",
      "feature"
    ]
  ]
}
```

### 3.2 The Entity File (`data/<project>.bejson`)
The entity file is a BEJSON 104 document that stores the actual file contents. One entity file holds all versions of a project; versions are distinguished by the `version` field in each row. This "Relational Archiving" approach is significantly faster than creating a new file for every version.

#### Example:
```json
{
  "Format": "BEJSON",
  "Format_Version": "104",
  "Format_Creator": "Elton Boehnen",
  "Parent_Hierarchy": "../104a.mfdb.bejson",
  "Records_Type": ["ProjectFile"],
  "Fields": [
    {"name": "version",   "type": "string"},
    {"name": "file_path", "type": "string"},
    {"name": "file_name", "type": "string"},
    {"name": "content",   "type": "string"},
    {"name": "is_binary", "type": "boolean"},
    {"name": "is_base64", "type": "boolean"}
  ],
  "Values": [
    [
      "v1_0_0",
      "src/main.py",
      "main.py",
      "print('Hello World')",
      false,
      false
    ],
    [
      "v1_0_0",
      "assets/logo.png",
      "logo.png",
      "iVBORw0KGgoAAAANSUhEUgAA...",
      true,
      true
    ],
    [
      "v1_1_0",
      "src/main.py",
      "main.py",
      "print('Hello Updated World')",
      false,
      false
    ]
  ]
}
```

### 3.3 Local Configuration (`chunker_config.json`)
Every project directory contains a local configuration file to define its identity and scanning rules. This file is automatically generated upon first addition but can be customized.

#### Configuration Fields:
- **project_name:** The identifier used in filenames and UI.
- **version:** The current version of the codebase.
- **extensions:** Whitelist of file types to include (e.g. `[".py", ".js"]`).
- **exclude_dirs:** Blacklist of directories to ignore (e.g. `[".git", "node_modules"]`).
- **output_base:** Absolute path where the MFDB files will be stored.
- **include_binary_base64:** Toggle for lossless binary serialization.

---

## 4. Command Line Interface (CLI) Guide

The `mfdb_chunker.py` script provides a powerful CLI for all core operations. It is designed for both human use and automation via shell scripts.

### 4.1 Primary Operations
- `--chunk [DIR]`: Scans the directory and appends it to the MFDB.
- `--unchunk [MANIFEST] --version [VER]`: Restores the requested version.
- `--snapshot [DIR]`: Creates a full ZIP backup of the project's MFDB.
- `--validate [MANIFEST]`: Performs integrity checks.
- `--list [MANIFEST]`: Displays version history.

### 4.2 Management Operations
- `--bump [DIR] --part [patch|minor|major]`: Increments the semantic version in the project's config file.
- `--prune [MANIFEST] --version [VER]`: Permanently deletes a version record and its data. Use with caution.
- `--update-changelog [MANIFEST] --version [VER] --msg [TEXT]`: Updates the changelog for a historical version.

### 4.3 Data Portability
- `--export [MANIFEST] --version [VER]`: Generates a portable `.mfdb.zip` containing only the specific version's data and a valid manifest.
- `--import [ZIP]`: Integrates an exported version into the current chunker workspace.

---

## 5. Web Dashboard (The Flask GUI)

The `mfdb_chunker_app.py` provides a high-fidelity visual interface for managing multiple projects. It is built to bridge the gap between complex CLI commands and high-speed developer workflows.

### 5.1 Project Dashboard
- **Sidebar Navigation:** A unified panel to switch between local projects and those discovered in the global **MFDB Layer Registry**.
- **Version History Table:** A high-contrast grid showing all chunked versions, their file counts, dates, and changelogs.
- **Real-time Feedback:** A status log console at the bottom of the screen provides live updates, "alive" animations, and detailed error messages.

### 5.2 Interactive File Selector (v6 Major Update)
Ported from the `Component-File_Selector` system, this feature eliminates the need for manual path input.
- **Visual Browser:** Navigate the internal storage and SD cards using a familiar folder/file interface.
- **One-Click Selection:** Select a project directory and automatically populate the Add Project form.
- **Storage Toggles:** Quick-jump buttons for different mount points (Internal vs SD).

### 5.3 Mobile Optimization & Safe Zones
- **Responsive Fluidity:** The layout collapses into a single-column view on mobile devices.
- **Safe Zone Padding:** The UI includes a `100px` bottom offset to account for mobile browser navigation bars and gesture bars.
- **Touch-Friendly Controls:** Larger button hit-areas and always-visible project removal controls ensure a "perfect" experience on Android tablets and phones.

---

## 6. Technical Workflow Guide

### 6.1 Initializing a Project
To start tracking a new codebase:
1. Open the MFDB Chunker Dashboard.
2. Click **BROWSE** in the sidebar to open the File Selector.
3. Navigate to your project folder, click **SELECT FOLDER**, then **+ ADD**.
4. The system will automatically create `chunker_config.json`.

### 6.2 The Development & Release Loop
1. Develop your code as usual.
2. When a milestone is reached, open the Dashboard.
3. Type a descriptive **Changelog** (e.g., "Fixed parser timeout").
4. Click **CHUNK**.
5. To release a new semantic version (e.g., moving from v1.0.1 to v1.1.0), use the **MINOR** bump button, then chunk.

### 6.3 Maintenance Best Practices
- **Validation:** Run a **VALIDATE** command after large imports or if you suspect file system corruption.
- **Snapshots:** Always create a **SNAPSHOT** before using the **PRUNE** command.
- **Exclusions:** Keep your `exclude_dirs` updated to prevent chunking large, unnecessary assets like `__pycache__` or `build` folders.
- **SemVer:** Always use consistent semantic versioning to ensure unchunking logic can resolve versions correctly.

---

## 7. Compliance & Standards

The MFDB Chunker is built to uphold the highest standards of the BEJSON ecosystem.

### 7.1 BEJSON Positional Integrity
The core engine strictly adheres to index-based value mapping. This ensures that every tool in the ecosystem—from Python sub-agents to JavaScript parsers—can read the data without needing complex key-value mapping logic.
- **Mandate:** Never change the order of fields in `MANIFEST_FIELDS` or `ENTITY_FIELDS`.
- **Validation:** v6's integrity checker verifies this alignment.

### 7.2 MFDB Layer Registry Integration
The chunker acts as a first-class citizen of the Admin workspace. It proactively synchronizes with the `project.bejson` registry, making your chunked projects discoverable by other system tools and automated auditing scripts.
- **Automation:** Adding a project in the UI optionally registers it in the global registry.

### 7.3 Data Privacy & Local-First Philosophy
All chunking, serialization, and archiving happen locally on your device. No data is transmitted to external servers unless you explicitly push your repository to a remote Git host.
- **Zero Cloud:** The Flask app runs on `localhost` only.
- **Lossless:** Base64 encoding ensures no binary data is lost during text-based serialization.

---

## 8. Advanced Internal Logic

### 8.1 The "Relational" Advantage
Traditional "chunking" (v1-v4) often created a new file for every version. v5 and v6 use a relational row-based approach. 
**Scenario:** A project has 100 versions.
- **Old Way:** 100 separate BEJSON files. Slow to search, heavy on the disk.
- **New Way (v6):** 1 manifest file + 1 entity file containing all 100 versions as rows. Instant querying, efficient storage.

### 8.2 Base64 Serialization Logic
When `include_binary_base64` is True:
1. The chunker reads the file as raw bytes.
2. Converts bytes to an ASCII string via Base64.
3. Marks `is_base64 = True` in the row.
4. On unchunk, the engine reverses this, writing raw bytes back to disk.
- **Note:** This increases file size by approx 33% but ensures 100% portability.

### 8.3 Exclusion Logic
The scanning engine uses a "pruning" walk:
- It removes excluded directories from the walk list before entering them.
- This prevents the system from even scanning large folders like `.git`, making the process highly performant.

---

## 9. Version Migration & Compatibility

### 9.1 Upgrading from v5 to v6
- v6 is fully backwards compatible with v5 MFDB files.
- The `do_validate` and `do_snapshot` features can be run on existing v5 databases immediately.
- The new `ROOT_ADMIN` library resolution replaces the deprecated `env_libs` module.

### 9.2 Semantic Versioning Rules
The system enforces `MAJOR.MINOR.PATCH` format.
- **PATCH:** Bug fixes, non-breaking changes.
- **MINOR:** New features, additions.
- **MAJOR:** Breaking changes, structural refactors.

---

## 10. Troubleshooting & v6 Diagnostics

### 10.1 Global Error Interceptor
The v6 Dashboard includes a global `window.onerror` handler. If a front-end crash occurs, a red alert will appear in the log box with the exact JS line number and message.

### 10.2 Common Scenarios & Fixes
- **`ModuleNotFoundError: No module named 'env_libs'`**: Fixed in v6.0.0 by using the standardized `ROOT_ADMIN` bootstrap. Ensure you are running the latest `mfdb_chunker_app.py`.
- **`CRITICAL CHUNK ERROR`**: Usually caused by file permission issues in Termux. Run `termux-setup-storage` and ensure the script has write access to the target and output directories.
- **`JS ERROR (Line 0)`**: Check if the browser has JavaScript enabled or if an extension is blocking local AJAX calls.
- **`Validation error: Manifest not found`**: Ensure you provided the correct path to the `104a.mfdb.bejson` file, not just the directory.

---

## 11. API Reference (Internal Web Services)

The Flask app exposes the following internal endpoints for GUI interaction:
- `GET /api/ls?path=...`: Returns JSON directory listing for the file browser.
- `POST /api/chunk`: Executes the chunking engine with changelog and tags.
- `POST /api/validate`: Runs the integrity checker on the selected project.
- `POST /api/snapshot`: Triggers a full zip backup of the project MFDB.
- `GET /api/view-files`: Returns metadata for files within a specific chunked version.
- `POST /api/bump`: Increments the version in the project's config file.
- `POST /api/unchunk`: Restores a specific version back to the project folder.

---

## 12. Frequently Asked Questions (FAQ)

**Q: Can I chunk a project located on my SD card?**
A: Yes. Use the interactive File Selector to navigate to your specific mount point (usually `/storage/sdcard1`).

**Q: Does chunking replace Git?**
A: No. MFDB Chunker is designed for **relational archiving** and **AI-agent ingestion**. It complements Git by providing a tabular, machine-readable history of your codebase that agents can query as a database.

**Q: What is the maximum size of a chunked project?**
A: The system is tested with projects up to 500MB. For larger codebases, we recommend excluding heavy binary assets and using the Base64 toggle judiciously.

**Q: Can I manually edit the BEJSON files?**
A: Yes, provided you maintain **positional integrity**. We recommend using the `bejson_writer.py` tool for any manual modifications to ensure the schema remains valid.

---

## 13. Conclusion
MFDB Chunker v6.0.0 is the definitive standard for codebase serialization in 2026. By unifying version control, data integrity, and high-fidelity GUI experiences, it empowers developers to manage their code as a relational asset rather than a loose collection of files.

---
**Document Version:** 1.2.0  
**Date:** Sunday, May 24, 2026  
**Release:** v6.0.0 OFFICIAL PRO  
**Author:** Elton Boehnen  
**Site:** [boehnenelton2024.pages.dev](https://boehnenelton2024.pages.dev)  
**GitHub:** [github.com/boehnenelton/mfdb-chunker](https://github.com/boehnenelton/mfdb-chunker)

---
*Created with Gemini CLI for the BEJSON Ecosystem.*
