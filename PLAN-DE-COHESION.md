# PLAN DE COHÉSION — Système multi-agents unifié

> **Statut** : v1.0 — 2026-09-24
> **Portée** : orchestration globale des CLI agents (Devin, Hermès, Kilo, Gemini, agy/Antigravity)
> **Principe directeur** : Devin = architecte/coordinateur ACP. Hermès = bus d'orchestration visible. Les autres CLI = exécutants derrière l'orchestrateur MCP.

---

## 1. Vision

```
                    utilisateur
                        │
                        ▼
              ┌──────────────────┐
              │   DEVIN (moi)    │  ← architecte : planifie, dispatche, vérifie
              │  client ACP hub  │
              └────────┬─────────┘
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
 ┌─────────────┐ ┌───────────┐    ┌──────────────┐
 │ orchestrator│ │  HERMÈS   │    │   Beacon     │
 │  MCP (file) │ │ bus ACP   │    │ observabilité│
 │ tasks_todo  │ │ gateway/  │    │ cross-agent  │
 │             │ │ kanban/   │    │              │
 │             │ │ webhook   │    │              │
 └──────┬──────┘ └─────┬─────┘    └──────────────┘
        │ dispatch_task │
        │ (command      │ acp-dispatch.mjs
        │  template)    │ session/prompt
        ▼               ▼
   ┌────────────────────────────────────────┐
   │  kilo acp │ gemini --acp │ hermes acp  │
   │  agy --print (stream-json, pas d'ACP)  │
   └────────────────────────────────────────┘
                       │
                       ▼ update_task / beacon
              retour d'état montant
              → hooks Devin (awareness.mjs)
```

**Le problème résolu** : MCP est request/response (agent → serveur). Le canal montant (serveur → agent) n'existe pas nativement. Ce plan le reconstruit via deux canaux :

1. **Hooks lifecycle Devin** (globaux, valables sur tous les clients ACP) — injection d'état à `SessionStart`/`UserPromptSubmit`, gate `Stop`.
2. **ACP `session/prompt`** — vrai push vers tout agent ACP natif (hermes, kilo, gemini, devin).

---

## 2. État des lieux — inventaire réel (audit 2026-09-24)

### 2.1 Capacités ACP des CLI

| CLI | Version | Commande ACP | Statut | Notes |
|-----|---------|--------------|--------|-------|
| Devin | 3000.10.31 | `devin acp` | ✅ natif | serveur + client ACP ; MCP injectables via `session/new` (v3.10.35) |
| Hermès | — | `hermes acp` | ✅ natif | `--check` OK ; + `gateway`, `webhook`, `send`, `kanban`, `serve`, `proxy`, `cron` |
| Kilo (KiloCode) | 7.7.5 | `kilo acp` | ✅ natif | + `kilo serve` headless, `kilo run`, daemon, `kilo cloud` |
| Gemini | 0.56.0 | `gemini --acp` | ✅ natif | voir §3.2 (deux profils) |
| agy (Antigravity) | 1.2.9 | — | ❌ pas d'ACP | voir §3.1 — alternatives existantes |
| OpenRouter | — | — | N/A | provider, pas un agent. Couvert par `model-discovery` + `hermes proxy` |

### 2.2 Agents enregistrés dans l'orchestrateur MCP

| Agent | id | Commande de réveil | Modèle |
|-------|----|--------------------|--------|
| agy | 2 | `agy --print "{message}" --dangerously-skip-permissions` | abonnement Antigravity |
| kilo | 3 | `kilo run "{message}" -m "{model}"` | openrouter-free / ollama |
| hermes | 4 | `hermes -z "{message}"` | ollama / openrouter-free |
| **devin** | **5** | `devin -p "{message}" --respect-workspace-trust false` | devin-subscription |

`dispatch_task` résout `config.command` avec `{message} {model} {provider} {workspace}` → le CLI cible se réveille avec la notif de tâche.

### 2.3 Déjà déployé aujourd'hui (couche `.agent/devin/`)

| Brique | Emplacement | Fonction |
|--------|-------------|----------|
| `mcp-call.mjs` | `~/.config/devin/scripts/` | client MCP stdio générique (orchestrator, beacon…) |
| `awareness.mjs` | idem | hook : contexte tâches+beacon à SessionStart/UserPromptSubmit ; bloque Stop si tâche pending pour `devin` |
| `acp-dispatch.mjs` | idem | client ACP minimal → `session/new` + `session/prompt` vers tout agent ACP |
| Hooks globaux | `~/.config/devin/config.json` | awareness greffé aux hooks Beacon existants |
| Skills | `%APPDATA%/devin/skills/` | 23 skills Hermès copiés (a2a-*, orchestrator-mcp, model-router…) |
| Agent `devin` | orchestrator MCP | enregistré, id=5 |

