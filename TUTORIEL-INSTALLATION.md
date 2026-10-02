# TUTORIEL — Installer Hephaistos-Kit de zéro

Guide pas à pas pour reproduire l'environnement agentique complet sur une
machine neuve. Temps estimé : **10-15 minutes** (hors builds des serveurs MCP).

---

## Étape 0 — Prérequis

| Outil | Vérifier | Installer |
|---|---|---|
| Git | `git --version` | [git-scm.com](https://git-scm.com) |
| Node.js 18+ | `node --version` | [nodejs.org](https://nodejs.org) |
| Python 3.10+ | `python --version` | [python.org](https://python.org) |
| uv (recommandé) | `uv --version` | `pip install uv` ou [docs.astral.sh/uv](https://docs.astral.sh/uv) |
| PowerShell | `powershell -v` | inclus Windows |

## Étape 1 — Cloner le kit (avec les sous-modules)

```powershell
git clone --recurse-submodules https://github.com/art-qalam-fr/Hephaistos-Kit.git
cd Hephaistos-Kit
```

⚠️ **Important** : `--recurse-submodules` clone aussi les 11 serveurs MCP
dans `mcp/servers/`. Sans lui, les dossiers `mcp/servers/*` restent vides.

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
│   ├── agents/                 # définitions d'agents + routage
│   ├── skills/                 # ~45 skills
│   ├── workflows/              # slash-commands
│   ├── scripts/                # run_chrome_opencli.bat, ingestion…
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

## Étape 3 — Configurer les secrets (une seule fois)

Créer `~/.hephaistos/env.local` — **jamais commité, hors de tout repo** :

```ini
# ~/.hephaistos/env.local
NVIDIA_API_KEY=nvapi-...        # NVIDIA NIM (agents délégués + orchestrateur)
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=...
AGENT_DB_ROOT=<HEPHAISTOS_DATA_DIR>      # racine mémoire unifiée
OPENAI_API_KEY=...              # si provider embedding OpenAI
```

Seules les clés nécessaires à vos serveurs sont requises — l'installateur
liste celles qui manquent.

## Étape 4 — Installer la stack MCP

```powershell
.\mcp\install.ps1 -Ide devin
# autres IDE : cursor | devin | kilocode | antigravity | trae
```

Le script :

1. `git submodule update --init` — clone les 11 serveurs dans `mcp/servers/`
2. Build chacun (`npm i && npm run build`, `uv sync` selon le serveur)
3. Déploie les launchers dans `~/.devin/launchers/`
4. Génère `mcp_config.json` de l'IDE (chemins de VOTRE machine + env résolus)
5. Backup de la config existante en `.bak-YYYYMMDDHHmmss`

Options :

```powershell
.\mcp\install.ps1 -Ide cursor -DryRun     # simule, affiche la config
.\mcp\install.ps1 -Tier standard          # sans les serveurs 'personal'
.\mcp\install.ps1 -SkipBuild              # config seule (serveurs déjà buildés)
```

## Étape 5 — Vérifier

| Vérification | Attendu |
|---|---|
| `projet/.agent/rules/global_rules.md` existe | ✅ injecté |
| `projet/.agent/REGISTRY.md` existe | ✅ registre présent |
| `%APPDATA%\<ide>\mcp_config.json` contient `mcpServers` | ✅ config écrite |
| Relancer l'IDE → serveurs MCP listés connectés | ✅ stack active |

## Étape 6 — Compléments optionnels

- **CLIs recommandés** : agents de délégation (`agy`, `hermes`), `gh`, `uv`…
  → `cli/README.md` (liens + commandes d'install pour chacun).
  Protocole **ACP** de dispatch : `cli/ACP.md`.
- **OpenCLI** (automatisation du Chrome réel) : `npm i -g @jackwener/opencli`,
  `opencli doctor`, Chrome lancé via `.agent/scripts/run_chrome_opencli.bat`
  du projet injecté. Adaptateur cookies (sous-module `cli/opencli-cookies`) :
  `npm i -g github:art-qalam-fr/opencli-cookies` — voir son `TUTORIEL.md`.
- **Beacon** : binaire externe (`beacon mcp serve`) — installer séparément.
- **Google Drive MCP** : déposer `gcp-oauth.keys.json` dans
  `~/.hephaistos/servers/google-drive-mcp/` puis `.\get-refresh-token.ps1`
  → voir `mcp/cards/google-drive.md`.

## Dépannage

| Symptôme | Cause | Fix |
|---|---|---|
| `mcp/servers/*` vides | clone sans submodules | `git submodule update --init --recursive` |
| `${VAR}` reste dans la config | `env.local` absent/incomplet | créer `~/.hephaistos/env.local`, relancer `install.ps1` |
| `EBUSY` pendant `update --force` | process tient `.agent/` | couper watchers/serveurs, relancer — le merge-copy tolère les locks |
| MCP affiché « failed » dans l'IDE | build manquant | `cd mcp/servers/<nom> && npm i && npm run build` |
| Execution Policy bloque le .ps1 | restriction Windows | `Set-ExecutionPolicy -Scope Process RemoteSigned` |

## Structure après installation complète

```
~/.hephaistos/
├── env.local          # VOS secrets — hors git
└── servers/           # MCP buildés (si build hors kit)
<projet>/
└── .agent/            # infra agent injectée (voir étape 2)
<IDE>/
└── mcp_config.json    # généré, pointe sur les serveurs
```
