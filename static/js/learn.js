/* Page 1: lesson content from /api/info + live particle boxes */
const COLORS = { solid: "#F5A700", liquid: "#1768C9", gas: "#08806B" };
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

class Sim {
  constructor(canvas, mode, count = 36, radius = 7) {
    this.c = canvas; this.ctx = canvas.getContext("2d");
    this.mode = mode; this.n = count; this.r = radius; this.visible = true;
    this.resize();
    this.reset();
  }
  resize() {
    const dpr = window.devicePixelRatio || 1;
    const rect = this.c.getBoundingClientRect();
    this.W = Math.max(rect.width, 120); this.H = Math.max(rect.height, 120);
    this.c.width = this.W * dpr; this.c.height = this.H * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.layoutHomes();
  }
  layoutHomes() {   // lattice positions used by solids
    const cols = Math.ceil(Math.sqrt(this.n * 1.5)), rows = Math.ceil(this.n / cols);
    const gap = this.r * 2.5, x0 = (this.W - (cols - 1) * gap) / 2, y0 = this.H - 14 - this.r - (rows - 1) * gap;
    this.homes = Array.from({ length: this.n }, (_, i) => ({ x: x0 + (i % cols) * gap, y: y0 + Math.floor(i / cols) * gap }));
  }
  reset() {
    this.p = this.homes.map(h => ({ x: h.x, y: h.y, vx: 0, vy: 0 }));
    if (this.mode === "gas") this.kick(2.4);
  }
  kick(speed) {
    this.p.forEach(q => { const a = Math.random() * 6.283; q.vx = Math.cos(a) * speed; q.vy = Math.sin(a) * speed; });
  }
  setMode(m) {
    if (m === this.mode) return;
    this.mode = m;
    if (m === "gas") this.kick(2.4);
    if (m === "liquid") this.p.forEach(q => { q.vx *= 0.3; q.vy *= 0.3; });
  }
  step() {
    const { p, r, W, H } = this;
    if (this.mode === "solid") {
      p.forEach((q, i) => {
        const h = this.homes[i];
        q.x += (h.x - q.x) * 0.15 + (Math.random() - 0.5) * 1.1;
        q.y += (h.y - q.y) * 0.15 + (Math.random() - 0.5) * 1.1;
        q.vx = q.vy = 0;
      });
      return;
    }
    const liquid = this.mode === "liquid";
    for (const q of p) {
      if (liquid) {
        q.vy += 0.16; q.vx += (Math.random() - 0.5) * 0.5; q.vy += (Math.random() - 0.5) * 0.3;
        q.vx *= 0.97; q.vy *= 0.97;
      } else {
        const sp = Math.hypot(q.vx, q.vy) || 1;      // keep gas speed steady
        const k = 1 + (2.4 - sp) * 0.05;
        q.vx *= k; q.vy *= k;
      }
      q.x += q.vx; q.y += q.vy;
      if (q.x < r) { q.x = r; q.vx = Math.abs(q.vx); }
      if (q.x > W - r) { q.x = W - r; q.vx = -Math.abs(q.vx); }
      if (q.y < r) { q.y = r; q.vy = Math.abs(q.vy); }
      if (q.y > H - r) { q.y = H - r; q.vy = -Math.abs(q.vy) * (liquid ? 0.25 : 1); }
    }
    if (liquid) {                                     // particles push each other apart
      for (let i = 0; i < p.length; i++) for (let j = i + 1; j < p.length; j++) {
        const dx = p[j].x - p[i].x, dy = p[j].y - p[i].y, d = Math.hypot(dx, dy), min = r * 2;
        if (d > 0 && d < min) {
          const push = (min - d) / 2, nx = dx / d, ny = dy / d;
          p[i].x -= nx * push; p[i].y -= ny * push; p[j].x += nx * push; p[j].y += ny * push;
        }
      }
    }
  }
  draw() {
    const { ctx, W, H } = this;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = COLORS[this.mode];
    for (const q of this.p) { ctx.beginPath(); ctx.arc(q.x, q.y, this.r, 0, 6.283); ctx.fill(); }
  }
}

