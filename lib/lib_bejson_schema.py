"""
Library:      lib_bejson_schema.py
Family:       Core
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.1.0 OFFICIAL (Unified Schema Registry)
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-22
Description:  Unified registry for authoritative BEJSON schemas.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# ===========================================================================
# AUTHORITATIVE SCHEMA DEFINITIONS
# ===========================================================================

# 1. Project Management v1.4.0 (22 Fields)
# Aligns ProjectService with official tracking standards.
SCHEMA_PROJECT_v140 = [
    {"name": "Record_Type_Parent",    "type": "string"},  # 0
    {"name": "Project_ID",            "type": "string"},  # 1
    {"name": "Project_Name",          "type": "string"},  # 2
    {"name": "Project_Path",          "type": "string"},  # 3
    {"name": "Version",               "type": "string"},  # 4
    {"name": "Created_At",            "type": "string"},  # 5
    {"name": "Project_Type",          "type": "string"},  # 6
    {"name": "Is_Active",             "type": "boolean"}, # 7
    {"name": "Is_Visible",            "type": "boolean"}, # 8
    {"name": "Is_Missing",            "type": "boolean"}, # 9
    {"name": "Description",           "type": "string"},  # 10
    {"name": "Tags",                  "type": "string"},  # 11
    {"name": "Primary_Agent",         "type": "string"},  # 12
    {"name": "Last_Sync",             "type": "string"},  # 13
    {"name": "File_Count",            "type": "integer"}, # 14
    {"name": "Total_Size_KB",         "type": "number"},  # 15
    {"name": "Git_Enabled",           "type": "boolean"}, # 16
    {"name": "Priority",              "type": "integer"}, # 17
    {"name": "Category",              "type": "string"},  # 18
    {"name": "Internal_Notes",        "type": "string"},  # 19
    {"name": "Is_Archived",           "type": "boolean"}, # 20
    {"name": "Is_Reset_Protected",    "type": "boolean"}, # 21
]

# 2. MFDB Chunker v5 Entity (6 Fields)
# Authoritative for project file contents.
SCHEMA_MFDB_ENTITY_v5 = [
    {"name": "version",   "type": "string"},
    {"name": "file_path", "type": "string"},
    {"name": "file_name", "type": "string"},
    {"name": "content",   "type": "string"},
    {"name": "is_binary", "type": "boolean"},
    {"name": "is_base64", "type": "boolean"},
]

# 3. MFDB Chunker v5 Manifest (9 Fields)
SCHEMA_MFDB_MANIFEST_v5 = [
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

# 4. AI Model Registry v2.0.1 (Fixed Model Drift)
# Defaulted to Gemini 2.5 Flash as per audit recommendation.
SCHEMA_MODEL_REGISTRY = {
    "Format": "BEJSON",
    "Format_Version": "104a",
    "Format_Creator": "Elton Boehnen",
    "Records_Type": ["AI_Model"],
    "Fields": [
        {"name": "Record_Type_Parent",    "type": "string"},
        {"name": "model_id",              "type": "string"},
        {"name": "display_name",          "type": "string"},
        {"name": "thinking_enabled",      "type": "boolean"},
        {"name": "google_search_enabled", "type": "boolean"},
        {"name": "currently_active",      "type": "boolean"}
    ],
    "Values": [
        ["AI_Model", "gemini-2.5-flash", "Gemini 2.5 Flash", False, True, True],
        ["AI_Model", "gemini-2.0-flash-thinking-preview", "Gemini 2.0 Flash Thinking", True, False, False],
        ["AI_Model", "gemini-3.1-pro-preview", "Gemini 3.1 Pro (Preview)", False, True, False]
    ]
}

# ===========================================================================
# UTILITY FUNCTIONS
# ===========================================================================

def bejson_schema_extract(doc: Dict[str, Any]) -> Dict[str, Any]:
    schema = doc.copy()
    schema["Values"] = []
    return schema

def bejson_schema_validate_against(doc: Dict[str, Any], schema_fields: List[Dict[str, Any]]) -> bool:
    doc_fields = doc.get("Fields", [])
    if len(doc_fields) != len(schema_fields):
        return False
    for i, (df, sf) in enumerate(zip(doc_fields, schema_fields)):
        if df.get("name") != sf.get("name") or df.get("type") != sf.get("type"):
            return False
    return True

