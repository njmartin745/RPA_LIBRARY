import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const __filename = fileURLToPath(import.meta.url);
const REPO_ROOT = path.resolve(path.dirname(__filename), "..");
const FIXTURE_DIR = path.join(REPO_ROOT, "dev", "fixtures", "rpa_studio_playwright_demo");
const OUT_ROOT = path.join(REPO_ROOT, "dev", "_smoke_artifacts", "rpa_studio_playwright_recorder");
const SCENARIO = "rpa-studio-playwright-controlled-recorder";

let browser = null;
let page = null;
let recording = false;
let running = false;
let actions = [];
let logs = [];
let injectionStatus = "not injected";
let injectionMessage = "Recorder has not been injected.";

function nowMs() {
  return Date.now();
}

function log(message, extra = {}) {
  const row = { timestamp_ms: nowMs(), message, ...extra };
  logs.push(row);
  return row;
}

function setInjectionStatus(status, message = "") {
  injectionStatus = status;
  injectionMessage = message || status;
  log("recorder injection status", { injection_status: injectionStatus, message: injectionMessage });
  return { injection_status: injectionStatus, injection_message: injectionMessage };
}

function uniqueRunDir() {
  fs.mkdirSync(OUT_ROOT, { recursive: true });
  const dir = path.join(OUT_ROOT, `run_${process.hrtime.bigint()}_${process.pid}`);
  fs.mkdirSync(dir, { recursive: false });
  return dir;
}

function writeJson(filePath, obj) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(obj, null, 2) + "\n", "utf8");
}

function writeText(filePath, text) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, text, "utf8");
}

function workflowFromActions(inputActions = actions) {
  return {
    schema_id: "RPA_STUDIO_PLAYWRIGHT_RECORDER_WORKFLOW_1A",
    name: "rpa_studio_playwright_controlled_recorder",
    scenario: SCENARIO,
    runtime_scope: "experimental_playwright_controlled_browser",
    actions: inputActions.map((action) => ({ ...action })),
  };
}

function appendAction(action) {
  if (!recording) return;
  const next = {
    ...action,
    order: actions.length + 1,
    timestamp_ms: nowMs(),
    source_url: page ? page.url() : action.source_url || "",
  };
  if (next.type === "Type") {
    const previous = actions[actions.length - 1];
    if (previous && previous.type === "Type" && previous.selector === next.selector) {
      next.order = previous.order;
      actions[actions.length - 1] = next;
      log("updated Type", { selector: next.selector });
      return;
    }
  }
  actions.push(next);
  log(`captured ${next.type}`, { selector: next.selector || "", url: next.url || "" });
}

function selectorFor(el) {
  if (!el || !el.tagName) return "";
  if (el.id) return `#${CSS.escape(el.id)}`;
  if (el.getAttribute("name")) return `${el.tagName.toLowerCase()}[name='${CSS.escape(el.getAttribute("name"))}']`;
  if (el.getAttribute("data-testid")) return `[data-testid='${CSS.escape(el.getAttribute("data-testid"))}']`;
  if (el.getAttribute("aria-label")) return `${el.tagName.toLowerCase()}[aria-label='${CSS.escape(el.getAttribute("aria-label"))}']`;
  if (el.getAttribute("placeholder")) return `${el.tagName.toLowerCase()}[placeholder='${CSS.escape(el.getAttribute("placeholder"))}']`;
  return el.tagName.toLowerCase();
}

