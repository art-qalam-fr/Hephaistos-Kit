<div align="center">
  <img src="logo/hephaistos-kit_banderole.jfif" alt="Hephaistos-Kit" width="100%"/>

  # Hephaistos-Kit

  **Le forgeron des environnements de développement agentiques.**

  Un kit d'infrastructure injectable : règles, agents, skills, workflows,
  scripts et la stack MCP complète — pour transformer n'importe quel dossier
  vide en workspace agent prêt à l'emploi.

  📖 <a href="docs/QUI-SOMMES-NOUS.md"><b>Qui sommes-nous</b></a> ·
  ☕ <a href="docs/QUI-SOMMES-NOUS.md#-soutenir-le-projet"><b>Offrir un café</b></a>

  `github.com/ArchNext/Hephaistos-Kit` · MIT
</div>

---

## Ce que fait le kit

Hephaistos-Kit forge en une commande l'environnement complet d'un projet :

| Pilier | Contenu | Destination |
|---|---|---|
| **Règles** | `global_rules.md` (délégation sous-agents, OpenCLI/puppeteer, uv, mémoire unifiée, sécurité) | `.agent/rules/` |
| **Agents** | 21 définitions + triggers de routage auto | `.agent/agents/` |
| **Skills** | 40 skills métier (+ `hephaistos-kit` auto-descriptive, `orchestrator`) | `.agent/skills/` |
| **Workflows** | 12 slash-commands (`/plan`, `/debug`…) | `.agent/workflows/` |
| **Scripts** | `beacon-sync.ps1`, `ingest-workspace.ps1`, `mass-inject.py`… | `.agent/scripts/` |
| **Registre** | `REGISTRY.md` — agents/providers canoniques + agent par défaut | `.agent/` |
| **MCP** | Stack complète : 19 serveurs, manifest, installateur, sous-modules | `mcp/` |
| **CLIs** | CLIs recommandés (sous-agents, OpenCLI + adaptateur cookies) + protocole ACP | `cli/` |
| **IDE** | Configs VS Code/MCP partagées | `.vscode/` |

### Ce que le kit met à disposition

- **Délégation par sous-agents** : CLIs externes (`agy`, `hermes`, `kilo`)
  enregistrés dans l'orchestrateur — dispatch de tâches, suivi, retour de
  résultats (procédure éprouvée, voir `cli/ACP.md`)
- **Mémoire unifiée** : Qdrant (recherche vectorielle 2048d), Zvec (graphes),
  SQLite, `memory_mcp.db` — un espace mémoire partagé entre agents et projets
- **Beacon → mémoire** : ingestion des traces de sessions (`beacon_ingest.py`
  + `beacon-sync.ps1`) vers Qdrant + relations mémoire
- **Orchestrateur** : tâches, agents, templates de prompt — SQLite, multi-clients
- **Embeddings de référence** : **NVIDIA NIM** `nvidia/nemotron-3-embed-1b` (2048d)
- **mcp-mux** : multiplexeur optionnel, partage les serveurs entre IDE/CLIs

## Installation du kit dans un projet

> 📖 **Guide complet pas à pas** : [TUTORIEL-INSTALLATION.md](TUTORIEL-INSTALLATION.md)
> ⚡ Version courte : [INSTALL.md](INSTALL.md)

```bash
# Dans le dossier du projet cible
hephaistos-kit init              # injecte .agent/ + .vscode/
hephaistos-kit init --dry-run    # simulation sans copie
hephaistos-kit init --path <dir> # autre cible
hephaistos-kit update --force    # réaligne sur le template (merge-copy tolérant)
```

Ou sans installation, depuis le clone du kit :

```bash
node bin/hephaistos-kit.js init --path <projet>
```

### Ce qui est préservé à chaque `--force`

- `.agent/memory-database/` — index/caches locaux du projet
- `.agent/rules/local_rules.md` — règles spécifiques au projet
- Fallback merge-copy si un dossier est verrouillé (EBUSY Windows)

