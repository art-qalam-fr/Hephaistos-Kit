# -*- coding: utf-8 -*-
"""scan-projects.py — Registre global des projets.

Scanne un arbre de projets (défaut F:\\Promgramation-teste), construit :
  1. F:\\Sqlite-DB\\projects-registry.db  — tables relationnelles détaillées
  2. memory_mcp.db (KG)                  — entités projet:* + observations + relations
  3. Qdrant collection projects_index    — vecteurs NVIDIA 2048D + payloads

Réutilisable : python scan-projects.py [ROOT]
Idempotent : réécrit le scan courant, conserve l'historique dans scan_runs.
"""
import os, re, sys, json, time, sqlite3, hashlib, datetime, urllib.request, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Racine des projets : argument > $PROJECTS_ROOT > parent du projet contenant .agent
ROOT = (sys.argv[1] if len(sys.argv) > 1
        else os.environ.get('PROJECTS_ROOT')
        or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
DB_ROOT = os.environ.get('AGENT_DB_ROOT') or os.path.join(os.path.expanduser('~'), '.agent-db')
REGISTRY_DB = os.path.join(DB_ROOT, 'projects-registry.db')
KG_DB = os.path.join(DB_ROOT, 'current_workspace', 'graph', 'memory_mcp.db')
QDRANT = os.environ.get('QDRANT_URL', 'http://localhost:6333')
EMBED_URL = 'https://integrate.api.nvidia.com/v1/embeddings'
EMBED_MODEL = 'nvidia/nemotron-3-embed-1b'
DIMS = 2048

MARKERS = ['.git', 'package.json', 'pyproject.toml', 'setup.py', 'Cargo.toml',
           'go.mod', 'composer.json', 'requirements.txt', 'Gemfile', 'pom.xml',
           '.agent', '.vscode', '.windsurf', '.cursor']
SKIP_DIRS = {'Hephaistos-Kit', 'NVM', 'Ollama', 'FFmpeg', 'pandoc-3.7.0.2',
             'nginx-1.28.0', 'ngrok-v3-stable-windows-amd64', 'nssm-2.24', 'vcpkg',
             'qdrant', 'qdrant_fresh', 'semantic-cache-data', 'memory-database-backup',
             'server-backup', 'acp-backup', 'logs', 'data', 'storage', 'snapshots',
             'tasks', 'temp_sqlite', '_batches', 'beacon_batches', 'tools', 'services'}
PRUNE = {'node_modules', '.git', 'venv', '.venv', '__pycache__', 'site-packages',
         'dist', 'build', '.next', 'target', '.pytest_cache', 'out', 'bin', 'obj'}
CODE_EXT = {'.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.tsx': 'typescript', '.jsx': 'javascript', '.rs': 'rust',
            '.go': 'go', '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.h': 'c/cpp',
            '.hpp': 'cpp', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby',
            '.ps1': 'powershell', '.sh': 'bash', '.html': 'html', '.css': 'css',
            '.vue': 'vue', '.svelte': 'svelte', '.sql': 'sql', '.ipynb': 'jupyter'}

def nvidia_key():
    k = os.environ.get('NVIDIA_API_KEY')
    if k:
        return k
    proj_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    for env in [proj_env, os.path.join(os.path.expanduser('~'), '.env')]:
        try:
            for ln in open(env, encoding='utf-8', errors='replace'):
                if ln.startswith('NVIDIA_API_KEY='):
                    return ln.split('=', 1)[1].strip().strip('"')
        except OSError:
            pass
    return None

API_KEY = nvidia_key()

def http_json(url, payload=None, method=None, timeout=30):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ('POST' if data else 'GET'))
    req.add_header('Content-Type', 'application/json')
    if API_KEY and 'nvidia' in url:
        req.add_header('Authorization', f'Bearer {API_KEY}')
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())

def is_project(d):
    for m in MARKERS:
        if os.path.exists(os.path.join(d, m)):
            return True
    try:
        if any(f.endswith(('.sln', '.csproj')) for f in os.listdir(d)):
            return True
    except OSError:
        pass
    return False

def collect_projects(root):
    """L1 + L2 dans les conteneurs sans marqueur."""
    targets = []
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if not os.path.isdir(p) or name in SKIP_DIRS or name.startswith('.'):
            continue
        if is_project(p):
            targets.append((name, p, 1))
        else:
            try:
                subs = sorted(os.listdir(p))
            except OSError:
                continue
            sub_found = False
            for sub in subs:
                sp = os.path.join(p, sub)
                if not os.path.isdir(sp) or sub.lower() in PRUNE:
                    continue
                if os.path.exists(os.path.join(sp, 'pyvenv.cfg')):
                    continue
                if is_project(sp):
                    targets.append((f'{name}/{sub}', sp, 2)); sub_found = True
            if not sub_found and any(os.path.isfile(os.path.join(p, x)) for x in subs):
                targets.append((name, p, 1))  # dossier à fichiers propres
    return targets