const RECORDER_INIT_SCRIPT = `
(() => {
  if (window.__rpaPwRecorderInstalled) return;
  window.__rpaPwRecorderInstalled = true;
  function selectorFor(el) {
    if (!el || !el.tagName) return "";
    if (el.id) return "#" + CSS.escape(el.id);
    if (el.getAttribute("name")) return el.tagName.toLowerCase() + "[name='" + CSS.escape(el.getAttribute("name")) + "']";
    if (el.getAttribute("data-testid")) return "[data-testid='" + CSS.escape(el.getAttribute("data-testid")) + "']";
    if (el.getAttribute("aria-label")) return el.tagName.toLowerCase() + "[aria-label='" + CSS.escape(el.getAttribute("aria-label")) + "']";
    if (el.getAttribute("placeholder")) return el.tagName.toLowerCase() + "[placeholder='" + CSS.escape(el.getAttribute("placeholder")) + "']";
    return el.tagName.toLowerCase();
  }
  function labelFor(el) {
    return ((el && (el.getAttribute("aria-label") || el.getAttribute("placeholder") || el.innerText || el.value)) || "").toString().slice(0, 80);
  }
  document.addEventListener("click", (event) => {
    const el = event.target;
    if (!el || el.type === "hidden" || el.type === "password") return;
    window.__rpaPwRecord({ type: "Click", selector: selectorFor(el), label: labelFor(el) });
  }, true);
  document.addEventListener("input", (event) => {
    const el = event.target;
    if (!el || el.type === "hidden") return;
    if (el.type === "password") {
      window.__rpaPwRecord({ type: "TypeSecret", selector: selectorFor(el), secret_ref: "secret://pm15-redacted", redacted: true, label: "password field redacted" });
      return;
    }
    window.__rpaPwRecord({ type: "Type", selector: selectorFor(el), text: String(el.value || ""), label: labelFor(el), redacted: false });
  }, true);
})();
`;

async function installRecorder(targetPage = page) {
  if (!targetPage) throw new Error("No controlled browser page is open.");
  try {
    await targetPage.exposeFunction("__rpaPwRecord", (action) => appendAction(action)).catch(() => {});
    await targetPage.addInitScript(RECORDER_INIT_SCRIPT);
    await targetPage.evaluate(RECORDER_INIT_SCRIPT);
    return setInjectionStatus(recording ? "recording active" : "injected", "Recorder injected into the active page.");
  } catch (error) {
    recording = false;
    setInjectionStatus("injection failed", `Recorder injection failed: ${String(error)}`);
    throw error;
  }
}

async function launchBrowser({ url, headed = true } = {}) {
  if (!browser) {
    try {
      browser = await chromium.launch({ channel: "msedge", headless: !headed, args: ["--window-size=1280,900"] });
      log("launched Edge controlled browser");
    } catch (edgeError) {
      browser = await chromium.launch({ headless: !headed, args: ["--window-size=1280,900"] });
      log("launched Chromium controlled browser", { edge_fallback: String(edgeError) });
    }
  }
  if (!page || page.isClosed()) {
    page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    page.on("framenavigated", async (frame) => {
      if (frame === page.mainFrame()) {
        setInjectionStatus("page changed, reinjection needed", "Page changed; recorder must be reinjected for this page.");
      }
      if (frame === page.mainFrame() && recording) {
        appendAction({ type: "Navigate", url: page.url(), label: "Navigate" });
        try {
          await installRecorder(page);
        } catch (error) {
          recording = false;
          setInjectionStatus("injection failed", `Recorder injection failed after navigation: ${String(error)}`);
        }
      }
    });
  }
  if (url) {
    try {
      await page.goto(url);
      if (!recording) {
        setInjectionStatus("not injected", "Page loaded. Recorder has not been injected yet.");
      }
    } catch (error) {
      recording = false;
      setInjectionStatus("injection failed", `Navigation failed before recorder injection: ${String(error)}`);
      throw error;
    }
  }
  return { status: "launched", url: page.url(), headed, browser: "edge-or-chromium" };
}

async function startRecording() {
  await launchBrowser({});
  recording = false;
  await installRecorder(page);
  recording = true;
  setInjectionStatus("recording active", "Recorder injected and recording is active.");
  appendAction({ type: "Navigate", url: page.url(), label: "Current page" });
  return { status: "recording", url: page.url(), action_count: actions.length, injection_status: injectionStatus, injection_message: injectionMessage };
}

