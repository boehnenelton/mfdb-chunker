#!/usr/bin/env python3
"""
<!--
FILE:        mfdb_chunker_app.py
VERSION:     5.0.0
AUTHOR:      Elton Boehnen
EMAIL:       boehnenelton2024@gmail.com
GITHUB:      github.com/boehnenelton
SITE:        boehnenelton2024.pages.dev
DESCRIPTION: Flask UI for MFDB Chunker v2. Project mode, version tagging,
             inline changelog editing, prune with confirmation, export zip,
             import zip with conflict resolution.
COMPLIANCE:  MFDB Spec v1.31
CHANGELOG:
  2.0.0 - Rebuilt for v2 architecture. Tagging, inline changelog edit,
          prune confirm modal, export zip, import zip.
  1.2.0 - Initial Flask UI release.
-->
"""
import os
import sys
import json
import socket
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string, send_file

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from mfdb_chunker import (
    do_chunk, do_bump, do_unchunk,
    do_update_changelog, do_update_tags,
    do_prune, do_export, do_import,
    list_versions, get_manifest_meta,
    load_or_create_config, get_manifest_path,
    MFDB_SPEC_VERSION,
)

PROJECTS_FILE = BASE_DIR / "projects.json"


def load_projects():
    if not PROJECTS_FILE.exists():
        return []
    try:
        with open(PROJECTS_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_projects(projects):
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
<title>MFDB CHUNKER</title>
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
.project-item{padding:10px 16px;cursor:pointer;border-left:3px solid transparent;transition:background .15s,border-color .15s}
.project-item:hover{background:#1a1a1a}
.project-item.active{border-left-color:var(--red);background:#1a1a1a}
.project-item .pname{font-family:var(--mono);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.project-item .ppath{font-size:10px;color:var(--muted);margin-top:2px;font-family:var(--mono);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.project-item .pver{font-size:10px;color:var(--red);margin-top:2px;font-family:var(--mono)}
.add-project-form{padding:12px 16px;border-top:1px solid var(--border)}
.add-project-form p{font-size:10px;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:1px;font-family:var(--mono)}
.add-project-form input{width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);padding:7px 9px;font-family:var(--mono);font-size:11px;border-radius:3px;outline:none}
.add-project-form input:focus{border-color:var(--red)}
.add-project-form button{width:100%;margin-top:6px;background:var(--red);color:#fff;border:none;padding:7px;font-family:var(--mono);font-size:11px;letter-spacing:1px;text-transform:uppercase;cursor:pointer;border-radius:3px}
.add-project-form button:hover{background:#c01f1f}

/* Main */
.main{flex:1;overflow-y:auto;display:flex;flex-direction:column}
.topbar{padding:16px 24px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;background:var(--surface)}
.topbar .proj-title{font-family:var(--mono);font-size:15px;font-weight:600}
.topbar .proj-meta{font-size:11px;color:var(--sub);font-family:var(--mono);margin-top:3px}
.version-badge{background:var(--red);color:#fff;font-family:var(--mono);font-size:12px;padding:4px 12px;border-radius:3px;letter-spacing:1px}

.content{padding:24px;max-width:960px;flex:1}
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
.btn:disabled{opacity:.4;cursor:not-allowed}

.bump-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.bump-row .cur{font-family:var(--mono);font-size:14px;color:var(--red);margin-right:6px}

/* Tag filter row */
.tag-filter-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.tag-filter-row span{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase}
.tag-pill{font-family:var(--mono);font-size:10px;padding:3px 10px;border-radius:20px;border:1px solid var(--border);background:transparent;color:var(--sub);cursor:pointer;letter-spacing:1px;text-transform:uppercase}
.tag-pill:hover,.tag-pill.active{border-color:var(--red);color:var(--red);background:#1a0a0a}
.tag-pill.all.active{background:#DE262622}

/* Version table */
.vtable{width:100%;border-collapse:collapse}
.vtable th{font-family:var(--mono);font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);padding:6px 8px;text-align:left;border-bottom:1px solid var(--border)}
.vtable td{font-family:var(--mono);font-size:11px;color:var(--text);padding:9px 8px;border-bottom:1px solid #1a1a1a;vertical-align:middle}
.vtable tr:last-child td{border-bottom:none}
.vtable tr.hidden-row{display:none}
.vtable td.ver{color:var(--red)}
.vtable td.dim{color:var(--muted)}

/* Tag badges in table */
.tag-badge{display:inline-block;font-family:var(--mono);font-size:9px;padding:2px 7px;border-radius:20px;border:1px solid;margin:0 2px;text-transform:uppercase;letter-spacing:.5px}
.tag-stable{border-color:#2a6a2a;color:#7ec87e}
.tag-release{border-color:#2a4a8a;color:#7ab0e8}
.tag-hotfix{border-color:#8a4a2a;color:#e8b07a}
.tag-default{border-color:var(--border);color:var(--sub)}

/* Inline edit */
.inline-edit{display:none;background:var(--bg);border:1px solid var(--red);color:var(--text);font-family:var(--mono);font-size:11px;padding:4px 8px;border-radius:3px;width:100%;outline:none}
.edit-val{cursor:pointer}
.edit-val:hover{color:var(--red)}

/* Row actions */
.row-actions{display:flex;gap:6px;white-space:nowrap}
.row-btn{background:none;border:1px solid var(--border);color:var(--sub);font-family:var(--mono);font-size:10px;padding:3px 9px;border-radius:2px;cursor:pointer;letter-spacing:1px;text-transform:uppercase;white-space:nowrap}
.row-btn:hover{border-color:var(--red);color:var(--red)}
.row-btn.danger:hover{border-color:#c04040;color:#c04040}

/* Import section */
.import-drop{border:2px dashed var(--border);border-radius:4px;padding:24px;text-align:center;cursor:pointer;transition:border-color .2s}
.import-drop:hover,.import-drop.over{border-color:var(--red)}
.import-drop p{font-family:var(--mono);font-size:11px;color:var(--muted);letter-spacing:1px}
.import-drop input[type=file]{display:none}

/* Confirm modal */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:1000;align-items:center;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:var(--surface);border:1px solid var(--border);border-radius:4px;padding:28px 32px;max-width:400px;width:90%}
.modal h2{font-family:var(--mono);font-size:13px;letter-spacing:2px;text-transform:uppercase;color:var(--red);margin-bottom:10px}
.modal p{font-family:var(--mono);font-size:11px;color:var(--text);margin-bottom:20px;line-height:1.6}
.modal-actions{display:flex;gap:10px;justify-content:flex-end}

/* Log box */
.log-box{background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:14px 16px;font-family:var(--mono);font-size:11px;line-height:1.7;min-height:54px;color:var(--sub);margin-top:14px;white-space:pre-wrap;word-break:break-all}
.log-box.ok{border-color:#2a6a2a;color:#7ec87e}
.log-box.err{border-color:#6a2a2a;color:var(--red)}

.empty{text-align:center;padding:80px 20px;color:var(--muted);font-family:var(--mono);font-size:12px;letter-spacing:1px}
.empty h2{font-size:13px;color:var(--sub);margin-bottom:8px;text-transform:uppercase}

.footer{padding:14px 24px;border-top:1px solid var(--border);font-family:var(--mono);font-size:10px;color:var(--muted);display:flex;justify-content:space-between}
.footer a{color:var(--muted);text-decoration:none}
.footer a:hover{color:var(--red)}

@media(max-width:640px){
  .shell{flex-direction:column}
  .sidebar{width:100%;min-width:100%;border-right:none;border-bottom:1px solid var(--border)}
  .project-list{max-height:180px}
}
</style>
</head>
<body>
<div class="shell">

<!-- Sidebar -->
<aside class="sidebar">
  <div class="sidebar-head">
    <h1>MFDB Chunker</h1>
    <p>MFDB SPEC {{ spec_ver }} · V2</p>
  </div>
  <div class="project-list">
    {% for p in projects %}
    <div class="project-item {% if selected and selected.id == p.id %}active{% endif %}"
         onclick="selectProject('{{ p.id }}')">
      <div class="pname">{{ p.name }}</div>
      <div class="ppath">{{ p.path }}</div>
      <div class="pver">v{{ p.version }}</div>
    </div>
    {% endfor %}
    {% if not projects %}
    <div style="padding:20px 16px;font-family:var(--mono);font-size:11px;color:var(--muted)">NO PROJECTS YET</div>
    {% endif %}
  </div>
  <div class="add-project-form">
    <p>Add Project</p>
    <input type="text" id="newProjectPath" placeholder="/path/to/project">
    <button onclick="addProject()">+ ADD</button>
  </div>
</aside>

<!-- Main -->
<div class="main">
{% if selected %}
<div class="topbar">
  <div>
    <div class="proj-title">{{ selected.name }}</div>
    <div class="proj-meta">{{ selected.path }}</div>
  </div>
  <div class="version-badge" id="versionBadge">v{{ selected.version }}</div>
</div>

<div class="content">

  <!-- BUMP -->
  <div class="section-label">Version Control</div>
  <div class="action-card">
    <h3>Bump Version</h3>
    <div class="bump-row">
      <span class="cur" id="curVersion">{{ selected.version }}</span>
      <button class="btn btn-ghost" onclick="bump('patch')">PATCH</button>
      <button class="btn btn-ghost" onclick="bump('minor')">MINOR</button>
      <button class="btn btn-ghost" onclick="bump('major')">MAJOR</button>
    </div>
  </div>

  <!-- CHUNK -->
  <div class="section-label">Chunk Project</div>
  <div class="action-card">
    <h3>Create New Version Snapshot</h3>
    <div class="form-row">
      <div class="field" style="flex:2">
        <label>Changelog / Notes</label>
        <textarea id="changelog" placeholder="What changed in this version?"></textarea>
      </div>
      <div class="field" style="flex:1">
        <label>Tags (comma-separated)</label>
        <input type="text" id="tags" placeholder="stable, release, hotfix">
      </div>
      <div class="field" style="flex:0 0 auto;justify-content:flex-end">
        <label>Options</label>
        <label style="display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:11px;color:var(--sub);cursor:pointer;padding:8px 0">
          <input type="checkbox" id="inclBase64" style="accent-color:var(--red);width:14px;height:14px">
          INCLUDE BINARY AS BASE64
        </label>
      </div>
      <button class="btn btn-primary" onclick="chunk()">CHUNK</button>
    </div>
  </div>

  <!-- HISTORY -->
  <div class="section-label">Version History</div>
  <div class="action-card">

    <!-- Tag filter -->
    {% if all_tags %}
    <div class="tag-filter-row">
      <span>Filter:</span>
      <button class="tag-pill all active" onclick="filterTag('', this)">ALL</button>
      {% for tag in all_tags %}
      <button class="tag-pill" onclick="filterTag('{{ tag }}', this)">{{ tag }}</button>
      {% endfor %}
    </div>
    {% endif %}

    {% if versions %}
    <table class="vtable" id="versionTable">
      <thead>
        <tr>
          <th>VERSION</th>
          <th>FILES</th>
          <th>CHUNKED AT</th>
          <th>CHANGELOG</th>
          <th>TAGS</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {% for v in versions|reverse %}
        <tr data-tags="{{ v.tags or '' }}">
          <td class="ver">{{ v.schema_version or v.entity_name }}</td>
          <td class="dim">{{ v.record_count }}</td>
          <td class="dim">{{ (v.chunked_at or '')[:19]|replace('T',' ') }}</td>
          <td>
            <span class="edit-val" title="Click to edit"
              onclick="startEditChangelog('{{ v.schema_version }}', this)">{{ v.changelog or '—' }}</span>
            <input class="inline-edit" type="text"
              onblur="saveChangelog('{{ v.schema_version }}', this)"
              onkeydown="if(event.key==='Enter')this.blur();if(event.key==='Escape')cancelEdit(this)">
          </td>
          <td>
            {% if v.tags %}
              {% for tag in v.tags.split(',') %}
                {% set t = tag.strip() %}
                {% if t %}
                <span class="tag-badge tag-{{ t if t in ['stable','release','hotfix'] else 'default' }}">{{ t }}</span>
                {% endif %}
              {% endfor %}
            {% else %}—{% endif %}
            <button class="row-btn" onclick="editTags('{{ v.schema_version }}', '{{ v.tags or '' }}')"
              title="Edit tags" style="margin-left:4px">✎</button>
          </td>
          <td>
            <div class="row-actions">
              <button class="row-btn" onclick="restore('{{ v.schema_version }}')">RESTORE</button>
              <button class="row-btn" onclick="exportVer('{{ v.schema_version }}')">EXPORT</button>
              <button class="row-btn danger" onclick="confirmPrune('{{ v.schema_version }}')">PRUNE</button>
            </div>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <div style="color:var(--muted);font-family:var(--mono);font-size:11px;padding:10px 0">
      NO VERSIONS YET — CHUNK THIS PROJECT TO BEGIN
    </div>
    {% endif %}
  </div>

  <!-- IMPORT -->
  <div class="section-label">Import</div>
  <div class="action-card">
    <h3>Import Zip Package</h3>
    <div class="form-row" style="align-items:flex-start">
      <div class="field" style="flex:2">
        <label>Zip File</label>
        <div class="import-drop" id="importDrop" onclick="document.getElementById('importFile').click()"
             ondragover="event.preventDefault();this.classList.add('over')"
             ondragleave="this.classList.remove('over')"
             ondrop="handleDropImport(event)">
          <p id="importDropLabel">CLICK OR DROP A .MFDB.ZIP FILE HERE</p>
          <input type="file" id="importFile" accept=".zip" onchange="handleImportFile(this)">
        </div>
      </div>
      <div class="field" style="flex:1">
        <label>On Conflict</label>
        <select id="conflictMode">
          <option value="reject">REJECT DUPLICATES</option>
          <option value="prefix">PREFIX (_imp)</option>
        </select>
      </div>
      <button class="btn btn-ghost" id="importBtn" disabled onclick="importZip()">IMPORT</button>
    </div>
  </div>

  <div class="log-box" id="statusLog">READY</div>

</div><!-- /content -->

<div class="footer">
  <span>Elton Boehnen ·
    <a href="https://boehnenelton2024.pages.dev" target="_blank">boehnenelton2024.pages.dev</a> ·
    <a href="https://github.com/boehnenelton" target="_blank">github.com/boehnenelton</a>
  </span>
  <span>MFDB {{ spec_ver }}</span>
</div>

{% else %}
<div class="empty">
  <h2>No Project Selected</h2>
  <p>Add a project path in the sidebar to get started.</p>
</div>
{% endif %}
</div><!-- /main -->
</div><!-- /shell -->

<!-- Prune confirm modal -->
<div class="modal-overlay" id="pruneModal">
  <div class="modal">
    <h2>⚠ CONFIRM PRUNE</h2>
    <p id="pruneMsg">This will permanently delete this version from the manifest and all its file records from the entity file. This cannot be undone.</p>
    <div class="modal-actions">
      <button class="btn btn-ghost" onclick="closePruneModal()">CANCEL</button>
      <button class="btn btn-danger" id="pruneConfirmBtn" onclick="executePrune()">DELETE VERSION</button>
    </div>
  </div>
</div>

<!-- Tag edit modal -->
<div class="modal-overlay" id="tagModal">
  <div class="modal">
    <h2>EDIT TAGS</h2>
    <p>Comma-separated tags. Suggested: <code style="color:var(--red)">stable, release, hotfix</code></p>
    <div class="field" style="margin:16px 0">
      <input type="text" id="tagModalInput" placeholder="stable,release">
    </div>
    <div class="modal-actions">
      <button class="btn btn-ghost" onclick="closeTagModal()">CANCEL</button>
      <button class="btn btn-primary" onclick="saveTags()">SAVE TAGS</button>
    </div>
  </div>
</div>

<script>
const PROJECT_ID = {{ ('"' + selected.id + '"') if selected else 'null' }};
let pendingPruneVersion = null;
let pendingTagVersion   = null;
let importFileData      = null;

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
  log('ADDING PROJECT...', '');
  const r = await fetch('/api/add-project', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({path})
  }).then(r => r.json());
  if (r.ok) { window.location.href = '/?project=' + encodeURIComponent(r.id); }
  else log('ERROR: ' + r.message, 'err');
}

async function bump(part) {
  if (!PROJECT_ID) return;
  log('BUMPING VERSION (' + part.toUpperCase() + ')...', '');
  const r = await fetch('/api/bump', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, part})
  }).then(r => r.json());
  if (r.ok) {
    document.getElementById('curVersion').textContent = r.new_version;
    document.getElementById('versionBadge').textContent = 'v' + r.new_version;
    log('VERSION BUMPED: ' + r.message, 'ok');
  } else log('ERROR: ' + r.message, 'err');
}

async function chunk() {
  if (!PROJECT_ID) return;
  const changelog    = document.getElementById('changelog').value.trim();
  const tags         = document.getElementById('tags').value.trim();
  const include_b64  = document.getElementById('inclBase64')?.checked || false;
  log('CHUNKING PROJECT...', '');
  const r = await fetch('/api/chunk', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, changelog, tags, include_b64})
  }).then(r => r.json());
  if (r.ok) {
    log(r.message + '\nFILES: ' + r.detail.file_count + '\nENTITY: ' + r.detail.entity_path, 'ok');
    document.getElementById('changelog').value = '';
    document.getElementById('tags').value = '';
    setTimeout(() => window.location.reload(), 1200);
  } else log('ERROR: ' + r.message, 'err');
}

async function restore(version) {
  if (!PROJECT_ID) return;
  log('RESTORING VERSION ' + version + '...', '');
  const r = await fetch('/api/unchunk', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, version})
  }).then(r => r.json());
  if (r.ok) log(r.message + '\nOUTPUT: ' + r.out_dir + '\nFILES: ' + r.file_count, 'ok');
  else log('ERROR: ' + r.message, 'err');
}

async function exportVer(version) {
  if (!PROJECT_ID) return;
  log('EXPORTING VERSION ' + version + '...', '');
  const r = await fetch('/api/export', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, version})
  }).then(r => r.json());
  if (r.ok) {
    log(r.message + '\nFILES: ' + r.files, 'ok');
    // Trigger download
    window.location.href = '/api/download-export?path=' + encodeURIComponent(r.zip_path);
  } else log('ERROR: ' + r.message, 'err');
}

