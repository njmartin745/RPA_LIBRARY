(function () {
  const state = {
    recording: false,
    sequence: 0
  };

  function selectorFor(el) {
    if (!el || el.nodeType !== 1) return "";
    if (el.id) return "#" + CSS.escape(el.id);
    const name = el.getAttribute("name");
    if (name) return el.tagName.toLowerCase() + "[name=\"" + CSS.escape(name) + "\"]";
    const testId = el.getAttribute("data-testid");
    if (testId) return "[data-testid=\"" + CSS.escape(testId) + "\"]";
    const aria = el.getAttribute("aria-label");
    if (aria) return "[aria-label=\"" + CSS.escape(aria) + "\"]";
    return el.tagName.toLowerCase();
  }

  function labelFor(el) {
    const direct = (el.getAttribute("aria-label") || el.getAttribute("data-testid") || el.id || "").trim();
    if (direct) return direct;
    return (el.textContent || el.value || el.tagName || "").trim().slice(0, 80);
  }

  function post(action) {
    window.parent.postMessage({ source: "rpa-studio-recorder", action }, "*");
  }

  function baseAction(type, el) {
    state.sequence += 1;
    return {
      type,
      selector: selectorFor(el),
      label: labelFor(el),
      order: state.sequence,
      timestamp_ms: Date.now()
    };
  }

  document.addEventListener("click", function (event) {
    if (!state.recording) return;
    const el = event.target;
    if (!el || el.closest("[data-recorder-ignore='true']")) return;
    post(baseAction("Click", el));
  }, true);

  document.addEventListener("input", function (event) {
    if (!state.recording) return;
    const el = event.target;
    if (!el || !/^(input|textarea)$/i.test(el.tagName)) return;
    const action = baseAction("Type", el);
    const inputType = String(el.getAttribute("type") || "text").toLowerCase();
    if (inputType === "password") {
      action.text = null;
      action.redacted = true;
      action.note = "Password input value was not captured.";
    } else {
      action.text = String(el.value || "");
      action.redacted = false;
    }
    post(action);
  }, true);

  window.addEventListener("message", function (event) {
    const data = event.data || {};
    if (data.source !== "rpa-studio-parent") return;
    if (data.command === "start-recording") {
      state.recording = true;
      state.sequence = 0;
      document.body.setAttribute("data-recording", "true");
      post({ type: "Recorder", event: "started", order: 0, timestamp_ms: Date.now() });
    }
    if (data.command === "stop-recording") {
      state.recording = false;
      document.body.removeAttribute("data-recording");
      post({ type: "Recorder", event: "stopped", order: state.sequence + 1, timestamp_ms: Date.now() });
    }
  });
}());
