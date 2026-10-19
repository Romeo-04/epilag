// Data for the web app: JSON from scripts/build_web.py in docs/web/data/, fetched lazily and cached in memory.
import { defaultOrigin, latestForecast, replayForecast, replayOrigins, rowsOf } from "./logic.js";

const BASE = `${import.meta.env.BASE_URL}web/data/`;
const cache = new Map();
const json = (name) => {
  if (!cache.has(name)) cache.set(name, fetch(BASE + name).then((r) => { if (!r.ok) throw new Error(`${name}: ${r.status}`); return r.json(); }));
  return cache.get(name);
};

export const meta = () => json("meta.json");
export const reports = () => json("reports.json");
export const barangays = () => json("qc_barangays.json");

/** One table of a panel as row objects ("forecast", "thresholds", "history", "backtest", "drivers"). */
const tables = new Map();
export function table(panel, name) {
  const key = `${panel}_${name}`;
  if (!tables.has(key)) {
    tables.set(key, Promise.all([meta(), json(`${key}.json`)]).then(([m, t]) => rowsOf(t, m.panels[panel].units)));
  }
  return tables.get(key);
}

/** Replay weeks of a panel (days), and the default one. */
export async function origins(panel) {
  const o = replayOrigins(await table(panel, "backtest"));
  return { list: o, fallback: defaultOrigin(o) };
}

/**
 * The forecast rows for the current state: all horizons (`fc`) and the chosen one (`fcH`).
 * Latest uses the published forecast; replay re-creates what the models said at a past week.
 */
const forecasts = new Map();
export async function forecastFor({ panel, mode, origin }) {
  const key = `${panel}|${mode}|${mode === "replay" ? origin : ""}`;
  if (!forecasts.has(key)) {
    forecasts.set(key, (async () => {
      const m = (await meta()).panels[panel], forecast = await table(panel, "forecast");
      if (mode !== "replay") return latestForecast({ forecast, meta: m });
      const [backtest, history] = await Promise.all([table(panel, "backtest"), table(panel, "history")]);
      return replayForecast({ backtest, history, forecast, meta: m }, origin);
    })());
  }
  return forecasts.get(key);
}
