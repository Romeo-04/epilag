// Dengue Drill rules and scoring, the same as scripts/drill_data.py (tests/test_drill_rules.py checks the two agree).
// A team (one "kit", PHP 500,000) covers kit.pesos / kit.per_person people, up to kit.max_share of a province, and
// prevents a share (kit.effect: low, central, high) of the cases reported 2 to 9 weeks after its turn, since people
// already infected still fall sick. Pure functions of the data (window.DRILL shape: weeks, turns, kit, regions).

export function rules(D) {
  const K = D.kit, WEEKS = D.weeks, TURNS = D.turns, PEOPLE = K.pesos / K.per_person;
  const idx = (w) => WEEKS.indexOf(w), FIRST = idx(TURNS[0]);

  /** The season's peak week (index), if it rose above the epidemic line (an outbreak); else null. */
  function peak(p) {
    let best = null;
    for (let i = FIRST; i < WEEKS.length; i++) if (p.cases[i] != null && (best == null || p.cases[i] > p.cases[best])) best = i;
    return best != null && p.epi[best] != null && p.cases[best] > p.epi[best] ? best : null;
  }

  /** Score a plan {provinceIndex: {turnIndex: teams}}: cases averted (lo/mid/hi) and how well-timed the teams were. */
  function score(planned, reg) {
    let lo = 0, mid = 0, hi = 0, onTime = 0, late = 0, noOutbreak = 0, used = 0;
    reg.provinces.forEach((p, k) => {
      const pk = peak(p);
      Object.entries(planned[k] || {}).forEach(([t, n]) => {
        if (!n) return;
        const i = idx(TURNS[t]);
        const window = p.cases.slice(i + 2, i + 10).reduce((s, c) => s + (c || 0), 0); // people already infected still fall sick
        const share = Math.min((n * PEOPLE) / p.pop, K.max_share);
        lo += window * share * K.effect[0]; mid += window * share * K.effect[1]; hi += window * share * K.effect[2];
        used += n;
        if (pk == null) noOutbreak += n; else if (i <= pk - 4) onTime += n; else late += n;
      });
    });
    return { lo, mid, hi, onTime, late, noOutbreak, used };
  }

  /** The plan a computer player makes: two teams a turn, by a fixed rule ("epilag" alerts or "react" to reports). */
  function autoplan(rule, reg) {
    const planned = {};
    let left = K.kits;
    TURNS.forEach((tw, t) => {
      const i = idx(tw);
      let picks = reg.provinces.map((p, k) => ({ p, k }));
      if (rule === "epilag") picks = picks.filter(({ p }) => p.fc[tw] && ["watch", "warning"].includes(p.fc[tw][0])).sort((a, b) => b.p.fc[tw][2] / b.p.pop - a.p.fc[tw][2] / a.p.pop);
      else picks = picks.filter(({ p }) => p.cases[i] != null && p.epi[i] != null && p.cases[i] > p.epi[i]);
      picks.slice(0, Math.min(2, left)).forEach(({ k }) => { (planned[k] ||= {})[t] = 1; left--; });
    });
    return planned;
  }
  const autopilot = (rule, reg) => score(autoplan(rule, reg), reg);
  /** Reported cases over the season, from the first turn on. */
  const total = (p) => p.cases.slice(FIRST).reduce((a, c) => a + (c || 0), 0);

  /** Grade against the better of the two computer players. */
  function gradeOf(mid, reg) {
    const best = Math.max(1, autopilot("epilag", reg).mid, autopilot("react", reg).mid), r = mid / best;
    return r >= 1.1 ? "S" : r >= 0.85 ? "A" : r >= 0.65 ? "B" : r >= 0.4 ? "C" : "D";
  }

  /** Across all regions: where the EpiLag bot averted more, about the same (within 5%), or fewer than the reactive bot. */
  function honest() {
    let better = 0, tie = 0, worse = 0;
    D.regions.forEach((r) => {
      const x = autopilot("epilag", r).mid, y = autopilot("react", r).mid;
      if (Math.abs(x - y) <= 0.05 * Math.max(x, y, 1)) tie++; else if (x > y) better++; else worse++;
    });
    return { better, tie, worse };
  }

  const teamsIn = (plan, k) => Object.values(plan[k] || {}).reduce((a, b) => a + b, 0);
  /** Would one more team in province k pass the max coverage? */
  const capped = (plan, k, reg) => ((teamsIn(plan, k) + 1) * PEOPLE) / reg.provinces[k].pop > K.max_share + 1e-9;

  /** Cases this week against the epidemic line, as a colour (the old board's heat ramp). */
  function heat(p, i) {
    const c = p.cases[i], e = p.epi[i];
    if (c == null || !e) return "#12352A";
    const r = c / e, stops = [[0, [18, 53, 42]], [0.5, [46, 107, 63]], [1, [242, 179, 61]], [1.6, [238, 138, 42]], [2.4, [229, 72, 60]]];
    let a = stops[0], b = stops.at(-1);
    for (let j = 1; j < stops.length; j++) if (r <= stops[j][0]) { a = stops[j - 1]; b = stops[j]; break; }
    const k = r >= b[0] ? 1 : Math.max(0, (r - a[0]) / (b[0] - a[0] || 1));
    return `rgb(${a[1].map((v, n) => Math.round(v + (b[1][n] - v) * k)).join(",")})`;
  }

  /** Region-wide outbreak pressure this week: reported cases over the sum of epidemic lines. */
  function pressure(reg, i) {
    const pr = reg.provinces.reduce((s, p) => s + (p.cases[i] || 0), 0) / Math.max(1, reg.provinces.reduce((s, p) => s + (p.epi[i] || 0), 0));
    return { value: pr, level: pr < 0.6 ? "low" : pr < 1 ? "rising" : pr < 1.6 ? "high" : "critical" };
  }

  return { K, WEEKS, TURNS, PEOPLE, FIRST, idx, peak, score, autoplan, autopilot, gradeOf, honest, teamsIn, capped, heat, pressure, total };
}
