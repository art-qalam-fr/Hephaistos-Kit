# MCP `filesystem`

**Rôle** : AccÃ¨s fichiers workspace (read/write/search)

| | |
|---|---|
| kind | `submodule` |
| tier | `standard` |
| repo | `art-qalam-fr/filesystem` |
| build | `npm install && npm run build` |

**Notes** :

Pointe {WORKSPACE} = cwd au moment de l'install. Sécurité: accès fichiers complet au workspace.

## Vérifier

`claude mcp list` / config IDE doit montrer `filesystem` connecté.
