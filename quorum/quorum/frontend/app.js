/* Quorum frontend controller
   - draws the seven-seat council semicircle
   - collects custom criteria weights from sliders
   - consumes the SSE deliberation stream
   - reveals turns, tool calls, and the final verdict + gauge */

const ROLES = [
  { id: "Moderator",    label: "Moderator",  init: "M", accent: "var(--moderator)" },
  { id: "Advocate",     label: "Advocate",   init: "A", accent: "var(--advocate)" },
  { id: "Skeptic",      label: "Skeptic",    init: "S", accent: "var(--skeptic)" },
  { id: "Researcher",   label: "Researcher", init: "R", accent: "var(--researcher)" },
  { id: "DomainAnalyst",label: "Analyst",    init: "D", accent: "var(--analyst)" },
  { id: "Ethicist",     label: "Ethicist",   init: "E", accent: "var(--ethicist)" },
  { id: "Synthesizer",  label: "Synthesizer",init:"\u03A3",accent:"var(--synth)" },
];
const roleById = Object.fromEntries(ROLES.map(r => [r.id, r]));

const SAMPLES = [
  "Should our team migrate the monolith to microservices this quarter?",
  "Should a bootstrapped startup take venture funding now, or stay lean?",
  "Should we adopt a four-day work week across the company?",
];

const GAUGE_CIRC = 2 * Math.PI * 58; // matches r=58 in CSS

/* ---------- build the semicircle of seats ---------- */
function layoutSeats() {
  const seats = document.getElementById("seats");
  const cx = 230, cy = 150, R = 132;
  // spread seven seats across a wide top arc (210deg .. -30deg)
  ROLES.forEach((role, i) => {
    const t = i / (ROLES.length - 1);
    const angle = (Math.PI) * (1.16 - 1.32 * t); // radians, left->right upper arc
    const x = cx + R * Math.cos(angle);
    const y = cy - R * Math.sin(angle) * 0.86;
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", "seat-node");
    g.setAttribute("id", "seat-" + role.id);
    g.setAttribute("transform", `translate(${x.toFixed(1)},${y.toFixed(1)})`);
    g.style.setProperty("--seat", role.accent);
    g.innerHTML = `
      <circle class="seat-pulse" r="24"></circle>
      <circle class="seat-ring" r="17"></circle>
      <text class="seat-init" y="0.5">${role.init}</text>
      <text class="seat-label" y="32">${role.label}</text>`;
    seats.appendChild(g);
  });
}

function setSeat(roleId, state) {
  const el = document.getElementById("seat-" + roleId);
  if (!el) return;
  if (state === "active") {
    document.querySelectorAll(".seat-node.active").forEach(n => n.classList.replace("active", "done"));
    el.classList.remove("done"); el.classList.add("active");
  } else if (state === "done") {
    el.classList.remove("active"); el.classList.add("done");
  }
}

/* ---------- transcript rendering ---------- */
const transcript = document.getElementById("transcript");
const emptyState = document.getElementById("emptyState");

function clearTranscript() { transcript.innerHTML = ""; }
function scrollDown() { transcript.scrollTop = transcript.scrollHeight; }

function addTurn(roleId, text) {
  const role = roleById[roleId] || { label: roleId, accent: "var(--muted)" };
  const div = document.createElement("div");
  div.className = "turn";
  div.style.setProperty("--accent", role.accent);
  div.innerHTML = `
    <div class="who"><span class="chip"></span><span class="name">${role.label.toUpperCase()}</span></div>
    <div class="body">${escapeHtml(text)}</div>`;
  transcript.appendChild(div);
  scrollDown();
}

function addToolChip(roleId, name, payload) {
  const summary = payload && payload.summary
    ? payload.summary
    : (name + " ran");
  const div = document.createElement("div");
  div.innerHTML = `<div class="tool-chip">\u2699 ${escapeHtml(name)} \u00b7 ${escapeHtml(summary)}</div>`;
  transcript.appendChild(div.firstElementChild);
  scrollDown();
}

function addStatus(text, isError) {
  const div = document.createElement("div");
  div.className = "status-line" + (isError ? " err" : "");
  div.textContent = text;
  transcript.appendChild(div);
  scrollDown();
}

