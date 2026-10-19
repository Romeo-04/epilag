// Open data page: static content in data/index.html (file links are the files the Python export writes to docs/data/);
// this adds pixel icons and scroll reveals.
import "../css/tokens.css";
import "../css/base.css";
import "../css/surfaces.css";
import "../css/components.css";
import "./pages.css";
import { hydrateIcons } from "../lib/icons.js";
import { reveal } from "../lib/motion.js";

hydrateIcons();
reveal("[data-reveal]");