async function stopRecording() {
  recording = false;
  if (injectionStatus === "recording active") {
    setInjectionStatus("injected", "Recorder remains injected; recording is stopped.");
  }
  return { status: "stopped", browser_open: Boolean(browser && browser.isConnected()), page_open: Boolean(page && !page.isClosed()), action_count: actions.length, injection_status: injectionStatus, injection_message: injectionMessage };
}

async function runSteps(fromIndex = 0) {
  if (!page || page.isClosed()) throw new Error("No controlled browser page is open.");
  running = true;
  const runLog = [];
  for (let i = Number(fromIndex) || 0; i < actions.length; i += 1) {
    const action = actions[i];
    try {
      if (!running) throw new Error("Run stopped");
      if (action.type === "Navigate") await page.goto(action.url);
      if (action.type === "Click") await page.locator(action.selector).click({ timeout: 4000 });
      if (action.type === "Type") await page.locator(action.selector).fill(action.text || "", { timeout: 4000 });
      if (action.type === "TypeSecret") log("skipped redacted secret replay", { selector: action.selector });
      if (action.type === "Wait for Selector") await page.locator(action.selector).waitFor({ timeout: 4000 });
      runLog.push({ step_index: i, status: "ok", action: action.type, selector: action.selector || "", url: action.url || "" });
    } catch (error) {
      running = false;
      const failed = { step_index: i, status: "error", action: action.type, selector: action.selector || "", error: String(error) };
      runLog.push(failed);
      return { status: "fail", failed_step: failed, run_log: runLog, browser_open: Boolean(browser && browser.isConnected()) };
    }
  }
  running = false;
  return { status: "pass", run_log: runLog, browser_open: Boolean(browser && browser.isConnected()), page_open: Boolean(page && !page.isClosed()) };
}

async function highlightStep(index) {
  if (!page || page.isClosed()) throw new Error("No controlled browser page is open.");
  const action = actions[Number(index)];
  if (!action || !action.selector) return { status: "missing", message: "Selected step has no selector." };
  const found = await page.locator(action.selector).count();
  if (!found) return { status: "missing", message: `Element not found: ${action.selector}` };
  await page.locator(action.selector).evaluate((el) => {
    const previous = el.getAttribute("data-rpa-old-outline") || "";
    el.setAttribute("data-rpa-old-outline", previous || el.style.outline || "");
    el.style.outline = "4px solid #ffbf00";
    el.scrollIntoView({ block: "center", inline: "center" });
    setTimeout(() => { el.style.outline = el.getAttribute("data-rpa-old-outline") || ""; }, 1500);
  });
  return { status: "highlighted", selector: action.selector };
}

function saveWorkflow() {
  const runDir = uniqueRunDir();
  const workflowPath = path.join(runDir, "workflow", "recorded_workflow.json");
  const logPath = path.join(runDir, "logs", "run.jsonl");
  writeJson(workflowPath, workflowFromActions());
  writeText(logPath, logs.map((row) => JSON.stringify(row)).join("\n") + "\n");
  return { status: "saved", workflow_json: workflowPath, run_dir: runDir, artifacts: [workflowPath, logPath], action_count: actions.length };
}

async function closeBrowser() {
  recording = false;
  running = false;
  if (browser) await browser.close();
  browser = null;
  page = null;
  setInjectionStatus("not injected", "Controlled browser closed.");
  return { status: "closed" };
}