function confirmPrune(version) {
  pendingPruneVersion = version;
  document.getElementById('pruneMsg').textContent =
    `Permanently delete version "${version}" from the manifest and all its file records from the entity file. This cannot be undone.`;
  document.getElementById('pruneModal').classList.add('open');
}
function closePruneModal() {
  pendingPruneVersion = null;
  document.getElementById('pruneModal').classList.remove('open');
}
async function executePrune() {
  if (!pendingPruneVersion || !PROJECT_ID) return;
  closePruneModal();
  log('PRUNING VERSION ' + pendingPruneVersion + '...', '');
  const r = await fetch('/api/prune', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, version: pendingPruneVersion})
  }).then(r => r.json());
  if (r.ok) {
    log(r.message + '\nROWS REMOVED: ' + r.rows_removed, 'ok');
    setTimeout(() => window.location.reload(), 1200);
  } else log('ERROR: ' + r.message, 'err');
}

// Inline changelog edit
function startEditChangelog(version, el) {
  const input = el.nextElementSibling;
  input.value = el.textContent === '—' ? '' : el.textContent;
  el.style.display = 'none';
  input.style.display = 'block';
  input.focus();
  input.dataset.version = version;
  input.dataset.origVal = el.textContent;
  input._spanEl = el;
}
function cancelEdit(input) {
  input.style.display = 'none';
  input._spanEl.style.display = '';
}
async function saveChangelog(version, input) {
  const newVal = input.value.trim();
  const origEl = input._spanEl;
  input.style.display = 'none';
  origEl.style.display = '';
  if (newVal === (origEl.textContent === '—' ? '' : origEl.textContent)) return;
  log('SAVING CHANGELOG...', '');
  const r = await fetch('/api/update-changelog', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, version, changelog: newVal})
  }).then(r => r.json());
  if (r.ok) {
    origEl.textContent = newVal || '—';
    log(r.message, 'ok');
  } else log('ERROR: ' + r.message, 'err');
}

