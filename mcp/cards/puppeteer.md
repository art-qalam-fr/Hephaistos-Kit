# MCP `puppeteer`

**Rôle** : Navigateur bac Ã  sable (pages publiques, screenshots, tests)

| | |
|---|---|
| kind | `submodule` |
| tier | `standard` |

**Notes** :

Repo autonome `art-qalam-fr/puppeteer` (vendored de
`@modelcontextprotocol/server-puppeteer`, MIT) — cloné dans `{INSTALL_ROOT}`
par install.ps1, `dist/` prébuildé commité, aucun fetch `npx` réseau.
Complément d'OpenCLI (vrai Chrome).

## Vérifier

`claude mcp list` / config IDE doit montrer `puppeteer` connecté.
