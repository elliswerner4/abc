# GMAT Focus Coach Web App

A lightweight single-page web app that helps you prepare for the GMAT Focus exam by:

- Serving adaptive **multiple-choice** practice questions that target weaker categories.
- Letting you select an answer and submit like the real exam flow.
- Providing immediate right/wrong feedback and a concise, GMAT-efficient solution method (including plug-in guidance where relevant).
- Tracking competency from **1-100** for each category in:
  - Quantitative Reasoning
  - Verbal Reasoning
  - Data Insights
- Estimating predicted score + percentile for each section and overall.
- Recommending study priorities based on your weakest categories and recent accuracy.

## Run locally

```bash
python3 -m http.server 4173
```

Then open <http://localhost:4173>.

## How adaptation works

- Each question has a suggested difficulty, answer choices, and an efficient solve strategy.
- Question selection prioritizes categories where your competency is below question difficulty.
- After you submit an answer, competency updates up/down based on correctness and challenge mismatch.
- All progress is saved in browser `localStorage`.
