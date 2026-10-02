<div align="center">
  <img src="logo/hephaistos-kit_banderole.jfif" alt="Hephaistos-Kit" width="100%"/>

  # Hephaistos-Kit

  **Le forgeron des environnements de développement agentiques.**

  Un kit d'infrastructure injectable : règles, agents, skills, workflows,
  scripts et la stack MCP complète — pour transformer n'importe quel dossier
  vide en workspace agent prêt à l'emploi.

  📖 <a href="docs/QUI-SOMMES-NOUS.md"><b>Qui sommes-nous</b></a> ·
  ☕ <a href="docs/QUI-SOMMES-NOUS.md#-soutenir-le-projet"><b>Offrir un café</b></a>

  `github.com/art-qalam-fr/Hephaistos-Kit` · MIT
</div>

---

## Ce que fait le kit

Hephaistos-Kit forge en une commande l'environnement complet d'un projet :

| Pilier | Contenu | Destination |
|---|---|---|
| **Règles** | `global_rules.md` (délégation agents, OpenCLI/puppeteer, uv, mémoire unifiée, sécurité) | `.agent/rules/` |
| **Agents** | Définitions + triggers de routage auto | `.agent/agents/` |
| **Skills** | ~45 skills métier (+ `hephaistos-kit` auto-descriptive, `orchestrator`) | `.agent/skills/` |
| **Workflows** | Slash-commands (`/plan`, `/debug`…) | `.agent/workflows/` |
| **Scripts** | `run_chrome_opencli.bat`, `beacon-sync.ps1`, `ingest-workspace.ps1`… | `.agent/scripts/` |
| **Registre** | `REGISTRY.md` — agents/providers canoniques + agent par défaut | `.agent/` |
| **MCP** | Stack complète : 18 serveurs, manifest, installateur, sous-modules | `mcp/` |
| **CLIs** | CLIs recommandés (agents, OpenCLI + adaptateur cookies) + protocole ACP | `cli/` |
| **IDE** | Configs VS Code/MCP partagées | `.vscode/` |

## Installation du kit dans un projet

> 📖 **Guide complet pas à pas** : [TUTORIEL-INSTALLATION.md](TUTORIEL-INSTALLATION.md)

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

18 serveurs MCP documentés et reproductibles :

```powershell
# Cloner AVEC les sous-modules (chaque MCP = son repo épinglé)
git clone --recurse-submodules https://github.com/art-qalam-fr/Hephaistos-Kit
cd Hephaistos-Kit

# Installer : clone/build les serveurs + écrit la config de l'IDE
.\mcp\install.ps1 -Ide devin          # devin | cursor | devin | kilocode | antigravity | trae
.\mcp\install.ps1 -Ide cursor -Tier standard -SkipBuild   # options
```

- `manifest.json` — inventaire : kind (`submodule`/`npx`/`url`/`binary`/`pip`/`launcher`), tier (`standard`/`personal`), env requis
- `servers/` — 11 sous-modules git (filesystem, orchestrator, qdrant, zvec, sqlite, sequentialthinking, kaggle, google-drive, agentMemory, nim-router, model-discovery)
- `cards/` — fiche par serveur (rôle, env, pièges)
- `install.ps1` — résolution `${VAR}`, backup `.bak` de la config existante, `-DryRun`

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
agents de délégation (`agy`, `hermes`, `kilo`), **OpenCLI** (pilotage du
Chrome réel) + l'adaptateur maison **opencli-cookies** (sous-module),
`gh`, `uv`… → [cli/README.md](cli/README.md). Protocole **ACP** de dispatch
d'agents : [cli/ACP.md](cli/ACP.md) (client `.agent/devin/scripts/acp-dispatch.mjs`).

## Règles livrées dans le template

- **Délégation agents** : agents CLI externes configurables (agy, hermes…), procédure éprouvée
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
├── mcp/             # stack MCP (manifest, install.ps1, cards, servers/*)
├── cli/             # CLIs recommandés + ACP + submodule opencli-cookies
├── logo/            # identité visuelle
└── INSTALL.md / MANIFEST.md / CHANGELOG.md
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