const sims = [];
function loop() {
  for (const s of sims) if (s.visible) { s.step(); s.draw(); }
  requestAnimationFrame(loop);
}
function addSim(canvas, mode, count, radius) {
  const s = new Sim(canvas, mode, count, radius);
  sims.push(s);
  new IntersectionObserver(e => { s.visible = e[0].isIntersecting; }).observe(canvas);
  if (reduceMotion) { for (let i = 0; i < 40; i++) s.step(); s.draw(); s.visible = false; }
  return s;
}

/* ---------- hero: heat it up ---------- */
const heat = document.getElementById("heat");
const slider = document.getElementById("heat-slider");
const heroSim = addSim(document.getElementById("hero-canvas"), "liquid", 60, 9);
let heroState = "liquid";
function stateAt(t) { return t < 0 ? "solid" : t < 100 ? "liquid" : "gas"; }
function names(t) { return t < 0 ? "Ice" : t < 100 ? "Water" : "Steam"; }
function updateHeat(playSound) {
  const t = Number(slider.value), s = stateAt(t);
  document.getElementById("heat-temp").textContent = t;
  document.getElementById("heat-name").textContent = names(t);
  document.getElementById("heat-state").textContent = s;
  slider.setAttribute("aria-valuetext", `${t} degrees, ${s}`);
  if (s !== heroState) {
    heroState = s; heat.dataset.state = s; heroSim.setMode(s);
    if (reduceMotion) { for (let i = 0; i < 60; i++) heroSim.step(); heroSim.draw(); }
    if (playSound) SFX.state(s);
  }
}
slider.addEventListener("input", () => updateHeat(true));
updateHeat(false);

/* ---------- lesson from the API ---------- */
async function loadLesson() {
  const box = document.getElementById("learn-content");
  let info;
  try { info = await api("/api/info"); }
  catch (e) { box.replaceChildren(h("p", { class: "error", text: e.message })); return; }

  const parts = [];
  parts.push(h("section", { class: "block intro" },
    h("h2", { text: info.definition.heading }),
    h("p", { class: "lead", text: info.definition.text })));

  for (const st of info.states) {
    const canvas = h("canvas", { class: "state-canvas", "aria-label": `${st.name} particles`, role: "img" });
    const chips = st.examples.map(([emoji, name]) => h("li", {}, h("span", { "aria-hidden": "true", text: emoji }), " ", name));
    parts.push(h("section", { class: `block state ${st.id}`, id: st.id },
      h("div", { class: "state-text" },
        h("h2", {}, st.emoji + " ", st.name),
        h("p", { class: "lead", text: st.summary }),
        h("p", { text: st.explain }),
        h("ul", { class: "props" }, st.properties.map(p => h("li", { text: p }))),
        h("h3", { text: "Examples" }),
        h("ul", { class: "examples" }, chips),
        h("p", { class: "try" }, h("strong", { text: "Try it: " }), st.try_it)),
      h("div", { class: "state-visual" }, canvas)));
  }

  parts.push(h("section", { class: "block changes" },
    h("h2", { text: "How matter changes" }),
    h("ul", { class: "change-list" }, info.changes.map(([e, title, text]) =>
      h("li", {}, h("span", { class: "ci", "aria-hidden": "true", text: e }),
        h("div", {}, h("strong", { text: title }), h("p", { text: text })))))));

  parts.push(h("section", { class: "block cta" },
    h("h2", { text: "Ready to test yourself?" }),
    h("div", { class: "cta-row" },
      h("a", { class: "btn", href: "/predict", "data-sfx": "" }, "Ask the AI"),
      h("a", { class: "btn ghost", href: "/quiz", "data-sfx": "" }, "Take the quiz"))));

  box.replaceChildren(...parts);
  box.querySelectorAll(".state-canvas").forEach((cv, i) => addSim(cv, info.states[i].id, 36, 8));
}
window.addEventListener("resize", () => sims.forEach(s => { s.resize(); }));
loadLesson();
if (!reduceMotion) requestAnimationFrame(loop);
