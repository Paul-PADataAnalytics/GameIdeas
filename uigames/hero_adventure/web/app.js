// Hero Adventure - browser front-end.
// Runs the real game_engine.py / game_controller.py / game_data.py (fetched
// straight from the repo) inside Pyodide (CPython-in-WASM) and renders the
// same JSON screen contract (frames + controls) that play.py and
// play_gui.py use. See ../UI_FRAME_PORTING_GUIDE.md for the schema this
// renderer implements.

const FRAME_IDS = ["status", "scene", "context", "actions"];

const BAR_COLORS = {
  health: "var(--good)",
  capacity: "var(--warn)",
  journey: "var(--accent)",
  dungeon: "#c77dff",
  levelup: "var(--warn)",
  honor: "#e07a3c",
  odds: "var(--good)",
};

let pyodide = null;
let controller = null;
const screenCache = new Map();

function $(id) {
  return document.getElementById(id);
}

function showError(message) {
  const banner = $("error-banner");
  banner.textContent = message;
  banner.hidden = false;
}

// -- Template formatting: mirrors play.py's SafeDict + str.format_map -----
function fmt(value, ctx) {
  return String(value).replace(/\{([a-zA-Z0-9_]+)\}/g, (whole, key) => {
    if (Object.prototype.hasOwnProperty.call(ctx, key) && ctx[key] !== null && ctx[key] !== undefined) {
      return String(ctx[key]);
    }
    return whole;
  });
}

function resolveNumber(value, ctx) {
  const rendered = fmt(value, ctx);
  const n = parseFloat(rendered);
  return Number.isNaN(n) ? 0 : n;
}

function formatAmount(n) {
  // Mirror Python's "{:g}" - integers show without a decimal point.
  if (Number.isInteger(n)) return String(n);
  return String(Math.round(n * 100) / 100);
}

// -- Fetching / caching screens and game source ---------------------------
async function fetchText(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.text();
}

async function loadScreen(screenId) {
  if (screenCache.has(screenId)) return screenCache.get(screenId);
  const data = JSON.parse(await fetchText(`../ui/${screenId}.json`));
  screenCache.set(screenId, data);
  return data;
}

