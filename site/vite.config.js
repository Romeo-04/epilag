// Multi-page build: each page in site/ becomes the same path in ../docs (served by GitHub Pages at /epilag/).
// docs/ also holds files Vite does not own (open data, film, deck, screenshots), so the build never empties it;
// scripts/clean-build.mjs clears only the hashed bundles in docs/assets/build/ first.
import { createReadStream, existsSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig } from "vite";

const here = import.meta.dirname;

// The open data (docs/data/*.csv|json) is written by the Python pipeline straight into docs/, not into
// site/public. In dev, serve it from there so the landing page and the data links work as on the live site.
const docsData = {
  name: "docs-data",
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      const m = /^\/epilag\/data\/([\w.-]+)$/.exec(req.url.split("?")[0]);
      const file = m && resolve(here, "../docs/data", m[1]);
      if (!file || !existsSync(file) || existsSync(resolve(here, "public/data", m[1]))) return next();
      res.setHeader("Content-Type", file.endsWith(".json") ? "application/json" : file.endsWith(".csv") ? "text/csv" : "text/plain");
      createReadStream(file).pipe(res);
    });
  },
};

// Pages move here one by one as they are rebuilt (REDESIGN_PLAN.md, section 14).
const PAGES = {
  index: "index.html",
  kit: "kit.html",
  web: "web/index.html",
  drill: "drill/index.html",
};

export default defineConfig({
  root: here,
  base: "/epilag/",
  publicDir: "public",
  plugins: [docsData],
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
