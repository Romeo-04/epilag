// Multi-page build: each page in site/ becomes the same path in ../docs (served by GitHub Pages at /epilag/).
// docs/ also holds files Vite does not own (open data, film, deck, screenshots), so the build never empties it;
// scripts/clean-build.mjs clears only the hashed bundles in docs/assets/build/ first.
import { resolve } from "node:path";
import { defineConfig } from "vite";

const here = import.meta.dirname;

// Pages move here one by one as they are rebuilt (REDESIGN_PLAN.md, section 14).
const PAGES = {
  index: "index.html",
  kit: "kit.html",
};

export default defineConfig({
  root: here,
  base: "/epilag/",
  publicDir: "public",
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