// -- Pyodide bootstrap ------------------------------------------------------
async function boot() {
  pyodide = await loadPyodide({ indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/" });

  const [gameEngineSrc, gameControllerSrc, gameDataSrc] = await Promise.all([
    fetchText("../game_engine.py"),
    fetchText("../game_controller.py"),
    fetchText("../game_data.py"),
  ]);

  pyodide.FS.writeFile("/home/pyodide/game_engine.py", gameEngineSrc);
  pyodide.FS.writeFile("/home/pyodide/game_controller.py", gameControllerSrc);
  pyodide.FS.writeFile("/home/pyodide/game_data.py", gameDataSrc);

  // Saves persist per-browser via an IndexedDB-backed virtual filesystem -
  // game_engine.py's SAVE_DIR ("./saves") works completely unmodified.
  pyodide.FS.mkdirTree("/home/pyodide/saves");
  pyodide.FS.mount(pyodide.FS.filesystems.IDBFS, {}, "/home/pyodide/saves");
  await new Promise((resolve, reject) => {
    pyodide.FS.syncfs(true, (err) => (err ? reject(err) : resolve()));
  });

  pyodide.runPython(`
import sys
sys.path.insert(0, "/home/pyodide")
from game_controller import GameController
controller = GameController()
`);
  controller = pyodide.globals.get("controller");

  $("boot").hidden = true;
  $("app").hidden = false;
  await refreshScreen();
}

async function persistSaves() {
  await new Promise((resolve, reject) => {
    pyodide.FS.syncfs(false, (err) => (err ? reject(err) : resolve()));
  });
}

// -- Rendering ---------------------------------------------------------------
function progressRatioAndColor(control, ctx) {
  const value = resolveNumber(control.value, ctx);
  const max = resolveNumber(String(control.max), ctx);
  const ratio = max > 0 ? value / max : 0;
  const clamped = Math.min(1, Math.max(0, ratio));
  const kind = control.kind || "journey";
  const thresholds = control.thresholds || {};
  let color = BAR_COLORS[kind] || "var(--accent)";
  if (kind === "health") {
    if (ratio <= (thresholds.critical ?? 0.15)) color = "var(--bad)";
    else if (ratio <= (thresholds.warning ?? 0.35)) color = "var(--warn)";
  } else if (kind === "capacity") {
    if (ratio >= (thresholds.critical ?? 1.0)) color = "var(--bad)";
    else if (ratio >= (thresholds.warning ?? 0.8)) color = "var(--warn)";
  }
  return { value, max, clamped, color };
}

function renderProgress(control, ctx) {
  const { value, max, clamped, color } = progressRatioAndColor(control, ctx);
  const wrap = document.createElement("div");
  wrap.className = "progress";
  const labelRow = document.createElement("div");
  labelRow.className = "progress-label-row";
  const label = document.createElement("span");
  label.textContent = fmt(control.label || control.id || "", ctx);
  labelRow.appendChild(label);
  if (control.show_text !== false) {
    const amount = document.createElement("span");
    amount.textContent =
      control.kind === "odds" && max === 100
        ? `${formatAmount(value)}%`
        : `${formatAmount(value)}/${formatAmount(max)}`;
    labelRow.appendChild(amount);
  }
  wrap.appendChild(labelRow);
  const track = document.createElement("div");
  track.className = "progress-track";
  const fill = document.createElement("div");
  fill.className = "progress-fill";
  fill.style.width = `${clamped * 100}%`;
  fill.style.background = color;
  track.appendChild(fill);
  wrap.appendChild(track);
  return wrap;
}

function renderText(control, ctx, extraClass) {
  const value = fmt(control.value || "", ctx);
  if (!value && !control.show_empty) return null;
  const el = document.createElement("p");
  el.className = control.variant === "title" ? "screen-title" : (extraClass || "scene-line");
  el.textContent = value;
  return el;
}

function renderInput(control, ctx, onCommit) {
  const row = document.createElement("div");
  row.className = "input-row";
  const label = document.createElement("label");
  label.textContent = fmt(control.label || "", ctx);
  const input = document.createElement("input");
  input.type = "text";
  input.placeholder = control.placeholder || "";
  input.value = controller.pending_name || "";
  input.addEventListener("input", () => {
    controller.set_pending_name(input.value);
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      controller.set_pending_name(input.value);
      onCommit();
    }
  });
  row.appendChild(label);
  row.appendChild(input);
  return row;
}

function renderList(control, ctx, onAction) {
  const container = document.createDocumentFragment();
  if (control.label) {
    const label = document.createElement("div");
    label.className = "list-label";
    label.textContent = fmt(control.label, ctx);
    container.appendChild(label);
  }
  const rows = ctx[control.id] || [];
  const maxRows = control.max_rows;
  const visibleRows = maxRows ? rows.slice(0, maxRows) : rows;
  for (const row of visibleRows) {
    const text = fmt(row.text || "", ctx);
    const action = row.action;
    const enabled = row.enabled !== false;
    if (action && enabled) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "list-row clickable";
      if (row.highlight === "better") btn.classList.add("better");
      if (row.highlight === "worse") btn.classList.add("worse");
      btn.textContent = text;
      btn.addEventListener("click", () => onAction(action));
      container.appendChild(btn);
    } else {
      const div = document.createElement("div");
      div.className = "list-row disabled";
      if (row.outcome) div.classList.add(`outcome-${row.outcome}`);
      div.textContent = `- ${text}`;
      container.appendChild(div);
    }
  }
  if (maxRows && rows.length > maxRows) {
    const note = document.createElement("div");
    note.className = "list-overflow-note";
    note.textContent = `Showing ${maxRows} of ${rows.length} entries; scroll for more.`;
    container.appendChild(note);
  }
  return container;
}

function renderButton(control, ctx, onAction) {
  const visibleIf = control.visible_if;
  if (visibleIf && !ctx[visibleIf]) return null;
  const label = fmt(control.label || "", ctx);
  if (!control.action) {
    const div = document.createElement("div");
    div.className = "list-row disabled";
    div.textContent = `- ${label}`;
    return div;
  }
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "action-btn";
  btn.textContent = label;
  btn.addEventListener("click", () => onAction(control.action));
  return btn;
}

function groupCompactProgressbars(controls) {
  // Mirrors play.py: consecutive compact progressbars are laid out together.
  const groups = [];
  let i = 0;
  while (i < controls.length) {
    const control = controls[i];
    if (control.type === "progressbar" && control.compact) {
      const run = [];
      while (i < controls.length && controls[i].type === "progressbar" && controls[i].compact) {
        run.push(controls[i]);
        i += 1;
      }
      groups.push({ compactRun: run });
    } else {
      groups.push({ control });
      i += 1;
    }
  }
  return groups;
}

