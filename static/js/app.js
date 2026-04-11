/**
 * app.js — ReplyIQ frontend
 * Handles real-time typing analysis, score rendering,
 * error highlighting, copy/apply, dark-mode toggle.
 */

"use strict";

// ── DOM refs ────────────────────────────────────────────────────────────────
const agentInput     = document.getElementById("agentInput");
const wordCount      = document.getElementById("wordCount");
const typingStatus   = document.getElementById("typingStatus");
const highlightOver  = document.getElementById("highlightOverlay");

const scoreCard      = document.getElementById("scoreCard");
const ringFill       = document.getElementById("ringFill");
const scoreNum       = document.getElementById("scoreNum");
const scoreLabel     = document.getElementById("scoreLabel");

const grammarBar     = document.getElementById("grammarBar");
const empathyBar     = document.getElementById("empathyBar");
const lengthBar      = document.getElementById("lengthBar");
const toneBar        = document.getElementById("toneBar");
const grammarPts     = document.getElementById("grammarPts");
const empathyPts     = document.getElementById("empathyPts");
const lengthPts      = document.getElementById("lengthPts");
const tonePts        = document.getElementById("tonePts");

const tagTone        = document.getElementById("tagTone");
const tagEmpathy     = document.getElementById("tagEmpathy");
const tagErrors      = document.getElementById("tagErrors");

const improvedText   = document.getElementById("improvedText");
const errorsList     = document.getElementById("errorsList");
const errorsCount    = document.getElementById("errorsCount");
const empathyCard    = document.getElementById("empathyCard");
const empathyText    = document.getElementById("empathyText");

const copyBtn        = document.getElementById("copyBtn");
const applyBtn       = document.getElementById("applyBtn");
const analyseBtn     = document.getElementById("analyseBtn");
const clearBtn       = document.getElementById("clearBtn");
const darkToggle     = document.getElementById("darkToggle");
const toast          = document.getElementById("toast");

// ── Ring circumference (r=52 → 2πr ≈ 326.7) ────────────────────────────────
const RING_CIRC = 326.7;

// ── State ────────────────────────────────────────────────────────────────────
let debounceTimer  = null;
let lastImproved   = "";
let isAnalysing    = false;

// ── Utility: debounce ────────────────────────────────────────────────────────
function debounce(fn, delay) {
  return function (...args) {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// ── Utility: show toast ──────────────────────────────────────────────────────
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2400);
}

// ── Word count update ────────────────────────────────────────────────────────
function updateWordCount(text) {
  const count = text.trim() ? text.trim().split(/\s+/).length : 0;
  wordCount.textContent = `${count} word${count !== 1 ? "s" : ""}`;
}

// ── Score ring update ────────────────────────────────────────────────────────
function setScore(score) {
  const s = parseFloat(score) || 0;
  const offset = RING_CIRC - (s / 10) * RING_CIRC;
  ringFill.style.strokeDashoffset = offset;
  scoreNum.textContent = s.toFixed(1);

  // Colour class
  scoreCard.classList.remove("score-good", "score-warn", "score-bad");
  if (s >= 7.5)      scoreCard.classList.add("score-good");
  else if (s >= 5)   scoreCard.classList.add("score-warn");
  else               scoreCard.classList.add("score-bad");
}

// ── Sub-score bars ───────────────────────────────────────────────────────────
function setBreakdown(bd) {
  if (!bd) return;
  const maxes = { grammar: 4, empathy: 3, length: 2, tone: 1 };
  const els   = { grammar: [grammarBar, grammarPts],
                  empathy: [empathyBar, empathyPts],
                  length:  [lengthBar,  lengthPts],
                  tone:    [toneBar,    tonePts] };

  for (const [key, [bar, pts]] of Object.entries(els)) {
    const val = bd[key] ?? 0;
    bar.style.width = `${(val / maxes[key]) * 100}%`;
    pts.textContent = val;
  }
}

