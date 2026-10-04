# Hephaistos-Kit — Stack MCP

La configuration MCP **canonique** ArchNext : 18 serveurs, reproductibles sur
n'importe quelle machine en une commande.

## Principe

- `manifest.json` — la liste des serveurs : kind, repo, build, env requis, tier
- `servers/` — **sous-modules git** (chaque MCP = son propre repo épinglé)
- `install.ps1` — clone, build, génère la config de votre IDE
- `cards/<nom>.md` — fiche par serveur (rôle, env, pièges)
- `mcp.config.template.json` — exemple de sortie générée

## Installer tout

```powershell
git clone --recurse-submodules https://github.com/ArchNext/Hephaistos-Kit
cd Hephaistos-Kit
.\mcp\install.ps1 -Ide devin          # ou cursor / devin / kilocode / antigravity / trae
```

Résultat : serveurs clonés sous `~/.hephaistos/servers/`, buildés, et la config
MCP de l'IDE écrite (backup automatique de l'ancienne en `.bak`).

## Secrets — la règle d'or

**Aucune clé dans le repo.** Les valeurs vivent dans `~/.hephaistos/env.local` :

```ini
# ~/.hephaistos/env.local — jamais commité
NVIDIA_API_KEY=...
QDRANT_URL=...
QDRANT_API_KEY=...
AGENT_DB_ROOT=...
```

Le manifeste déclare seulement les **noms** de variables. L'installateur résout
les valeurs depuis `env.local`, ou laisse `${VAR}` en placeholder et avertit.

## standard vs personal

`tier: standard` = générique, prêt pour n'importe qui.
`tier: personal` = nécessite des données/setup perso (OAuth Google Drive,
AGENT_DB_ROOT, NVIDIA_API_KEY). `-Tier standard` installe le socle seul.

## Les 4 familles

| kind | comment ça s'installe |
|---|---|
| `submodule` | sous-module git → `npm i && npm run build` (ou `uv sync`) |
| `npx` | rien à installer |
| `local` | dossier pré-installé sous `{INSTALL_ROOT}`, non buildé par le kit (`postgres`, `memory-f`) |
| `url` | distant (`github-mcp-server`) |
| `binary` | outil externe à installer (`beacon`) |
| `pip` | `uv tool install <pkg>` (`colab-mcp`) |
| `launcher` | fichier `.devin/launchers/` (notebooks, visualization, data-agent-kit) |
| `npm` | `npm i -g <pkg>` (`mcp-mux`) |

## mcp-mux (multiplexeur optionnel)

`mcp-mux` (`npm i -g mcp-mux`) est un **broker** qui expose plusieurs serveurs
derrière un seul point d'entrée stdio, avec partage de processus entre clients
(IDE, mcporter, dashboard). Outils namespacés `mcp-mux.<serveur>__<outil>`.

- Entrée générée par `install.ps1` : `node <npm-g>/node_modules/mcp-mux/src/shim.mjs --config ~/.config/mcp-mux/mcp-mux.json`
- Le template `mcp-mux.config.template.json` liste les 17 serveurs de référence. Chaque entrée suppose le binaire correspondant **installé** : `npm i -g` pour `context7`/`memory`, build sous `INSTALL_ROOT` pour les autres, chemins machine (`{MEMORY_F_ROOT}`, `{BEACON_EXE}`) à adapter — sinon le mux logue l'échec et masque les outils.
- Config broker : copier `mcp/mcp-mux.config.template.json` vers
  `~/.config/mcp-mux/mcp-mux.json` et adapter `{INSTALL_ROOT}`/`{WORKSPACE}`
- Recharger le broker après modif de sa config : tuer le process `node … broker.mjs`
- Doublon volontaire : un serveur peut être en direct dans l'IDE **et** dans le
  mux (ex. `orchestrator` — même DB SQLite en WAL, voir `.agent/REGISTRY.md`)

## Ajouter un MCP au kit

1. Pousser le serveur dans son repo (`ArchNext/<nom>`)
2. `git submodule add https://github.com/ArchNext/<nom>.git mcp/servers/<nom>`
3. Ajouter l'entrée dans `manifest.json` + une fiche dans `cards/`
4. Commit + push — la prochaine install l'embarque.
