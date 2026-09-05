// JavaScript frontend for Guess the Number Game

let currentSession = null;
let currentDifficulty = "Easy";
let minBound = 1;
let maxBound = 50;
let currentLow = 1;
let currentHigh = 50;
let maxAttempts = 10;
let attemptsUsed = 0;
let currentPlayerName = "Player 1";

// DOM Elements
const setupCard = document.getElementById("setup-card");
const gameplayCard = document.getElementById("gameplay-card");
const resultCard = document.getElementById("result-card");
const playerInput = document.getElementById("player-input");
const currentPlayerDisplay = document.getElementById("current-player-display");
const btnChangePlayer = document.getElementById("btn-change-player");
const btnStartGame = document.getElementById("btn-start-game");
const customFields = document.getElementById("custom-fields");
const diffBtns = document.querySelectorAll(".diff-btn");

const gameDiffTag = document.getElementById("game-diff-tag");
const gameRangeLabel = document.getElementById("game-range-label");
const attemptsLeftCount = document.getElementById("attempts-left-count");
const maxAttemptsCount = document.getElementById("max-attempts-count");
const attemptsPills = document.getElementById("attempts-pills");
const visualRangeText = document.getElementById("visual-range-text");
const rangeBarActive = document.getElementById("range-bar-active");
const guessForm = document.getElementById("guess-form");
const guessInput = document.getElementById("guess-input");
const hintBanner = document.getElementById("hint-banner");
const historyList = document.getElementById("history-list");
const btnAbandonGame = document.getElementById("btn-abandon-game");

const resultIcon = document.getElementById("result-icon");
const resultTitle = document.getElementById("result-title");
const resultMessage = document.getElementById("result-message");
const resultTarget = document.getElementById("result-target");
const resultScore = document.getElementById("result-score");
const resultTime = document.getElementById("result-time");
const btnPlayAgain = document.getElementById("btn-play-again");
const btnViewStatsTab = document.getElementById("btn-view-stats-tab");

const tabBtns = document.querySelectorAll(".tab-btn");
const tabLeaderboard = document.getElementById("tab-leaderboard");
const tabPlayerStats = document.getElementById("tab-player-stats");
const leaderboardTbody = document.getElementById("leaderboard-tbody");
const btnRefreshLeaderboard = document.getElementById("btn-refresh-leaderboard");

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  loadLeaderboard();
  setupEventListeners();
});

function setupEventListeners() {
  // Difficulty selection
  diffBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      diffBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentDifficulty = btn.getAttribute("data-diff");

      if (currentDifficulty === "Custom") {
        customFields.classList.remove("hidden");
      } else {
        customFields.classList.add("hidden");
      }
    });
  });

  // Switch player
  btnChangePlayer.addEventListener("click", () => {
    const newName = prompt("Enter new player name:", currentPlayerName);
    if (newName && newName.trim()) {
      currentPlayerName = newName.trim();
      playerInput.value = currentPlayerName;
      currentPlayerDisplay.innerText = currentPlayerName;
      loadPlayerStats();
    }
  });

  // Start game
  btnStartGame.addEventListener("click", startGame);

  // Submit guess
  guessForm.addEventListener("submit", (e) => {
    e.preventDefault();
    submitGuess();
  });

  // Abandon game
  btnAbandonGame.addEventListener("click", () => {
    if (confirm("Are you sure you want to abandon this game?")) {
      showSetupCard();
    }
  });

  // Play again
  btnPlayAgain.addEventListener("click", () => {
    showSetupCard();
  });

  // View stats button from result card
  btnViewStatsTab.addEventListener("click", () => {
    showSetupCard();
    switchTab("player-stats");
    loadPlayerStats();
  });

  // Tabs
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const tab = btn.getAttribute("data-tab");
      switchTab(tab);
    });
  });

  // Refresh leaderboard
  btnRefreshLeaderboard.addEventListener("click", loadLeaderboard);
}