---

## 3. Points d'attention par CLI

### 3.1 agy (Antigravity CLI) — pas d'ACP, mais trois leviers

`agy --help` complet : `-p/--print`, `--input-format stream-json` + `--output-format stream-json` (NDJSON multi-turn, **équivalent scriptable d'ACP**), `--conversation` (reprise), `--agent`, `--model`, `--mode`, `agy mcp` (gestion MCP serveurs !), `agy plugin`, `agy remote-control` (daemon de connexion distante).

**Options d'intégration** :

| Option | Mécanisme | Verdict |
|--------|-----------|---------|
| A. stream-json wrapper | `agy --print --input-format stream-json --output-format stream-json` — NDJSON ligne par ligne, un tour par message | ✅ recommandé : le plus proche d'ACP sans ACP |
| B. remote-control daemon | `agy remote-control start` → connexion externe à la session | ⚠️ à tester — surface réseau |
| C. orchestrator command | déjà enregistré : `agy --print "{message}"` | ✅ actif (one-shot) |
| D. Beacon | logs déjà présents (`~/.beacon/antigravity/logs/*.log`) | ✅ observabilité passive |

**Recommandation** : garder C pour le dispatch one-shot ; ajouter un wrapper `agy-bridge.mjs` (A) si on veut du multi-tour scripté. agy n'aura jamais besoin d'ACP si Hermès sert de bus — `hermes send`/webhook peut relayer.

### 3.2 Gemini — deux profils, un seul binaire

- **Un seul exécutable** : `<USERPROFILE>\AppData\Roaming\npm\gemini` (v0.56.0, npm `@google/gemini-cli`).
- **Deux profils de config** dans `~/.gemini/` :
  - `~/.gemini/` (profil principal) → `security.auth.selectedType: "oauth-personal"`, compte Google actif `lascardm@gmail.com`. C'est le profil OAuth = quota gratuit Google (Code Assist).
  - `~/.gemini/antigravity-acp/` → profil séparé pour l'agent Gemini ACP d'Antigravity : `auth.type: "oauth-personal"` aussi, avec son propre `acp_token.json` (credentials OAuth réels — **ne pas committer/exposer**), `conversations/`, `brain/`, MCP servers propres.
  - `settings.json.bak-oauth-switch` → trace d'un basculement API-key → OAuth déjà effectué.

**Conclusion** : les "deux versions" = même binaire, deux profils OAuth distincts. Les deux utilisent le forfait gratuit Google. Pour en exploiter deux en parallèle : `GEMINI_CLI_HOME=<dir>` permet de lancer une seconde instance `gemini --acp` avec le profil `antigravity-acp` — double quota OAuth sur le même compte (⚠️ limites Google partagées par compte, pas par profil).

**Règle** : toujours lancer `gemini --acp` avec le profil `oauth-personal` (défaut). Ne jamais repasser en `api-key` — quota moindre sur l'autre forfait.

### 3.3 Ollama — local + cloud

`ollama list` : ~25 modèles locaux (qwen3.5, Newton-7B, gpt-oss:20b, deepseek-ocr, glm-ocr, nomic-embed-text pour l'embedding 768D) **+ modèles cloud** : `gpt-oss:120b-cloud`, `nemotron-3-ultra:cloud`, `gemma4:31b-cloud`, `nemotron-3-nano:30b-cloud`. Le cache Hermès (`ollama_cloud_models_cache.json`) liste ~60 cloud (kimi-k2.x, glm-5.x, deepseek-v4.x, minimax-m3, qwen3.5:397b, mistral-large-3:675b…).

**Connu** : l'API Ollama directe (`:11434`) a des tool-calling instable avec certains modèles (tests passés "galéraient"). `gpt-oss` passe mieux mais avec des problèmes.

**Position dans l'archi** : Ollama n'est pas un agent — c'est un provider de modèles. Son rôle = alimenter kilo/hermes/agy en modèles free. Le `model-router` skill + `orchestrator.available_models` (Ollama local+cloud, cache 60s) font déjà le sondage. **Action requise** : qualification des modèles cloud pour tool-calling (voir Phase 3).

### 3.4 Hermès — le bus

Hermès est le candidat naturel au rôle d'orchestrateur visible : `gateway` (messaging), `webhook` (souscriptions dynamiques — vrai push entrant !), `send` (CLI → plateformes), `kanban` (board multi-profils, `kanban.db` existant), `acp`, `serve`, `proxy` (OpenAI-compatible local → providers OAuth), `cron`, `hooks`, `pairing`.

`hermes webhook` + `hermes send` = le canal montant le plus propre du système : n'importe quel agent/process peut pousser un message visible dans Hermès.

---

## 4. Plan de mise en œuvre

### Phase 0 — Fondations ✅ (fait le 2026-09-24)

- [x] Inventaire ACP des CLI
- [x] `mcp-call.mjs`, `awareness.mjs`, `acp-dispatch.mjs` dans `~/.config/devin/scripts/`
- [x] Hooks awareness dans `~/.config/devin/config.json` (SessionStart, UserPromptSubmit, Stop)
- [x] Agent `devin` enregistré dans l'orchestrateur (id=5)
- [x] 23 skills Hermès → `%APPDATA%/devin/skills/`
- [x] Couche `.agent/devin/` dans Hephaistos-Kit + ADR-004

### Phase 1 — Validation du canal montant

- [ ] Test `acp-dispatch.mjs --agent hermes --prompt "ping"` (auth Hermès à vérifier)
- [ ] Test `acp-dispatch.mjs --agent kilo` et `--agent gemini`
- [ ] Vérifier `dispatch_task` → `devin -p` réellement lancé (log debug orchestrator)
- [ ] Vérifier que les hooks awareness remontent bien en session réelle (`/hooks`)

### Phase 2 — Hermès comme bus

- [ ] `hermes webhook` : créer une souscription qui reçoit les `update_task` de l'orchestrateur (le MCP devra pousser, ou un hook `PostToolUse` sur `mcp__orchestrator__update_task` → `hermes send`)
- [ ] `hermes kanban` : board de visibilité des tâches dispatchées
- [ ] `hermes proxy` : exposer les providers OAuth en OpenAI-compatible local → agy/gemini peuvent taper dedans

### Phase 3 — agy + Ollama qualification

- [ ] Wrapper `agy-bridge.mjs` stream-json si multi-tour nécessaire
- [ ] Qualification tool-calling : bench des modèles Ollama cloud (gpt-oss:120b-cloud, nemotron-3-ultra:cloud, kimi-k2.7-code) vs local — critère : appels d'outils fiables
- [ ] Mettre à jour `model_prefs` des agents kilo/hermes selon les résultats

### Phase 4 — Boucle complète

- [ ] Hook `PostToolUse` matcher `^mcp__orchestrator__update_task` → notifie Hermès (`hermes send`) quand une tâche passe `completed` → visibilité temps réel du travail terminé
- [ ] `/loop` Devin comme poller de secours si session longue idle
- [ ] Documenter le diagramme de séquence complet dans `wiki-doc/`

---

## 5. Risques & limites

| Risque | Impact | Mitigation |
|--------|--------|-----------|
| Stop-hook en boucle (tâche jamais résoluble) | blocage du turn | `stop_hook_active` guard déjà en place ; `update_task` manuel pour débloquer |
| Timeout hooks (30s) | awareness silencieuse si orchestrator lent | hooks no-fail by design (exit 0 silencieux) |
| Credentials OAuth dans `~/.gemini/antigravity-acp/acp_token.json` | fuite secrets | jamais dans les docs/commits ; déjà hors du repo |
| `agy` sans ACP | pas de push natif | stream-json wrapper + relay Hermès |
| Quotas OAuth Gemini partagés par compte | deux profils ≠ deux quotas | monitoring `gemini /stats` ; fallback kilo/ollama |
| Tool-calling Ollama instable | dispatch échoue silencieusement | qualification Phase 3 ; model_prefs restrictifs |

---

## 6. Questions ouvertes

1. Le profil `antigravity-acp` de Gemini : faut-il le garder tel quel (Antigravity l'utilise) ou le réutiliser comme seconde instance standalone ?
2. `hermes webhook` : quelle URL/payload attend le souscripteur — faut-il un endpoint local (petit serveur Node) pour recevoir ?
3. Faut-il que `dispatch_task` vers `devin` passe par `devin -p` (one-shot, nouvelle session) ou par `acp-dispatch` dans une session ACP persistante ?

---

*Document vivant — mis à jour à chaque phase. Prochaine session de travail : Phase 1 dans ce workspace.*
