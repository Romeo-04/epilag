// Remove the previous build's hashed bundles so old files do not pile up in docs/. Nothing else in docs/ is touched.
import { rmSync } from "node:fs";
import { resolve } from "node:path";

const dir = resolve(import.meta.dirname, "../../docs/assets/build");
rmSync(dir, { recursive: true, force: true });
console.log("cleaned", dir);
