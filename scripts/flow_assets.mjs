// Copy the site's pixel icons and sprites into docs/reel/flow/assets.js, so the flow video's page is a plain
// script (it opens from file:// without a server). Run with: node scripts/flow_assets.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { ICONS, LOGO } from "../site/src/lib/icons.js";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const sprite = (name) => JSON.parse(readFileSync(join(root, "site/public/sprites", `${name}.json`), "utf8"));
const out = { icons: { ...ICONS, logo: LOGO }, sprites: { props: sprite("props"), frog: sprite("frog"), mosquito: sprite("mosquito") } };
writeFileSync(join(root, "docs/reel/flow/assets.js"), `window.ASSETS = ${JSON.stringify(out)};\n`);
console.log("saved docs/reel/flow/assets.js");