function switchTab(tabName) {
  tabBtns.forEach((b) => {
    b.classList.toggle("active", b.getAttribute("data-tab") === tabName);
  });
  if (tabName === "leaderboard") {
    tabLeaderboard.classList.add("active");
    tabPlayerStats.classList.remove("active");
    loadLeaderboard();
  } else {
    tabLeaderboard.classList.remove("active");
    tabPlayerStats.classList.add("active");
    loadPlayerStats();
  }
}

async function startGame() {
  const username = playerInput.value.trim() || "Guest";
  currentPlayerName = username;
  currentPlayerDisplay.innerText = username;

  const payload = {
    username: username,
    difficulty: currentDifficulty,
  };

  if (currentDifficulty === "Custom") {
    payload.min_val = parseInt(document.getElementById("custom-min").value) || 1;
    payload.max_val = parseInt(document.getElementById("custom-max").value) || 100;
    payload.max_attempts = parseInt(document.getElementById("custom-attempts").value) || 7;
    if (payload.min_val >= payload.max_val) {
      alert("Max Number must be greater than Min Number!");
      return;
    }
  }

  try {
    const res = await fetch("/api/start-game", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (data.status === "success") {
      currentSession = data.session_id;
      minBound = data.min_val;
      maxBound = data.max_val;
      currentLow = minBound;
      currentHigh = maxBound;
      maxAttempts = data.max_attempts;
      attemptsUsed = 0;

      // Update UI
      gameDiffTag.innerText = `${data.difficulty} Mode`;
      gameRangeLabel.innerText = `Range: ${minBound} to ${maxBound}`;
      attemptsLeftCount.innerText = maxAttempts;
      maxAttemptsCount.innerText = maxAttempts;
      hintBanner.innerText = `I'm thinking of a number between ${minBound} and ${maxBound}. What is your first guess?`;
      historyList.innerHTML = "";
      guessInput.value = "";
      guessInput.min = minBound;
      guessInput.max = maxBound;

      updateAttemptsPills();
      updateRangeVisualizer();

      setupCard.classList.add("hidden");
      resultCard.classList.add("hidden");
      gameplayCard.classList.remove("hidden");
      guessInput.focus();
    }
  } catch (err) {
    console.error("Failed to start game:", err);
    alert("Could not connect to server.");
  }
}

async function submitGuess() {
  const guess = parseInt(guessInput.value);
  if (isNaN(guess)) return;

  if (guess < minBound || guess > maxBound) {
    alert(`Please enter a number within bounds (${minBound} to ${maxBound})!`);
    return;
  }

  try {
    const res = await fetch("/api/guess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSession,
        guess: guess,
      }),
    });
    const data = await res.json();

    if (data.status === "success") {
      attemptsUsed = data.meta.attempts_used;
      attemptsLeftCount.innerText = data.meta.remaining_attempts;
      hintBanner.innerText = data.hint;

      if (data.meta.range) {
        currentLow = data.meta.range[0];
        currentHigh = data.meta.range[1];
      }

      // Add to turn history list
      addHistoryItem(guess, data.hint);
      updateAttemptsPills();
      updateRangeVisualizer();

      guessInput.value = "";
      guessInput.focus();

      if (data.is_game_over) {
        setTimeout(() => {
          showGameOver(data);
        }, 600);
      }
    } else {
      alert(data.message || "Error processing guess");
    }
  } catch (err) {
    console.error("Failed to submit guess:", err);
  }
}

function addHistoryItem(guess, hint) {
  const item = document.createElement("div");
  item.className = "history-item";
  item.innerHTML = `
    <span class="history-guess">Guess #${attemptsUsed}: <strong>${guess}</strong></span>
    <span class="history-clue">${hint.split("|")[0]}</span>
  `;
  historyList.prepend(item);
}

function updateAttemptsPills() {
  attemptsPills.innerHTML = "";
  for (let i = 0; i < maxAttempts; i++) {
    const pill = document.createElement("div");
    pill.className = "pill" + (i < attemptsUsed ? " used" : "");
    attemptsPills.appendChild(pill);
  }
}

