// Dengue Drill audio, all synthesised in the browser (no audio files): sound effects, rain on the roof, and a looping
// chiptune with a piece for each part of the game (title, round 1, round 2, reports). Three buses (music, effects, rain) feed one master,
// and every level comes from the player's settings (S: sound, music, musicVol, sfx, sfxVol, rain, rainVol; volumes 0-100).

const midi = (n) => 440 * 2 ** ((n - 69) / 12);
// Four pieces, one per part of the game, all in minor keys: lively on top (a driving bass, drums, a running
// arpeggio) with a falling, mournful tune, because the season is a tragedy in motion. Each is eight bars: `bars` is
// the chord of each bar as MIDI notes (root first) and `lead` the tune over it as [sixteenth step, MIDI note, length
// in steps]. `drive` is the full band (syncopated bass, kick, snare, hats); without it the piece is a slow lament.
const TRACKS = {
  // title, briefing, choosing a model: the theme. A minor over the falling Am-G-F-E bass line
  title: { bpm: 120, wave: "square", drive: true, snare: false,
    bars: [[57, 60, 64], [55, 59, 62], [53, 57, 60], [52, 56, 59], [57, 60, 64], [55, 59, 62], [53, 57, 60], [52, 56, 59]],
    lead: [
      [[0, 81, 3], [3, 79, 1], [4, 76, 4], [8, 72, 2], [10, 76, 2], [12, 81, 4]], [[0, 79, 3], [3, 77, 1], [4, 74, 4], [8, 71, 2], [10, 74, 2], [12, 79, 4]],
      [[0, 77, 3], [3, 76, 1], [4, 72, 4], [8, 69, 2], [10, 72, 2], [12, 77, 4]], [[0, 76, 4], [4, 80, 4], [8, 83, 4], [12, 80, 2], [14, 76, 2]],
      [[0, 84, 6], [6, 83, 2], [8, 81, 4], [12, 76, 4]], [[0, 83, 6], [6, 81, 2], [8, 79, 4], [12, 74, 4]],
      [[0, 81, 4], [4, 77, 2], [6, 76, 2], [8, 77, 4], [12, 72, 4]], [[0, 76, 2], [2, 77, 2], [4, 76, 4], [8, 80, 2], [10, 83, 2], [12, 88, 4]],
    ] },
  // round 1, no forecasts: D minor, pressing forward while the tune keeps falling back
  r1: { bpm: 126, wave: "square", drive: true, snare: true,
    bars: [[50, 53, 57], [48, 52, 55], [46, 50, 53], [45, 49, 52], [50, 53, 57], [55, 58, 62], [46, 50, 53], [45, 49, 52]],
    lead: [
      [[0, 74, 2], [2, 77, 2], [4, 81, 4], [8, 82, 2], [10, 81, 2], [12, 77, 4]], [[0, 76, 2], [2, 79, 2], [4, 84, 4], [8, 82, 2], [10, 79, 2], [12, 76, 4]],
      [[0, 77, 4], [4, 74, 2], [6, 77, 2], [8, 82, 4], [12, 81, 2], [14, 79, 2]], [[0, 81, 6], [6, 79, 2], [8, 76, 4], [12, 73, 4]],
      [[0, 86, 4], [4, 84, 2], [6, 82, 2], [8, 81, 4], [12, 77, 4]], [[0, 82, 4], [4, 79, 2], [6, 82, 2], [8, 86, 4], [12, 82, 4]],
      [[0, 81, 2], [2, 82, 2], [4, 81, 2], [6, 77, 2], [8, 74, 4], [12, 77, 4]], [[0, 76, 4], [4, 73, 4], [8, 76, 2], [10, 79, 2], [12, 81, 4]],
    ] },
  // round 2, with forecasts: E minor and faster, fighting back with the same grief underneath
  r2: { bpm: 138, wave: "square", drive: true, snare: true,
    bars: [[52, 55, 59], [48, 52, 55], [50, 54, 57], [47, 51, 54], [52, 55, 59], [48, 52, 55], [45, 48, 52], [47, 51, 54]],
    lead: [
      [[0, 83, 2], [2, 88, 2], [4, 86, 2], [6, 83, 2], [8, 79, 4], [12, 83, 4]], [[0, 84, 2], [2, 88, 2], [4, 84, 2], [6, 79, 2], [8, 76, 4], [12, 79, 4]],
      [[0, 81, 2], [2, 86, 2], [4, 90, 4], [8, 86, 2], [10, 81, 2], [12, 78, 4]], [[0, 83, 4], [4, 87, 4], [8, 90, 2], [10, 87, 2], [12, 83, 4]],
      [[0, 88, 6], [6, 86, 2], [8, 83, 2], [10, 79, 2], [12, 76, 4]], [[0, 79, 2], [2, 84, 2], [4, 88, 6], [10, 86, 2], [12, 84, 4]],
      [[0, 81, 2], [2, 84, 2], [4, 88, 4], [8, 84, 2], [10, 81, 2], [12, 76, 4]], [[0, 75, 2], [2, 78, 2], [4, 83, 4], [8, 87, 2], [10, 90, 2], [12, 83, 4]],
    ] },
  // reports and the debrief: a slow lament in D minor, no drums
  report: { bpm: 96, wave: "triangle", drive: false, snare: false,
    bars: [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55], [55, 58, 62], [50, 53, 57], [45, 49, 52], [50, 53, 57]],
    lead: [
      [[0, 81, 6], [6, 77, 2], [8, 74, 8]], [[0, 82, 6], [6, 77, 2], [8, 74, 8]], [[0, 81, 4], [4, 77, 4], [8, 72, 8]], [[0, 79, 6], [6, 76, 2], [8, 72, 4], [12, 76, 4]],
      [[0, 82, 4], [4, 79, 4], [8, 74, 8]], [[0, 81, 4], [4, 77, 4], [8, 74, 8]], [[0, 76, 6], [6, 73, 2], [8, 76, 4], [12, 79, 4]], [[0, 74, 12]],
    ] },
};

