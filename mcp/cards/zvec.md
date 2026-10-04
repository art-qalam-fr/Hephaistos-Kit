# MCP `zvec`

**Rôle** : Recherche sÃ©mantique mÃ©moire (entitÃ©s/concepts/actions, 384D)

| | |
|---|---|
| kind | `submodule` |
| tier | `standard` |
| repo | `ArchNext/Zvec` |
| build | `npm install && npm run build` |

**Env** :

- `ZVEC_DATA_DIR` **(requis)**
- `EMBEDDING_PROVIDER` **(requis)**
- `EMBEDDING_MODEL` **(requis)**
- `EMBEDDING_DIMENSIONS` **(requis)**
- `OPENAI_API_KEY` (optionnel)
- `EMBEDDING_BASE_URL` (optionnel)
- `QDRANT_BRIDGE_ENABLED` (optionnel)
- `QDRANT_URL` (optionnel)
- `QDRANT_COLLECTION` (optionnel)

**Notes** :

384D mémoire sémantique. ZVEC_DATA_DIR = dossier données local (défaut ~/.hephaistos/zvec-data).

## Vérifier

`claude mcp list` / config IDE doit montrer `zvec` connecté.
