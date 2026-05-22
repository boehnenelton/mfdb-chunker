"""
Library:      lib_be_core.py
Family:       Core
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  BE-specific core system abstractions and utility wrappers.
"""

import os
import sys
import time
from pathlib import Path

try:
    import fcntl
except ImportError:
    fcntl = None

_DEFAULT_BEC_ROOT = str(Path(__file__).resolve().parent.parent.parent)

class SimpleLock:
    """Portable file lock using directory creation."""
    def __init__(self, lock_path):
        self.lock_dir = lock_path + ".lockdir"
        self.is_locked = False

    def acquire(self, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                os.mkdir(self.lock_dir)
                self.is_locked = True
                return True
            except FileExistsError:
                time.sleep(0.1)
        return False

    def release(self):
        if self.is_locked:
            try:
                os.rmdir(self.lock_dir)
            except OSError:
                pass
            self.is_locked = False

def get_bec_root():
    root_env = os.environ.get("BEC_ROOT")
    if root_env: return root_env
    root_file = os.path.join(_DEFAULT_BEC_ROOT, "data/state/BEC_ROOT.txt")
    if os.path.exists(root_file):
        with open(root_file, 'r') as f: return f.read().strip()
    return _DEFAULT_BEC_ROOT

def save_state(manager, key, value):
    """Saves a key-value pair to a manager state file with locking to prevent races."""
    root = get_bec_root()
    state_file = os.path.join(root, f"data/state/{manager}_manager_state.txt")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    
    lock = SimpleLock(state_file)
    if not lock.acquire():
        print(f"Error: Timeout acquiring lock for {state_file}")
        return

    try:
        lines = []
        if os.path.exists(state_file):
            with open(state_file, 'r') as f: lines = f.readlines()
        
        key_found = False
        new_lines = []
        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                key_found = True
            else: new_lines.append(line)
        
        if not key_found: new_lines.append(f"{key}={value}\n")
        
        tmp_file = state_file + ".tmp"
        with open(tmp_file, 'w') as f:
            f.writelines(new_lines)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_file, state_file)
    except Exception as e:
        print(f"Error saving state: {e}")
    finally:
        lock.release()

def load_state(manager, key):
    root = get_bec_root()
    state_file = os.path.join(root, f"data/state/{manager}_manager_state.txt")
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            for line in f:
                if line.startswith(f"{key}="): return line.split("=", 1)[1].strip()
    return ""

def load_all_state(manager):
    root = get_bec_root()
    state_file = os.path.join(root, f"data/state/{manager}_manager_state.txt")
    state_dict = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            for line in f:
                if "=" in line:
                    k, v = line.split("=", 1)
                    state_dict[k.strip()] = v.strip()
    return state_dict
