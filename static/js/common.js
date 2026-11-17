/* Shared helpers: sounds (made with the browser's Web Audio, no files needed) + fetch + DOM */
const SFX = (() => {
  let ctx = null;
  let on = true;
  try { on = localStorage.getItem("sound") !== "off"; } catch (e) {}

  const audio = () => {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
    }
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  };

  function tone(freq, start, dur, type = "sine", vol = 0.18, slideTo = null) {
    const c = audio(); if (!c || !on) return;
    const t0 = c.currentTime + start;
    const osc = c.createOscillator(), gain = c.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, t0);
    if (slideTo) osc.frequency.exponentialRampToValueAtTime(slideTo, t0 + dur);
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(vol, t0 + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    osc.connect(gain).connect(c.destination);
    osc.start(t0); osc.stop(t0 + dur + 0.05);
  }

  function noise(start, dur, freqFrom, freqTo, vol = 0.25) {
    const c = audio(); if (!c || !on) return;
    const t0 = c.currentTime + start;
    const buf = c.createBuffer(1, Math.floor(c.sampleRate * dur), c.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    const src = c.createBufferSource(); src.buffer = buf;
    const filter = c.createBiquadFilter(); filter.type = "bandpass"; filter.Q.value = 0.8;
    filter.frequency.setValueAtTime(freqFrom, t0);
    filter.frequency.exponentialRampToValueAtTime(freqTo, t0 + dur);
    const gain = c.createGain();
    gain.gain.setValueAtTime(0.0001, t0);
    gain.gain.exponentialRampToValueAtTime(vol, t0 + dur * 0.4);
    gain.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    src.connect(filter).connect(gain).connect(c.destination);
    src.start(t0);
  }

  return {
    get on() { return on; },
    toggle() {
      on = !on;
      try { localStorage.setItem("sound", on ? "on" : "off"); } catch (e) {}
      if (on) this.click();
      return on;
    },
    click()   { tone(660, 0, 0.08, "triangle", 0.12); },
    correct() { [523, 659, 784].forEach((f, i) => tone(f, i * 0.09, 0.22, "triangle", 0.16)); },
    wrong()   { tone(220, 0, 0.28, "sawtooth", 0.09, 130); },
    win()     { [523, 659, 784, 1047, 784, 1047, 1319].forEach((f, i) => tone(f, i * 0.12, 0.28, "triangle", 0.16)); },
    // one sound per state: knock / water drop / whoosh
    solid()   { tone(150, 0, 0.18, "sine", 0.35, 60); tone(110, 0.12, 0.18, "sine", 0.3, 50); },
    liquid()  { tone(500, 0, 0.14, "sine", 0.2, 1000); tone(700, 0.12, 0.14, "sine", 0.16, 1300); },
    gas()     { noise(0, 0.7, 400, 3000, 0.3); },
    state(s)  { if (this[s]) this[s](); },
  };
})();

/* fetch JSON helper */
async function api(path, options) {
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong. Please try again.");
  return data;
}

/* tiny element builder: h("div", {class:"x"}, "text", childNode) - text is always escaped */
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v == null) continue;
    if (k === "text") el.textContent = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  kids.flat().forEach(k => el.append(k instanceof Node ? k : document.createTextNode(k)));
  return el;
}

const cap = s => s.charAt(0).toUpperCase() + s.slice(1);

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("sound-toggle");
  const paint = () => {
    btn.textContent = SFX.on ? "🔊" : "🔇";
    btn.setAttribute("aria-pressed", String(SFX.on));
    btn.setAttribute("aria-label", SFX.on ? "Sounds on" : "Sounds off");
  };
  paint();
  btn.addEventListener("click", () => { SFX.toggle(); paint(); });
  document.addEventListener("click", e => {
    const t = e.target.closest("[data-sfx]");
    if (t) SFX.click();
  });
});