// Tag editing
function editTags(version, currentTags) {
  pendingTagVersion = version;
  document.getElementById('tagModalInput').value = currentTags;
  document.getElementById('tagModal').classList.add('open');
}
function closeTagModal() {
  pendingTagVersion = null;
  document.getElementById('tagModal').classList.remove('open');
}
async function saveTags() {
  if (!pendingTagVersion || !PROJECT_ID) return;
  const tags = document.getElementById('tagModalInput').value.trim();
  closeTagModal();
  log('SAVING TAGS...', '');
  const r = await fetch('/api/update-tags', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({project_id: PROJECT_ID, version: pendingTagVersion, tags})
  }).then(r => r.json());
  if (r.ok) { log(r.message, 'ok'); setTimeout(() => window.location.reload(), 800); }
  else log('ERROR: ' + r.message, 'err');
}

// Tag filter
function filterTag(tag, btn) {
  document.querySelectorAll('.tag-pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  const rows = document.querySelectorAll('#versionTable tbody tr');
  rows.forEach(row => {
    if (!tag) { row.classList.remove('hidden-row'); return; }
    const rowTags = (row.dataset.tags || '').split(',').map(t => t.trim());
    row.classList.toggle('hidden-row', !rowTags.includes(tag));
  });
}

// Import
function handleImportFile(input) {
  if (!input.files[0]) return;
  importFileData = input.files[0];
  document.getElementById('importDropLabel').textContent = input.files[0].name;
  document.getElementById('importBtn').disabled = false;
}
function handleDropImport(e) {
  e.preventDefault();
  document.getElementById('importDrop').classList.remove('over');
  const file = e.dataTransfer.files[0];
  if (!file) return;
  importFileData = file;
  document.getElementById('importDropLabel').textContent = file.name;
  document.getElementById('importBtn').disabled = false;
}
async function importZip() {
  if (!importFileData || !PROJECT_ID) return;
  log('IMPORTING ZIP...', '');
  const conflictMode = document.getElementById('conflictMode').value;
  const formData = new FormData();
  formData.append('zip', importFileData);
  formData.append('project_id', PROJECT_ID);
  formData.append('on_conflict', conflictMode);
  const r = await fetch('/api/import', { method:'POST', body: formData })
    .then(r => r.json());
  if (r.ok) {
    let msg = r.message;
    if (r.imported.length) msg += '\nIMPORTED: ' + r.imported.join(', ');
    if (r.skipped.length)  msg += '\nSKIPPED:  ' + r.skipped.join(', ');
    log(msg, 'ok');
    setTimeout(() => window.location.reload(), 1500);
  } else log('ERROR: ' + r.message, 'err');
}
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    projects    = load_projects()
    selected_id = request.args.get("project")
    selected    = None
    versions    = []
    all_tags    = set()

    if selected_id:
        selected = find_project(selected_id)
    if not selected and projects:
        selected = projects[0]

    if selected:
        config = load_or_create_config(Path(selected["path"]))
        selected["version"] = config.get("version", "?")
        manifest = get_manifest_path(config)
        if manifest.exists():
            versions = list_versions(str(manifest))
            for v in versions:
                for t in (v.get("tags") or "").split(","):
                    t = t.strip()
                    if t:
                        all_tags.add(t)

    return render_template_string(
        HTML,
        projects=projects,
        selected=selected,
        versions=versions,
        all_tags=sorted(all_tags),
        spec_ver=MFDB_SPEC_VERSION,
    )


@app.route("/api/add-project", methods=["POST"])
def api_add_project():
    data = request.get_json() or {}
    path = (data.get("path") or "").strip()
    if not path or not Path(path).is_dir():
        return jsonify({"ok": False, "message": "Invalid or non-existent path."})
    projects = load_projects()
    pid      = project_id_from_path(path)
    if any(p["id"] == pid for p in projects):
        return jsonify({"ok": True, "message": "Already exists.", "id": pid})
    config = load_or_create_config(Path(path))
    projects.append({
        "id":      pid,
        "name":    config.get("project_name", Path(path).name),
        "path":    path,
        "version": config.get("version", "1.0.0"),
    })
    save_projects(projects)
    return jsonify({"ok": True, "id": pid})


@app.route("/api/chunk", methods=["POST"])
def api_chunk():
    data    = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project:
        return jsonify({"ok": False, "message": "Project not found.", "detail": {}})
    incl_b64 = data.get("include_b64", False)
    from pathlib import Path
    config = load_or_create_config(Path(project["path"]))
    config["include_binary_base64"] = incl_b64
    # Save to config so do_chunk picks it up
    from mfdb_chunker import save_config
    save_config(Path(project["path"]), config)
    return jsonify(do_chunk(project["path"], data.get("changelog", ""), data.get("tags", "")))


@app.route("/api/bump", methods=["POST"])
def api_bump():
    data    = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project:
        return jsonify({"ok": False, "message": "Project not found.", "new_version": ""})
    result = do_bump(project["path"], data.get("part", "patch"))
    if result["ok"]:
        projects = load_projects()
        for p in projects:
            if p["id"] == project["id"]:
                p["version"] = result["new_version"]
        save_projects(projects)
    return jsonify(result)


@app.route("/api/unchunk", methods=["POST"])
def api_unchunk():
    data    = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project:
        return jsonify({"ok": False, "message": "Project not found.", "out_dir": ""})
    config   = load_or_create_config(Path(project["path"]))
    manifest = str(get_manifest_path(config))
    return jsonify(do_unchunk(manifest, data.get("version", "")))


@app.route("/api/update-changelog", methods=["POST"])
def api_update_changelog():
    data    = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project:
        return jsonify({"ok": False, "message": "Project not found."})
    config   = load_or_create_config(Path(project["path"]))
    manifest = str(get_manifest_path(config))
    return jsonify(do_update_changelog(manifest, data.get("version", ""), data.get("changelog", "")))


@app.route("/api/update-tags", methods=["POST"])
def api_update_tags():
    data    = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project:
        return jsonify({"ok": False, "message": "Project not found."})
    config   = load_or_create_config(Path(project["path"]))
    manifest = str(get_manifest_path(config))
    return jsonify(do_update_tags(manifest, data.get("version", ""), data.get("tags", "")))


@app.route("/api/prune", methods=["POST"])
def api_prune():
    data    = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project:
        return jsonify({"ok": False, "message": "Project not found."})
    config   = load_or_create_config(Path(project["path"]))
    manifest = str(get_manifest_path(config))
    return jsonify(do_prune(manifest, data.get("version", "")))


@app.route("/api/export", methods=["POST"])
def api_export():
    data    = request.get_json() or {}
    project = find_project(data.get("project_id", ""))
    if not project:
        return jsonify({"ok": False, "message": "Project not found.", "zip_path": ""})
    config   = load_or_create_config(Path(project["path"]))
    manifest = str(get_manifest_path(config))
    version  = data.get("version", "")
    out_path = str(Path(config["output_base"]) / "exports" /
                   f"{config['project_name']}-{version}.mfdb.zip")
    return jsonify(do_export(manifest, version, out_path))


@app.route("/api/download-export")
def api_download_export():
    zip_path = request.args.get("path", "")
    if not zip_path or not Path(zip_path).exists():
        return "File not found", 404
    return send_file(zip_path, as_attachment=True,
                     download_name=Path(zip_path).name)


@app.route("/api/import", methods=["POST"])
def api_import():
    project = find_project(request.form.get("project_id", ""))
    if not project:
        return jsonify({"ok": False, "message": "Project not found.",
                        "imported": [], "skipped": []})
    zip_file    = request.files.get("zip")
    on_conflict = request.form.get("on_conflict", "reject")
    if not zip_file:
        return jsonify({"ok": False, "message": "No zip uploaded.",
                        "imported": [], "skipped": []})

    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        zip_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        config   = load_or_create_config(Path(project["path"]))
        manifest = str(get_manifest_path(config))
        result   = do_import(manifest, tmp_path, on_conflict)
    finally:
        os.unlink(tmp_path)

    return jsonify(result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def get_free_port(start=5100, end=5120):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


if __name__ == "__main__":
    port = get_free_port()
    print(f"--- MFDB CHUNKER UI v4.0.0 ---")
    print(f"MFDB Spec : {MFDB_SPEC_VERSION}")
    print(f"URL       : http://localhost:{port}")
    print(f"Author    : Elton Boehnen — boehnenelton2024.pages.dev")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