function updateRangeVisualizer() {
  visualRangeText.innerText = `[ ${currentLow} ... ${currentHigh} ]`;
  const totalSpan = maxBound - minBound;
  if (totalSpan <= 0) return;

  const leftPct = ((currentLow - minBound) / totalSpan) * 100;
  const widthPct = Math.max(2, ((currentHigh - currentLow) / totalSpan) * 100);

  rangeBarActive.style.left = `${leftPct}%`;
  rangeBarActive.style.width = `${widthPct}%`;
}

function showGameOver(data) {
  gameplayCard.classList.add("hidden");
  resultCard.classList.remove("hidden");

  if (data.is_won) {
    resultIcon.innerText = "🏆";
    resultTitle.innerText = "Congratulations! You Won!";
    resultTitle.style.color = "var(--accent-green)";
    resultMessage.innerText = `You correctly discovered the secret number in ${data.meta.attempts_used} attempt(s)!`;
  } else {
    resultIcon.innerText = "💀";
    resultTitle.innerText = "Game Over!";
    resultTitle.style.color = "var(--accent-red)";
    resultMessage.innerText = `You ran out of attempts! Better luck next time.`;
  }

  resultTarget.innerText = data.target_number;
  resultScore.innerText = `${data.score} pts`;
  resultTime.innerText = `${data.meta.duration || "0"}s`;

  // Reload stats & leaderboard in background
  loadLeaderboard();
  loadPlayerStats();
}

function showSetupCard() {
  gameplayCard.classList.add("hidden");
  resultCard.classList.add("hidden");
  setupCard.classList.remove("hidden");
}

async function loadLeaderboard() {
  try {
    const res = await fetch("/api/leaderboard?limit=8");
    const data = await res.json();
    if (data.status === "success") {
      const rows = data.leaderboard;
      if (!rows || rows.length === 0) {
        leaderboardTbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No wins recorded yet.</td></tr>`;
        return;
      }

      leaderboardTbody.innerHTML = rows
        .map((r, i) => {
          const medal = i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `#${i + 1}`;
          return `
            <tr>
              <td><strong>${medal}</strong></td>
              <td>${escapeHtml(r.username)}</td>
              <td><span class="tag">${r.difficulty}</span></td>
              <td><strong class="text-warning">${r.score}</strong></td>
              <td>${r.attempts_used}/${r.max_attempts}</td>
            </tr>
          `;
        })
        .join("");
    }
  } catch (err) {
    console.error("Leaderboard load failed:", err);
  }
}

async function loadPlayerStats() {
  const username = currentPlayerName;
  document.getElementById("stats-player-name").innerText = `${username}'s Stats`;

  try {
    const res = await fetch(`/api/stats?username=${encodeURIComponent(username)}`);
    const data = await res.json();
    if (data.status === "success") {
      const stats = data.stats;
      if (stats) {
        document.getElementById("stat-games").innerText = stats.total_games;
        document.getElementById("stat-wins").innerText = stats.games_won;
        document.getElementById("stat-winrate").innerText = `${stats.win_rate}%`;
        document.getElementById("stat-highscore").innerText = stats.high_score;
      } else {
        document.getElementById("stat-games").innerText = 0;
        document.getElementById("stat-wins").innerText = 0;
        document.getElementById("stat-winrate").innerText = "0%";
        document.getElementById("stat-highscore").innerText = 0;
      }

      const recentContainer = document.getElementById("recent-games-list");
      const recents = data.recent_games;
      if (recents && recents.length > 0) {
        recentContainer.innerHTML = recents
          .map((g) => {
            const statusClass = g.is_won ? "text-success" : "text-danger";
            const statusText = g.is_won ? "WON" : "LOST";
            return `
              <div class="recent-game-row">
                <span><strong>${g.difficulty}</strong> • <span class="${statusClass}">${statusText}</span></span>
                <span>${g.attempts_used}/${g.max_attempts} tries • <strong>${g.score} pts</strong></span>
              </div>
            `;
          })
          .join("");
      } else {
        recentContainer.innerHTML = `<p class="text-muted text-center">No recent games for ${escapeHtml(username)}.</p>`;
      }
    }
  } catch (err) {
    console.error("Stats load failed:", err);
  }
}

function escapeHtml(str) {
  return (str || "").replace(/[&<>'"]/g, (tag) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  }[tag] || tag));
}