def scan_project(name, path, depth):
    info = {'name': name, 'path': path, 'depth': depth, 'ptype': 'unknown',
            'state': 'developpement', 'description': '', 'languages': {},
            'file_count': 0, 'code_files': 0, 'size_mb': 0.0,
            'has_git': 0, 'git_remote': '', 'last_commit': '',
            'last_modified': '', 'has_agent': 0, 'has_tests': 0,
            'has_readme': 0, 'is_container': 0, 'deps': []}
    info['has_git'] = int(os.path.isdir(os.path.join(path, '.git')))
    info['has_agent'] = int(os.path.isdir(os.path.join(path, '.agent')))
    try:
        entries = os.listdir(path)
        info['has_tests'] = int(any(e.lower() in ('tests', 'test', '__tests__', 'spec') for e in entries))
        info['has_readme'] = int(any(e.lower().startswith('readme') for e in entries))
    except OSError:
        entries = []

    # manifests
    pj = os.path.join(path, 'package.json')
    if os.path.exists(pj):
        try:
            j = json.load(open(pj, encoding='utf-8', errors='replace'))
            info['ptype'] = 'node'
            info['description'] = info['description'] or (j.get('description') or '')
            deps = list((j.get('dependencies') or {}).keys()) + list((j.get('devDependencies') or {}).keys())
            info['deps'] += deps[:60]
        except Exception:
            pass
    for m, t in [('pyproject.toml', 'python'), ('setup.py', 'python'),
                 ('requirements.txt', 'python'), ('Cargo.toml', 'rust'),
                 ('go.mod', 'go'), ('composer.json', 'php'), ('Gemfile', 'ruby')]:
        if os.path.exists(os.path.join(path, m)) and info['ptype'] == 'unknown':
            info['ptype'] = t
    req = os.path.join(path, 'requirements.txt')
    if os.path.exists(req):
        try:
            for ln in open(req, encoding='utf-8', errors='replace').read().splitlines()[:80]:
                pkg = re.split(r'[<>=!~\[ ;]', ln.strip())[0]
                if pkg and not ln.startswith(('#', '-')):
                    info['deps'].append(pkg.lower())
        except OSError:
            pass

    # README → description
    for e in entries:
        if e.lower().startswith('readme'):
            try:
                txt = open(os.path.join(path, e), encoding='utf-8', errors='replace').read(4000)
                for para in re.split(r'\n\s*\n', txt):
                    clean = re.sub(r'[#*`>\[\]!()\-=]', '', para).strip()
                    if len(clean) > 30 and not clean.startswith(('http', '|', '<')):
                        info['description'] = info['description'] or clean[:300]
                        break
            except OSError:
                pass
            break

    # arborescence : langues + taille + last_modified
    latest = 0.0
    langs = {}
    for base, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in PRUNE and not d.startswith('.')
                   and not os.path.exists(os.path.join(base, d, 'pyvenv.cfg'))]
        if base.count(os.sep) - path.count(os.sep) > 4:
            dirs[:] = []
        for fn in files:
            info['file_count'] += 1
            ext = os.path.splitext(fn)[1].lower()
            if ext in CODE_EXT:
                info['code_files'] += 1
                langs[CODE_EXT[ext]] = langs.get(CODE_EXT[ext], 0) + 1
            try:
                st = os.stat(os.path.join(base, fn))
                info['size_mb'] += st.st_size / 1048576
                if st.st_mtime > latest:
                    latest = st.st_mtime
            except OSError:
                pass
    info['languages'] = dict(sorted(langs.items(), key=lambda x: -x[1])[:6])
    if info['ptype'] == 'unknown' and langs:
        info['ptype'] = max(langs, key=langs.get)
    if latest:
        info['last_modified'] = datetime.datetime.fromtimestamp(latest).isoformat(' ', 'seconds')
        age_days = (time.time() - latest) / 86400
    else:
        age_days = 0

    # git
    if info['has_git']:
        try:
            import subprocess
            r = subprocess.run(['git', '-C', path, 'log', '-1', '--format=%ci'],
                               capture_output=True, text=True, timeout=10)
            info['last_commit'] = r.stdout.strip()[:19]
            r = subprocess.run(['git', '-C', path, 'remote', 'get-url', 'origin'],
                               capture_output=True, text=True, timeout=10)
            info['git_remote'] = r.stdout.strip()
        except Exception:
            pass

    # état
    if depth == 2 and not info['has_git']:
        pass
    if info['code_files'] < 15:
        info['state'] = 'embryonnaire'
    elif info['has_readme'] and info['has_tests'] and info['code_files'] >= 50:
        info['state'] = 'abouti'
    if age_days > 540:
        info['state'] = 'dormant'
    elif info['state'] != 'embryonnaire':
        info['state'] = 'developpement'
    info['description'] = info['description'] or '(pas de description)'
    return info