## Stack MCP — `mcp/`

19 serveurs MCP documentés et reproductibles :

```powershell
# Cloner AVEC les sous-modules (chaque MCP = son repo épinglé)
git clone --recurse-submodules https://github.com/ArchNext/Hephaistos-Kit
cd Hephaistos-Kit

# Installer : clone/build les serveurs + écrit la config de l'IDE
.\mcp\install.ps1 -Ide devin          # devin | cursor | kilocode | antigravity | trae
.\mcp\install.ps1 -Ide cursor -Tier standard -SkipBuild   # options
```

- `manifest.json` — inventaire : kind (`submodule`/`npm`/`npx`/`url`/`binary`/`pip`/`launcher`), tier (`standard`/`personal`), env requis
- `servers/` — 11 sous-modules git (filesystem, orchestrator, qdrant, zvec, sqlite, sequentialthinking, kaggle, google-drive, agentMemory, nim-router, model-discovery)
- `cards/` — fiche par serveur (rôle, env, pièges)
- `install.ps1` — résolution `${VAR}`, backup `.bak` de la config existante, `-DryRun`
- `mcp-mux.config.template.json` — config du multiplexeur (optionnel)

### Secrets

**Jamais dans le repo.** Le manifeste déclare les noms de variables ;
les valeurs vivent dans `~/.hephaistos/env.local` :

```ini
NVIDIA_API_KEY=...
QDRANT_URL=...
AGENT_DB_ROOT=...
```

## CLIs — `cli/`

Les outils en ligne de commande préconisés (chacun s'installe séparément) :
sous-agents de délégation (`agy`, `hermes`, `kilo`), **OpenCLI** (pilotage du
Chrome réel) + l'adaptateur maison **opencli-cookies** (sous-module),
`gh`, `uv`… → [cli/README.md](cli/README.md). Protocole **ACP** de dispatch
d'agents : [cli/ACP.md](cli/ACP.md) (client `.agent/devin/scripts/acp-dispatch.mjs`).

## Règles livrées dans le template

- **Délégation sous-agents** : CLIs externes configurables (agy, hermes, kilo),
  procédure éprouvée — distincts des sub-agents internes de l'IDE
- **Navigateur** : OpenCLI pour le Chrome de l'utilisateur ; Puppeteer MCP en bac à sable
- **Python** : `uv` standard (`uv sync` / `uv run` / `uv add`, `uv.lock` committé)
- **Mémoire unifiée** : `AGENT_DB_ROOT/current_workspace/`, sourcing avant tâche
- **Sécurité** : aucun secret, aucun chemin perso, `.env` toujours gitignoré

## Structure

```
Hephaistos-Kit/
├── .agent/          # template injecté (rules, agents, skills, workflows, scripts)
├── .vscode/         # configs IDE injectées
├── bin/hephaistos-kit.js   # CLI init/update
├── mcp/             # stack MCP (manifest, install.ps1, cards, servers/*, template mux)
├── cli/             # CLIs recommandés + ACP + submodule opencli-cookies
├── logo/            # identité visuelle
└── INSTALL.md / TUTORIEL-INSTALLATION.md / MANIFEST.md / CHANGELOG.md
```

## Qui sommes-nous

Forgé pour un besoin personnel, maintenant offert à tous — voir
**[docs/QUI-SOMMES-NOUS.md](docs/QUI-SOMMES-NOUS.md)**. Puissiez-vous y
trouver de quoi démarrer sereinement, que vous soyez débutant ou simple pressé.

## ☕ Soutenir le projet

MIT ne change rien à la gratuité — mais si le kit vous fait gagner du temps :

<div align="center">
  <a href="docs/QUI-SOMMES-NOUS.md#-soutenir-le-projet">
    <img src="logo/paypal-qr.png" alt="PayPal — offrir un café" width="180"/>
  </a>
  <br/><sub>Scannez pour offrir un café via PayPal</sub>
</div>

## Licence

MIT — voir `LICENSE`.
