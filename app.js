const EXAM_BLUEPRINT = {
  "Quantitative Reasoning": ["Algebra", "Arithmetic", "Word Problems", "Statistics"],
  "Verbal Reasoning": ["Reading Comprehension", "Critical Reasoning", "Sentence Correction"],
  "Data Insights": ["Data Sufficiency", "Multi-Source Reasoning", "Table Analysis", "Graphics Interpretation"]
};

const QUESTIONS = [
  {
    section: "Quantitative Reasoning",
    category: "Algebra",
    difficulty: 60,
    prompt: "If 3x + 5 = 26, what is x?",
    choices: ["5", "6", "7", "8"],
    answerIndex: 2,
    efficientMethod:
      "Subtract 5 first: 3x = 21, then divide by 3. GMAT-efficient move: isolate in one operation per line. Plug-in check: x=7 gives 21+5=26, so it fits exactly."
  },
  {
    section: "Quantitative Reasoning",
    category: "Arithmetic",
    difficulty: 45,
    prompt: "A store discounts an item from $80 by 15%. What is the sale price?",
    choices: ["$66", "$68", "$70", "$72"],
    answerIndex: 1,
    efficientMethod:
      "On GMAT, percent-off is often faster with multiplier: 100%-15%=85%=0.85. Compute 80×0.85=68. Alternate quick split: 10% is 8 and 5% is 4, so discount is 12; 80-12=68."
  },
  {
    section: "Quantitative Reasoning",
    category: "Word Problems",
    difficulty: 68,
    prompt: "A train travels 120 miles in 2 hours, then 150 miles in 3 hours. What is the average speed for the entire trip?",
    choices: ["50 mph", "54 mph", "56 mph", "60 mph"],
    answerIndex: 1,
    efficientMethod:
      "Average speed is total distance/total time, not average of rates. Distance=120+150=270. Time=2+3=5. So 270/5=54 mph."
  },
  {
    section: "Quantitative Reasoning",
    category: "Statistics",
    difficulty: 62,
    prompt: "The mean of 5 numbers is 14. If four numbers sum to 50, what is the fifth number?",
    choices: ["18", "20", "22", "24"],
    answerIndex: 1,
    efficientMethod:
      "Mean×count gives total sum: 14×5=70. Missing value is 70-50=20. This is a classic GMAT shortcut for mean problems."
  },
  {
    section: "Verbal Reasoning",
    category: "Reading Comprehension",
    difficulty: 58,
    prompt:
      "Passage claim: urban density increases innovation. Which new evidence most strongly supports the claim?",
    choices: [
      "A dense city has more public parks than suburbs.",
      "Patent output per capita rises as cross-industry worker interactions increase in denser districts.",
      "A suburban town reduced traffic congestion after road expansion.",
      "A survey shows city residents spend more on rent."
    ],
    answerIndex: 1,
    efficientMethod:
      "GMAT RC support questions favor direct causal linkage. Choice B directly ties density mechanism (cross-industry contact) to innovation outcome (patents), so it is the strongest evidence."
  },
  {
    section: "Verbal Reasoning",
    category: "Critical Reasoning",
    difficulty: 66,
    prompt:
      "Argument: Company profits rose after ad spend increased, so the ad campaign caused the increase. Which assumption is required?",
    choices: [
      "No major non-ad changes occurred that could explain the profit increase.",
      "The company doubled employee headcount during the same period.",
      "Competitors reduced prices at the same time.",
      "The firm had a profit increase two years ago as well."
    ],
    answerIndex: 0,
    efficientMethod:
      "Use the GMAT negation test. Negate A: if major non-ad factors did drive profits, the conclusion collapses. So A is necessary."
  },
  {
    section: "Verbal Reasoning",
    category: "Sentence Correction",
    difficulty: 54,
    prompt:
      "Choose the best sentence: 'The analyst reviewed the data, writing the report, and the presentation was delivered by her team.'",
    choices: [
      "The analyst reviewed the data, writing the report, and the presentation was delivered by her team.",
      "The analyst reviewed the data, wrote the report, and her team delivered the presentation.",
      "Reviewing the data, the report was written by the analyst, and her team delivered the presentation.",
      "The analyst reviewed the data, and the report writing, while the presentation delivery was by her team."
    ],
    answerIndex: 1,
    efficientMethod:
      "GMAT SC prioritizes parallel structure and clear agency. Choice B keeps parallel verbs with a clear subject in each clause: reviewed, wrote, delivered."
  },
  {
    section: "Data Insights",
    category: "Data Sufficiency",
    difficulty: 70,
    prompt: "Is x > y? (1) x − y = 2 (2) x/y = 1.5",
    choices: ["Statement (1) alone is sufficient.", "Statement (2) alone is sufficient.", "Both together are sufficient, neither alone.", "Each statement alone is sufficient."],
    answerIndex: 0,
    efficientMethod:
      "(1) gives x-y=2, so x is definitely greater than y. Sufficient. (2) gives x=1.5y. With positive or negative y, relation could flip? Actually if y is negative, x is more negative and not greater; if y is positive, x>y. So (2) alone is not sufficient. Correct DS letter is A, i.e., statement (1) alone."
  },
  {
    section: "Data Insights",
    category: "Multi-Source Reasoning",
    difficulty: 67,
    prompt:
      "Exhibit 1 (on-time %): Supplier A 92, B 95, C 94. Exhibit 2 (defect %): A 1.8, B 2.4, C 1.9. Which supplier has highest on-time with defect under 2.0%?",
    choices: ["Supplier A", "Supplier B", "Supplier C", "No supplier qualifies"],
    answerIndex: 2,
    efficientMethod:
      "Filter first by defect<2.0 => A and C remain. Compare their on-time rates: C=94 vs A=92, so C wins. GMAT-efficient DI method: constrain then optimize."
  },
  {
    section: "Data Insights",
    category: "Table Analysis",
    difficulty: 63,
    prompt:
      "Revenue benchmark is >$120M and margin benchmark is >18%. Region X: $130M, 17%. Region Y: $125M, 20%. Region Z: $119M, 22%. Which region meets both benchmarks?",
    choices: ["X only", "Y only", "Z only", "X and Y"],
    answerIndex: 1,
    efficientMethod:
      "Check each row against both conditions. X fails margin, Z fails revenue, Y passes both. Fast table strategy: evaluate fail-fast criteria first."
  },
  {
    section: "Data Insights",
    category: "Graphics Interpretation",
    difficulty: 60,
    prompt:
      "A trendline shows churn at Q1 6.0%, Q2 5.2%, Q3 4.6%, Q4 3.9%. In which quarter does churn first fall below 4%?",
    choices: ["Q2", "Q3", "Q4", "Q1 of next year"],
    answerIndex: 2,
    efficientMethod:
      "Read threshold crossing directly: 4.6 is above 4, 3.9 is below 4, so first crossing is Q4."
  }
];

