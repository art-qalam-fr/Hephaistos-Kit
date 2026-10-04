# MCP `qdrant`

**Rôle** : Recherche vectorielle code/docs (768D projet + 2048D gÃ©nÃ©rique)

| | |
|---|---|
| kind | `submodule` |
| tier | `standard` |
| repo | `ArchNext/qdrant-mcp-server` |
| build | `npm install && npm run build` |

**Env** :

- `QDRANT_URL` **(requis)**
- `EMBEDDING_PROVIDER` **(requis)**
- `EMBEDDING_MODEL` **(requis)**
- `EMBEDDING_DIMENSIONS` **(requis)**
- `QDRANT_API_KEY` (optionnel)
- `OPENAI_API_KEY` (optionnel)
- `OPENAI_BASE_URL` (optionnel)
- `EMBEDDING_BASE_URL` (optionnel)

**Notes** :

Toutes les collections sont 2048D via NVIDIA NIM `nvidia/nemotron-3-embed-1b` (`NVIDIA_API_KEY`). Voir règle EMBED-FIRST.

## Vérifier

`claude mcp list` / config IDE doit montrer `qdrant` connecté.
