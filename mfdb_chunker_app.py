#!/usr/bin/env python3
"""
<!--
FILE:        mfdb_chunker_app.py
VERSION:     5.0.0
AUTHOR:      Elton Boehnen
EMAIL:       boehnenelton2024@gmail.com
GITHUB:      github.com/boehnenelton
SITE:        boehnenelton2024.pages.dev
DESCRIPTION: Flask UI for MFDB Chunker v5. Direct wrapper for all CLI features
             plus MFDB Layer Registry integration for project discovery.
COMPLIANCE:  MFDB Spec v1.31 | BEJSON Lib Family v2.0.1 OFFICIAL
-->
"""
import os
import sys
import json
import socket
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "lib"))

try:
    import lib_bejson_env as BEJSONEnv
    import lib_bejson_core as BEJSONCore
except ImportError:
    pass

from mfdb_chunker import (
    do_chunk, do_bump, do_unchunk,
    do_update_changelog, do_update_tags,
    do_prune, do_export, do_import,
    list_versions, get_manifest_meta,
    load_or_create_config, get_manifest_path,
    MFDB_SPEC_VERSION,
)

PROJECTS_FILE = BASE_DIR / "projects.json"
# Authoritative registry path
REGISTRY_PATH = "/storage/emulated/0/Admin/init/registry/mfdb_layers/data/project.bejson"
WRITER_TOOL   = "/storage/emulated/0/Admin/tools/bejson_writer.py"

def load_projects():
    """Loads projects from local file and merges with Layer Registry."""
    local_projects = []
    if PROJECTS_FILE.exists():
        try:
            with open(PROJECTS_FILE) as f:
                local_projects = json.load(f)
        except Exception:
            pass

    registry_projects = []
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH) as f:
                reg_doc = json.load(f)
                fields = reg_doc.get("Fields", [])
                values = reg_doc.get("Values", [])
                # Map fields to indices
                f_map = {f["name"].lower(): i for i, f in enumerate(fields)}
                for row in values:
                    if row is None or not any(row): continue
                    p_path = row[f_map.get("local_path", 2)]
                    if not p_path: continue
                    registry_projects.append({
                        "id": project_id_from_path(p_path),
                        "name": row[f_map.get("name", 0)],
                        "path": p_path,
                        "version": row[f_map.get("version", 4)],
                        "in_registry": True,
                        "guid": row[f_map.get("project_guid", 1)]
                    })
        except Exception:
            pass

    # Merge: Local projects take precedence if duplicate path
    merged = {p["path"]: p for p in registry_projects}
    for p in local_projects:
        p["in_registry"] = any(rp["path"] == p["path"] for rp in registry_projects)
        merged[p["path"]] = p
    
    return list(merged.values())

def save_projects(projects):
    # Only save local projects to projects.json (non-registry ones or local overrides)
    local_only = [p for p in projects if not p.get("in_registry") or "guid" not in p]
    # Actually, keep all in local for quick access, but mark them
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f, indent=2)

def find_project(pid):
    return next((p for p in load_projects() if p["id"] == pid), None)

def project_id_from_path(path):
    return path.strip("/\\").replace(os.sep, "_").replace(" ", "_")[-60:]

app = Flask(__name__)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MFDB CHUNKER v5</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Source+Code+Pro:wght@400;600&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --red:#DE2626;--bg:#0a0a0a;--surface:#111;--border:#222;
  --muted:#555;--text:#e0e0e0;--sub:#888;
  --mono:'Source Code Pro',monospace;--ui:'Inter',sans-serif;
}
body{background:var(--bg);color:var(--text);font-family:var(--ui);min-height:100vh}
.shell{display:flex;min-height:100vh}