const STORAGE_KEY = "gmat-focus-coach-v2";
const baseSkill = 55;

let state = loadState();
let activeQuestion = null;

const questionCard = document.querySelector("#question-card");
const feedback = document.querySelector("#feedback");
const solution = document.querySelector("#solution");

function bindEvents() {
  document.querySelector("#next-question-btn").addEventListener("click", () => {
    activeQuestion = chooseNextQuestion();
    feedback.textContent = "";
    solution.textContent = "";
    renderQuestion();
  });

  document.querySelector("#submit-answer-btn").addEventListener("click", submitSelectedAnswer);
  document.querySelector("#reset-btn").addEventListener("click", resetProgress);
}

function loadState() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw) {
    return JSON.parse(raw);
  }

  const competencies = {};
  for (const [section, categories] of Object.entries(EXAM_BLUEPRINT)) {
    competencies[section] = {};
    for (const category of categories) {
      competencies[section][category] = baseSkill;
    }
  }

  return { competencies, history: [] };
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function chooseNextQuestion() {
  const scored = QUESTIONS.map((question) => {
    const competence = state.competencies[question.section][question.category];
    const weaknessGap = Math.max(0, question.difficulty - competence);
    const explorationBonus = Math.random() * 10;
    return { question, score: weaknessGap * 1.25 + explorationBonus };
  });

  scored.sort((a, b) => b.score - a.score);
  return scored[0].question;
}

function renderQuestion() {
  if (!activeQuestion) {
    questionCard.innerHTML = "<p>Click <strong>Get New Question</strong> to receive an adaptive prompt.</p>";
    return;
  }

  const optionsHtml = activeQuestion.choices
    .map(
      (choice, idx) => `
        <label class="choice">
          <input type="radio" name="answer" value="${idx}" />
          <span><strong>${String.fromCharCode(65 + idx)}.</strong> ${choice}</span>
        </label>
      `
    )
    .join("");

  questionCard.innerHTML = `
    <p class="question-meta"><strong>${activeQuestion.section}</strong> · ${activeQuestion.category} · Difficulty ${activeQuestion.difficulty}/100</p>
    <p>${activeQuestion.prompt}</p>
    <form id="choices-form" class="choices">${optionsHtml}</form>
  `;
}

