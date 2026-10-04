# Hephaistos-Kit — Installation rapide

> 📖 Version détaillée pas à pas (clés API, dépannage, mcp-mux) :
> **[TUTORIEL-INSTALLATION.md](TUTORIEL-INSTALLATION.md)**

## Install express

```powershell
# 1. Cloner AVEC les sous-modules
git clone --recurse-submodules https://github.com/ArchNext/Hephaistos-Kit.git
cd Hephaistos-Kit

# 2. Injecter .agent/ dans votre projet (depuis son dossier)
node <chemin>\Hephaistos-Kit\bin\hephaistos-kit.js init
#   ou : npm install -g .  puis  hephaistos-kit init

# 3. Secrets dans ~/.hephaistos/env.local (jamais commité)
#    NVIDIA_API_KEY=nvapi-...   <- build.nvidia.com (gratuit)
#    AGENT_DB_ROOT=<chemin>     <- racine mémoire unifiée

# 4. Stack MCP : build + config de l'IDE
.\mcp\install.ps1 -Ide devin
```

## Ce qui est injecté dans le projet

| Composant | Contenu |
|---|---|
| `.agent/rules/` | `global_rules.md` — règles universelles |
| `.agent/agents/` | 21 agents spécialisés + triggers de routage |
| `.agent/skills/` | 40 skills métier |
| `.agent/workflows/` | 12 workflows `/plan`, `/debug`, `/orchestrate`… |
| `.agent/scripts/` | beacon-sync, ingestion workspace, mass-inject… |
| `.agent/REGISTRY.md` | agents/providers canoniques |
| `.vscode/` | configs IDE partagées |

## Commandes du CLI

| Commande | Rôle |
|---|---|
| `hephaistos-kit init` | Injecte `.agent/` + `.vscode/` |
| `hephaistos-kit init --dry-run` | Simulation sans écriture |
| `hephaistos-kit init --path <dir>` | Cible explicite |
| `hephaistos-kit update --force` | Réaligne sur le template (préserve `memory-database/` et `local_rules.md`) |
| `hephaistos-kit status` | État de l'injection |

## Stack MCP (19 serveurs)

`mcp/install.ps1` clone, builde et génère la config IDE. Détail :
**[mcp/README.md](mcp/README.md)** — manifest, cards par serveur, tiers
`standard`/`personal`, multiplexeur optionnel `mcp-mux`.

## Sécurité

- **Aucun secret** dans le repo — tout vit dans `~/.hephaistos/env.local`
- `.env` toujours gitignoré ; les templates n'utilisent que des placeholders
- Embeddings de référence : NVIDIA `nvidia/nemotron-3-embed-1b` (2048d)