/* Sidebar */
.sidebar{width:260px;min-width:260px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column}
.sidebar-head{padding:18px 16px 14px;border-bottom:1px solid var(--border)}
.sidebar-head h1{font-family:var(--mono);font-size:13px;letter-spacing:2px;color:var(--red);text-transform:uppercase;font-weight:600}
.sidebar-head p{font-size:10px;color:var(--muted);margin-top:3px;font-family:var(--mono)}
.project-list{flex:1;overflow-y:auto;padding:8px 0}
.project-item{padding:10px 16px;cursor:pointer;border-left:3px solid transparent;transition:background .15s,border-color .15s;position:relative}
.project-item:hover{background:#1a1a1a}
.project-item.active{border-left-color:var(--red);background:#1a1a1a}
.project-item .pname{font-family:var(--mono);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.project-item .ppath{font-size:10px;color:var(--muted);margin-top:2px;font-family:var(--mono);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.project-item .pver{font-size:10px;color:var(--red);margin-top:2px;font-family:var(--mono)}
.reg-indicator{position:absolute;right:10px;top:10px;width:6px;height:6px;border-radius:50%;background:#333}
.reg-indicator.on{background:#2a6a2a;box-shadow:0 0 5px #2a6a2a}

.add-project-form{padding:12px 16px;border-top:1px solid var(--border)}
.add-project-form p{font-size:10px;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:1px;font-family:var(--mono)}
.add-project-form input{width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:7px 9px;font-family:var(--mono);font-size:11px;border-radius:3px;outline:none}
.add-project-form input:focus{border-color:var(--red)}
.add-project-form button{width:100%;margin-top:6px;background:var(--red);color:#fff;border:none;padding:7px;font-family:var(--mono);font-size:11px;letter-spacing:1px;text-transform:uppercase;cursor:pointer;border-radius:3px}
.add-project-form button:hover{background:#c01f1f}
.sync-btn{width:100%;margin-top:6px;background:transparent;color:var(--sub);border:1px solid var(--border);padding:5px;font-family:var(--mono);font-size:9px;text-transform:uppercase;cursor:pointer;border-radius:2px}

/* Main */
.main{flex:1;overflow-y:auto;display:flex;flex-direction:column}
.topbar{padding:16px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:var(--surface)}
.topbar .proj-title{font-family:var(--mono);font-size:15px;font-weight:600}
.topbar .proj-meta{font-size:11px;color:var(--sub);font-family:var(--mono);margin-top:3px}
.topbar-right{display:flex;align-items:center;gap:12px}
.version-badge{background:var(--red);color:#fff;font-family:var(--mono);font-size:12px;padding:4px 12px;border-radius:3px;letter-spacing:1px}

.content{padding:24px;max-width:1000px;flex:1}
.section-label{font-family:var(--mono);font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:10px;margin-top:28px}
.section-label:first-child{margin-top:0}
.action-card{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:18px 20px;margin-bottom:14px}
.action-card h3{font-family:var(--mono);font-size:12px;letter-spacing:1px;text-transform:uppercase;color:var(--text);margin-bottom:12px}

.form-row{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap}
.field{display:flex;flex-direction:column;gap:5px;flex:1;min-width:160px}
.field label{font-size:10px;color:var(--muted);font-family:var(--mono);text-transform:uppercase;letter-spacing:1px}
.field input,.field textarea,.field select{background:var(--bg);border:1px solid var(--border);color:var(--text);padding:8px 10px;font-family:var(--mono);font-size:12px;border-radius:3px;outline:none;width:100%}
.field input:focus,.field textarea:focus,.field select:focus{border-color:var(--red)}
.field textarea{resize:vertical;min-height:58px}

.btn{font-family:var(--mono);font-size:11px;letter-spacing:1.5px;text-transform:uppercase;border:none;padding:9px 18px;border-radius:3px;cursor:pointer;white-space:nowrap;font-weight:600}
.btn-primary{background:var(--red);color:#fff}
.btn-primary:hover{background:#c01f1f}
.btn-ghost{background:transparent;color:var(--text);border:1px solid var(--border)}
.btn-ghost:hover{border-color:var(--red);color:var(--red)}
.btn-danger{background:transparent;color:#c04040;border:1px solid #6a2a2a}
.btn-danger:hover{background:#6a2a2a;color:#fff}
.btn-small{padding:5px 12px;font-size:10px}
.btn:disabled{opacity:.4;cursor:not-allowed}

.bump-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.bump-row .cur{font-family:var(--mono);font-size:14px;color:var(--red);margin-right:6px}

/* Version table */
.vtable{width:100%;border-collapse:collapse}
.vtable th{font-family:var(--mono);font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);padding:6px 8px;text-align:left;border-bottom:1px solid var(--border)}
.vtable td{font-family:var(--mono);font-size:11px;color:var(--text);padding:9px 8px;border-bottom:1px solid #1a1a1a;vertical-align:middle}
.vtable tr:last-child td{border-bottom:none}
.vtable td.ver{color:var(--red)}
.vtable td.dim{color:var(--muted)}

.tag-badge{display:inline-block;font-family:var(--mono);font-size:9px;padding:2px 7px;border-radius:20px;border:1px solid;margin:0 2px;text-transform:uppercase;letter-spacing:.5px}
.tag-stable{border-color:#2a6a2a;color:#7ec87e}
.tag-release{border-color:#2a4a8a;color:#7ab0e8}
.tag-hotfix{border-color:#8a4a2a;color:#e8b07a}
.tag-default{border-color:var(--border);color:var(--sub)}

.log-box{background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:14px 16px;font-family:var(--mono);font-size:11px;line-height:1.7;min-height:54px;color:var(--sub);margin-top:14px;white-space:pre-wrap;word-break:break-all}
.log-box.ok{border-color:#2a6a2a;color:#7ec87e}
.log-box.err{border-color:#6a2a2a;color:var(--red)}

.footer{padding:14px 24px;border-top:1px solid var(--border);font-family:var(--mono);font-size:10px;color:var(--muted);display:flex;justify-content:space-between}
.footer a{color:var(--muted);text-decoration:none}
.footer a:hover{color:var(--red)}

/* Modal */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:1000;align-items:center;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:28px 32px;max-width:400px;width:90%}
.modal h2{font-family:var(--mono);font-size:13px;letter-spacing:2px;text-transform:uppercase;color:var(--red);margin-bottom:10px}
.modal p{font-family:var(--mono);font-size:11px;color:var(--text);margin-bottom:20px;line-height:1.6}
.modal-actions{display:flex;gap:10px;justify-content:flex-end}
</style>
</head>
<body>
<div class="shell">

<aside class="sidebar">
  <div class="sidebar-head">
    <h1>MFDB Chunker v5</h1>
    <p>SPEC {{ spec_ver }} · LIB v2.0.1</p>
  </div>
  <div class="project-list">
    {% for p in projects %}
    <div class="project-item {% if selected and selected.id == p.id %}active{% endif %}"
         onclick="selectProject('{{ p.id }}')">
      <div class="pname">{{ p.name }}</div>
      <div class="ppath">{{ p.path }}</div>
      <div class="pver">v{{ p.version }}</div>
      <div class="reg-indicator {% if p.in_registry %}on{% endif %}" title="{% if p.in_registry %}In Registry{% else %}Local Only{% endif %}"></div>
    </div>
    {% endfor %}
  </div>
  <div class="add-project-form">
    <p>Add Project</p>
    <input type="text" id="newProjectPath" placeholder="/path/to/project">
    <button onclick="addProject()">+ ADD</button>
    <button class="sync-btn" onclick="syncRegistry()">↻ Sync from Registry</button>
  </div>
</aside>

<div class="main">
{% if selected %}
<div class="topbar">
  <div>
    <div class="proj-title">{{ selected.name }}</div>
    <div class="proj-meta">{{ selected.path }}</div>
  </div>
  <div class="topbar-right">
    {% if not selected.in_registry %}
    <button class="btn btn-ghost btn-small" onclick="registerProject()">REGISTER</button>
    {% endif %}
    <div class="version-badge">v{{ selected.version }}</div>
  </div>
</div>

<div class="content">
  <div class="section-label">Version Control</div>
  <div class="action-card">
    <h3>Bump Version</h3>
    <div class="bump-row">
      <span class="cur">{{ selected.version }}</span>
      <button class="btn btn-ghost" onclick="bump('patch')">PATCH</button>
      <button class="btn btn-ghost" onclick="bump('minor')">MINOR</button>
      <button class="btn btn-ghost" onclick="bump('major')">MAJOR</button>
    </div>
  </div>

  <div class="section-label">Snapshot</div>
  <div class="action-card">
    <h3>Create New Version Snapshot</h3>
    <div class="form-row">
      <div class="field" style="flex:2">
        <label>Changelog</label>
        <textarea id="changelog" placeholder="What changed?"></textarea>
      </div>
      <div class="field" style="flex:1">
        <label>Tags</label>
        <input type="text" id="tags" placeholder="stable, release">
      </div>
      <button class="btn btn-primary" onclick="chunk()">CHUNK</button>
    </div>
  </div>

  <div class="section-label">History</div>
  <div class="action-card">
    {% if versions %}
    <table class="vtable">
      <thead><tr><th>VERSION</th><th>FILES</th><th>DATE</th><th>CHANGELOG</th><th></th></tr></thead>
      <tbody>
        {% for v in versions|reverse %}
        <tr>
          <td class="ver">{{ v.schema_version }}</td>
          <td class="dim">{{ v.record_count }}</td>
          <td class="dim">{{ (v.chunked_at or '')[:16]|replace('T',' ') }}</td>
          <td>{{ v.changelog or '—' }}</td>
          <td>
            <div style="display:flex;gap:5px">
              <button class="btn btn-ghost btn-small" onclick="restore('{{ v.schema_version }}')">RESTORE</button>
              <button class="btn btn-ghost btn-small" onclick="exportVer('{{ v.schema_version }}')">EXPORT</button>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div style="color:var(--muted);font-size:11px">NO VERSIONS RECORDED</div>
    {% endif %}
  </div>

  <div class="log-box" id="statusLog">READY</div>
</div>

<div class="footer">
  <span>BEJSON Ecosystem · v5.0.0</span>
  <span>MFDB {{ spec_ver }} · LIB v2.0.1 OFFICIAL</span>
</div>
{% else %}
<div class="empty"><h2>No Project Selected</h2><p>Add or sync projects to begin.</p></div>
{% endif %}
</div>
</div>

<script>
const PROJECT_ID = {{ ('"' + selected.id + '"') if selected else 'null' }};
function log(msg, state) {
  const el = document.getElementById('statusLog');
  if (!el) return;
  el.textContent = msg;
  el.className = 'log-box ' + (state || '');
}
function selectProject(id) { window.location.href = '/?project=' + encodeURIComponent(id); }
async function addProject() {
  const path = document.getElementById('newProjectPath').value.trim();
  if (!path) return;
  const r = await fetch('/api/add-project', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({path})
  }).then(r => r.json());
  if (r.ok) window.location.reload();
}
async function syncRegistry() {
    log('SYNCING WITH LAYER REGISTRY...', '');
    const r = await fetch('/api/sync-registry', {method:'POST'}).then(r=>r.json());
    if(r.ok) window.location.reload();
    else log('SYNC FAILED: ' + r.message, 'err');
}
async function registerProject() {
    if(!PROJECT_ID) return;
    log('REGISTERING PROJECT IN GLOBAL REGISTRY...', '');
    const r = await fetch('/api/register-in-registry', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({project_id: PROJECT_ID})
    }).then(r=>r.json());
    if(r.ok) { log('SUCCESSFULLY REGISTERED', 'ok'); setTimeout(()=>window.location.reload(), 1000); }
    else log('REGISTRATION FAILED: ' + r.message, 'err');
}
async function bump(part) {
  const r = await fetch('/api/bump', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, part})
  }).then(r => r.json());
  if (r.ok) window.location.reload();
}
async function chunk() {
  const changelog = document.getElementById('changelog').value;
  const tags = document.getElementById('tags').value;
  log('CHUNKING...', '');
  const r = await fetch('/api/chunk', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, changelog, tags})
  }).then(r => r.json());
  if (r.ok) window.location.reload();
}
async function restore(ver) {
  log('RESTORING '+ver+'...', '');
  const r = await fetch('/api/unchunk', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, version:ver})
  }).then(r => r.json());
  if (r.ok) log('RESTORED TO: ' + r.out_dir, 'ok');
}
async function exportVer(ver) {
  log('EXPORTING...', '');
  const r = await fetch('/api/export', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, version:ver})
  }).then(r => r.json());
  if (r.ok) window.location.href = '/api/download-export?path=' + encodeURIComponent(r.zip_path);
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    projects = load_projects()
    sid = request.args.get("project")
    selected = find_project(sid) if sid else (projects[0] if projects else None)
    versions = []
    if selected:
        config = load_or_create_config(Path(selected["path"]))
        selected["version"] = config.get("version", "1.0.0")
        manifest = get_manifest_path(config)
        if manifest.exists():
            versions = list_versions(str(manifest))
    return render_template_string(HTML, projects=projects, selected=selected, versions=versions, spec_ver=MFDB_SPEC_VERSION)

@app.route("/api/add-project", methods=["POST"])
def api_add_project():
    data = request.get_json() or {}
    path = data.get("path", "").strip()
    if not path or not os.path.isdir(path): return jsonify({"ok":False, "message":"Invalid path"})
    projects = load_projects()
    pid = project_id_from_path(path)
    if not any(p["id"] == pid for p in projects):
        config = load_or_create_config(Path(path))
        projects.append({"id":pid, "name":config.get("project_name", Path(path).name), "path":path, "version":config.get("version","1.0.0")})
        save_projects(projects)
    return jsonify({"ok":True, "id":pid})

@app.route("/api/sync-registry", methods=["POST"])
def api_sync_registry():
    # reload_projects already merges from registry
    return jsonify({"ok":True, "message":"Synced with Layer Registry"})

@app.route("/api/register-in-registry", methods=["POST"])
def api_register_in_registry():
    data = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project: return jsonify({"ok":False, "message":"Project not found"})
    
    guid = f"proj-{project['id'][:12]}-{datetime.now().strftime('%H%M%S')}"
    # Register in Layer Registry via bejson_writer
    # Fields: name, project_guid, local_path, repo_url, status, is_active, last_sync
    row = [project["name"], guid, project["path"], "", "ACTIVE", True, datetime.now().isoformat()]
    
    try:
        subprocess.run(["python3", WRITER_TOOL, "--file", REGISTRY_PATH, "--action", "append", "--data", json.dumps(row)], check=True)
        return jsonify({"ok":True, "message":"Registered in global registry"})
    except Exception as e:
        return jsonify({"ok":False, "message":str(e)})

@app.route("/api/chunk", methods=["POST"])
def api_chunk():
    data = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project: return jsonify({"ok":False, "message":"Project not found"})
    return jsonify(do_chunk(project["path"], data.get("changelog", ""), data.get("tags", "")))

@app.route("/api/bump", methods=["POST"])
def api_bump():
    data = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project: return jsonify({"ok":False})
    return jsonify(do_bump(project["path"], data.get("part", "patch")))

@app.route("/api/unchunk", methods=["POST"])
def api_unchunk():
    data = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project: return jsonify({"ok":False})
    config = load_or_create_config(Path(project["path"]))
    return jsonify(do_unchunk(str(get_manifest_path(config)), data.get("version", "")))

@app.route("/api/export", methods=["POST"])
def api_export():
    data = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project: return jsonify({"ok":False})
    config = load_or_create_config(Path(project["path"]))
    manifest = str(get_manifest_path(config))
    version = data.get("version", "")
    out_path = str(Path(config["output_base"]) / "exports" / f"{config['project_name']}-{version}.mfdb.zip")
    return jsonify(do_export(manifest, version, out_path))

@app.route("/api/download-export")
def api_download_export():
    path = request.args.get("path", "")
    if not path or not os.path.exists(path): return "Not found", 404
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    port = 5100
    for p in range(5100, 5120):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                port = p
                break
    print(f"--- MFDB CHUNKER UI v5.0.0 ---")
    print(f"MFDB Spec : {MFDB_SPEC_VERSION}")
    print(f"URL       : http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
