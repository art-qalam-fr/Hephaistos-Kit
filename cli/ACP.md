# Protocole ACP — dispatch d'agents

**ACP (Agent Client Protocol)** = protocole JSON-RPC sur stdio pour parler à
un agent CLI depuis un autre agent. Le kit embarque un client minimal :
`.agent/devin/scripts/acp-dispatch.mjs` (injecté dans chaque projet).

## Usage

```bash
node .agent/devin/scripts/acp-dispatch.mjs --agent hermes --prompt "ta tâche" [--cwd DIR] [--timeout SEC]
node .agent/devin/scripts/acp-dispatch.mjs --cmd "kilo acp" --prompt "..."
```

Agents connus du dispatch : `devin` (`devin acp`), `hermes` (`hermes acp
--accept-hooks`), `kilo` (`kilo acp`), `gemini` (`gemini --acp`). Tout autre
CLI ACP-compatible passe par `--cmd`.

## Différence avec la délégation one-shot

| | `acp-dispatch` | délégation directe |
|---|---|---|
| Canal | ACP/stdin-stdout streamé | flags CLI (`--print`, `-z`, `run`) |
| Streaming | oui (tokens temps réel) | réponse finale seule |
| Use | conversation/suivi | tâche one-shot |

Pour les tâches one-shot, la délégation directe suffit — voir la procédure
testée dans `.agent/rules/global_rules.md` (flags, timeouts, écueils).

## Discipline post-dispatch

1. `git status` / `git diff --stat` — vérifier le travail produit
2. `tsc --noEmit` / `py_compile` — compiler soi-même, ne jamais faire
   confiance au rapport seul
3. Reformattage massif suspect → revert + refaire les edits fonctionnels
