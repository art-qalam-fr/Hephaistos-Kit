# MANIFEST - Hephaistos-Kit

> Dernière mise à jour: 2026-04-03
> Version: 1.0.0

## 📋 ÉTAT DU PROJET

### Objectif Principal
Système de mémoire unifiée multi-agents avec RAG, logs MCP, et coordination inter-IDE.

### Statut Actuel
- **Phase**: Production
- **Progression**: 80%
- **Stabilité**: ✅ Stable

---

## 🏗️ ARCHITECTURE

### Composants Actifs

| Composant | Technologie | Statut |
|-----------|------------|--------|
| Mémoire unifiée | SQLite + Memory MCP | ✅ Opérationnel |
| Vector Store | Zvec (HNSW) + Qdrant | ✅ Opérationnel |
| Logs MCP | 7 MCP avec LOGGER | ✅ Opérationnel |
| Ingestion RAG | ingest-workspace.ps1 | ✅ Opérationnel |
| Apprentissage | Beacon digests + `/reflect` + `memory-maintenance.ps1` | ✅ Actif |

### MCP Configurés

| MCP | Port | Log |
|-----|------|-----|
| cache | stdio | cache.log |
| memory | stdio | memory.log |
| zvec | stdio | zvec.log |
| qdrant | stdio | qdrant.log |
| sqlite-node | stdio | sqlite.log |
| filesystem | stdio | filesystem.log |
| sequential-thinking | stdio | sequential-thinking.log |

---

## 🤖 AGENTS

### Agents Disponibles

| Agent | Rôle | Skills |
|-------|------|--------|
| orchestrator | Coordination | plan-writing, parallel-agents |
| security-auditor | Sécurité | security-review |
| backend-specialist | API/Backend | api-patterns |
| frontend-specialist | UI/Frontend | frontend-design |
| test-engineer | Tests | testing-patterns, tdd-workflow |
| database-architect | Schema/DB | database-design |
| debugger | Debug | systematic-debugging |
| devops-engineer | Deploy/CI | deployment-procedures |

### IDE Supportés

| IDE | Handoff |
|-----|---------|
| Devin | ✅ |
| Trae | ✅ |
| KiloCode | ✅ |
| Antigravity | ✅ |
| Devin | ✅ (hooks globaux + ACP, voir `.agent/devin/`) |

---

## 📊 MÉTRIQUES

### Collections Vectorielles

| Collection | Points | Dimensions |
|------------|--------|------------|
| skills_unified_rag | 556 | 384 |

### Logs Actifs

```
./logs/
├── cache.log
├── memory.log
├── zvec.log
├── qdrant.log
├── sqlite.log
├── filesystem.log
└── sequential-thinking.log
```

---

## 🚧 CONTRAINTES

### Règles Critiques

1. **Boundary Enforcement**: Chaque agent reste dans son domaine
2. **Handoff Protocol**: Transfert explicite entre agents/IDE
3. **Log Level**: `info` pour tous les MCP
4. **Ingestion**: `logs/` inclus dans RAG

### Limitations Connues

- Memory MCP: Erreurs JSON occasionnelles (contourné via SQLite direct)
- Sequential-thinking: Pas de persistance des sessions

---

## 🎯 ROADMAP

### Sprint Actuel (2026-Q2)

- [x] Système de logs MCP
- [x] Intégration RAG des logs
- [x] Coordination inter-agents
- [x] Orchestrateur intégré
- [ ] Manifeste automatique (ce fichier)

### Backlog

- [ ] Auto-génération du MANIFEST
- [ ] Synchronisation inter-IDE temps réel
- [ ] Analyse prédictive des erreurs

---

## 📝 DÉCISIONS ARCHITECTURALES

### ADR-001: Pas de nouveau MCP Analytics
**Date**: 2026-04-03 — **révisée 2026-10-02**
**Décision**: Pas de MCP analytics dédié. L'apprentissage repose sur : digests Beacon (`beacon_ingest.py` au start-workspace), workflow `/reflect` (distillation → memory_write + ADR `knowledge/decisions/`), et `memory-maintenance.ps1` (purge caches, relations orphelines, rapport auto-observé dans `kv`).
**Raison**: ~~Capacités natives Zvec `analyze_learning`/`auto_tune`~~ — **ces outils n'existent pas** dans le serveur Zvec réel (tools : `zvec_*` CRUD + search uniquement). Le pipeline Beacon `memory evaluations` existe mais exige le service Jev (clé TypeSafe) — désactivé. La correction sémantique est donc faite par l'agent dans `/reflect`.

### ADR-002: Logs intégrés au RAG
**Date**: 2026-04-03
**Décision**: Inclure `logs/` dans l'ingestion malgré exclusion de `memory-database`
**Raison**: Permettre l'analyse des erreurs par le RAG

### ADR-004: Intégration Devin globale via hooks + ACP
**Date**: 2026-09-24
**Décision**: Devin agit comme architecte/orchestrateur ACP. Trois briques installées au niveau utilisateur (`~/.config/devin/`, `%APPDATA%/devin/skills/`) : hooks `awareness.mjs` (SessionStart/UserPromptSubmit injectent l'état orchestrateur+Beacon ; Stop bloque si tâche pending pour `devin`), client `acp-dispatch.mjs` (session/prompt vers hermes/kilo/gemini ACP natifs), agent `devin` enregistré dans l'orchestrateur (`devin -p "{message}"`).
**Raison**: MCP est request/response (agent→serveur) ; le canal montant passe par les hooks lifecycle et par ACP `session/prompt`. Valable sur tous les clients ACP (Desktop, Zed, JetBrains) puisque les hooks sont agent-side.
**Détails**: `.agent/devin/README.md`

### ADR-003: Handoff inter-agents via SQLite
**Date**: 2026-04-03
**Décision**: Stocker les tâches et handoffs dans la mémoire unifiée SQLite
**Raison**: Portabilité entre tous les IDE/agents

---

## 🔄 CHANGEMENT DE PARADIGME

### Détection de Blocage

Si l'agent détecte:
- 3+ tentatives sans progrès
- Erreur identique répétée
- Boucle de correction

### Action Automatique

1. **Stop**: Arrêter l'action courante
2. **Analyze**: `beacon.summarize_activity` (erreurs similaires passées) + `memory_search`
3. **Pivot**: Proposer approche alternative
4. **Log**: Documenter dans les observations + `/reflect` en fin de session

---

## 📂 STRUCTURE FICHIERS

```
├── .agent/
│   ├── agents/          # Définitions agents
│   ├── skills/          # Skills atomiques
│   ├── knowledge/       # Documentation
│   ├── scripts/         # Scripts PowerShell
│   └── rules/           # Règles globales
├── memory-database/     # Junction → current_workspace
└── MANIFEST.md          # Ce fichier
```

---

## 🔗 POINTS D'ENTRÉE

### Pour Reprendre le Contexte

1. **Lire ce MANIFEST**
2. **Consulter les logs**: `./logs/`
3. **Vérifier les tâches**: SQLite `entities` WHERE `entityType='task'`
4. **Insights récents**: `memory_search` + clé `maintenance:last_report` dans `runtime-cache.db` (kv) + digests Beacon

### Commande Rapide

```powershell
# Statut complet
pwsh -File .agent/scripts/start-workspace.ps1 -IngestMode auto
```

---

*Ce manifeste est versionné dans Git. Mettre à jour à chaque changement majeur.*
