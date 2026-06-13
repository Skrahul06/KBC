/* ═══════════════════════════════════════════════════════════════
   KBC - Kaun Banega Crorepati  |  script.js
   ═══════════════════════════════════════════════════════════════
   API_BASE points to your Python Flask server.
   Change this if you run Flask on a different port.
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = "http://localhost:5000/api";

/* ── State ──────────────────────────────────────────────────────── */
let state = {
  playerName: "",
  currentQuestion: null,
  currentQuestionId: 1,
  selectedOption: null,
  answered: false,
  balance: "₹0",
  totalQuestions: 15,
  lifelinesAvailable: { fifty_fifty: true, phone_a_friend: true, audience_poll: true },
  prizeLadder: [],
  safeMilestones: {},
  fiftyFiftyRemoved: [],        // track which options were removed
};

/* ── DOM refs ────────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const screens = {
  welcome: $("welcome-screen"),
  game:    $("game-screen"),
  result:  $("result-screen"),
};

/* ── Screen switching ────────────────────────────────────────────── */
function showScreen(name) {
  Object.values(screens).forEach(s => s.classList.remove("active"));
  screens[name].classList.add("active");
}

/* ── Loader ─────────────────────────────────────────────────────── */
function setLoading(on) {
  $("loader").classList.toggle("active", on);
}

/* ── API helpers ─────────────────────────────────────────────────── */
async function apiFetch(path, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API_BASE + path, opts);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

/* ── Init game ───────────────────────────────────────────────────── */
async function initGame() {
  setLoading(true);
  try {
    const data = await apiFetch("/start");
    state.totalQuestions  = data.total_questions;
    state.prizeLadder     = data.prize_ladder;
    state.safeMilestones  = data.safe_milestones;
    state.currentQuestionId = 1;
    state.balance         = "₹0";
    state.lifelinesAvailable = { fifty_fifty: true, phone_a_friend: true, audience_poll: true };
    state.fiftyFiftyRemoved  = [];

    buildPrizeLadder();
    updateHeaderBalance();
    resetLifelineButtons();

    await loadQuestion(1);
    showScreen("game");
  } catch (e) {
    showFeedback(`⚠ Could not connect to server. (${e.message})`, "wrong");
  } finally {
    setLoading(false);
  }
}

/* ── Load a question ─────────────────────────────────────────────── */
async function loadQuestion(id) {
  setLoading(true);
  try {
    const q = await apiFetch(`/question/${id}`);
    state.currentQuestion   = q;
    state.selectedOption    = null;
    state.answered          = false;
    state.fiftyFiftyRemoved = [];

    renderQuestion(q);
    updatePrizeLadder(id);
    showFeedback("Select your answer, then click Confirm.", "");
    $("confirm-btn").disabled = true;
  } catch (e) {
    showFeedback(`⚠ Failed to load question. (${e.message})`, "wrong");
  } finally {
    setLoading(false);
  }
}

/* ── Render question + options ───────────────────────────────────── */
function renderQuestion(q) {
  $("q-number").textContent  = `Question ${q.id} of ${state.totalQuestions}`;
  $("q-prize").textContent   = q.prize;
  $("q-text").textContent    = q.question;

  const grid = $("options-grid");
  grid.innerHTML = "";

  Object.entries(q.options).forEach(([letter, text]) => {
    const btn = document.createElement("button");
    btn.className    = "option-btn";
    btn.dataset.key  = letter;
    btn.innerHTML    = `<span class="option-letter">${letter}</span>${text}`;
    btn.addEventListener("click", () => selectOption(letter));
    grid.appendChild(btn);
  });
}

/* ── Option selection ────────────────────────────────────────────── */
function selectOption(letter) {
  if (state.answered) return;

  state.selectedOption = letter;

  document.querySelectorAll(".option-btn").forEach(btn => {
    btn.classList.remove("selected");
    if (btn.dataset.key === letter) btn.classList.add("selected");
  });

  $("confirm-btn").disabled = false;
}

/* ── Confirm answer ──────────────────────────────────────────────── */
async function confirmAnswer() {
  if (!state.selectedOption || state.answered) return;
  state.answered = true;
  $("confirm-btn").disabled = true;

  setLoading(true);
  try {
    const data = await apiFetch("/answer", "POST", {
      question_id: state.currentQuestion.id,
      selected:    state.selectedOption,
    });

    revealAnswer(data);
  } catch (e) {
    showFeedback(`⚠ Error checking answer. (${e.message})`, "wrong");
  } finally {
    setLoading(false);
  }
}

/* ── Reveal result ────────────────────────────────────────────────── */
function revealAnswer(data) {
  // Colour all options
  document.querySelectorAll(".option-btn").forEach(btn => {
    btn.disabled = true;
    const key = btn.dataset.key;
    if (key === data.correct_answer) btn.classList.add("correct");
    else if (key === data.selected && !data.correct) btn.classList.add("wrong");
  });

  if (data.correct) {
    state.balance = data.prize_won;
    updateHeaderBalance();

    if (data.is_final) {
      showFeedback("🎉 INCREDIBLE! You've won ₹1 Crore! Congratulations!", "correct");
      setTimeout(() => showResult(true, data.prize_won), 2500);
    } else {
      showFeedback(`✅ Correct! You've won ${data.prize_won}. Moving to next question…`, "correct");
      setTimeout(() => loadQuestion(data.next_question_id), 2400);
    }
  } else {
    state.balance = data.prize_won;
    updateHeaderBalance();
    showFeedback(
      `❌ Wrong! The correct answer was (${data.correct_answer}) ${data.correct_option_text}. You take home ${data.prize_won}.`,
      "wrong"
    );
    setTimeout(() => showResult(false, data.prize_won), 3000);
  }
}

