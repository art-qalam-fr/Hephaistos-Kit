# MCP `google-drive`

**Rôle** : Google Drive â€” upload/list/fichiers

| | |
|---|---|
| kind | `submodule` |
| tier | `personal` |
| repo | `ArchNext/google-drive-mcp` |
| build | `npm install` |

⚠️ **Setup** : Placer gcp-oauth.keys.json + .gdrive-server-credentials.json dans le dossier du serveur (jamais commitÃ©s â€” obtenus via get-refresh-token.ps1)

**Notes** :

SETUP MANUEL requis : gcp-oauth.keys.json (console GCP) + get-refresh-token.ps1 → .gdrive-server-credentials.json. Ces 2 fichiers = secrets, gitignorés.

## Vérifier

`claude mcp list` / config IDE doit montrer `google-drive` connecté.
