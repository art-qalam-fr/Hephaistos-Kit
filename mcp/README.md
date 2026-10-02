# Hephaistos-Kit — Stack MCP

La configuration MCP **canonique** art-qalam-fr : 18 serveurs, reproductibles sur
n'importe quelle machine en une commande.

## Principe

- `manifest.json` — la liste des serveurs : kind, repo, build, env requis, tier
- `servers/` — **sous-modules git** (chaque MCP = son propre repo épinglé)
- `install.ps1` — clone, build, génère la config de votre IDE
- `cards/<nom>.md` — fiche par serveur (rôle, env, pièges)
- `mcp.config.template.json` — exemple de sortie générée

## Installer tout

```powershell
git clone --recurse-submodules https://github.com/art-qalam-fr/Hephaistos-Kit
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
| `npx` | rien à installer (`puppeteer`) |
| `url` | distant (`github-mcp-server`) |
| `binary` | outil externe à installer (`beacon`) |
| `pip` | `uv tool install <pkg>` (`colab-mcp`) |
| `launcher` | fichier `.devin/launchers/` (notebooks, visualization, data-agent-kit) |

## Ajouter un MCP au kit

1. Pousser le serveur dans son repo (`art-qalam-fr/<nom>`)
2. `git submodule add https://github.com/art-qalam-fr/<nom>.git mcp/servers/<nom>`
3. Ajouter l'entrée dans `manifest.json` + une fiche dans `cards/`
4. Commit + push — la prochaine install l'embarque.