function htmlPage(demoUrl) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RPA Studio Playwright Recorder</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #eef2f6; color: #182534; }
    header { background: #123b5d; color: #fff; padding: 18px 22px; }
    main { display: grid; grid-template-columns: 380px minmax(520px, 1fr); gap: 14px; padding: 14px; }
    section { background: #fff; border: 1px solid #d6dee8; border-radius: 8px; padding: 14px; }
    button { border: 0; border-radius: 6px; background: #1769aa; color: white; cursor: pointer; font-weight: 700; margin: 5px 4px 5px 0; padding: 8px 10px; }
    button.secondary { background: #586677; }
    button.danger { background: #9b2d30; }
    input { box-sizing: border-box; border: 1px solid #aab6c5; border-radius: 6px; padding: 8px; width: 100%; }
    textarea, pre { box-sizing: border-box; width: 100%; min-height: 220px; overflow: auto; white-space: pre-wrap; background: #f8fafc; border: 1px solid #d6dee8; border-radius: 6px; padding: 10px; }
    .notice { background: #fff7d6; border: 1px solid #dec35f; border-radius: 6px; padding: 9px; }
    .actions { padding-left: 20px; }
    .actions li { margin-bottom: 8px; cursor: pointer; }
    .selected { background: #dbeafe; }
  </style>
</head>
<body>
  <header>
    <h1>RPA Studio Playwright Recorder</h1>
    <p>Experimental controlled browser recorder. Not production-ready.</p>
  </header>
  <main>
    <section>
      <h2>Controls</h2>
      <div class="notice">Uses a real headed Edge/Chromium browser. External replay, universal website support, credentials, downloads, CAPTCHA, anti-bot bypass, retry/resume, scheduling, and multi-agent execution are not proven.</div>
      <label for="target-url">URL</label>
      <input id="target-url" value="${demoUrl}">
      <button id="start">Start Recording</button>
      <button id="inject" class="secondary">Inject Recorder / Reattach</button>
      <button id="stop" class="secondary">Stop Recording</button>
      <button id="run-all">Run All</button>
      <button id="run-from">Run From Selected Step</button>
      <button id="stop-run" class="secondary">Stop Run</button>
      <button id="save">Save Workflow JSON</button>
      <button id="clear" class="danger">Clear Actions</button>
      <p id="browser-status">Browser not launched.</p>
      <p id="injection-status">Recorder injection: not injected.</p>
      <p id="current-url">Current URL: none</p>
      <h3>Recorded Actions</h3>
      <ol id="actions" class="actions"></ol>
    </section>
    <section>
      <h2>Workflow JSON</h2>
      <textarea id="workflow-json"></textarea>
      <h2>Live Log</h2>
      <pre id="live-log">Ready.</pre>
      <h2>Run Evidence</h2>
      <pre id="evidence">No run yet.</pre>
    </section>
  </main>
  <script>
    let actions = [];
    let selected = 0;
    const actionsEl = document.getElementById('actions');
    const jsonEl = document.getElementById('workflow-json');
    const logEl = document.getElementById('live-log');
    const evidenceEl = document.getElementById('evidence');
    const browserStatusEl = document.getElementById('browser-status');
    const injectionStatusEl = document.getElementById('injection-status');
    const currentUrlEl = document.getElementById('current-url');
    function log(line) { logEl.textContent += '\\n' + new Date().toISOString() + ' ' + line; logEl.scrollTop = logEl.scrollHeight; }
    function render() {
      actionsEl.innerHTML = '';
      actions.forEach((action, index) => {
        const li = document.createElement('li');
        li.className = index === selected ? 'selected' : '';
        li.textContent = index + ': ' + action.type + ' ' + (action.selector || action.url || '') + (action.text ? ' = ' + action.text : action.secret_ref ? ' = [secret_ref]' : '');
        li.addEventListener('click', async () => {
          selected = index;
          render();
          const res = await fetch('/api/highlight', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ index }) });
          log('highlight: ' + JSON.stringify(await res.json()));
        });
        actionsEl.appendChild(li);
      });
      jsonEl.value = JSON.stringify({ schema_id: 'RPA_STUDIO_PLAYWRIGHT_RECORDER_WORKFLOW_1A', scenario: '${SCENARIO}', actions }, null, 2);
    }
    async function refresh() {
      const data = await (await fetch('/api/state')).json();
      actions = data.actions || [];
      browserStatusEl.textContent = 'Browser status: ' + data.browser_status;
      injectionStatusEl.textContent = 'Recorder injection: ' + data.injection_status + (data.injection_message ? ' - ' + data.injection_message : '');
      currentUrlEl.textContent = 'Current URL: ' + (data.current_url || 'none');
      render();
    }
    setInterval(refresh, 1000);
    document.getElementById('start').addEventListener('click', async () => {
      const res = await fetch('/api/start-recording', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ url: document.getElementById('target-url').value }) });
      const data = await res.json(); log('start: ' + JSON.stringify(data)); await refresh();
    });
    document.getElementById('stop').addEventListener('click', async () => { const data = await (await fetch('/api/stop-recording', { method: 'POST' })).json(); log('stop: ' + JSON.stringify(data)); await refresh(); });
    document.getElementById('inject').addEventListener('click', async () => { const res = await fetch('/api/inject-recorder', { method: 'POST' }); const data = await res.json(); log('inject: ' + JSON.stringify(data)); evidenceEl.textContent = JSON.stringify(data, null, 2); await refresh(); });
    document.getElementById('run-all').addEventListener('click', async () => { const data = await (await fetch('/api/run', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ fromIndex: 0 }) })).json(); evidenceEl.textContent = JSON.stringify(data, null, 2); log('run all: ' + data.status); await refresh(); });
    document.getElementById('run-from').addEventListener('click', async () => { const data = await (await fetch('/api/run', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ fromIndex: selected }) })).json(); evidenceEl.textContent = JSON.stringify(data, null, 2); log('run from: ' + data.status); await refresh(); });
    document.getElementById('stop-run').addEventListener('click', async () => { const data = await (await fetch('/api/stop-run', { method: 'POST' })).json(); log('stop run: ' + JSON.stringify(data)); });
    document.getElementById('save').addEventListener('click', async () => { const data = await (await fetch('/api/save', { method: 'POST' })).json(); evidenceEl.textContent = JSON.stringify(data, null, 2); log('save: ' + data.workflow_json); });
    document.getElementById('clear').addEventListener('click', async () => { const data = await (await fetch('/api/clear', { method: 'POST' })).json(); log('clear: ' + JSON.stringify(data)); await refresh(); });
    refresh();
  </script>
