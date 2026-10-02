# Hephaistos-Kit — CLIs recommandés

Les outils en ligne de commande qui complètent le kit. Chacun s'installe
séparément — ce dossier ne contient que la documentation et les liens.
Les règles injectées (`.agent/rules/global_rules.md`) savent comment
les utiliser une fois présents.

## Agents IA (délégation)

| CLI | Rôle | Installation | Vérifier |
|---|---|---|---|
| **agy** (Antigravity) | Agent principal — génération d'images incluse | via l'IDE Antigravity ([antigravity.google](https://antigravity.google)) ; binaire sous `%LOCALAPPDATA%\agy\bin\` | `agy --print="test" --print-timeout 60s` |
| **hermes** | Agent délégué, provider configurable (NVIDIA NIM…) | installateur Hermes → `%LOCALAPPDATA%\hermes\` | `hermes -z "test"` |
| **kilo** (KiloCode) | Agent délégué alternatif | `npm i -g kilocode` | `kilo run "test"` |
| **devin** | Agent Devin — `devin acp` | via Devin CLI | `devin --help` |

> Délégation : syntaxe testée + pièges dans `.agent/rules/global_rules.md`
> (section « DÉLÉGATION SOUS-AGENTS CLI ») et [ACP.md](ACP.md) pour le
> dispatch par protocole ACP.

## Navigateur

| CLI | Rôle | Installation | Vérifier |
|---|---|---|---|
| **opencli** | Pilote le Chrome réel (session loguée) : click/fill/eval/screenshot + ~150 adaptateurs site | `npm i -g @jackwener/opencli` puis `opencli doctor` + Chrome avec l'extension (`%USERPROFILE%\.opencli\extension`, ou `.agent/scripts/run_chrome_opencli.bat`) | `opencli doctor` → Extension: connected |
| **opencli-cookies** *(sous-module)* | Dump/export de cookies (HttpOnly inclus, Cookie-Editor) | `npm i -g github:art-qalam-fr/opencli-cookies` ou tarball — voir `opencli-cookies/TUTORIEL.md` | `opencli cookies dump --domain example.com` |

> ⚠️ OpenCLI agit sur la session authentifiée — valeurs de cookies masquées
> par défaut, `--reveal` explicite. Jamais d'export commité.
>
> Astuce avancée : poster une **vidéo** sur X (l'adaptateur n'accepte que des
> images) via presse-papiers + Ctrl+V natif → [X-POSTING.md](X-POSTING.md).

## Forge & versionning

| CLI | Rôle | Installation |
|---|---|---|
| **gh** | GitHub CLI (repos, PR, releases) | [cli.github.com](https://cli.github.com) → `gh auth login` |
| **uv** | Gestionnaire Python standard (venv/deps/lock/tools) | `pip install uv` ou [docs.astral.sh/uv](https://docs.astral.sh/uv) |
| **node/npm** | Runtime des serveurs MCP + CLIs | [nodejs.org](https://nodejs.org) (18+) |
| **python** | Runtime serveurs MCP python | [python.org](https://python.org) (3.10+) |

## Ordre d'installation conseillé

1. `node` + `git` + `python` + `uv` (socle)
2. `opencli` + extension Chrome + `opencli-cookies`
3. `agy` / `hermes` (agents délégués — clés via `~/.hephaistos/env.local`)
4. `gh auth login`
5. Stack MCP : `mcp/install.ps1` (voir [../mcp/README.md](../mcp/README.md))