function renderFrameControls(frameId, controls, ctx, onAction) {
  const el = document.createElement("div");

  if (frameId === "status") {
    const identity = document.createElement("div");
    identity.className = "status-identity";
    const bars = document.createElement("div");
    bars.className = "status-bars";
    for (const control of controls) {
      if (control.type === "progressbar") {
        bars.appendChild(renderProgress(control, ctx));
      } else if (control.type === "text") {
        const node = renderText(control, ctx, "status-identity");
        if (node) identity.appendChild(node);
      }
    }
    el.appendChild(identity);
    el.appendChild(bars);
    return el;
  }

  if (frameId === "actions") {
    for (const control of controls) {
      if (control.type !== "button") {
        appendGenericControl(el, control, ctx, onAction);
        continue;
      }
      const btn = renderButton(control, ctx, onAction);
      if (btn) el.appendChild(btn);
    }
    return el;
  }

  // scene / context: group consecutive compact progressbars into a row.
  for (const group of groupCompactProgressbars(controls)) {
    if (group.compactRun) {
      const row = document.createElement("div");
      row.className = "compact-progress-row";
      for (const control of group.compactRun) {
        row.appendChild(renderProgress(control, ctx));
      }
      el.appendChild(row);
    } else {
      appendGenericControl(el, group.control, ctx, onAction);
    }
  }
  return el;
}

function appendGenericControl(parent, control, ctx, onAction) {
  switch (control.type) {
    case "text": {
      const node = renderText(control, ctx);
      if (node) parent.appendChild(node);
      break;
    }
    case "input":
      parent.appendChild(renderInput(control, ctx, () => refreshScreen()));
      break;
    case "progressbar":
      parent.appendChild(renderProgress(control, ctx));
      break;
    case "list":
      parent.appendChild(renderList(control, ctx, onAction));
      break;
    case "button": {
      const btn = renderButton(control, ctx, onAction);
      if (btn) parent.appendChild(btn);
      break;
    }
    default:
      throw new Error(`Unsupported control type ${control.type}`);
  }
}

// -- Main render/dispatch loop ----------------------------------------------
async function handleAction(action) {
  try {
    controller.dispatch(action);
    if (action.startsWith("save_game") || action.startsWith("load_slot") || action.startsWith("save_and_quit")) {
      await persistSaves();
    }
    await refreshScreen();
  } catch (err) {
    console.error(err);
    showError(`Something went wrong handling "${action}": ${err.message || err}`);
  }
}

async function refreshScreen() {
  if (controller.quit_requested) {
    controller.quit_requested = false;
    $("frame-scene").innerHTML =
      "<p class=\"screen-title\">Thanks for playing!</p><p class=\"scene-line\">You can close this tab, or start again below.</p>";
    $("frame-status").innerHTML = "";
    $("frame-context").innerHTML = "";
    $("frame-context").classList.add("hidden");
    $("frame-actions").innerHTML = "";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "action-btn";
    btn.textContent = "Back to Front Page";
    btn.addEventListener("click", () => {
      controller.screen = "front_page";
      refreshScreen();
    });
    $("frame-actions").appendChild(btn);
    return;
  }

  let screenId = controller.screen;
  let screen;
  try {
    screen = await loadScreen(screenId);
  } catch (err) {
    console.error(err);
    controller.screen = "front_page";
    screenId = "front_page";
    screen = await loadScreen(screenId);
  }

  const ctx = controller.get_context().toJs({ dict_converter: Object.fromEntries });

  const controlsByFrame = { status: [], scene: [], context: [], actions: [] };
  for (const control of screen.controls) {
    if (!(control.frame in controlsByFrame)) {
      throw new Error(`Control uses unknown frame ${control.frame}`);
    }
    controlsByFrame[control.frame].push(control);
  }

  const contextControls = controlsByFrame.context;
  const contextVisible = contextControls.length > 0;
  const listCount = contextControls.filter((c) => c.type === "list").length;
  const progressCount = contextControls.filter((c) => c.type === "progressbar").length;
  const contextDense = contextControls.length >= 4 || listCount >= 2 || progressCount >= 4;

  document.title = `Hero Adventure - ${fmt(screen.title || screenId, ctx)}`;

  for (const frameId of FRAME_IDS) {
    const container = $(`frame-${frameId}`);
    container.innerHTML = "";
    container.appendChild(renderFrameControls(frameId, controlsByFrame[frameId], ctx, handleAction));
  }

  $("frame-context").classList.toggle("hidden", !contextVisible);
  $("frame-context").classList.toggle("dense", contextDense);
}

boot().catch((err) => {
  console.error(err);
  $("boot").innerHTML = `<p>Failed to start Hero Adventure.</p><p class="boot-sub">${err.message || err}</p>`;
});
