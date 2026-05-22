"""
Library:      lib_bejson_utility.py
Family:       Utility
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.2.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-21
Description:  Cross-compatible chunking utilities for CLI_CHUNKER and MFDB_V5.
              Follows strict best practices: Standard JSON module only, NO REGEX.
"""

import os
import sys
import json
import time
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Sibling Path Resolution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_LIB_DIR = os.path.dirname(CURRENT_DIR)
CORE_DIR = os.path.join(PARENT_LIB_DIR, "Core")
if CORE_DIR not in sys.path:
    sys.path.append(CORE_DIR)

try:
    import lib_bejson_core as BEJSONCore
except ImportError:
    print(f"Error: Core sibling not found at {CORE_DIR}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants & Official Schemas
# ---------------------------------------------------------------------------

DEFAULT_EXTENSIONS = [".py", ".js", ".ts", ".html", ".css", ".md", ".json", ".sh", ".txt", ".bejson", ".tsx", ".jsx"]
DEFAULT_EXCLUDES = [".git", "__pycache__", "node_modules", "lib", "output", ".mfdb_lock", "dist", "build"]

# Text Chunk Separators (Standardized)
SEP_START = "--- FILE: "
SEP_END = " ---"

# Official CLI_CHUNKER Schema (BEJSON 104db)
SCHEMA_CLI_CHUNKER = [
    {"name": "Record_Type_Parent", "type": "string"},
    {"name": "project_name", "type": "string", "Record_Type_Parent": "ProjectMeta"},
    {"name": "version", "type": "string", "Record_Type_Parent": "ProjectMeta"},
    {"name": "root_path", "type": "string", "Record_Type_Parent": "ProjectMeta"},
    {"name": "file_path", "type": "string", "Record_Type_Parent": "FileContent"},
    {"name": "file_name", "type": "string", "Record_Type_Parent": "FileContent"},
    {"name": "content", "type": "string", "Record_Type_Parent": "FileContent"},
    {"name": "is_binary", "type": "boolean", "Record_Type_Parent": "FileContent"}
]

# Official MFDB_V5 Entity Schema (BEJSON 104)
SCHEMA_MFDB_ENTITY = [
    {"name": "version",   "type": "string"},
    {"name": "file_path", "type": "string"},
    {"name": "file_name", "type": "string"},
    {"name": "content",   "type": "string"},
    {"name": "is_binary", "type": "boolean"},
    {"name": "is_base64", "type": "boolean"},
]

# Official MFDB_V5 Manifest Schema (BEJSON 104a)
SCHEMA_MFDB_MANIFEST = [
    {"name": "entity_name",    "type": "string"},
    {"name": "file_path",      "type": "string"},
    {"name": "description",    "type": "string"},
    {"name": "record_count",   "type": "integer"},
    {"name": "schema_version", "type": "string"},
    {"name": "primary_key",    "type": "string"},
    {"name": "changelog",      "type": "string"},
    {"name": "chunked_at",     "type": "string"},
    {"name": "tags",           "type": "string"},
]

# ---------------------------------------------------------------------------
# Data Sanitization (Best Practices - No Regex)
# ---------------------------------------------------------------------------

def bejson_utility_sanitize_name(name: str) -> str:
    """Sanitizes names for filesystem safety without using regex."""
    invalid = '<>:"/\\|?*'
    sanitized = name
    for char in invalid:
        sanitized = sanitized.replace(char, '_')
    return sanitized

def bejson_utility_slugify(text: str) -> str:
    """Creates a simple lowercase alphanumeric slug without regex."""
    slug = ""
    for char in text.lower():
        if char.isalnum():
            slug += char
        elif char in " -_":
            slug += "_"
    return slug

# ---------------------------------------------------------------------------
# Core Detection & Encoding
# ---------------------------------------------------------------------------

def bejson_utility_is_binary(file_path: Union[str, Path]) -> bool:
    """Detection logic matching official chunker tools."""
    try:
        with open(file_path, 'tr', encoding='utf-8') as f:
            f.read(1024)
            return False
    except (UnicodeDecodeError, PermissionError):
        return True

def bejson_utility_encode_file(file_path: Union[str, Path], use_base64: bool = False) -> tuple:
    """
    Reads file content and returns (content, is_binary, is_base64).
    Matches MFDB v5 lossless binary logic.
    """
    is_bin = bejson_utility_is_binary(file_path)
    if not is_bin:
        try:
            return Path(file_path).read_text(encoding="utf-8"), False, False
        except Exception:
            return "", True, False
    
    if use_base64:
        try:
            raw = Path(file_path).read_bytes()
            return base64.b64encode(raw).decode('utf-8'), True, True
        except Exception:
            return "", True, True
    
    return "", True, False

# ---------------------------------------------------------------------------
# Cross-Format Generators
# ---------------------------------------------------------------------------

def bejson_utility_create_cli_chunk(target_dir: str, project_name: str, version: str) -> dict:
    """Generates a BEJSON 104db document compatible with Cli_Chunker."""
    target_path = Path(target_dir).resolve()
    values = []
    
    # Meta record
    values.append(["ProjectMeta", project_name, version, str(target_path), None, None, None, None])
    
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDES]
        for file in files:
            f_path = Path(root) / file
            if f_path.suffix.lower() in DEFAULT_EXTENSIONS:
                try:
                    rel_path = f_path.relative_to(target_path)
                    content, binary, _ = bejson_utility_encode_file(f_path, use_base64=False)
                    values.append(["FileContent", None, None, None, str(rel_path), file, content, binary])
                except Exception: continue
                
    return BEJSONCore.bejson_core_create_104db(["ProjectMeta", "FileContent"], SCHEMA_CLI_CHUNKER, values)

