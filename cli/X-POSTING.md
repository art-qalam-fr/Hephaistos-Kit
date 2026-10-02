# Poster une vidéo sur X via OpenCLI — procédure testée

`opencli twitter post` n'accepte que des images (`--images`, max 4). Pour une
vidéo, on pilote le composer de x.com directement. `twitter reply` est
peu fiable (échoue à sa vérification interne) → faire les replies à la main.

Prérequis : `opencli doctor` → daemon `:19825` OK + extension Chrome connectée,
compte X déjà logué dans le Chrome piloté.

## Pièges (déjà testés — inutile de réessayer)

- `browser upload <input[type=file]>` → timeout `Page.fileChooserOpened` :
  un `.click()` JS sur l'input caché n'ouvre pas le chooser (pas d'activation).
- `fetch` vers `localhost` ou `file:` depuis la page → bloqué par le CSP de x.com.
- Injecter le média en base64 via `eval` → limite ~32K par commande.
- `Input.insertText` via `curl -d` → casse l'UTF-8 (accents, emojis) →
  toujours passer par `opencli browser fill` pour le texte.

## La méthode qui marche : presse-papiers + paste natif

```powershell
# 1. Mettre le fichier dans le clipboard Windows
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; `
  $l=New-Object Collections.Specialized.StringCollection; `
  $l.Add('C:\chemin\video.mp4'); `
  [Windows.Forms.Clipboard]::SetFileDropList($l)"
```

```bash
# 2. Ouvrir le composer
opencli browser main open "https://x.com/compose/post"

# 3. Coordonnées du textbox du composer
opencli browser main eval "(()=>{const t=[...document.querySelectorAll(
  '[data-testid=tweetTextarea_0]')].find(e=>e.closest('[role=dialog]'));
  const r=t.getBoundingClientRect();
  return {x:Math.round(r.x+r.width/2), y:Math.round(r.y+15)}})()"

# 4. Vrai clic CDP (trusted) sur le textbox via le daemon opencli
curl -X POST http://127.0.0.1:19825/command -H "X-OpenCLI: 1" \
  -H "Content-Type: application/json" -d '{"id":"c1","action":"cdp",
  "session":"main","cdpMethod":"Input.dispatchMouseEvent","cdpParams":
  {"type":"mousePressed","x":<X>,"y":<Y>,"button":"left","clickCount":1}}'
curl -X POST http://127.0.0.1:19825/command -H "X-OpenCLI: 1" \
  -H "Content-Type: application/json" -d '{"id":"c2","action":"cdp",
  "session":"main","cdpMethod":"Input.dispatchMouseEvent","cdpParams":
  {"type":"mouseReleased","x":<X>,"y":<Y>,"button":"left","clickCount":1}}'

# 5. Ctrl+V natif → le paste transporte le fichier → X uploade tout seul
curl -X POST http://127.0.0.1:19825/command -H "X-OpenCLI: 1" \
  -H "Content-Type: application/json" -d '{"id":"v1","action":"cdp",
  "session":"main","cdpMethod":"Input.dispatchKeyEvent","cdpParams":
  {"type":"rawKeyDown","modifiers":2,"windowsVirtualKeyCode":86,
   "code":"KeyV","key":"v"}}'
curl -X POST http://127.0.0.1:19825/command -H "X-OpenCLI: 1" \
  -H "Content-Type: application/json" -d '{"id":"v2","action":"cdp",
  "session":"main","cdpMethod":"Input.dispatchKeyEvent","cdpParams":
  {"type":"keyUp","modifiers":2,"windowsVirtualKeyCode":86,
   "code":"KeyV","key":"v"}}'
# Attendre l'état « <fichier> : Prêt » dans le composer avant la suite.

# 6. Texte du post (UTF-8 + emojis safe via fill)
opencli browser main fill "[data-testid=tweetTextarea_0]" "…texte…"

# 7. Poster — un clic JS suffit pour les boutons
opencli browser main click "[data-testid=tweetButton]"

# 8. Vérifier et récupérer l'ID du tweet
opencli twitter tweets <handle> --limit 1 -f json
```

## Réponses (thread)

```bash
opencli browser main open "https://x.com/<handle>/status/<id>"
opencli browser main fill "[data-testid=tweetTextarea_0]" "…reply…"
opencli browser main eval "(()=>{const b=document.querySelector(
  '[data-testid=tweetButtonInline]')||document.querySelector(
  '[data-testid=tweetButton]');b.click();return 'ok'})()"
```

⚠️ `opencli twitter tweets` ne liste PAS les réponses — vérifier le thread
complet avec `opencli twitter thread <url-du-premier-post> -f json`.

## Bonus : og:image GitHub (Settings → Social preview)

Même logique : l'input `#repo-image-file-input` refuse le clic, mais le
`DataTransfer` fonctionne en `eval` — l'image doit être fetchable depuis une
origine autorisée par le CSP de github.com (`raw.githubusercontent.com` OK)
et **< 1 Mo** sinon erreur « file is empty » / classe `is-too-big` :

```js
const r = await fetch('https://raw.githubusercontent.com/<org>/<repo>/main/logo/social-preview.jpg');
const blob = await r.blob();
const dt = new DataTransfer();
dt.items.add(new File([blob], 'social-preview.jpg', {type:'image/jpeg'}));
const inp = document.querySelector('#repo-image-file-input');
inp.files = dt.files;
inp.dispatchEvent(new Event('change', {bubbles:true}));
// Le composant file-attachment uploadé puis soumet le formulaire tout seul.
```

*Testé en production le 2026-10-01 : thread vidéo complet posté sans intervention
manuelle sur un compte non-Premium.*
