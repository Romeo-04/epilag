// Multi-page build: each page in site/ becomes the same path in ../docs (served by GitHub Pages at /epilag/).
// docs/ also holds files Vite does not own (open data, film, deck, screenshots), so the build never empties it;
// scripts/clean-build.mjs clears only the hashed bundles in docs/assets/build/ first.
import { createHash } from "node:crypto";
import { createReadStream, existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig } from "vite";

const here = import.meta.dirname;

// The open data (docs/data/*.csv|json) is written by the Python pipeline straight into docs/, not into
// site/public. In dev, serve it from there so the landing page and the data links work as on the live site.
const docsData = {
  name: "docs-data",
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      // data/index.html is a Vite page (site/data/index.html), so only the data files are served from docs/
      const m = /^\/epilag\/data\/([\w.-]+\.(?:csv|json|md|xml|ics))$/.exec(req.url.split("?")[0]);
      const file = m && resolve(here, "../docs/data", m[1]);
      if (!file || !existsSync(file) || existsSync(resolve(here, "public/data", m[1]))) return next();
      const type = { json: "application/json", csv: "text/csv", xml: "application/rss+xml", ics: "text/calendar" }[file.split(".").pop()];
      res.setHeader("Content-Type", type || "text/plain");
      createReadStream(file).pipe(res);
    });
  },
};

// The offline app: after the build, write docs/sw.js from src/sw.js with the files to save on first visit: the
// dashboard page, every bundle it can load (its own and its lazy views), and the data, map grids, sprites, textures
// and icons it fetches. VERSION changes whenever any of those change, so the old saved copy is replaced.
const serviceWorker = {
  name: "service-worker",
  apply: "build",
  writeBundle(options, bundle) {
    const chunks = Object.values(bundle);
    const byName = new Map(chunks.map((c) => [c.fileName, c]));
    const files = new Set(["web/", "manifest.webmanifest", "favicon.svg"]);
    const visit = (name) => {
      const c = byName.get(name);
      if (!c || files.has(name)) return;
      files.add(name);
      if (c.type !== "chunk") return;
      [...c.imports, ...c.dynamicImports].forEach(visit);
      [...(c.viteMetadata?.importedCss || []), ...(c.viteMetadata?.importedAssets || [])].forEach((f) => files.add(f));
    };
    chunks.filter((c) => c.type === "chunk" && c.isEntry && c.name === "web").forEach((c) => visit(c.fileName));
    for (const dir of ["web/data", "geo", "sprites", "textures", "icons"]) {
      for (const f of readdirSync(resolve(here, "public", dir))) if (!f.startsWith(".")) files.add(`${dir}/${f}`);
    }
    const list = [...files].sort();
    const hash = createHash("sha256");
    for (const f of list) {
      const path = resolve(options.dir, f === "web/" ? "web/index.html" : f);
      hash.update(f).update(existsSync(path) ? readFileSync(path) : "");
    }
    const sw = readFileSync(resolve(here, "src/sw.js"), "utf8")
      .replace("__VERSION__", hash.digest("hex").slice(0, 12)).replace("__PRECACHE__", JSON.stringify(list));
    writeFileSync(resolve(options.dir, "sw.js"), sw);
  },
};

// The site's pages (Vite entry points).
const PAGES = {
  index: "index.html",
  web: "web/index.html",
  drill: "drill/index.html",
  methodology: "methodology.html",
  research: "research.html",
  data: "data/index.html",
};

export default defineConfig({
  root: here,
  base: "/epilag/",
  publicDir: "public",
  plugins: [docsData, serviceWorker],
  build: {
    outDir: resolve(here, "../docs"),
    emptyOutDir: false,
    assetsDir: "assets/build",
    // three.js is one lazy chunk (~190 kB gzip) loaded only by pages with a 3D map
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      input: Object.fromEntries(Object.entries(PAGES).map(([name, file]) => [name, resolve(here, file)])),
    },
  },
});
