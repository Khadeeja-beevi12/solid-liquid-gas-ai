/* Page 3: quiz */
const quizBox = document.getElementById("quiz");
const TOTAL = 8;
let questions = [], index = 0, score = 0, locked = false;

function stars(n) { return "⭐".repeat(n) + "☆".repeat(5 - n); }

async function start() {
  SFX.click();
  quizBox.replaceChildren(h("p", { class: "loading", text: "Getting your questions…" }));
  try { questions = await api(`/api/quiz?n=${TOTAL}`); }
  catch (e) { quizBox.replaceChildren(h("p", { class: "error", text: e.message })); return; }
  index = 0; score = 0;
  showQuestion();
}

function showQuestion() {
  locked = false;
  const q = questions[index];
  const feedback = h("div", { class: "feedback", role: "status" });
  const next = h("button", { class: "btn", type: "button", hidden: true, onclick: () => { SFX.click(); index++; index < questions.length ? showQuestion() : finish(); } },
    index === questions.length - 1 ? "See my score" : "Next question");

  const options = q.options.map(opt => h("button", { type: "button", class: "option", onclick: ev => answer(ev.currentTarget, q, opt, options, feedback, next) }, opt));

  quizBox.replaceChildren(
    h("div", { class: "quiz-top" },
      h("span", { text: `Question ${index + 1} of ${questions.length}` }),
      h("span", { text: `Score: ${score}` })),
    h("div", { class: "progress", role: "progressbar", "aria-valuemin": "0", "aria-valuemax": String(questions.length), "aria-valuenow": String(index) },
      h("div", { class: "progress-fill", style: `width:${(index / questions.length) * 100}%` })),
    h("h2", { class: "question", text: q.question }),
    h("div", { class: "options" }, options),
    feedback, next);
  quizBox.querySelector(".option").focus({ preventScroll: true });
}

async function answer(btn, q, choice, options, feedback, next) {
  if (locked) return;
  locked = true;
  options.forEach(o => (o.disabled = true));
  let res;
  try {
    res = await api("/api/quiz/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: q.id, answer: choice }) });
  } catch (e) { feedback.textContent = e.message; locked = false; options.forEach(o => (o.disabled = false)); return; }

  if (res.correct) { score++; btn.classList.add("right"); SFX.correct(); }
  else {
    btn.classList.add("wrong"); SFX.wrong();
    options.find(o => o.textContent === res.answer)?.classList.add("right");
  }
  feedback.className = `feedback ${res.correct ? "ok" : "no"}`;
  feedback.replaceChildren(h("strong", { text: res.correct ? "Correct! 🎉 " : `Not quite. The answer is ${res.answer}. ` }), res.why);
  quizBox.querySelector(".quiz-top span:last-child").textContent = `Score: ${score}`;
  next.hidden = false;
  next.focus({ preventScroll: true });
}

function finish() {
  const n = questions.length, ratio = score / n, st = Math.round(ratio * 5);
  const msg = ratio === 1 ? "Perfect! You are a matter master!" : ratio >= 0.75 ? "Great job! You know your states of matter." : ratio >= 0.5 ? "Good try! Read the lesson once more and play again." : "Keep practising. Visit the Learn page and try again!";
  ratio >= 0.5 ? SFX.win() : SFX.click();
  quizBox.replaceChildren(h("div", { class: "quiz-end" },
    h("p", { class: "big-emoji", "aria-hidden": "true", text: ratio >= 0.75 ? "🏆" : ratio >= 0.5 ? "👍" : "📚" }),
    h("h2", { text: `You got ${score} out of ${n}` }),
    h("p", { class: "stars", "aria-label": `${st} out of 5 stars`, text: stars(st) }),
    h("p", { class: "lead", text: msg }),
    h("div", { class: "cta-row" },
      h("button", { class: "btn", type: "button", onclick: start }, "Play again"),
      h("a", { class: "btn ghost", href: "/", "data-sfx": "" }, "Back to the lesson"))));
}

document.getElementById("start-btn").addEventListener("click", start);