# ---------- SQL ----------
def init_registry(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS projects(
      id INTEGER PRIMARY KEY, name TEXT, path TEXT UNIQUE, depth INTEGER,
      ptype TEXT, state TEXT, description TEXT, languages TEXT,
      file_count INT, code_files INT, size_mb REAL,
      has_git INT, git_remote TEXT, last_commit TEXT, last_modified TEXT,
      has_agent INT, has_tests INT, has_readme INT, is_container INT,
      first_seen TEXT, last_seen TEXT);
    CREATE TABLE IF NOT EXISTS project_techs(
      project_id INT REFERENCES projects(id), name TEXT, kind TEXT,
      PRIMARY KEY(project_id, name));
    CREATE TABLE IF NOT EXISTS project_relations(
      src INT, dst INT, rtype TEXT, PRIMARY KEY(src, dst, rtype));
    CREATE TABLE IF NOT EXISTS scan_runs(
      id INTEGER PRIMARY KEY, ts TEXT, root TEXT, count INT, duration_s REAL);
    CREATE INDEX IF NOT EXISTS idx_projects_state ON projects(state);
    CREATE INDEX IF NOT EXISTS idx_projects_ptype ON projects(ptype);
    ''')

def write_registry(infos):
    db = sqlite3.connect(REGISTRY_DB)
    init_registry(db)
    now = datetime.datetime.now().isoformat(' ', 'seconds')
    db.execute('INSERT INTO scan_runs(ts,root,count) VALUES(?,?,?)',
               (now, ROOT, len(infos)))
    for i in infos:
        row = db.execute('SELECT id, first_seen FROM projects WHERE path=?', (i['path'],)).fetchone()
        if row:
            pid, first_seen = row
            db.execute('''UPDATE projects SET name=?,depth=?,ptype=?,state=?,description=?,
              languages=?,file_count=?,code_files=?,size_mb=?,has_git=?,git_remote=?,
              last_commit=?,last_modified=?,has_agent=?,has_tests=?,has_readme=?,
              is_container=?,last_seen=? WHERE id=?''',
              (i['name'], i['depth'], i['ptype'], i['state'], i['description'],
               json.dumps(i['languages']), i['file_count'], i['code_files'],
               round(i['size_mb'], 1), i['has_git'], i['git_remote'], i['last_commit'],
               i['last_modified'], i['has_agent'], i['has_tests'], i['has_readme'],
               i['is_container'], now, pid))
        else:
            cur = db.execute('''INSERT INTO projects(name,path,depth,ptype,state,description,
              languages,file_count,code_files,size_mb,has_git,git_remote,last_commit,
              last_modified,has_agent,has_tests,has_readme,is_container,first_seen,last_seen)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (i['name'], i['path'], i['depth'], i['ptype'], i['state'], i['description'],
               json.dumps(i['languages']), i['file_count'], i['code_files'],
               round(i['size_mb'], 1), i['has_git'], i['git_remote'], i['last_commit'],
               i['last_modified'], i['has_agent'], i['has_tests'], i['has_readme'],
               i['is_container'], now, now))
            pid = cur.lastrowid
        i['_pid'] = pid
        db.execute('DELETE FROM project_techs WHERE project_id=?', (pid,))
        for lang in i['languages']:
            db.execute('INSERT OR IGNORE INTO project_techs VALUES(?,?,?)', (pid, lang, 'language'))
        for dep in set(i['deps']):
            db.execute('INSERT OR IGNORE INTO project_techs VALUES(?,?,?)', (pid, dep, 'dependency'))
    # marque les disparus
    paths = {i['path'] for i in infos}
    for (pid, pth) in db.execute('SELECT id,path FROM projects').fetchall():
        if pth not in paths:
            db.execute("UPDATE projects SET state='disparu' WHERE id=?", (pid,))
    db.commit(); db.close()