</body>
</html>`;
}

function sendJson(res, obj, status = 200) {
  const body = JSON.stringify(obj, null, 2);
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "content-length": Buffer.byteLength(body) });
  res.end(body);
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  if (!chunks.length) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

async function startStudioServer(port = 8879) {
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url, `http://127.0.0.1:${port}`);
      if (req.method === "GET" && url.pathname === "/") {
        const demo = `http://127.0.0.1:${server.address().port}/demo/index.html`;
        const body = htmlPage(demo);
        res.writeHead(200, { "content-type": "text/html; charset=utf-8", "content-length": Buffer.byteLength(body) });
        res.end(body);
        return;
      }
      if (req.method === "GET" && url.pathname.startsWith("/demo/")) {
        const target = path.join(FIXTURE_DIR, url.pathname.slice("/demo/".length));
        if (!target.startsWith(FIXTURE_DIR) || !fs.existsSync(target)) { res.writeHead(404); res.end(); return; }
        const body = fs.readFileSync(target);
        res.writeHead(200, { "content-type": "text/html; charset=utf-8", "content-length": body.length });
        res.end(body);
        return;
      }
      if (req.method === "GET" && url.pathname === "/api/state") {
        sendJson(res, { actions, browser_status: browser && browser.isConnected() ? "open" : "closed", current_url: page && !page.isClosed() ? page.url() : "", injection_status: injectionStatus, injection_message: injectionMessage });
        return;
      }
      if (req.method === "POST" && url.pathname === "/api/start-recording") { const body = await readBody(req); await launchBrowser({ url: body.url, headed: true }); const out = await startRecording(); sendJson(res, out); return; }
      if (req.method === "POST" && url.pathname === "/api/inject-recorder") { sendJson(res, await installRecorder(page)); return; }
      if (req.method === "POST" && url.pathname === "/api/stop-recording") { sendJson(res, await stopRecording()); return; }
      if (req.method === "POST" && url.pathname === "/api/run") { const body = await readBody(req); sendJson(res, await runSteps(body.fromIndex || 0)); return; }
      if (req.method === "POST" && url.pathname === "/api/stop-run") { running = false; sendJson(res, { status: "stopping" }); return; }
      if (req.method === "POST" && url.pathname === "/api/highlight") { const body = await readBody(req); sendJson(res, await highlightStep(body.index)); return; }
      if (req.method === "POST" && url.pathname === "/api/save") { sendJson(res, saveWorkflow()); return; }
      if (req.method === "POST" && url.pathname === "/api/clear") { actions = []; logs = []; sendJson(res, { status: "cleared" }); return; }
      res.writeHead(404); res.end();
    } catch (error) {
      sendJson(res, { status: "fail", message: String(error) }, 500);
    }
  });
  await new Promise((resolve) => server.listen(port, "127.0.0.1", resolve));
  return server;
}