/* ---------- verdict + gauge ---------- */
function renderVerdict(v) {
  const card = document.getElementById("verdictCard");
  card.hidden = false;
  document.getElementById("verdictWinner").textContent = v.winner || "\u2014";

  // gauge
  const conf = Math.max(0, Math.min(1, v.confidence ?? 0));
  const fill = document.getElementById("gaugeFill");
  fill.style.strokeDasharray = GAUGE_CIRC;
  requestAnimationFrame(() => {
    fill.style.strokeDashoffset = (GAUGE_CIRC * (1 - conf)).toFixed(1);
  });
  document.getElementById("gaugeValue").textContent = Math.round(conf * 100) + "%";
  document.getElementById("gaugeLabel").textContent = "confidence";

  // matrix ranking bars
  const matrix = document.getElementById("matrix");
  matrix.innerHTML = "";
  const top = v.ranking && v.ranking.length ? v.ranking[0].pct : 100;
  (v.ranking || []).forEach((r, i) => {
    const rel = top ? Math.round((r.pct / top) * 100) : 0;
    const row = document.createElement("div");
    row.className = "mrow" + (i === 0 ? " win" : "");
    row.innerHTML = `
      <div>
        <div class="opt"><span>${escapeHtml(r.option)}</span><span class="pct">${r.pct}%</span></div>
        <div class="bar"><span style="width:${rel}%"></span></div>
      </div>
      <div style="font-family:'JetBrains Mono';color:var(--muted)">${r.weighted_score}</div>`;
    matrix.appendChild(row);
  });

  // bias flags
  const flags = document.getElementById("flags");
  flags.innerHTML = "";
  (v.bias_flags || []).forEach(f => {
    const s = document.createElement("span");
    s.className = "flag";
    s.textContent = f.bias + " bias";
    s.title = f.note || "";
    flags.appendChild(s);
  });

  if (v.positions && v.positions.length) {
    const audit = document.createElement("div");
    audit.className = "audit";
    audit.innerHTML = "<div class=\"audit-title\">advisor ledger</div>";
    v.positions.forEach(p => {
      const item = document.createElement("div");
      item.className = "audit-item";
      item.innerHTML = `<span>${escapeHtml(p.role || "advisor")}</span><b>${escapeHtml(p.stance || "neutral")}</b>`;
      audit.appendChild(item);
    });
    flags.appendChild(audit);
  }
}

function resetChamber() {
  document.querySelectorAll(".seat-node").forEach(n => n.classList.remove("active", "done"));
  document.getElementById("verdictCard").hidden = true;
  const fill = document.getElementById("gaugeFill");
  fill.style.strokeDashoffset = GAUGE_CIRC;
  document.getElementById("gaugeValue").textContent = "--";
  document.getElementById("gaugeLabel").textContent = "awaiting verdict";
}

/* ---------- weights collection ---------- */
function collectWeights() {
  const sliders = document.querySelectorAll(".weight-slider");
  const weights = {};
  sliders.forEach(slider => {
    weights[slider.dataset.criterion] = parseInt(slider.value, 10);
  });
  return weights;
}

function setupWeightSliders() {
  const sliders = document.querySelectorAll(".weight-slider");
  sliders.forEach(slider => {
    slider.addEventListener("input", () => {
      const valSpan = document.querySelector(`.weight-val[data-for="${slider.dataset.criterion}"]`);
      if (valSpan) valSpan.textContent = slider.value;
    });
  });
}

/* ---------- stream consumption ---------- */
const composer = document.getElementById("composer");
const decisionInput = document.getElementById("decision");
const contextInput = document.getElementById("context");
const askBtn = document.getElementById("askBtn");

async function convene(decision, context = "") {
  clearTranscript();
  resetChamber();
  askBtn.disabled = true;
  addStatus("convening the council\u2026");

  const weights = collectWeights();

  try {
    const res = await fetch("/api/deliberate/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, context, weights }),
    });
    if (!res.ok || !res.body) throw new Error("stream unavailable (" + res.status + ")");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const chunks = buf.split("\n\n");
      buf = chunks.pop();               // keep incomplete tail
      for (const chunk of chunks) {
        const line = chunk.split("\n").find(l => l.startsWith("data:"));
        if (!line) continue;
        handleEvent(JSON.parse(line.slice(5).trim()));
      }
    }
  } catch (err) {
    addStatus("The council could not convene: " + err.message, true);
  } finally {
    askBtn.disabled = false;
  }
}

function handleEvent(evt) {
  switch (evt.kind) {
    case "status":
      if (evt.text === "finished") { addStatus("deliberation complete"); }
      else if (evt.text !== "started") { addStatus(evt.text); }
      break;
    case "turn":
      setSeat(evt.role, "active");
      addTurn(evt.role, evt.text || "");
      break;
    case "tool":
      addToolChip(evt.role, evt.text || "tool", evt.payload);
      break;
    case "verdict":
      setSeat("Synthesizer", "done");
      renderVerdict(evt.payload || {});
      break;
    case "error":
      addStatus(evt.text || "error", true);
      break;
  }
}

/* ---------- helpers & wiring ---------- */
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function autogrow() {
  [decisionInput, contextInput].forEach(input => {
    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 120) + "px";
  });
}

composer.addEventListener("submit", e => {
  e.preventDefault();
  const val = decisionInput.value.trim();
  if (val) convene(val, contextInput.value.trim());
});
decisionInput.addEventListener("input", autogrow);
contextInput.addEventListener("input", autogrow);
decisionInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); composer.requestSubmit(); }
});
contextInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); composer.requestSubmit(); }
});

async function loadHealth() {
  try {
    const h = await (await fetch("/api/health")).json();
    const pill = document.getElementById("modePill");
    pill.classList.add(h.mode);
    document.getElementById("modeText").textContent =
      h.mode === "live" ? `live \u00b7 ${h.llm_model}` : "demo mode";
  } catch { document.getElementById("modeText").textContent = "offline"; }
}

function mountSamples() {
  const box = document.getElementById("samples");
  SAMPLES.forEach(s => {
    const b = document.createElement("button");
    b.textContent = s;
    b.onclick = () => { decisionInput.value = s; contextInput.value = ""; autogrow(); convene(s); };
    box.appendChild(b);
  });
}

layoutSeats();
mountSamples();
loadHealth();
setupWeightSliders();
