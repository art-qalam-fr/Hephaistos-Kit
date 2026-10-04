# MCP `orchestrator`

**Rôle** : Orchestrateur de tÃ¢ches multi-agents (dispatch/list/update)

| | |
|---|---|
| kind | `submodule` |
| tier | `standard` |
| repo | `ArchNext/orchestrator-server` |
| build | `npm install && npm run build` |

**Env** :

- `ORCHESTRATOR_DB` **(requis)**
- `NVIDIA_API_KEY` (optionnel)

**Notes** :

ORCHESTRATOR_DB = chemin sqlite des tâches. Ne jamais écrire la base à la main — outils MCP uniquement.

## Vérifier

`claude mcp list` / config IDE doit montrer `orchestrator` connecté.
