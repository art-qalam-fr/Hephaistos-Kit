# Changelog

All notable changes to the Hephaistos-Kit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),

## [Publication publique]

- `tools/publish-public.ps1` : publication snapshot vers l'organisation
  publique `art-qalam-fr` — historique neuf par repo (zéro fuite privée),
  sanitisation automatique des références internes, gitlinks réparés vers
  les SHA publics, idempotent.
- Purge de clés API Mistral en dur (qdrant-mcp-server, Zvec, RAG-PRD.md)
  détectées par GitHub Push Protection — remplacées par variables d'env.
- README des sous-modules : bannière kit + crédits upstream / signature.
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `.agent/scripts/run_chrome_opencli.bat` — lanceur Chrome + extension OpenCLI, injecté avec le kit (chemins portables `%USERPROFILE%`, détection Chrome multi-emplacements, erreurs explicites).
- `.agent/REGISTRY.md` — section « Agent exécutant par défaut » (`agy`) + ordre de repli.
- `global_rules.md` — section « STANDARD PYTHON (uv) » : `uv sync`/`uv run`/`uv add`, `uv.lock` committé, équivalences pip/pipx/poetry.
- `.agent/skills/hephaistos-kit/` — skill auto-descriptive du kit : contenu injecté, commandes init/update, préservations, réparation injection ratée.
- `cli/` — CLIs recommandés (`cli/README.md` : agy, hermes, kilo, opencli, gh, uv…), doc protocole ACP (`cli/ACP.md`), sous-module `cli/opencli-cookies` (adaptateur cookies OpenCLI).
- `TUTORIEL-INSTALLATION.md` — guide d'installation pas à pas (prérequis → clone submodules → env.local → install.ps1 → vérification).
- `mcp/` — **stack MCP canonique portable** : `manifest.json` (18 serveurs, kind/tier/env requis), `install.ps1` (clone submodules → build → génère config par IDE, backup .bak), `mcp.config.template.json` sanitizé, `cards/*.md` (fiche par serveur), `launchers/` (datacloud). **11 sous-modules git** sous `mcp/servers/` : filesystem, sequentialthinking_1tools, mcp-quick-sqlite3, qdrant-mcp-server, Zvec, orchestrator-server, kaggle-mcp, google-drive-mcp, agentMemory, nim-router-mcp, model-discovery-mcp. Secrets : noms de vars seulement, valeurs via `~/.hephaistos/env.local` (jamais commité).

### Changed
- `.agent/rules/global_rules.md` — ajout section « AUTOMATISATION NAVIGATEUR — OpenCLI vs Puppeteer » (routage session loguée vs bac à sable, prérequis daemon/extension, syntaxe) + compléments délégation testés (`kilo run`, `hermes -z`, discipline post-délégation). Sync avec les règles globales machine (2026-10-02).


## [2.0.2] - 2026-02-04
- **New Skills**:
    - `rust-pro` - Master Rust 1.75+ 
- **Agent Workflows**:
    - Updated `orchestrate.md` fix output turkish


## [2.0.1] - 2026-01-26

### Added

- **Agent Flow Documentation**: New comprehensive workflow documentation
    - Added `.agent/AGENT_FLOW.md` - Complete agent flow architecture guide
    - Documented Agent Routing Checklist (mandatory steps before code/design work)
    - Documented Socratic Gate Protocol for requirement clarification
    - Added Cross-Skill References pattern documentation
- **New Skills**:
    - `react-best-practices` - Consolidated Next.js and React expertise
    - `web-design-guidelines` - Professional web design standards and patterns

### Changed

- **Skill Consolidation**: Merged `nextjs-best-practices` and `react-patterns` into unified `react-best-practices` skill
- **Architecture Updates**:
    - Enhanced `.agent/ARCHITECTURE.md` with improved flow diagrams
    - Updated `.agent/rules/GEMINI.md` with Agent Routing Checklist
- **Agent Updates**:
    - Updated `frontend-specialist.md` with new skill references
    - Updated `qa-automation-engineer.md` with enhanced testing workflows
- **Frontend Design Skill**: Enhanced `frontend-design/SKILL.md` with cross-references to `web-design-guidelines`

### Removed

- Deprecated `nextjs-best-practices` skill (consolidated into `react-best-practices`)
- Deprecated `react-patterns` skill (consolidated into `react-best-practices`)

### Fixed

- **Agent Flow Accuracy**: Corrected misleading terminology in AGENT_FLOW.md
    - Changed "Parallel Execution" → "Sequential Multi-Domain Execution"
    - Changed "Integration Layer" → "Code Coherence" with accurate description
    - Added reality notes about AI's sequential processing vs. simulated multi-agent behavior
    - Clarified that scripts require user approval (not auto-executed)

## [2.0.0] - Unreleased

### Initial Release

- Initial release of Hephaistos-Kit
- 20 specialized AI agents
- 37 domain-specific skills
- 11 workflow slash commands
- CLI tool for easy installation and updates
- Comprehensive documentation and architecture guide

[Unreleased]: https://github.com/ArchNext/Hephaistos-Kit/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/ArchNext/Hephaistos-Kit/releases/tag/v2.0.0