// ── Grammar error list ───────────────────────────────────────────────────────
function renderErrors(errors) {
  errorsCount.textContent = errors.length;

  if (!errors.length) {
    errorsList.innerHTML = '<li class="error-empty">✓ No issues detected.</li>';
    return;
  }

  errorsList.innerHTML = errors.map(e => `
    <li class="error-item">
      <span class="error-original">"${e.original}"</span>
      <span class="error-arrow">→ suggest:</span>
      <span class="error-suggestion">"${e.suggestion}"</span>
      <span class="error-rule">${e.rule}</span>
    </li>
  `).join("");
}

// ── Inline highlight overlay ─────────────────────────────────────────────────
function renderHighlights(text, errors) {
  if (!errors || !errors.length) {
    highlightOver.innerHTML = "";
    return;
  }
  let html = escapeHtml(text);
  errors.forEach(e => {
    const safeOrig = escapeRegex(e.original);
    html = html.replace(
      new RegExp(`\\b${safeOrig}\\b`, "gi"),
      `<span class="err-word">$&</span>`
    );
  });
  highlightOver.innerHTML = html;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// ── Tags update ──────────────────────────────────────────────────────────────
function updateTags(data) {
  tagTone.textContent = `Tone: ${data.tone || "—"}`;

  if (data.has_empathy) {
    tagEmpathy.textContent = "Empathy: ✓ Present";
    tagEmpathy.classList.remove("missing");
  } else {
    tagEmpathy.textContent = "Empathy: ✗ Missing";
    tagEmpathy.classList.add("missing");
  }

  const ec = data.error_count || 0;
  if (ec > 0) {
    tagErrors.textContent = `Errors: ${ec}`;
  } else {
    tagErrors.textContent = "No issues";
  }
  if (ec > 0) tagErrors.classList.add("has-errors");
  else tagErrors.classList.remove("has-errors");
}

// ── Empathy hint card ────────────────────────────────────────────────────────
function updateEmpathyCard(data) {
  if (!data.has_empathy && data.empathy_suggestion) {
    empathyText.textContent = data.empathy_suggestion;
    empathyCard.style.display = "flex";
  } else {
    empathyCard.style.display = "none";
  }
}

// ── Improved response ────────────────────────────────────────────────────────
function renderImproved(text) {
  lastImproved = text || "";
  if (text) {
    improvedText.textContent = text;
    improvedText.classList.add("has-content");
  } else {
    improvedText.textContent = "Your enhanced response will appear here as you type…";
    improvedText.classList.remove("has-content");
  }
}

// ── Typing indicator ─────────────────────────────────────────────────────────
function setTypingStatus(state) {
  if (state === "typing") {
    typingStatus.innerHTML = `Analysing<span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>`;
    typingStatus.style.color = "var(--accent)";
  } else if (state === "done") {
    typingStatus.textContent = "Analysis complete ✓";
    typingStatus.style.color = "var(--good)";
  } else {
    typingStatus.textContent = "";
  }
}

// ── Real-time API call ───────────────────────────────────────────────────────
async function realtimeAnalysis(text) {
  if (!text.trim()) {
    resetUI();
    return;
  }

  setTypingStatus("typing");

  try {
    const res = await fetch("/realtime", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();

    // Score
    if (data.score) {
      setScore(data.score.total);
      scoreLabel.textContent = data.score.label || "—";
      setBreakdown(data.score.breakdown);
    }

    // Improved text
    renderImproved(data.improved);

    // Tags
    updateTags(data);

    // Empathy card
    updateEmpathyCard(data);

    // Error list + highlights
    renderErrors(data.grammar_errors || []);
    renderHighlights(text, data.grammar_errors || []);

    setTypingStatus("done");
  } catch (err) {
    console.error("ReplyIQ API error:", err);
    setTypingStatus("idle");
  }
}

const debouncedAnalysis = debounce(realtimeAnalysis, 500);

// ── Full analysis (button click) ─────────────────────────────────────────────
async function fullAnalysis() {
  const text = agentInput.value;
  if (!text.trim()) {
    showToast("Please enter some text first.");
    return;
  }
  if (isAnalysing) return;
  isAnalysing = true;
  analyseBtn.disabled = true;
  analyseBtn.innerHTML = `<span class="btn-icon">⏳</span> Analysing…`;

  try {
    const res = await fetch("/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();

    setScore(data.score?.total ?? 0);
    scoreLabel.textContent = data.score?.label || "—";
    setBreakdown(data.score?.breakdown);
    renderImproved(data.improved);
    updateTags({
      tone: data.tone,
      has_empathy: data.empathy?.has_empathy,
      empathy_suggestion: data.empathy?.suggestion,
      error_count: data.grammar_errors?.length || 0,
    });
    updateEmpathyCard({
      has_empathy: data.empathy?.has_empathy,
      empathy_suggestion: data.empathy?.suggestion,
    });
    renderErrors(data.grammar_errors || []);
    renderHighlights(text, data.grammar_errors || []);
    setTypingStatus("done");
    showToast("Analysis complete!");
  } catch (err) {
    showToast("Error connecting to server.");
    console.error(err);
  } finally {
    isAnalysing = false;
    analyseBtn.disabled = false;
    analyseBtn.innerHTML = `<span class="btn-icon">⚡</span> Analyse Now`;
  }
}

// ── Reset UI ─────────────────────────────────────────────────────────────────
function resetUI() {
  ringFill.style.strokeDashoffset = RING_CIRC;
  scoreNum.textContent = "—";
  scoreLabel.textContent = "Awaiting input…";
  scoreCard.classList.remove("score-good", "score-warn", "score-bad");
  [grammarBar, empathyBar, lengthBar, toneBar].forEach(b => b.style.width = "0%");
  [grammarPts, empathyPts, lengthPts, tonePts].forEach(p => p.textContent = "—");
  tagTone.textContent = "Tone: —";
  tagEmpathy.textContent = "Empathy: —";
  tagEmpathy.classList.remove("missing");
  tagErrors.textContent = "Errors: —";
  tagErrors.classList.remove("has-errors");
  renderImproved("");
  errorsList.innerHTML = '<li class="error-empty">No issues detected yet.</li>';
  errorsCount.textContent = "0";
  empathyCard.style.display = "none";
  highlightOver.innerHTML = "";
  setTypingStatus("idle");
}

// ── Copy improved response ───────────────────────────────────────────────────
copyBtn.addEventListener("click", () => {
  if (!lastImproved) { showToast("Nothing to copy yet."); return; }
  navigator.clipboard.writeText(lastImproved).then(() => {
    copyBtn.innerHTML = `<span id="copyIcon">✓</span> Copied!`;
    setTimeout(() => { copyBtn.innerHTML = `<span id="copyIcon">⎘</span> Copy`; }, 2000);
    showToast("Copied to clipboard!");
  });
});

// ── Apply improved response → textarea ──────────────────────────────────────
applyBtn.addEventListener("click", () => {
  if (!lastImproved) { showToast("No improved response to apply."); return; }
  agentInput.value = lastImproved;
  updateWordCount(lastImproved);
  debouncedAnalysis(lastImproved);
  showToast("Improved response applied!");
});

// ── Clear ────────────────────────────────────────────────────────────────────
clearBtn.addEventListener("click", () => {
  agentInput.value = "";
  updateWordCount("");
  resetUI();
  agentInput.focus();
});

// ── Analyse Now button ───────────────────────────────────────────────────────
analyseBtn.addEventListener("click", fullAnalysis);

// ── Input event: real-time ───────────────────────────────────────────────────
agentInput.addEventListener("input", () => {
  const text = agentInput.value;
  updateWordCount(text);
  if (text.trim()) {
    setTypingStatus("typing");
    debouncedAnalysis(text);
  } else {
    resetUI();
  }
});

// ── Sample prompt buttons ────────────────────────────────────────────────────
document.querySelectorAll(".sample-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const sample = btn.dataset.sample;
    agentInput.value = sample;
    updateWordCount(sample);
    debouncedAnalysis(sample);
    agentInput.focus();
  });
});

// ── Dark / Light mode toggle ─────────────────────────────────────────────────
darkToggle.addEventListener("click", () => {
  document.body.classList.toggle("light");
  darkToggle.textContent = document.body.classList.contains("light") ? "☀" : "☾";
});

// ── Keyboard shortcut: Ctrl+Enter → Analyse ──────────────────────────────────
agentInput.addEventListener("keydown", e => {
  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
    e.preventDefault();
    fullAnalysis();
  }
});