def write_kg(infos):
    db = sqlite3.connect(KG_DB)
    now = datetime.datetime.now().isoformat(' ', 'seconds')
    def ent(name, etype):
        r = db.execute('SELECT id FROM entities WHERE name=?', (name,)).fetchone()
        if r:
            return r[0]
        return db.execute('INSERT INTO entities(name,entityType,created_at) VALUES(?,?,?)',
                          (name, etype, now)).lastrowid
    def obs(eid, content):
        hexed = content.encode('utf-8').hex()
        if not db.execute('SELECT 1 FROM observations WHERE entity_id=? AND content=?',
                          (eid, hexed)).fetchone():
            db.execute('INSERT INTO observations(entity_id,content,created_at) VALUES(?,?,?)',
                       (eid, hexed, now))
    def rel(a, b, rt):
        if not db.execute('SELECT 1 FROM relations WHERE from_entity=? AND to_entity=? AND relationType=?',
                          (a, b, rt)).fetchone():
            db.execute('INSERT INTO relations(from_entity,to_entity,relationType,created_at) VALUES(?,?,?,?)',
                       (a, b, rt, now))
    for i in infos:
        ename = f'project:{i["name"]}'
        eid = ent(ename, 'project')
        obs(eid, f'Path: {i["path"]}')
        obs(eid, f'Type: {i["ptype"]} | État: {i["state"]} | Modifié: {i["last_modified"]}')
        obs(eid, f'Stack: {", ".join(i["languages"].keys()) or "?"} | {i["code_files"]} fichiers code, {round(i["size_mb"],1)} Mo')
        obs(eid, f'Description: {i["description"][:250]}')
        if i['git_remote']:
            obs(eid, f'Git remote: {i["git_remote"]} | dernier commit: {i["last_commit"]}')
        for lang in i['languages']:
            tid = ent(f'tech:{lang}', 'technology')
            rel(ename, f'tech:{lang}', 'utilise')
        if i['depth'] == 2:
            parent = i['name'].split('/')[0]
            ent(f'container:{parent}', 'container')
            rel(f'container:{parent}', ename, 'contient')
    db.commit(); db.close()

def write_qdrant(infos):
    if not API_KEY:
        print('!! pas de NVIDIA_API_KEY — qdrant ignoré'); return
    try:
        cols = http_json(f'{QDRANT}/collections')['result']['collections']
        if 'projects_index' not in {c['name'] for c in cols}:
            http_json(f'{QDRANT}/collections/projects_index',
                      {'vectors': {'size': DIMS, 'distance': 'Cosine'}}, method='PUT')
    except Exception as e:
        print('!! qdrant:', e); return
    pts = []
    for i in infos:
        txt = (f"{i['name']} — {i['description'][:200]}. Type: {i['ptype']}. "
               f"Stack: {', '.join(i['languages'])}. État: {i['state']}. Chemin: {i['path']}")
        try:
            r = http_json(EMBED_URL, {'model': EMBED_MODEL, 'input': txt,
                                      'input_type': 'passage', 'encoding_format': 'float'})
            vec = r['data'][0]['embedding']
        except Exception as e:
            print('!! embed', i['name'], e); continue
        pid = int(hashlib.md5(i['path'].encode()).hexdigest()[:15], 16)
        pts.append({'id': pid, 'vector': vec, 'payload': {
            'name': i['name'], 'path': i['path'], 'ptype': i['ptype'],
            'state': i['state'], 'languages': list(i['languages'].keys()),
            'description': i['description'][:300], 'last_modified': i['last_modified'],
            'code_files': i['code_files'], 'has_agent': i['has_agent']}})
        if len(pts) >= 20:
            http_json(f'{QDRANT}/collections/projects_index/points?wait=true',
                      {'points': pts}, method='PUT'); pts = []
    if pts:
        http_json(f'{QDRANT}/collections/projects_index/points?wait=true',
                  {'points': pts}, method='PUT')

if __name__ == '__main__':
    t0 = time.time()
    targets = collect_projects(ROOT)
    print(f'{len(targets)} projets détectés — scan...')
    infos = []
    for n, (name, p, d) in enumerate(targets):
        try:
            infos.append(scan_project(name, p, d))
        except Exception as e:
            print('!!', name, e)
        if n % 25 == 24:
            print(f'  {n+1}/{len(targets)}')
    write_registry(infos); print('registry DB OK')
    write_kg(infos); print('KG OK')
    write_qdrant(infos); print('qdrant OK')
    print(f'=== terminé en {round(time.time()-t0)}s : {len(infos)} projets ===')
