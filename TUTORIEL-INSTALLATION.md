# TUTORIEL — Installer Hephaistos-Kit de zéro

Guide pas à pas pour reproduire l'environnement agentique complet sur une
machine neuve. Temps estimé : **15-20 minutes** (hors builds des serveurs MCP).

**Ordre des opérations** : prérequis → clone → injection `.agent/` → clés
API → stack MCP → vérification → compléments optionnels.

---

## Étape 0 — Prérequis

| Outil | Vérifier | Installer |
|---|---|---|
| Git | `git --version` | [git-scm.com](https://git-scm.com) |
| Node.js 18+ | `node --version` | [nodejs.org](https://nodejs.org) |
| Python 3.10+ | `python --version` | [python.org](https://python.org) |
| uv (recommandé) | `uv --version` | `pip install uv` ou [docs.astral.sh/uv](https://docs.astral.sh/uv) |
| PowerShell | `powershell -v` | inclus Windows |

> **Execution Policy** (Windows) : si les `.ps1` sont bloqués —
> `Set-ExecutionPolicy -Scope Process RemoteSigned`

## Étape 1 — Cloner le kit (avec les sous-modules)

```powershell
git clone --recurse-submodules https://github.com/ArchNext/Hephaistos-Kit.git
cd Hephaistos-Kit
```

⚠️ **Important** : `--recurse-submodules` clone aussi les 11 serveurs MCP
dans `mcp/servers/` + `cli/opencli-cookies`. Sans lui, ces dossiers restent vides.

Déjà cloné sans ? → `git submodule update --init --recursive`.

## Étape 2 — Injecter `.agent/` dans un projet

```powershell
# Depuis le dossier du projet cible :
node <chemin>\Hephaistos-Kit\bin\hephaistos-kit.js init

# Ou installer le CLI une fois :
npm install -g .
# puis dans n'importe quel projet :
hephaistos-kit init
```

Ce que ça dépose dans le projet :

```
projet/
├── .agent/
│   ├── rules/global_rules.md   # règles universelles
│   ├── agents/                 # 21 définitions d'agents + routage
│   ├── skills/                 # 40 skills
│   ├── workflows/              # 12 slash-commands
│   ├── scripts/                # beacon-sync.ps1, ingestion…
│   ├── REGISTRY.md             # agents/providers canoniques
│   ├── devin/  hermes/         # couches IDE/agents
│   └── memory-database/        # squelette (les données restent locales)
└── .vscode/                    # configs IDE partagées
```

### Mettre à jour un projet déjà injecté

```bash
hephaistos-kit update --force
```

**Préservé automatiquement** : `memory-database/` (données) et
`rules/local_rules.md` (règles du projet). Jamais écrasés.

## Étape 3 — Les clés API : quoi, pour qui, où les prendre

Toutes les clés vivent dans `~/.hephaistos/env.local` — **jamais commité,
hors de tout repo**. Une seule clé est réellement **indispensable** pour le
cœur du kit (embeddings + sous-agents) : `NVIDIA_API_KEY`. Le reste est
conditionnel selon les serveurs que vous activez.

| Variable | Pour quoi | Où la créer | Gratuit ? |
|---|---|---|---|
| `NVIDIA_API_KEY` | **Embeddings** (`nemotron-3-embed-1b`, 2048d) + LLM NIM (orchestrateur, sous-agents) | [build.nvidia.com](https://build.nvidia.com) → compte → *Get API Key* (`nvapi-…`) | ✅ tier gratuit |
| `AGENT_DB_ROOT` | Racine de la **mémoire unifiée** (Qdrant data, Zvec, SQLite) | Chemin local de votre choix, ex. `F:/Sqlite-DB` | local |
| `QDRANT_URL` | Serveur vectoriel | Local : `http://localhost:6333` (Docker) ou cloud [cloud.qdrant.io](https://cloud.qdrant.io) | ✅ local |
| `QDRANT_API_KEY` | Qdrant **cloud** seulement (inutile en local) | Console Qdrant Cloud → API Keys | optionnel |
| `GITHUB_TOKEN` | Serveur `github-mcp-server` | [github.com/settings/tokens](https://github.com/settings/tokens) → *Fine-grained* | ✅ |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REFRESH_TOKEN` | `google-drive-mcp` | [console.cloud.google.com](https://console.cloud.google.com) → OAuth client + `get-refresh-token.ps1` (voir `mcp/cards/google-drive.md`) | ✅ |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | `kaggle-mcp` | [kaggle.com/settings](https://www.kaggle.com/settings) → *Create New API Token* | ✅ |
| `ORCHESTRATOR_DB` | Chemin de la base tâches/agents | Défaut `data/orchestrator.db` dans le serveur | local |
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | Provider embedding **alternatif** (non requis — la référence est NVIDIA) | platform.openai.com | payant |

Exemple minimal de `~/.hephaistos/env.local` :

```ini
# ~/.hephaistos/env.local — jamais commité
NVIDIA_API_KEY=nvapi-...
AGENT_DB_ROOT=F:/Sqlite-DB
QDRANT_URL=http://localhost:6333
EMBEDDING_PROVIDER=nvidia
EMBEDDING_MODEL=nvidia/nemotron-3-embed-1b
EMBEDDING_DIMENSIONS=2048
```

> **Référence embeddings** : NVIDIA `nvidia/nemotron-3-embed-1b` (2048
> dimensions) — c'est la référence canonique du kit. Ne pas substituer un
> autre modèle sans recréer les collections Qdrant à la même dimension.

## Étape 4 — Installer la stack MCP

```powershell
.\mcp\install.ps1 -Ide devin
# autres IDE : cursor | kilocode | antigravity | trae
```

Le script, dans l'ordre :

1. `git submodule update --init` — clone les 11 serveurs dans `mcp/servers/`
2. Build chacun (`npm i && npm run build`, `uv sync` selon le serveur)
3. Déploie les launchers dans `~/.devin/launchers/`
4. Génère `mcp_config.json` de l'IDE (chemins de VOTRE machine + env résolus
   depuis `env.local`)
5. Backup de la config existante en `.bak-YYYYMMDDHHmmss`

Options :

```powershell
.\mcp\install.ps1 -Ide cursor -DryRun     # simule, affiche la config
.\mcp\install.ps1 -Tier standard          # sans les serveurs 'personal'
.\mcp\install.ps1 -SkipBuild              # config seule (serveurs déjà buildés)
```

## Étape 5 — mcp-mux (optionnel, multi-clients)

Le multiplexeur partage les mêmes serveurs entre IDE, CLI et dashboard
(processus uniques, outils namespacés `mcp-mux.<serveur>__<outil>`).

```powershell
npm i -g mcp-mux
copy mcp\mcp-mux.config.template.json $env:USERPROFILE\.config\mcp-mux\mcp-mux.json
# adapter {INSTALL_ROOT} / {WORKSPACE} dans le fichier copié
```

L'entrée `mcp-mux` est déjà générée par `install.ps1` (kind `npm`).
Recharger le broker après modif de sa config : tuer le process `node … broker.mjs`.

## Étape 6 — Vérifier

| Vérification | Attendu |
|---|---|
| `projet/.agent/rules/global_rules.md` existe | ✅ injecté |
| `projet/.agent/REGISTRY.md` existe | ✅ registre présent |
| `%APPDATA%\<ide>\mcp_config.json` contient `mcpServers` | ✅ config écrite |
| Relancer l'IDE → serveurs MCP listés connectés | ✅ stack active |
| `memory_stats` / `list_agents` répondent | ✅ mémoire + orchestrateur |

## Étape 7 — Compléments optionnels

- **Sous-agents** : CLIs de délégation (`agy`, `hermes`, `kilo`) —
  → `cli/README.md` (liens + commandes d'install). Protocole **ACP** :
  `cli/ACP.md`. L'orchestrateur enregistre les agents (`register_agent`).
- **OpenCLI** (automatisation du Chrome réel) : `npm i -g @jackwener/opencli`,
  `opencli doctor`, Chrome lancé via `.agent/scripts/run_chrome_opencli.bat`.
  Adaptateur cookies (sous-module `cli/opencli-cookies`) :
  `npm i -g github:ArchNext/opencli-cookies` — voir son `TUTORIEL.md`.
- **Beacon** : binaire externe (`beacon mcp serve`) — installer séparément ;
  l'ingestion des traces se fait via `.agent/scripts/beacon-sync.ps1`.
- **Google Drive MCP** : déposer `gcp-oauth.keys.json` dans
  `~/.hephaistos/servers/google-drive-mcp/` puis `.\get-refresh-token.ps1`
  → voir `mcp/cards/google-drive.md`.
- **Qdrant local** : `docker run -p 6333:6333 qdrant/qdrant` — collections
  attendues en **2048 dimensions**.

## Dépannage

| Symptôme | Cause | Fix |
|---|---|---|
| `mcp/servers/*` vides | clone sans submodules | `git submodule update --init --recursive` |
| `${VAR}` reste dans la config | `env.local` absent/incomplet | créer `~/.hephaistos/env.local`, relancer `install.ps1` |
| `EBUSY` pendant `update --force` | process tient `.agent/` | couper watchers/serveurs, relancer — le merge-copy tolère les locks |
| MCP affiché « failed » dans l'IDE | build manquant | `cd mcp/servers/<nom> && npm i && npm run build` |
| `better-sqlite3` ABI error | module compilé pour une autre version de Node | `cd <serveur> && npm rebuild better-sqlite3` |
| Execution Policy bloque le .ps1 | restriction Windows | `Set-ExecutionPolicy -Scope Process RemoteSigned` |
| `Failed to connect` orchestrator | DB verrouillée/chemin faux | vérifier `ORCHESTRATOR_DB` ; le serveur inclut `busy_timeout` |
| Embeddings rejetés (dim error) | collection ≠ modèle | tout doit être en **2048d** (`nemotron-3-embed-1b`) |
| Scripts `.ps1` corrompus (accents) | encodage UTF-8 sans BOM | les scripts du kit sont livrés **avec BOM** — ne pas les réenregistrer en « UTF-8 sans BOM » |

## Structure après installation complète

```
~/.hephaistos/
├── env.local          # VOS secrets — hors git
└── servers/           # MCP buildés (si build hors kit)
~/.config/mcp-mux/
└── mcp-mux.json       # broker multiplexeur (optionnel)
<projet>/
└── .agent/            # infra agent injectée (voir étape 2)
<IDE>/
└── mcp_config.json    # généré, pointe sur les serveurs
```