async function runSmoke() {
  const server = await startStudioServer(0);
  const demoUrl = `http://127.0.0.1:${server.address().port}/demo/index.html`;
  try {
    await launchBrowser({ url: demoUrl, headed: true });
    await startRecording();
    if (injectionStatus !== "recording active") throw new Error("Recorder injection did not become recording active");
    await page.click("#pm15-message");
    await page.keyboard.type("Hello");
    await page.keyboard.type(" from PM15");
    await page.click("#pm15-secret");
    await page.keyboard.type("NeverStoreMe123!");
    await page.click("#pm15-submit");
    await stopRecording();
    const actionSnapshot = actions.map((action) => ({ ...action }));
    const typeActions = actionSnapshot.filter((action) => action.type === "Type" && action.selector === "#pm15-message");
    if (typeActions.length !== 1 || typeActions[0].text !== "Hello from PM15") throw new Error("Type action was not collapsed");
    const secretActions = actionSnapshot.filter((action) => action.type === "TypeSecret");
    if (!secretActions.length || JSON.stringify(actionSnapshot).includes("NeverStoreMe")) throw new Error("Password value was captured");
    const allRun = await runSteps(0);
    if (allRun.status !== "pass") throw new Error("Replay all failed: " + JSON.stringify(allRun));
    const fromIndex = actions.findIndex((action) => action.type === "Click" && action.selector === "#pm15-submit");
    const fromRun = await runSteps(fromIndex);
    if (fromRun.status !== "pass") throw new Error("Replay from selected step failed: " + JSON.stringify(fromRun));
    if (!browser || !browser.isConnected() || !page || page.isClosed()) throw new Error("Browser closed after replay");
    const highlight = await highlightStep(fromIndex);
    if (highlight.status !== "highlighted") throw new Error("Highlight failed: " + JSON.stringify(highlight));
    await startRecording();
    await page.click("#pm15-message");
    await page.keyboard.press(process.platform === "darwin" ? "Meta+A" : "Control+A");
    await page.keyboard.type("Hello again");
    await stopRecording();
    if (actions.length <= actionSnapshot.length) throw new Error("Continuation recording did not append steps");
    const saved = saveWorkflow();
    return { status: "pass", headed: true, browser_open: browser.isConnected(), workflow_json: saved.workflow_json, artifacts: saved.artifacts, actions, injection_status: injectionStatus };
  } finally {
    await closeBrowser();
    await new Promise((resolve) => server.close(resolve));
  }
}

async function main() {
  const command = process.argv[2] || "serve";
  if (command === "serve") {
    const portArg = process.argv.indexOf("--port");
    const port = portArg >= 0 ? Number(process.argv[portArg + 1]) : 8879;
    const server = await startStudioServer(port);
    console.log(`RPA Studio Playwright Recorder: http://127.0.0.1:${server.address().port}/`);
    return;
  }
  if (command === "run-smoke") {
    const result = await runSmoke();
    if (process.argv.includes("--json")) console.log(JSON.stringify(result, null, 2));
    else console.log("DEV_SMOKE_OK: production_milestone_15");
    return;
  }
  throw new Error(`Unknown command: ${command}`);
}

main().catch((error) => {
  console.error(String(error && error.stack ? error.stack : error));
  process.exit(1);
});
