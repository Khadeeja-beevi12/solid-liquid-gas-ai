/* Page 2: ask the AI */
const form = document.getElementById("ask-form");
const input = document.getElementById("material");
const resultBox = document.getElementById("result");
const history = [];

const STATE_WORD = { solid: "a solid", liquid: "a liquid", gas: "a gas" };
const fmtTemp = v => (v == null ? "not known" : `${v} °C`);

function bar(state, value, top) {
  const pct = Math.round(value * 100);
  return h("div", { class: "bar-row" },
    h("span", { class: "bar-name", text: cap(state) }),
    h("div", { class: "bar", role: "img", "aria-label": `${cap(state)} ${pct} percent` },
      h("div", { class: `fill ${state}${top ? " top" : ""}`, style: `width:${pct}%` })),
    h("span", { class: "bar-pct", text: pct + "%" }));
}

function render(r) {
  const name = cap(r.matched || r.input);
  const kids = [];
  if (r.state) {
    kids.push(h("div", { class: "answer" },
      h("div", { class: "answer-emoji", "aria-hidden": "true", text: r.emoji }),
      h("div", {},
        h("h2", { text: `${name} is ${STATE_WORD[r.state]}!` }),
        h("p", { class: "explain", text: r.explanation }))));
  } else {
    kids.push(h("div", { class: "answer" },
      h("div", { class: "answer-emoji", "aria-hidden": "true", text: r.emoji }),
      h("div", {}, h("h2", { text: "Hmm, I am not sure" }), h("p", { class: "explain", text: r.explanation }))));
  }
  if (r.typo_fixed) kids.push(h("p", { class: "note", text: `I think you meant “${r.matched}”.` }));
  if (r.note) kids.push(h("p", { class: "note", text: r.note }));
  if (r.fact) kids.push(h("p", { class: "fact" }, h("strong", { text: "Did you know? " }), r.fact));

  const topState = r.state || Object.keys(r.probabilities).reduce((a, b) => r.probabilities[a] >= r.probabilities[b] ? a : b);
  kids.push(h("div", { class: "bars" }, h("h3", { text: "How sure is the AI?" }),
    ["solid", "liquid", "gas"].map(s => bar(s, r.probabilities[s], s === topState))));

  if (r.properties) {
    const p = r.properties;
    kids.push(h("div", { class: "props-table" }, h("h3", { text: "What the AI looked at" }),
      h("dl", {},
        h("dt", { text: "Usual temperature" }), h("dd", { text: fmtTemp(p.temperature_c) }),
        h("dt", { text: "Melts at" }), h("dd", { text: fmtTemp(p.melting_point_c) }),
        h("dt", { text: "Boils at" }), h("dd", { text: fmtTemp(p.boiling_point_c) }),
        h("dt", { text: "Weight for its size (density)" }), h("dd", { text: `${p.density_g_cm3} g/cm³` }))));
    if (p.clues.length) kids.push(h("p", { class: "clues" }, h("strong", { text: "Clues: " }), cap(p.clues.join(", ")) + "."));
  }
  resultBox.className = `result ${r.state || "unsure"}`;
  resultBox.replaceChildren(...kids);
  resultBox.hidden = false;
}

function addHistory(r) {
  history.unshift({ name: cap(r.matched || r.input), state: r.state, emoji: r.emoji });
  const list = document.getElementById("history");
  list.replaceChildren(...history.slice(0, 8).map(x =>
    h("li", { class: x.state || "unsure" }, h("span", { "aria-hidden": "true", text: x.emoji }), ` ${x.name} → ${x.state || "not sure"}`)));
  document.getElementById("history-wrap").hidden = false;
}

async function ask(text) {
  const q = text.trim();
  if (!q) return;
  const btn = form.querySelector("button");
  btn.disabled = true;
  try {
    const r = await api("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ material: q }) });
    render(r); addHistory(r);
    if (r.state) { SFX.correct(); setTimeout(() => SFX.state(r.state), 330); } else SFX.wrong();
  } catch (e) {
    resultBox.className = "result unsure";
    resultBox.replaceChildren(h("p", { class: "error", text: e.message }));
    resultBox.hidden = false; SFX.wrong();
  } finally { btn.disabled = false; }
}

form.addEventListener("submit", e => { e.preventDefault(); ask(input.value); });

/* suggestions + example chips */
(async () => {
  try {
    const mats = await api("/api/materials");
    document.getElementById("material-list").replaceChildren(...mats.map(m => h("option", { value: m.name })));
    const pick = ["water", "stone", "air", "milk", "ice", "steam", "honey", "sand", "helium", "wood"];
    document.getElementById("chips").replaceChildren(...pick.map(n => {
      const m = mats.find(x => x.name === n);
      return h("button", { type: "button", class: "chip", "data-sfx": "", onclick: () => { input.value = n; ask(n); } }, (m && m.emoji ? m.emoji + " " : "") + n);
    }));
  } catch (e) { /* suggestions are optional */ }
})();

/* "How good is the AI?" - accuracy, precision, recall, F1 */
(async () => {
  const box = document.getElementById("metrics");
  try {
    const m = await api("/api/metrics");
    const pct = v => (v * 100).toFixed(1) + "%";
    const row = (label, mm) => h("tr", {}, h("th", { scope: "row", text: label }),
      h("td", { text: pct(mm.test.accuracy) }), h("td", { text: pct(mm.test.precision) }),
      h("td", { text: pct(mm.test.recall) }), h("td", { text: pct(mm.test.f1) }));
    box.replaceChildren(
      h("div", { class: "table-wrap" }, h("table", {},
        h("thead", {}, h("tr", {}, h("th", { text: "Model (scores on test data it never saw)" }),
          ["Accuracy", "Precision", "Recall", "F1"].map(t => h("th", { text: t })))),
        h("tbody", {}, row(`Property model · ${m.property_model.algorithm}`, m.property_model),
          row("Name model · " + m.name_model.algorithm.split(" (")[0], m.name_model)))),
      h("ul", { class: "legend" },
        h("li", {}, h("strong", { text: "Accuracy: " }), "how many answers were right."),
        h("li", {}, h("strong", { text: "Precision: " }), "when the AI says “liquid”, how often it is really a liquid."),
        h("li", {}, h("strong", { text: "Recall: " }), "of all the real liquids, how many the AI found."),
        h("li", {}, h("strong", { text: "F1: " }), "one score that balances precision and recall.")),
      h("p", { class: "note", text: "Precision, recall and F1 are averaged over solid, liquid and gas (macro average)." }));
  } catch (e) { box.replaceChildren(h("p", { class: "error", text: e.message })); }
})();