export function createAudio(S) {
  let ac = null, master, bus = {}, noise = null, rainLevel = 0, track = "title", tense = false, fade = null, echo = null, swap = 0, timer = 0, next = 0, step = 0;
  const on = (k) => S.sound && S[k];
  function ensure() {
    if (ac) return ac;
    ac = new (window.AudioContext || window.webkitAudioContext)();
    master = ac.createGain(); master.connect(ac.destination);
    const soft = ac.createBiquadFilter(); soft.type = "lowpass"; soft.frequency.value = 3200; // takes the edge off the square waves
    for (const k of ["music", "sfx", "rain"]) bus[k] = ac.createGain();
    fade = ac.createGain(); // dips to silence while one piece hands over to the next
    bus.music.connect(fade).connect(soft).connect(master);
    // an echo for the tune: it trails off behind itself
    echo = ac.createDelay(1); echo.delayTime.value = 0.3;
    const again = ac.createGain(), wet = ac.createGain(); again.gain.value = 0.3; wet.gain.value = 0.32;
    echo.connect(again).connect(echo); echo.connect(wet).connect(bus.music); bus.sfx.connect(master); bus.rain.connect(master);
    noise = ac.createBuffer(1, ac.sampleRate * 2, ac.sampleRate);
    const d = noise.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    // the rain: looping noise through a low-pass; its level follows the week's rain
    const src = ac.createBufferSource(), lp = ac.createBiquadFilter();
    src.buffer = noise; src.loop = true; lp.type = "lowpass"; lp.frequency.value = 1400;
    src.connect(lp).connect(bus.rain); src.start();
    levels(0);
    return ac;
  }
  /** Set every bus from the settings. */
  function levels(glide = 0.08) {
    if (!ac) return;
    const set = (g, v) => (glide ? g.gain.setTargetAtTime(v, ac.currentTime, glide) : g.gain.setValueAtTime(v, ac.currentTime));
    set(master, S.sound ? 1 : 0);
    set(bus.music, S.music ? S.musicVol / 100 : 0);
    set(bus.sfx, S.sfx ? S.sfxVol / 100 : 0);
    set(bus.rain, S.rain ? (S.rainVol / 100) * rainLevel * 0.07 : 0);
  }

  // ------------------------------------------------------------------ effects
  function tone(freq, dur, type = "sine", vol = 0.06, when = 0, slide = 0) {
    if (!on("sfx")) return;
    try {
      ensure();
      const t0 = ac.currentTime + when, o = ac.createOscillator(), g = ac.createGain();
      o.type = type; o.frequency.setValueAtTime(freq, t0); if (slide) o.frequency.exponentialRampToValueAtTime(slide, t0 + dur);
      g.gain.setValueAtTime(vol * 1.25, t0); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
      o.connect(g).connect(bus.sfx); o.start(t0); o.stop(t0 + dur);
    } catch { /* no audio available */ }
  }
  const sfx = {
    click: () => tone(880, 0.06, "square", 0.025),
    deploy: () => { tone(330, 0.09, "square", 0.04); tone(660, 0.14, "square", 0.04, 0.08); },
    recall: () => tone(440, 0.12, "square", 0.035, 0, 220),
    turn: () => { tone(120, 0.5, "sawtooth", 0.035, 0, 60); tone(300, 0.35, "sine", 0.03, 0.1, 900); },
    alarm: () => { tone(740, 0.12, "square", 0.04); tone(740, 0.12, "square", 0.04, 0.18); },
    grade: () => [523, 659, 784, 1047].forEach((f, i) => tone(f, 0.18, "triangle", 0.06, i * 0.11)),
    thunder: () => { tone(60, 1.2, "sawtooth", 0.05, 0.15, 30); tone(90, 0.8, "triangle", 0.04, 0.1, 40); },
  };

  // ------------------------------------------------------------------ music
  function voice(type, freq, t, dur, vol) {
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = type; o.frequency.value = freq;
    g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(vol, t + 0.012);
    g.gain.setValueAtTime(vol, t + dur * 0.55); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(bus.music); o.start(t); o.stop(t + dur + 0.03);
  }
  function hat(t, vol) {
    const s = ac.createBufferSource(), hp = ac.createBiquadFilter(), g = ac.createGain();
    s.buffer = noise; hp.type = "highpass"; hp.frequency.value = 6500;
    g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);
    s.connect(hp).connect(g).connect(bus.music); s.start(t, Math.random()); s.stop(t + 0.06);
  }
  function kick(t) {
    const o = ac.createOscillator(), g = ac.createGain();
    o.frequency.setValueAtTime(130, t); o.frequency.exponentialRampToValueAtTime(42, t + 0.12);
    g.gain.setValueAtTime(0.2, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.16);
    o.connect(g).connect(bus.music); o.start(t); o.stop(t + 0.18);
  }
  /** The tune's voice: a held note gets a slow vibrato after it settles, and every note feeds the echo. */
  function sing(type, freq, t, dur, vol) {
    const o = ac.createOscillator(), g = ac.createGain();
    o.type = type; o.frequency.value = freq;
    if (dur > 0.3) {
      const lfo = ac.createOscillator(), depth = ac.createGain();
      lfo.frequency.value = 5.6; depth.gain.setValueAtTime(0, t); depth.gain.linearRampToValueAtTime(freq * 0.007, t + 0.28);
      lfo.connect(depth).connect(o.frequency); lfo.start(t); lfo.stop(t + dur + 0.03);
    }
    g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(vol, t + 0.015);
    g.gain.setValueAtTime(vol, t + dur * 0.6); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(bus.music); g.connect(echo); o.start(t); o.stop(t + dur + 0.03);
  }
  function snare(t) {
    const s = ac.createBufferSource(), bp = ac.createBiquadFilter(), g = ac.createGain();
    s.buffer = noise; bp.type = "bandpass"; bp.frequency.value = 1900; bp.Q.value = 0.7;
    g.gain.setValueAtTime(0.11, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
    s.connect(bp).connect(g).connect(bus.music); s.start(t, Math.random()); s.stop(t + 0.14);
  }
  /** A mosquito's whine over one bar: a thin, high, wavering note that swells and fades. Heard when the region is in outbreak. */
  function whine(freq, t, dur) {
    const o = ac.createOscillator(), g = ac.createGain(), lfo = ac.createOscillator(), depth = ac.createGain();
    o.type = "sawtooth"; o.frequency.setValueAtTime(freq, t); o.frequency.linearRampToValueAtTime(freq * 1.04, t + dur);
    lfo.frequency.value = 17; depth.gain.value = freq * 0.018; lfo.connect(depth).connect(o.frequency);
    g.gain.setValueAtTime(0.0001, t); g.gain.linearRampToValueAtTime(0.013, t + dur * 0.5); g.gain.linearRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(bus.music); o.start(t); o.stop(t + dur + 0.02); lfo.start(t); lfo.stop(t + dur + 0.02);
  }
  /** One sixteenth of the current piece, scheduled at time t. With `tense` (the region is in outbreak) the bass runs
   *  in eighths, the kick doubles and a mosquito whines over each bar. */
  function play(n, t) {
    const T = TRACKS[track], STEP = 60 / T.bpm / 4, s = n % 16, bar = Math.floor(n / 16) % 8, chord = T.bars[bar], root = chord[0] - 12;
    if (T.drive) {
      // bass: a syncopated root-fifth-octave figure, or straight eighths when tense
      const figure = { 0: 0, 3: 0, 6: 7, 8: 0, 11: 12, 14: 7 };
      if (tense) { if (s % 2 === 0) voice("triangle", midi(root + (s % 4 ? 12 : 0)), t, STEP * 1.7, 0.12); }
      else if (s in figure) voice("triangle", midi(root + figure[s]), t, STEP * (s === 0 || s === 8 ? 2.6 : 1.8), 0.12);
      // the chord running in sixteenths, an octave up, quiet
      voice("square", midi(chord[[0, 1, 2, 1][s % 4]] + 12), t, STEP * 0.9, s % 4 ? 0.014 : 0.02);
      if (s === 0 || s === 8 || (tense && (s === 6 || s === 11))) kick(t);
      if (T.snare && (s === 4 || s === 12)) snare(t);
      if (s % 2) hat(t, s % 4 === 3 ? 0.035 : 0.022); else if (T.snare && s % 4 === 2) hat(t, 0.015);
      if (tense && s === 0) whine(midi(chord[2] + 24), t, STEP * 16);
    } else {
      // the lament: long bass notes and a slow broken chord
      if (s === 0 || s === 8) voice("triangle", midi(root), t, STEP * 7, 0.11);
      if (s % 2 === 0 && s % 8) voice("square", midi(chord[[0, 1, 2, 1][(s / 2) % 4]] + 12), t, STEP * 1.8, 0.018);
    }
    for (const [at, note, len] of T.lead[bar]) if (at === s) sing(T.wave, midi(note), t, STEP * len * 0.95, T.wave === "triangle" ? 0.075 : 0.036);
    return STEP;
  }
  function pump() {
    if (!ac || ac.state !== "running") return;
    if (next < ac.currentTime) next = ac.currentTime + 0.05; // after a pause, pick the loop up from now
    while (next < ac.currentTime + 0.15) next += play(step++, next);
  }
  /** Start or stop the scheduler to match the settings. */
  function music() {
    const want = on("music") && !!ac;
    if (want && !timer) timer = setInterval(pump, 30);
    if (!want && timer) { clearInterval(timer); timer = 0; }
  }

  // browsers only allow sound after the player's first press or key
  let touched = false;
  const wake = () => {
    if (!touched || !S.sound) return;
    try { ensure(); if (ac.state === "suspended" && !document.hidden) ac.resume(); music(); } catch { /* no audio available */ }
  };
  const unlock = () => { touched = true; wake(); };
  addEventListener("pointerdown", unlock); addEventListener("keydown", unlock);
  document.addEventListener("visibilitychange", () => { if (ac) (document.hidden ? ac.suspend() : S.sound && ac.resume()); });

  return {
    sfx,
    /** The week's rain, 0 to 1. */
    rain(level) { rainLevel = level; if (level && on("rain")) { try { ensure(); } catch { /* no audio available */ } } levels(0.6); },
    /** Change piece ("title", "r1", "r2", "report"): the old one fades out, the new one starts from its first bar. */
    setTrack(name) {
      if (!TRACKS[name] || name === track) return;
      track = name; tense = false;
      if (!ac) { step = 0; return; }
      clearTimeout(swap);
      fade.gain.setTargetAtTime(0, ac.currentTime, 0.07);
      clearInterval(timer); timer = 0; // nothing new is scheduled during the fade
      swap = setTimeout(() => { step = 0; next = 0; fade.gain.setTargetAtTime(1, ac.currentTime, 0.05); music(); }, 320);
    },
    /** The region is in outbreak: the current piece tightens. */
    setTense(on) { tense = !!on; },
    /** The settings changed: apply them. */
    apply() { wake(); levels(); music(); },
    /** For tests: the loudest sample across the output right now, 0 to 1. */
    probe() {
      if (!ac) return null;
      const an = ac.createAnalyser(); master.connect(an);
      return () => { const b = new Float32Array(an.fftSize); an.getFloatTimeDomainData(b); return Math.max(...b.map(Math.abs)); };
    },
    get track() { return `${track}${tense ? " (tense)" : ""}`; },
  };
}
