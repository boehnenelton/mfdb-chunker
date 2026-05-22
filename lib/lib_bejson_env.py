"""
Library:      lib_bejson_env.py
Family:       Core
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Environment and path resolution utility for the BEJSON ecosystem.
"""

import os
import sys

def resolve_path(path_str: str) -> str:
    """
    Resolves system placeholders and absolute paths to environment-relative paths.
    Prioritizes environment variables (SC_ROOT, INTERNAL_STORAGE, etc).
    """
    if not path_str:
        return path_str
    
    # Define standard roots with defaults
    # Use os.path.expanduser("~") for a more portable home default
    default_home = os.path.expanduser("~")
    home = os.getenv("HOME", default_home)
    
    # INTERNAL_STORAGE often points to /storage/emulated/0 on Android
    internal_storage = os.getenv("INTERNAL_STORAGE", "/storage/emulated/0")
    
    # SC_ROOT is typically within INTERNAL_STORAGE
    default_sc_root = os.path.join(internal_storage, "Brain-Container/BEJSON_Core")
    sc_root = os.getenv("SC_ROOT", default_sc_root)
    
    mappings = {
        "{SC_ROOT}": sc_root,
        "{INTERNAL_STORAGE}": internal_storage,
        "{HOME}": home,
        # Legacy absolute paths to be replaced
        "/storage/emulated/0": internal_storage,
        "/Data/Data/com.termux/files/home": home,
        "/data/data/com.termux/files/home": home
    }
    
    resolved = str(path_str)
    
    # Sort keys by length descending to avoid partial matches (e.g. {HOME}_STUFF)
    for placeholder in sorted(mappings.keys(), key=len, reverse=True):
        actual = mappings[placeholder]
        if actual:
            resolved = resolved.replace(placeholder, actual)
    
    # Handle home expansion
    resolved = os.path.expanduser(resolved)
    # Handle environment variables in path (e.g. $SC_ROOT)
    resolved = os.path.expandvars(resolved)
    
    return os.path.normpath(resolved)

def get_env_path(env_var: str, default: str) -> str:
    """Retrieves an environment variable and resolves it as a path."""
    val = os.getenv(env_var, default)
    return resolve_path(val)
