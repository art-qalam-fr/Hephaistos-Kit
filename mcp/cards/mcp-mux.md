# mcp-mux

**Rôle** : multiplexeur de serveurs MCP — un seul point d'entrée stdio qui
expose les serveurs de sa config broker, processus partagés entre clients
(IDE, mcporter CLI, dashboard). Outils namespacés `mcp-mux.<serveur>__<outil>`.

- **Kind** : `npm` (package global, hors repo)
- **Tier** : `standard`
- **Install** : `npm i -g mcp-mux`
- **Lancement** : `node <npm-global>/node_modules/mcp-mux/src/shim.mjs --config ~/.config/mcp-mux/mcp-mux.json`

## Config broker

Copier `mcp/mcp-mux.config.template.json` → `~/.config/mcp-mux/mcp-mux.json`,
adapter `{INSTALL_ROOT}` et `{WORKSPACE}`. `mode: "shared"` = un processus
par serveur, partagé entre tous les clients.

## Env

Aucune variable requise — les env des serveurs multiplexés se déclarent dans
le bloc `env` de chaque entrée broker (ex. `NVIDIA_API_KEY` pour nim-router).

## Pièges

- **Reload** : modifier `mcp-mux.json` ne recharge pas — tuer le process
  `node … broker.mjs`, le prochain appel respawne.
- **Doublon volontaire** : un même serveur peut être en direct dans l'IDE
  **et** dans le mux (ex. `orchestrator` — même DB SQLite en WAL). Ne pas
  « corriger » la duplication.
- **`{VAR}` non résolues** : le broker lit les valeurs littéralement — les
  secrets passent par `${env:VAR}` ou des valeurs résolues au déploiement.
