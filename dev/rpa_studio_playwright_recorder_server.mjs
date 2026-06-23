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

function isBrowserErrorUrl(url = "") {
  return String(url).startsWith("chrome-error://");
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

function isBareGenericSelector(selector = "") {
  return ["input", "button", "div", "span"].includes(String(selector).trim().toLowerCase());
}

function appendAction(action) {
  if (!recording) return;
  const next = {
    ...action,
    order: actions.length + 1,
    timestamp_ms: nowMs(),
    source_url: page ? page.url() : action.source_url || "",
  };
  const previous = actions[actions.length - 1];
  if (next.type === "Navigate" && previous && previous.type === "Navigate" && previous.url === next.url) {
    previous.timestamp_ms = next.timestamp_ms;
    previous.source_url = next.source_url;
    previous.label = next.label || previous.label;
    if (next.caused_by_step) previous.caused_by_step = next.caused_by_step;
    log("coalesced duplicate Navigate", { url: next.url });
    return;
  }
  if (next.selector && !next.selector_quality) {
    next.selector_quality = isBareGenericSelector(next.selector) ? "ambiguous" : "usable";
  }
  if (["Click", "Type", "TypeSecret", "Wait for Selector"].includes(next.type) && next.selector && !next.wait_before) {
    next.wait_before = { type: "selector", selector: next.selector, state: "visible", timeout: 10 };
  }
  if (next.type === "Type" || next.type === "TypeSecret") {
    if (previous && previous.type === next.type && previous.selector === next.selector) {
      next.order = previous.order;
      actions[actions.length - 1] = next;
      log(`updated ${next.type}`, { selector: next.selector });
      return;
    }
  }
  actions.push(next);
  log(`captured ${next.type}`, { selector: next.selector || "", url: next.url || "" });
}

function reindexActions() {
  actions = actions.map((action, index) => ({ ...action, order: index + 1 }));
  return actions;
}

function selectedAction(index) {
  const numeric = Number(index);
  if (!Number.isInteger(numeric) || numeric < 0 || numeric >= actions.length) {
    throw new Error(`Selected step is out of range: ${index}`);
  }
  return { index: numeric, action: actions[numeric] };
}

function insertAt(index, position, action) {
  const offset = position === "before" ? 0 : 1;
  actions.splice(index + offset, 0, action);
  reindexActions();
}

function redactLabel(action) {
  const text = String(action.text || "");
  const label = String(action.label || "");
  if (text && label.toLowerCase().includes(text.toLowerCase())) return "secret field redacted";
  return label || "secret field redacted";
}

function editStep({ operation, index = 0, position = "after" } = {}) {
  const current = operation === "insert-wait-seconds" && actions.length === 0
    ? { index: 0, action: {} }
    : selectedAction(index);
  if (operation === "delete") {
    const removed = actions.splice(current.index, 1)[0];
    reindexActions();
    log("edited workflow: deleted step", { index: current.index, action: removed.type });
    return { status: "edited", operation, selected_index: Math.min(current.index, Math.max(actions.length - 1, 0)), actions };
  }
  if (operation === "insert-wait-selector") {
    if (!current.action.selector) throw new Error("Selected step has no selector for Wait for Selector.");
    const waitAction = {
      type: "Wait for Selector",
      selector: current.action.selector,
      selector_quality: current.action.selector_quality || "usable",
      selector_candidates: current.action.selector_candidates || [],
      timeout: 10,
      enabled: true,
      wait_before: { type: "selector", selector: current.action.selector, state: "visible", timeout: 10 },
      label: "Wait for selected element",
      timestamp_ms: nowMs(),
      source_url: page ? page.url() : current.action.source_url || "",
    };
    insertAt(current.index, position, waitAction);
    log("edited workflow: inserted Wait for Selector", { index: current.index, position, selector: waitAction.selector });
    return { status: "edited", operation, selected_index: position === "before" ? current.index : current.index + 1, actions };
  }
  if (operation === "insert-wait-seconds") {
    const waitAction = { type: "Wait Seconds", seconds: 1, enabled: true, label: "Wait 1 second", timestamp_ms: nowMs(), source_url: page ? page.url() : "" };
    if (actions.length === 0) {
      actions.push(waitAction);
      reindexActions();
      return { status: "edited", operation, selected_index: 0, actions };
    }
    insertAt(current.index, position, waitAction);
    log("edited workflow: inserted Wait Seconds", { index: current.index, position, seconds: waitAction.seconds });
    return { status: "edited", operation, selected_index: position === "before" ? current.index : current.index + 1, actions };
  }
  if (operation === "mark-secret") {
    if (current.action.type !== "Type" && current.action.type !== "TypeSecret") throw new Error("Only Type steps can be marked as secret.");
    actions[current.index] = {
      ...current.action,
      type: "TypeSecret",
      secret_ref: current.action.secret_ref || "secret://pm16-user-marked",
      redacted: true,
      label: redactLabel(current.action),
    };
    delete actions[current.index].text;
    reindexActions();
    log("edited workflow: marked Type step as secret", { index: current.index, selector: actions[current.index].selector });
    return { status: "edited", operation, selected_index: current.index, actions };
  }
  if (operation === "toggle-enabled") {
    actions[current.index] = { ...current.action, enabled: current.action.enabled === false };
    reindexActions();
    log("edited workflow: toggled step enabled", { index: current.index, enabled: actions[current.index].enabled !== false });
    return { status: "edited", operation, selected_index: current.index, actions };
  }
  if (operation === "move-up") {
    if (current.index > 0) {
      [actions[current.index - 1], actions[current.index]] = [actions[current.index], actions[current.index - 1]];
      reindexActions();
    }
    log("edited workflow: moved step up", { index: current.index });
    return { status: "edited", operation, selected_index: Math.max(current.index - 1, 0), actions };
  }
  if (operation === "move-down") {
    if (current.index < actions.length - 1) {
      [actions[current.index + 1], actions[current.index]] = [actions[current.index], actions[current.index + 1]];
      reindexActions();
    }
    log("edited workflow: moved step down", { index: current.index });
    return { status: "edited", operation, selected_index: Math.min(current.index + 1, actions.length - 1), actions };
  }
  throw new Error(`Unknown edit operation: ${operation}`);
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
  const GENERIC_SELECTORS = new Set(["input", "button", "div", "span"]);
  function cssEscape(value) {
    return window.CSS && CSS.escape ? CSS.escape(String(value)) : String(value).replace(/[^a-zA-Z0-9_-]/g, "\\\\$&");
  }
  function attrEscape(value) {
    return String(value).replace(/\\\\/g, "\\\\\\\\").replace(/'/g, "\\\\'");
  }
  function isClickableCandidate(el) {
    if (!el || !el.tagName) return false;
    const tag = el.tagName.toLowerCase();
    const role = (el.getAttribute("role") || "").toLowerCase();
    const type = (el.getAttribute("type") || "").toLowerCase();
    return tag === "a"
      || tag === "button"
      || role === "button"
      || role === "link"
      || role === "menuitem"
      || role === "tab"
      || (tag === "input" && ["button", "submit", "reset", "checkbox", "radio"].includes(type));
  }
  function addCandidate(candidates, selector, quality, reason) {
    if (!selector || candidates.some((candidate) => candidate.selector === selector)) return;
    let count = 0;
    try { count = document.querySelectorAll(selector).length; } catch (_error) { return; }
    candidates.push({ selector, quality: count === 1 ? quality : "ambiguous", count, reason });
  }
  function nthPath(el) {
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1 && node !== document.documentElement) {
      const tag = node.tagName.toLowerCase();
      if (node.id) {
        parts.unshift("#" + cssEscape(node.id));
        break;
      }
      const siblings = Array.from(node.parentElement ? node.parentElement.children : []).filter((sibling) => sibling.tagName === node.tagName);
      const index = siblings.indexOf(node) + 1;
      parts.unshift(tag + ":nth-of-type(" + index + ")");
      node = node.parentElement;
      if (node === document.body) {
        parts.unshift("body");
        break;
      }
    }
    return parts.join(" > ");
  }
  function selectorForElement(el) {
    if (!el || !el.tagName) return { selector: "", selector_quality: "ambiguous", selector_candidates: [] };
    const tag = el.tagName.toLowerCase();
    const type = (el.getAttribute("type") || "").toLowerCase();
    const candidates = [];
    if (el.id) addCandidate(candidates, "#" + cssEscape(el.id), "strong", "id");
    if (el.getAttribute("data-testid")) addCandidate(candidates, "[data-testid='" + attrEscape(el.getAttribute("data-testid")) + "']", "strong", "data-testid");
    if (el.getAttribute("name")) addCandidate(candidates, tag + "[name='" + attrEscape(el.getAttribute("name")) + "']", "strong", "name");
    if (el.getAttribute("aria-label")) addCandidate(candidates, tag + "[aria-label='" + attrEscape(el.getAttribute("aria-label")) + "']", "usable", "aria-label");
    if (el.getAttribute("placeholder")) addCandidate(candidates, tag + "[placeholder='" + attrEscape(el.getAttribute("placeholder")) + "']", "usable", "placeholder");
    if (type && ["button", "submit", "reset"].includes(type) && el.getAttribute("value")) {
      addCandidate(candidates, tag + "[type='" + attrEscape(type) + "'][value='" + attrEscape(el.getAttribute("value")) + "']", "usable", "button-value");
    }
    if (type) addCandidate(candidates, tag + "[type='" + attrEscape(type) + "']", "usable", "type");
    addCandidate(candidates, nthPath(el), "fragile", "nth-of-type");
    let chosen = candidates.find((candidate) => candidate.count === 1 && candidate.quality === "strong")
      || candidates.find((candidate) => candidate.count === 1 && candidate.quality === "usable")
      || candidates.find((candidate) => candidate.count === 1)
      || candidates[0]
      || { selector: tag, quality: "ambiguous", count: 0, reason: "fallback" };
    let selector_quality = chosen.count === 1 ? chosen.quality : "ambiguous";
    if (GENERIC_SELECTORS.has(chosen.selector)) selector_quality = "ambiguous";
    return {
      selector: chosen.selector,
      selector_quality,
      selector_candidates: candidates.slice(0, 8),
    };
  }
  function selectorFor(el, options = {}) {
    if (!options.preferClickableAncestor) return selectorForElement(el);
    let node = el;
    while (node && node !== document.documentElement) {
      if (isClickableCandidate(node)) {
        const candidate = selectorForElement(node);
        if (candidate.selector_quality === "strong" || candidate.selector_quality === "usable") return candidate;
      }
      node = node.parentElement;
    }
    return selectorForElement(el);
  }
  function labelFor(el) {
    return ((el && (el.getAttribute("aria-label") || el.getAttribute("placeholder") || el.innerText || el.value)) || "").toString().slice(0, 80);
  }
  document.addEventListener("click", (event) => {
    const el = event.target;
    if (!el || el.type === "hidden" || el.type === "password") return;
    window.__rpaPwRecord({ type: "Click", ...selectorFor(el, { preferClickableAncestor: true }), label: labelFor(el) });
  }, true);
  document.addEventListener("input", (event) => {
    const el = event.target;
    if (!el || el.type === "hidden") return;
    if (el.type === "password") {
      window.__rpaPwRecord({ type: "TypeSecret", ...selectorFor(el), secret_ref: "secret://pm15-redacted", redacted: true, label: "password field redacted" });
      return;
    }
    window.__rpaPwRecord({ type: "Type", ...selectorFor(el), text: String(el.value || ""), label: labelFor(el), redacted: false });
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

async function reattachRecorder() {
  log("reattach requested");
  if (!browser || !browser.isConnected() || !page || page.isClosed()) {
    const message = "No active browser page. Start Recording or open a browser first.";
    setInjectionStatus("not injected", message);
    log("injection failed", { reason: message });
    return {
      status: "fail",
      message,
      injection_status: injectionStatus,
      injection_message: injectionMessage,
      action_count: actions.length,
    };
  }
  try {
    const injection = await installRecorder(page);
    log("recorder injected", { injection_status: injection.injection_status, current_url: page.url() });
    return {
      status: injection.injection_status === "recording active" ? "recording active" : "injected",
      message: injection.injection_message,
      current_url: page.url(),
      injection_status: injection.injection_status,
      injection_message: injection.injection_message,
      action_count: actions.length,
      recording,
    };
  } catch (error) {
    const message = `Recorder injection failed: ${String(error)}`;
    log("injection failed", { reason: message });
    return {
      status: "fail",
      message,
      current_url: page && !page.isClosed() ? page.url() : "",
      injection_status: injectionStatus,
      injection_message: injectionMessage,
      action_count: actions.length,
      recording,
    };
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
      const currentUrl = page.url();
      if (frame === page.mainFrame()) {
        if (isBrowserErrorUrl(currentUrl)) {
          recording = false;
          setInjectionStatus("injection failed", "Browser loaded an error page; navigation or recorder injection is unavailable for this URL.");
          return;
        }
        setInjectionStatus("page changed, reinjection needed", "Page changed; recorder must be reinjected for this page.");
      }
      if (frame === page.mainFrame() && recording) {
        appendAction({ type: "Navigate", url: currentUrl, label: "Navigate" });
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

async function locatorForAction(action) {
  if (!action.selector) throw new Error(`Step has no selector: ${action.type}`);
  if (action.selector_quality === "ambiguous" || isBareGenericSelector(action.selector)) {
    throw new Error(`Selector is ambiguous; refine selector before replay. Selector: ${action.selector}`);
  }
  const locator = page.locator(action.selector);
  const count = await locator.count();
  if (count > 1) throw new Error(`Selector is ambiguous; refine selector before replay. Selector: ${action.selector} matched ${count} elements.`);
  if (count < 1) throw new Error(`Selector not found before replay. Selector: ${action.selector}`);
  return locator;
}

async function waitBeforeAction(action) {
  if (!["Click", "Type", "TypeSecret", "Wait for Selector"].includes(action.type) || !action.selector) return { waited: false };
  const waitBefore = action.wait_before && action.wait_before.type === "selector"
    ? action.wait_before
    : { type: "selector", selector: action.selector, state: "visible", timeout: 10 };
  const selector = waitBefore.selector || action.selector;
  const timeoutMs = (Number(waitBefore.timeout) || 10) * 1000;
  const locator = page.locator(selector);
  await locator.waitFor({ state: waitBefore.state || "visible", timeout: timeoutMs });
  if (action.type === "Type" || action.type === "TypeSecret") {
    const editableCount = await locator.count();
    if (editableCount === 1) await locator.waitFor({ state: "visible", timeout: timeoutMs });
  }
  return { waited: true, selector, state: waitBefore.state || "visible", timeout: Number(waitBefore.timeout) || 10 };
}

async function runSteps(fromIndex = 0) {
  if (!page || page.isClosed()) throw new Error("No controlled browser page is open.");
  running = true;
  const runLog = [];
  for (let i = Number(fromIndex) || 0; i < actions.length; i += 1) {
    const action = actions[i];
    try {
      if (!running) throw new Error("Run stopped");
      if (action.enabled === false) {
        runLog.push({ step_index: i, status: "skipped", action: action.type, selector: action.selector || "", message: "Step disabled in edited workflow." });
        continue;
      }
      if (action.type === "Navigate") await page.goto(action.url);
      const waitInfo = await waitBeforeAction(action);
      if (action.type === "Click") await (await locatorForAction(action)).click({ timeout: 4000 });
      if (action.type === "Type") await (await locatorForAction(action)).fill(action.text || "", { timeout: 4000 });
      if (action.type === "TypeSecret") {
        const message = "Secret value unavailable; no credential vault configured.";
        log("skipped redacted secret replay", { selector: action.selector, message });
        runLog.push({ step_index: i, status: "skipped", action: action.type, selector: action.selector || "", message });
        continue;
      }
      if (action.type === "Wait for Selector") await (await locatorForAction(action)).waitFor({ timeout: (Number(action.timeout) || 10) * 1000 });
      if (action.type === "Wait Seconds") await page.waitForTimeout((Number(action.seconds) || 1) * 1000);
      runLog.push({ step_index: i, status: "ok", action: action.type, selector: action.selector || "", url: action.url || "", wait_before: waitInfo.waited ? waitInfo : undefined });
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
  if (found > 1 || action.selector_quality === "ambiguous" || isBareGenericSelector(action.selector)) {
    return { status: "ambiguous", message: "Selector is ambiguous; refine selector before replay.", selector: action.selector, matches: found };
  }
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
  <title>RPA Studio Playwright Recorder — PM15</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; background: #eef2f6; color: #182534; }
    header { background: #123b5d; color: #fff; padding: 18px 22px; }
    main { display: grid; grid-template-columns: 380px minmax(520px, 1fr); gap: 14px; padding: 14px; }
    section { background: #fff; border: 1px solid #d6dee8; border-radius: 8px; padding: 14px; }
    button { border: 0; border-radius: 6px; background: #1769aa; color: white; cursor: pointer; font-weight: 700; margin: 5px 4px 5px 0; padding: 8px 10px; }
    button.secondary { background: #586677; }
    button.danger { background: #9b2d30; }
    .badge { display: inline-block; background: #dbeafe; border: 1px solid #93c5fd; border-radius: 999px; color: #123b5d; font-weight: 700; margin-bottom: 8px; padding: 5px 10px; }
    .mode-details { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }
    .mode-details span { background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.32); border-radius: 6px; padding: 5px 8px; }
    input { box-sizing: border-box; border: 1px solid #aab6c5; border-radius: 6px; padding: 8px; width: 100%; }
    textarea, pre { box-sizing: border-box; width: 100%; min-height: 220px; overflow: auto; white-space: pre-wrap; background: #f8fafc; border: 1px solid #d6dee8; border-radius: 6px; padding: 10px; }
    .notice { background: #fff7d6; border: 1px solid #dec35f; border-radius: 6px; padding: 9px; }
    .actions { padding-left: 20px; }
    .actions li { margin-bottom: 8px; cursor: pointer; }
    .actions li.selector-warning { color: #9b5c00; }
    .actions li.disabled-step { color: #667085; text-decoration: line-through; }
    .selected { background: #dbeafe; }
    .editor-panel { background: #eef6ff; border: 1px solid #9cc9f5; border-radius: 8px; margin-top: 12px; padding: 10px; }
    .editor-panel h3 { margin: 0 0 6px; }
  </style>
</head>
<body>
  <header>
    <div class="badge">PM15 · Playwright Controlled Browser Recorder</div>
    <h1>RPA Studio Playwright Recorder — PM15</h1>
    <p>Experimental controlled browser recorder. Not production-ready.</p>
    <div class="badge">PM16 &middot; Recorder Step Editing MVP</div>
    <h2>RPA Studio Step Editor &mdash; PM16</h2>
    <div class="mode-details">
      <span>Recorder mode: Playwright controlled browser</span>
      <span>Replay mode: Playwright recorder replay</span>
      <span>Status: experimental / not production-ready</span>
    </div>
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
      <div class="editor-panel">
        <h3>Step Editing</h3>
        <p>Replay automatically waits for each action's target element before interacting. Use explicit waits for unusual pacing or custom readiness.</p>
        <p>Selected step: <span id="selected-step">0</span></p>
        <button id="delete-step" class="danger">Delete Step</button>
        <button id="wait-selector-before" class="secondary">Add Explicit Wait for Selected Element before</button>
        <button id="wait-selector-after" class="secondary">Add Explicit Wait for Selected Element after</button>
        <button id="wait-seconds-before" class="secondary">Add Wait Seconds before</button>
        <button id="wait-seconds-after" class="secondary">Add Wait Seconds after</button>
        <button id="mark-secret" class="secondary">Mark Type as Secret / Password</button>
        <button id="toggle-enabled" class="secondary">Enable / Disable Step</button>
        <button id="move-up" class="secondary">Move Up</button>
        <button id="move-down" class="secondary">Move Down</button>
      </div>
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
    const selectedStepEl = document.getElementById('selected-step');
    function log(line) { logEl.textContent += '\\n' + new Date().toISOString() + ' ' + line; logEl.scrollTop = logEl.scrollHeight; }
    function render() {
      if (selected >= actions.length) selected = Math.max(actions.length - 1, 0);
      selectedStepEl.textContent = String(selected);
      actionsEl.innerHTML = '';
      actions.forEach((action, index) => {
        const li = document.createElement('li');
        const quality = action.selector_quality ? ' [' + action.selector_quality + ']' : '';
        const warning = action.selector_quality === 'ambiguous' || action.selector_quality === 'fragile';
        const disabled = action.enabled === false;
        li.className = (index === selected ? 'selected ' : '') + (warning ? 'selector-warning ' : '') + (disabled ? 'disabled-step' : '');
        li.textContent = index + ': ' + action.type + ' ' + (action.selector || action.url || '') + quality + (disabled ? ' [disabled]' : '') + (action.text ? ' = ' + action.text : action.secret_ref ? ' = [secret_ref]' : action.seconds ? ' = ' + action.seconds + 's' : '');
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
    async function editStep(operation, position) {
      const res = await fetch('/api/edit-step', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ operation, index: selected, position }) });
      const data = await res.json();
      if (typeof data.selected_index === 'number') selected = data.selected_index;
      evidenceEl.textContent = JSON.stringify(data, null, 2);
      log('edit ' + operation + (position ? ' ' + position : '') + ': ' + data.status);
      await refresh();
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
    document.getElementById('inject').addEventListener('click', async () => {
      log('reattach requested');
      const res = await fetch('/api/inject-recorder', { method: 'POST' });
      const data = await res.json();
      if (data.status === 'fail') log('injection failed: ' + (data.message || data.injection_message || 'unknown error'));
      else log('recorder injected: ' + (data.injection_status || data.status));
      evidenceEl.textContent = JSON.stringify(data, null, 2);
      await refresh();
    });
    document.getElementById('run-all').addEventListener('click', async () => { const data = await (await fetch('/api/run', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ fromIndex: 0 }) })).json(); evidenceEl.textContent = JSON.stringify(data, null, 2); log('run all: ' + data.status); await refresh(); });
    document.getElementById('run-from').addEventListener('click', async () => { const data = await (await fetch('/api/run', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ fromIndex: selected }) })).json(); evidenceEl.textContent = JSON.stringify(data, null, 2); log('run from: ' + data.status); await refresh(); });
    document.getElementById('stop-run').addEventListener('click', async () => { const data = await (await fetch('/api/stop-run', { method: 'POST' })).json(); log('stop run: ' + JSON.stringify(data)); });
    document.getElementById('save').addEventListener('click', async () => { const data = await (await fetch('/api/save', { method: 'POST' })).json(); evidenceEl.textContent = JSON.stringify(data, null, 2); log('save: ' + data.workflow_json); });
    document.getElementById('clear').addEventListener('click', async () => { const data = await (await fetch('/api/clear', { method: 'POST' })).json(); log('clear: ' + JSON.stringify(data)); await refresh(); });
    document.getElementById('delete-step').addEventListener('click', () => editStep('delete'));
    document.getElementById('wait-selector-before').addEventListener('click', () => editStep('insert-wait-selector', 'before'));
    document.getElementById('wait-selector-after').addEventListener('click', () => editStep('insert-wait-selector', 'after'));
    document.getElementById('wait-seconds-before').addEventListener('click', () => editStep('insert-wait-seconds', 'before'));
    document.getElementById('wait-seconds-after').addEventListener('click', () => editStep('insert-wait-seconds', 'after'));
    document.getElementById('mark-secret').addEventListener('click', () => editStep('mark-secret'));
    document.getElementById('toggle-enabled').addEventListener('click', () => editStep('toggle-enabled'));
    document.getElementById('move-up').addEventListener('click', () => editStep('move-up'));
    document.getElementById('move-down').addEventListener('click', () => editStep('move-down'));
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
      if (req.method === "POST" && url.pathname === "/api/inject-recorder") { sendJson(res, await reattachRecorder()); return; }
      if (req.method === "POST" && url.pathname === "/api/stop-recording") { sendJson(res, await stopRecording()); return; }
      if (req.method === "POST" && url.pathname === "/api/run") { const body = await readBody(req); sendJson(res, await runSteps(body.fromIndex || 0)); return; }
      if (req.method === "POST" && url.pathname === "/api/stop-run") { running = false; sendJson(res, { status: "stopping" }); return; }
      if (req.method === "POST" && url.pathname === "/api/highlight") { const body = await readBody(req); sendJson(res, await highlightStep(body.index)); return; }
      if (req.method === "POST" && url.pathname === "/api/edit-step") { const body = await readBody(req); sendJson(res, editStep(body)); return; }
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
    await page.click("#anch_49 h3");
    await stopRecording();
    const actionSnapshot = actions.map((action) => ({ ...action }));
    const genericSelector = actionSnapshot.find((action) => ["input", "button", "div", "span"].includes(String(action.selector || "").toLowerCase()));
    if (genericSelector) throw new Error("Recorder emitted a bare generic selector: " + JSON.stringify(genericSelector));
    const messageClickActions = actionSnapshot.filter((action) => action.type === "Click" && action.selector === "#pm15-message");
    if (messageClickActions.length !== 1) throw new Error("Message input click did not use stable selector: " + JSON.stringify(actionSnapshot));
    if (messageClickActions[0].selector_quality !== "strong") throw new Error("Message input click selector was not strong: " + JSON.stringify(messageClickActions[0]));
    const typeActions = actionSnapshot.filter((action) => action.type === "Type" && action.selector === "#pm15-message");
    if (typeActions.length !== 1 || typeActions[0].text !== "Hello from PM15") throw new Error("Type action was not collapsed");
    if (typeActions[0].selector_quality !== "strong") throw new Error("Type selector was not strong: " + JSON.stringify(typeActions[0]));
    if (!Array.isArray(typeActions[0].selector_candidates) || !typeActions[0].selector_candidates.length) throw new Error("Type selector candidates were not captured");
    const secretActions = actionSnapshot.filter((action) => action.type === "TypeSecret");
    if (!secretActions.length || JSON.stringify(actionSnapshot).includes("NeverStoreMe")) throw new Error("Password value was captured");
    const anchorClick = actionSnapshot.find((action) => action.type === "Click" && action.selector === "#anch_49");
    if (!anchorClick || anchorClick.selector_quality !== "strong" || anchorClick.label !== "Device Characteristics") throw new Error("Clickable ancestor selector was not preferred: " + JSON.stringify(actionSnapshot));
    if (JSON.stringify(actionSnapshot).includes("#anch_49 > h3:nth-of-type")) throw new Error("Fragile child selector was recorded for clickable ancestor");
    const adjacentDuplicateNavigate = actionSnapshot.some((action, index) => index > 0 && action.type === "Navigate" && actionSnapshot[index - 1].type === "Navigate" && action.url === actionSnapshot[index - 1].url);
    if (adjacentDuplicateNavigate) throw new Error("Adjacent duplicate Navigate actions were not deduped: " + JSON.stringify(actionSnapshot));
    const allRun = await runSteps(0);
    if (allRun.status !== "pass") throw new Error("Replay all failed: " + JSON.stringify(allRun));
    if (!allRun.run_log.some((entry) => entry.action === "Click" && entry.selector === "#pm15-submit" && entry.wait_before && entry.wait_before.selector === "#pm15-submit")) throw new Error("Default readiness wait was not logged before click replay: " + JSON.stringify(allRun));
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

async function runPm16Smoke() {
  const server = await startStudioServer(0);
  const demoUrl = `http://127.0.0.1:${server.address().port}/demo/index.html`;
  const rawSecretText = "PM16 text that must be removed";
  try {
    const noPageReattach = await reattachRecorder();
    if (noPageReattach.status !== "fail" || !String(noPageReattach.message || "").includes("No active browser page")) {
      throw new Error("Reattach without an active page did not report a clear failure: " + JSON.stringify(noPageReattach));
    }
    await launchBrowser({ url: demoUrl, headed: true });
    await startRecording();
    await page.click("#pm15-message");
    await page.keyboard.type(rawSecretText);
    await page.click("#pm15-reference");
    await page.click("#anch_49 h3");
    await page.click("#pm15-submit");
    await stopRecording();
    const actionCountBeforeReattach = actions.length;
    const idleReattach = await reattachRecorder();
    if (idleReattach.status !== "injected" || idleReattach.injection_status !== "injected") {
      throw new Error("Idle reattach did not inject recorder: " + JSON.stringify(idleReattach));
    }
    if (actions.length !== actionCountBeforeReattach) throw new Error("Idle reattach changed recorded actions");
    await page.reload({ waitUntil: "domcontentloaded" });
    const afterReloadReattach = await reattachRecorder();
    if (afterReloadReattach.status !== "injected" || afterReloadReattach.injection_status !== "injected") {
      throw new Error("Reattach after navigation did not inject recorder: " + JSON.stringify(afterReloadReattach));
    }
    if (actions.length !== actionCountBeforeReattach) throw new Error("Reattach after navigation changed recorded actions");
    if (!logs.some((entry) => entry.message === "reattach requested")) throw new Error("Reattach request was not logged");
    if (!logs.some((entry) => entry.message === "recorder injected")) throw new Error("Recorder injection success was not logged");
    if (!logs.some((entry) => entry.message === "injection failed" && String(entry.reason || "").includes("No active browser page"))) {
      throw new Error("No-page reattach failure was not logged clearly");
    }

    if (!actions.some((action) => action.type === "Type" && action.selector === "#pm15-message")) throw new Error("Sample Type action was not recorded");
    if (!actions.some((action) => action.type === "Click" && action.selector === "#pm15-submit")) throw new Error("Sample Click action was not recorded");
    const anchorClick = actions.find((action) => action.type === "Click" && action.selector === "#anch_49");
    if (!anchorClick || anchorClick.selector_quality !== "strong") throw new Error("Clickable ancestor selector was not recorded for PM16 smoke: " + JSON.stringify(actions));
    if (JSON.stringify(actions).includes("#anch_49 > h3:nth-of-type")) throw new Error("Fragile child selector was recorded in PM16 smoke");
    appendAction({ type: "Navigate", url: page.url(), label: "Duplicate navigation test" });
    const adjacentDuplicateNavigate = actions.some((action, index) => index > 0 && action.type === "Navigate" && actions[index - 1].type === "Navigate" && action.url === actions[index - 1].url);
    if (adjacentDuplicateNavigate) throw new Error("Adjacent duplicate Navigate actions were not deduped in PM16 smoke");

    const referenceIndex = actions.findIndex((action) => action.type === "Click" && action.selector === "#pm15-reference");
    editStep({ operation: "delete", index: referenceIndex });
    if (actions.some((action) => action.selector === "#pm15-reference")) throw new Error("Delete step did not remove reference input action");

    const typeIndex = actions.findIndex((action) => action.type === "Type" && action.selector === "#pm15-message");
    editStep({ operation: "insert-wait-selector", index: typeIndex, position: "before" });
    const waitSelectorIndex = actions.findIndex((action) => action.type === "Wait for Selector" && action.selector === "#pm15-message");
    if (waitSelectorIndex < 0 || actions[waitSelectorIndex].timeout !== 10 || actions[waitSelectorIndex].enabled !== true) throw new Error("Wait for Selector insert failed");

    editStep({ operation: "insert-wait-seconds", index: waitSelectorIndex, position: "after" });
    const waitSecondsIndex = actions.findIndex((action) => action.type === "Wait Seconds");
    if (waitSecondsIndex < 0 || actions[waitSecondsIndex].seconds !== 1 || actions[waitSecondsIndex].enabled !== true) throw new Error("Wait Seconds insert failed");

    const beforeMoveOrder = actions.map((action) => action.type).join("|");
    editStep({ operation: "move-down", index: waitSecondsIndex });
    const afterMoveOrder = actions.map((action) => action.type).join("|");
    if (beforeMoveOrder === afterMoveOrder) throw new Error("Move Down did not change execution order");

    const clickIndex = actions.findIndex((action) => action.type === "Click" && action.selector === "#pm15-message");
    editStep({ operation: "toggle-enabled", index: clickIndex });
    if (actions[clickIndex].enabled !== false) throw new Error("Toggle enabled did not disable selected step");

    const typeIndexAfterMove = actions.findIndex((action) => action.type === "Type" && action.selector === "#pm15-message");
    editStep({ operation: "mark-secret", index: typeIndexAfterMove });
    const secretAction = actions.find((action) => action.type === "TypeSecret" && action.selector === "#pm15-message");
    if (!secretAction || !secretAction.secret_ref || JSON.stringify(secretAction).includes(rawSecretText)) throw new Error("Mark secret did not redact raw text");

    const runResult = await runSteps(0);
    if (runResult.status !== "pass") throw new Error("Edited workflow replay failed: " + JSON.stringify(runResult));
    if (!runResult.run_log.some((entry) => entry.action === "Click" && entry.wait_before && entry.wait_before.selector)) throw new Error("Default readiness wait was not applied before replay interaction");
    if (!runResult.run_log.some((entry) => entry.status === "skipped" && entry.message === "Step disabled in edited workflow.")) throw new Error("Disabled step was not skipped in run log");
    if (!runResult.run_log.some((entry) => entry.action === "TypeSecret" && entry.status === "skipped")) throw new Error("Secret step did not produce clear skipped replay log");

    const highlight = await highlightStep(waitSelectorIndex);
    if (highlight.status !== "highlighted") throw new Error("Highlight after editing failed: " + JSON.stringify(highlight));

    const saved = saveWorkflow();
    const savedWorkflow = JSON.parse(fs.readFileSync(saved.workflow_json, "utf8"));
    const serialized = JSON.stringify(savedWorkflow);
    if (serialized.includes(rawSecretText)) throw new Error("Saved edited workflow leaked raw secret text");
    if (!savedWorkflow.actions.some((action) => action.enabled === false)) throw new Error("Saved workflow did not retain disabled step");
    if (!savedWorkflow.actions.some((action) => action.type === "Wait for Selector")) throw new Error("Saved workflow missing Wait for Selector");
    if (!savedWorkflow.actions.some((action) => action.type === "Wait Seconds")) throw new Error("Saved workflow missing Wait Seconds");

    return { status: "pass", headed: true, workflow_json: saved.workflow_json, artifacts: saved.artifacts, actions: savedWorkflow.actions, run_log: runResult.run_log, highlight };
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
  if (command === "run-pm16-smoke") {
    const result = await runPm16Smoke();
    if (process.argv.includes("--json")) console.log(JSON.stringify(result, null, 2));
    else console.log("DEV_SMOKE_OK: production_milestone_16");
    return;
  }
  throw new Error(`Unknown command: ${command}`);
}

main().catch((error) => {
  console.error(String(error && error.stack ? error.stack : error));
  process.exit(1);
});
