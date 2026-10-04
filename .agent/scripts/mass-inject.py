# -*- coding: utf-8 -*-
"""Injection massive .agent/ + .vscode/ Hephaistos-Kit -> tous les projets de la racine dev.

Strategie :
- Dirs TEMPLATE (mirror) : agents, docs, hermes, devin, scripts, workflows,
  skills, .shared, consciousness, rag + fichiers racine .agent
- Dirs DONNEES (merge, jamais de delete) : knowledge, memory
- JAMAIS touche : memory-database (jonction/DB), logs, __pycache__,
  *.db/*.log/*.env/*.pem/*.key, rules/local_rules.md
- .vscode : copie ou merge JSON (tasks folderOpen + settings)
"""
import os, json, shutil, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# --dry-run : simule tout l'inventaire sans écrire ni supprimer quoi que
# ce soit (audit avant propagation réelle — rapport identique)
DRY = '--dry-run' in sys.argv

# KIT = dossier racine du kit (3 niveaux au-dessus de ce script : scripts -> .agent -> kit)
# ROOT = dossier parent du kit = racine des projets. Surcharge possible via env.
KIT = os.environ.get('HEPHAISTOS_KIT') or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = os.environ.get('DEV_ROOT') or os.path.dirname(KIT)
SRC_AGENT = os.path.join(KIT, '.agent')
SRC_VSCODE = os.path.join(KIT, '.vscode')

MIRROR_DIRS = ['agents', 'docs', 'hermes', 'devin', 'scripts', 'workflows',
               'skills', '.shared', 'consciousness', 'rag']
MERGE_DIRS = ['knowledge', 'memory']
ROOT_FILES = ['ARCHITECTURE.md', 'REGISTRY.md', 'bootstrap.ps1',
              'mcp-config.json.exemple', 'CHANGELOG_ZVEC_PERSISTANCE.md']

# dans les dirs mirror, ces fichiers dest ne sont JAMAIS supprimes
PRESERVE_NAMES = {'local_rules.md', '.env', 'ingestion_state.json',
                  'beacon_state.json', 'ingestion.log', 'rag_bridge.log'}
PRESERVE_EXT = {'.db', '.log', '.env', '.pem', '.key', '.pyc', '.sqlite', '.sqlite3'}
SKIP_DIRNAMES = {'memory-database', 'logs', '__pycache__', '.git', 'venv', '.venv', 'node_modules'}
# fichiers du kit propres au kit lui-meme -> ne pas propager
KIT_ONLY = {os.path.join('knowledge', 'decisions', '001-architecture-cascade.md'),
            os.path.join('rag', 'rag_bridge.log')}

# repertoires infra/donnees qui ne sont PAS des projets meme s'ils matchent
SKIP_DIRS = {'Hephaistos-Kit', 'NVM', 'Ollama', 'FFmpeg', 'pandoc-3.7.0.2',
             'nginx-1.28.0', 'ngrok-v3-stable-windows-amd64', 'nssm-2.24', 'vcpkg',
             'qdrant', 'qdrant_fresh', 'semantic-cache-data', 'memory-database-backup',
             'server-backup', 'acp-backup', 'logs', 'data', 'storage', 'snapshots',
             'tasks', 'temp_sqlite', '_batches', 'beacon_batches', 'tools', 'services'}

PROJECT_MARKERS = ['.git', 'package.json', 'pyproject.toml', 'setup.py',
                   'Cargo.toml', 'go.mod', 'composer.json', 'requirements.txt',
                   'Gemfile', 'pom.xml', '.agent']

REPARSE = 0x400

def is_reparse(p):
    try:
        return bool(os.stat(p, follow_symlinks=False).st_file_attributes & REPARSE)
    except Exception:
        return True  # en cas de doute, on ne touche pas

def is_project(d):
    for m in PROJECT_MARKERS:
        if os.path.exists(os.path.join(d, m)):
            return True
    for f in os.listdir(d):
        if f.endswith(('.sln', '.csproj')):
            return True
    return False

def copy_file(src, dst):
    if DRY:
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)

def mirror_dir(src, dst, stats):
    """Copie src->dst et supprime les fichiers dest absents de src (sauf preserves)."""
    src_files = set()
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRNAMES and not is_reparse(os.path.join(base, d))]
        rel = os.path.relpath(base, src)
        for fn in files:
            sp = os.path.normpath(os.path.join(rel, fn))
            if sp in KIT_ONLY or os.path.splitext(fn)[1].lower() in PRESERVE_EXT or fn in PRESERVE_NAMES:
                continue
            src_files.add(sp)
            s, d = os.path.join(base, fn), os.path.join(dst, rel, fn)
            if not os.path.exists(d) or os.path.getsize(s) != os.path.getsize(d) or \
               os.path.getmtime(s) > os.path.getmtime(d) + 2:
                copy_file(s, d); stats['written'] += 1
    if os.path.isdir(dst) and not is_reparse(dst):
        for base, dirs, files in os.walk(dst):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRNAMES and not is_reparse(os.path.join(base, d))]
            rel = os.path.relpath(base, dst)
            for fn in files:
                sp = os.path.normpath(os.path.join(rel, fn))
                if sp in src_files or os.path.splitext(fn)[1].lower() in PRESERVE_EXT or fn in PRESERVE_NAMES:
                    continue
                # knowledge/decisions geres en merge -> ici seulement mirror dirs
                try:
                    if not DRY:
                        os.remove(os.path.join(base, fn))
                    stats['stale_removed'] += 1
                except OSError:
                    pass