/* ── Quit early ───────────────────────────────────────────────────── */
function quitGame() {
  if (!confirm("Are you sure you want to quit and take your winnings?")) return;
  showResult(false, state.balance, true);
}

/* ── Show result screen ───────────────────────────────────────────── */
function showResult(won, amount, quit = false) {
  $("result-name-display").textContent   = state.playerName;
  $("result-amount-display").textContent = amount;

  if (won) {
    $("result-emoji").textContent   = "🏆";
    $("result-title").textContent   = "Congratulations!";
    $("result-label").textContent   = "You are a Crorepati!";
  } else if (quit) {
    $("result-emoji").textContent   = "👋";
    $("result-title").textContent   = "You Quit!";
    $("result-label").textContent   = "Smart move — you walk away with:";
  } else {
    $("result-emoji").textContent   = "😔";
    $("result-title").textContent   = "Game Over";
    $("result-label").textContent   = "You take home:";
  }

  showScreen("result");
}

/* ── Lifelines ────────────────────────────────────────────────────── */
async function useLifeline(type) {
  if (!state.lifelinesAvailable[type] || state.answered) return;
  state.lifelinesAvailable[type] = false;
  document.querySelector(`[data-lifeline="${type}"]`).disabled = true;

  setLoading(true);
  try {
    const data = await apiFetch(`/lifeline/${type}`, "POST", {
      question_id: state.currentQuestion.id,
    });
    handleLifelineResult(type, data);
  } catch (e) {
    showFeedback(`⚠ Lifeline failed. (${e.message})`, "wrong");
    state.lifelinesAvailable[type] = true;
    document.querySelector(`[data-lifeline="${type}"]`).disabled = false;
  } finally {
    setLoading(false);
  }
}

function handleLifelineResult(type, data) {
  if (type === "fifty_fifty") {
    state.fiftyFiftyRemoved = data.removed;
    document.querySelectorAll(".option-btn").forEach(btn => {
      if (data.removed.includes(btn.dataset.key)) {
        btn.disabled  = true;
        btn.style.opacity = "0.2";
      }
    });
    showFeedback(`50:50 used! Options ${data.removed.join(" and ")} removed.`, "info");

  } else if (type === "audience_poll") {
    const votes    = data.votes;
    const sorted   = Object.entries(votes).sort((a, b) => b[1] - a[1]);
    const barLines = sorted.map(([opt, pct]) =>
      `(${opt}) ${"█".repeat(Math.round(pct / 5))} ${pct}%`
    ).join("  |  ");
    showFeedback(`📊 Audience Poll: ${barLines}`, "info");

  } else if (type === "phone_a_friend") {
    showFeedback(`📞 Phone a Friend: ${data.message}`, "info");
  }
}

/* ── Prize ladder ─────────────────────────────────────────────────── */
function buildPrizeLadder() {
  const container = $("prize-ladder");
  container.innerHTML = `<p class="card-title">Prize Ladder</p>`;

  // Render in reverse (highest first)
  [...state.prizeLadder].reverse().forEach(item => {
    const row = document.createElement("div");
    row.className   = "prize-row";
    row.id          = `prize-row-${item.id}`;
    const isSafe    = !!state.safeMilestones[item.id];
    if (isSafe) row.classList.add("safe");

    row.innerHTML = `<span class="q-num">Q${item.id}</span><span class="amount">${item.prize}</span>`;
    container.appendChild(row);
  });
}

function updatePrizeLadder(currentId) {
  state.prizeLadder.forEach(item => {
    const row = $(`prize-row-${item.id}`);
    if (!row) return;
    row.classList.remove("current", "cleared");
    if (item.id === currentId)      row.classList.add("current");
    else if (item.id < currentId)   row.classList.add("cleared");
  });
}

/* ── Header balance ───────────────────────────────────────────────── */
function updateHeaderBalance() {
  $("header-balance").textContent = `Balance: ${state.balance}`;
}

/* ── Feedback bar ─────────────────────────────────────────────────── */
function showFeedback(msg, type) {
  const bar = $("feedback-bar");
  bar.textContent = msg;
  bar.className   = "feedback-bar";
  if (type) bar.classList.add(type);
}

/* ── Reset lifeline buttons ───────────────────────────────────────── */
function resetLifelineButtons() {
  document.querySelectorAll(".lifeline-btn").forEach(btn => {
    btn.disabled = false;
    btn.style.opacity = "";
  });
}

/* ── Welcome form submit ──────────────────────────────────────────── */
$("start-btn").addEventListener("click", async () => {
  const name = $("player-name").value.trim();
  if (!name) { alert("Please enter your name!"); return; }
  state.playerName = name;
  $("header-player").textContent = name;
  await initGame();
});

$("player-name").addEventListener("keydown", e => {
  if (e.key === "Enter") $("start-btn").click();
});

/* ── Game buttons ─────────────────────────────────────────────────── */
$("confirm-btn").addEventListener("click", confirmAnswer);
$("quit-btn").addEventListener("click", quitGame);
$("play-again-btn").addEventListener("click", () => {
  showScreen("welcome");
  $("player-name").value = "";
});

/* ── Lifeline buttons ─────────────────────────────────────────────── */
document.querySelectorAll(".lifeline-btn").forEach(btn => {
  btn.addEventListener("click", () => useLifeline(btn.dataset.lifeline));
});