function submitSelectedAnswer() {
  if (!activeQuestion) {
    feedback.className = "feedback incorrect";
    feedback.textContent = "Pick a question first.";
    return;
  }

  const selected = document.querySelector('input[name="answer"]:checked');
  if (!selected) {
    feedback.className = "feedback incorrect";
    feedback.textContent = "Select one answer choice before submitting.";
    return;
  }

  const selectedIndex = Number(selected.value);
  const isCorrect = selectedIndex === activeQuestion.answerIndex;
  const current = state.competencies[activeQuestion.section][activeQuestion.category];
  const delta = computeDelta(isCorrect, current, activeQuestion.difficulty);
  const updated = clamp(current + delta, 1, 100);

  state.competencies[activeQuestion.section][activeQuestion.category] = updated;
  state.history.push({
    at: new Date().toISOString(),
    section: activeQuestion.section,
    category: activeQuestion.category,
    difficulty: activeQuestion.difficulty,
    selectedIndex,
    correctIndex: activeQuestion.answerIndex,
    correct: isCorrect,
    scoreBefore: current,
    scoreAfter: updated
  });

  saveState();

  const correctLetter = String.fromCharCode(65 + activeQuestion.answerIndex);
  if (isCorrect) {
    feedback.className = "feedback correct";
    feedback.textContent = `Correct. ${activeQuestion.category} moved from ${Math.round(current)} to ${Math.round(updated)}.`;
  } else {
    feedback.className = "feedback incorrect";
    feedback.textContent = `Incorrect. Correct answer is ${correctLetter}. ${activeQuestion.category} moved from ${Math.round(current)} to ${Math.round(updated)}.`;
  }

  solution.innerHTML = `<strong>Most GMAT-efficient approach:</strong> ${activeQuestion.efficientMethod}`;

  renderDashboard();
  renderPredictions();
  renderSuggestions();
}

function computeDelta(isCorrect, current, targetDifficulty) {
  const challengeGap = targetDifficulty - current;
  const magnitude = 2 + Math.min(8, Math.abs(challengeGap) * 0.08);
  return isCorrect ? magnitude : -magnitude;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function average(values) {
  return values.reduce((sum, val) => sum + val, 0) / values.length;
}

function competencyToScore(competency) {
  return Math.round(205 + (competency / 100) * 600);
}

function competencyToPercentile(competency) {
  return Math.round(3 + (competency / 100) * 96);
}

function renderDashboard() {
  const container = document.querySelector("#dashboard");
  const template = document.querySelector("#metric-template");
  container.innerHTML = "";

  for (const [section, categories] of Object.entries(state.competencies)) {
    for (const [category, score] of Object.entries(categories)) {
      const node = template.content.firstElementChild.cloneNode(true);
      node.querySelector("h3").textContent = `${section} · ${category}`;
      node.querySelector(".meter span").style.width = `${score}%`;
      node.querySelector(".score").textContent = `Competency: ${Math.round(score)}/100`;
      container.appendChild(node);
    }
  }
}

function renderPredictions() {
  const container = document.querySelector("#predictions");
  container.innerHTML = "";

  const sectionCompetencies = {};
  for (const [section, categories] of Object.entries(state.competencies)) {
    sectionCompetencies[section] = average(Object.values(categories));
  }

  const overallCompetency = average(Object.values(sectionCompetencies));
  const rows = [
    ...Object.entries(sectionCompetencies).map(([label, competency]) => ({ label, competency })),
    { label: "Overall GMAT Focus", competency: overallCompetency }
  ];

  for (const row of rows) {
    const score = competencyToScore(row.competency);
    const percentile = competencyToPercentile(row.competency);
    const card = document.createElement("article");
    card.className = "metric-card";
    card.innerHTML = `
      <h3>${row.label}</h3>
      <p class="score">Predicted score: ${score}</p>
      <p class="score">Predicted percentile: ${percentile}th</p>
      <p class="score">Readiness: ${Math.round(row.competency)}/100</p>
    `;
    container.appendChild(card);
  }
}

function renderSuggestions() {
  const ul = document.querySelector("#suggestions");
  ul.innerHTML = "";

  const flattened = Object.entries(state.competencies).flatMap(([section, categories]) =>
    Object.entries(categories).map(([category, score]) => ({ section, category, score }))
  );

  flattened.sort((a, b) => a.score - b.score);
  const weakestThree = flattened.slice(0, 3);

  for (const item of weakestThree) {
    const li = document.createElement("li");
    li.textContent = `${item.section} → ${item.category}: prioritize mixed drills and timed sets until competency reaches at least ${Math.min(100, Math.round(item.score + 10))}.`;
    ul.appendChild(li);
  }

  const recentAccuracy = calculateRecentAccuracy(12);
  const tip = document.createElement("li");
  tip.textContent = `Recent accuracy (last up to 12 attempts): ${recentAccuracy}% — ${recentAccuracy < 60 ? "slow down and review misses in detail" : "keep increasing difficulty gradually"}.`;
  ul.appendChild(tip);
}

function calculateRecentAccuracy(limit) {
  const recent = state.history.slice(-limit);
  if (!recent.length) {
    return 0;
  }

  const correct = recent.filter((x) => x.correct).length;
  return Math.round((correct / recent.length) * 100);
}

function renderAll() {
  if (!activeQuestion) {
    activeQuestion = chooseNextQuestion();
  }

  renderQuestion();
  renderDashboard();
  renderPredictions();
  renderSuggestions();
}

function resetProgress() {
  localStorage.removeItem(STORAGE_KEY);
  state = loadState();
  activeQuestion = chooseNextQuestion();
  feedback.className = "feedback";
  feedback.textContent = "Progress reset.";
  solution.textContent = "";
  renderAll();
}

bindEvents();
renderAll();