def bejson_utility_create_mfdb_version(target_dir: str, version: str, use_base64: bool = True) -> list:
    """
    Generates a list of values for an MFDB v5 Entity file (BEJSON 104).
    """
    target_path = Path(target_dir).resolve()
    rows = []
    
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDES]
        for file in files:
            f_path = Path(root) / file
            if f_path.suffix.lower() in DEFAULT_EXTENSIONS:
                try:
                    rel_path = f_path.relative_to(target_path)
                    content, binary, b64 = bejson_utility_encode_file(f_path, use_base64=use_base64)
                    rows.append([version, str(rel_path), file, content, binary, b64])
                except Exception: continue
                
    return rows

# ---------------------------------------------------------------------------
# Text Chunking Logic (Non-Regex Implementation)
# ---------------------------------------------------------------------------

def bejson_utility_chunk_to_text(target_dir: str) -> str:
    """Concatenates files into a single text block with separators."""
    target_path = Path(target_dir).resolve()
    output = []
    
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUDES]
        for file in files:
            f_path = Path(root) / file
            if f_path.suffix.lower() in DEFAULT_EXTENSIONS and not bejson_utility_is_binary(f_path):
                try:
                    rel_path = f_path.relative_to(target_path)
                    content = f_path.read_text(encoding="utf-8")
                    output.append(f"{SEP_START}{rel_path}{SEP_END}")
                    output.append(content)
                    output.append("\n")
                except Exception: continue
                
    return "\n".join(output)

def bejson_utility_unchunk_from_text(text: str, output_dir: str) -> int:
    """Restores files from a text block using strictly string splitting."""
    count = 0
    out_root = Path(output_dir).resolve()
    
    # Split by the start separator
    parts = text.split(SEP_START)
    
    for part in parts:
        if not part.strip(): continue
        
        # Each part starts with: filename --- content
        if SEP_END in part:
            header, content = part.split(SEP_END, 1)
            rel_path = header.strip()
            
            if rel_path:
                target_file = out_root / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                target_file.write_text(content.lstrip("\n"), encoding="utf-8")
                count += 1
                
    return count

# ---------------------------------------------------------------------------
# Lifecycle Utilities (Standard JSON Module)
# ---------------------------------------------------------------------------

def bejson_utility_parse_json(text: str) -> Any:
    """Robust JSON parsing using strictly the json module."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Best practice: try to find the actual JSON object in a dirty string
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end+1])
        raise

def bejson_utility_save_chunk(path: str, doc: dict) -> bool:
    """Standardized atomic write for all chunking operations."""
    return BEJSONCore.bejson_core_atomic_write(path, doc)

def bejson_utility_get_timestamp() -> str:
    """ISO 8601 UTC timestamp for manifest consistency."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
