# Hero Adventure - Web Version

A browser front-end for Hero Adventure that runs the real game engine
(`../game_engine.py`, `../game_controller.py`, and `../game_data.py`,
fetched straight from this repo, unmodified) inside
[Pyodide](https://pyodide.org/) (CPython compiled to WebAssembly). It
renders the same `frames`/`controls` JSON screen contract
described in [`../UI_FRAME_PORTING_GUIDE.md`](../UI_FRAME_PORTING_GUIDE.md)
that `play.py` (terminal) and `play_gui.py` (desktop GUI) use, so gameplay
matches those versions exactly - there is only one game engine and one set
of `ui/*.json` screens; this is just a third renderer for them.

## How it works

- `index.html` / `style.css` / `app.js` are static files - no build step,
  no server-side code. `app.js` boots Pyodide, fetches `game_engine.py`,
  `game_controller.py`, and `game_data.py` as text and writes them into
  Pyodide's in-browser virtual filesystem, then imports `GameController`
  exactly as the other front-ends do.
- Each `ui/*.json` screen is fetched on demand (`../ui/<screen_id>.json`)
  and cached in memory.
- Save games use `GameController`'s existing file-based save/load code
  unmodified - the "saves" directory lives in an IndexedDB-backed virtual
  filesystem, so saves persist in that browser/device only (there is no
  server to store them on).
- Because it fetches the actual source files at runtime (not a copied
  build), pushing gameplay/engine changes to this repo is enough to update
  the web version too - nothing in `web/` needs to change when the game
  changes.

## Local testing

Pyodide requires the page to be served over `http(s)://`, not opened as a
`file://` URL. From the repo root:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000/uigames/hero_adventure/web/index.html`
(or `http://localhost:8000/` if using the root redirect).

## Hosting on GitHub Pages

This repo has no build step, so Pages just needs to serve the raw repo
tree so relative fetches (`../game_engine.py`, `../game_controller.py`,
`../ui/*.json`) resolve correctly:

1. GitHub repo -> **Settings -> Pages**.
2. **Build and deployment -> Source:** `Deploy from a branch`.
3. **Branch:** `master`, folder `/ (root)`.
4. Save. The site will be published at
   `https://<username>.github.io/<repo>/`, which redirects (via the root
   `index.html`) to this game.

No GitHub Actions workflow is required - every push to `master` republishes
automatically once Pages is enabled.