def merge_dir(src, dst, stats):
    for base, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRNAMES and not is_reparse(os.path.join(base, d))]
        rel = os.path.relpath(base, src)
        for fn in files:
            sp = os.path.normpath(os.path.join(rel, fn))
            if sp in KIT_ONLY or os.path.splitext(fn)[1].lower() in PRESERVE_EXT or fn in PRESERVE_NAMES:
                continue
            s, d = os.path.join(base, fn), os.path.join(dst, rel, fn)
            if not os.path.exists(d):
                copy_file(s, d); stats['written'] += 1

def inject_vscode(proj, stats):
    dst_dir = os.path.join(proj, '.vscode')
    tasks_src = os.path.join(SRC_VSCODE, 'tasks.json')
    set_src = os.path.join(SRC_VSCODE, 'settings.json')
    if not DRY:
        os.makedirs(dst_dir, exist_ok=True)
    # settings : merge cles (existant gagne)
    ds = os.path.join(dst_dir, 'settings.json')
    try:
        cur = json.load(open(ds, encoding='utf-8')) if os.path.exists(ds) else {}
        add = json.load(open(set_src, encoding='utf-8'))
        merged = {**add, **cur}
        if merged != cur:
            if not DRY:
                json.dump(merged, open(ds, 'w', encoding='utf-8'), indent=4)
            stats['vscode'] += 1
    except Exception:
        if not os.path.exists(ds):
            if not DRY:
                shutil.copy2(set_src, ds)
            stats['vscode'] += 1
    # tasks : ajoute la tache folderOpen si absente
    dt = os.path.join(dst_dir, 'tasks.json')
    try:
        cur = json.load(open(dt, encoding='utf-8')) if os.path.exists(dt) else {"version": "2.0.0", "tasks": []}
        has = any('start-workspace.ps1' in json.dumps(t) for t in cur.get('tasks', []))
        if not has:
            kit_task = json.load(open(tasks_src, encoding='utf-8'))['tasks'][0]
            cur.setdefault('tasks', []).append(kit_task)
            if not DRY:
                json.dump(cur, open(dt, 'w', encoding='utf-8'), indent=4)
            stats['vscode'] += 1
    except Exception:
        if not os.path.exists(dt):
            if not DRY:
                shutil.copy2(tasks_src, dt)
            stats['vscode'] += 1

def inject(proj):
    stats = {'written': 0, 'stale_removed': 0, 'vscode': 0}
    da = os.path.join(proj, '.agent')
    # jamais dans une jonction
    if os.path.exists(da) and is_reparse(da):
        return None
    for rf in ROOT_FILES:
        s = os.path.join(SRC_AGENT, rf)
        if os.path.exists(s):
            copy_file(s, os.path.join(da, rf)); stats['written'] += 1
    for d in MIRROR_DIRS:
        mirror_dir(os.path.join(SRC_AGENT, d), os.path.join(da, d), stats)
    for d in MERGE_DIRS:
        sd = os.path.join(SRC_AGENT, d)
        if os.path.isdir(sd):
            merge_dir(sd, os.path.join(da, d), stats)
    # dirs locaux attendus par le systeme
    if not DRY:
        for d in ['knowledge/decisions', 'logs', 'memory']:
            os.makedirs(os.path.join(da, d), exist_ok=True)
    inject_vscode(proj, stats)
    return stats

results, skipped = {}, []
for name in sorted(os.listdir(ROOT)):
    p = os.path.join(ROOT, name)
    if not os.path.isdir(p) or is_reparse(p):
        continue
    if name in SKIP_DIRS:
        skipped.append((name, 'infra/donnees'))
        continue
    if not is_project(p):
        skipped.append((name, 'aucun marqueur projet'))
        continue
    try:
        r = inject(p)
        results[name] = r if r else 'JONCTION .agent - SKIP'
    except Exception as e:
        results[name] = f'ERREUR: {e}'

print(('\n================= RAPPORT INJECTION'
       + (' (DRY-RUN — rien écrit) =================' if DRY
          else ' =================')))
ok = [k for k, v in results.items() if isinstance(v, dict)]
err = [(k, v) for k, v in results.items() if not isinstance(v, dict)]
print(f'\nINJECTES : {len(ok)}')
for k in ok:
    s = results[k]
    print(f'  + {k}: {s["written"]} fichiers, {s["stale_removed"]} obsoletes retires, vscode:{s["vscode"]}')
print(f'\nERREURS : {len(err)}')
for k, v in err:
    print(f'  ! {k}: {v}')
print(f'\nSKIPPES : {len(skipped)}')
for n, why in skipped:
    print(f'  - {n} ({why})')
