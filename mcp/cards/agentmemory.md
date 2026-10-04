# MCP `agentmemory`

**Rôle** : MÃ©moire unifiÃ©e â€” KV + graph + vector persistant

| | |
|---|---|
| kind | `submodule` |
| tier | `personal` |
| repo | `lascard-m/agentMemory` |
| build | `npm install && npm run build` |

**Env** :

- `AGENT_DB_ROOT` **(requis)**

⚠️ **Setup** : Pointer {AGENTMEMORY_REPO} vers le clone local du repo (contient les modifs ingestion)

**Notes** :

Repo perso avec modifs ingestion. AGENT_DB_ROOT requis. {AGENTMEMORY_REPO} = chemin du clone local.

## Vérifier

`claude mcp list` / config IDE doit montrer `agentmemory` connecté.
