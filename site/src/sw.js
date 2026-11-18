// EpiLag-PH service worker: makes the dashboard work offline once it has been opened.
// Built by the "service-worker" plugin in vite.config.js, which fills in VERSION and PRECACHE (the app's pages,
// bundles, data, map grids, sprites and icons) and writes it to docs/sw.js.
//   - pages and forecast data: network first, so a connected user always gets this week's numbers; the saved copy
//     is used only when the network fails or takes longer than NET_TIMEOUT
//   - hashed bundles (assets/build/): cache first, they never change under the same name
//   - everything else on the site, and Google Fonts: the saved copy at once, refreshed in the background
// Video, range requests and other sites are left to the browser.
const VERSION = "__VERSION__";
const PRECACHE = __PRECACHE__;
const CACHE = `epilag-${VERSION}`;
const RUNTIME = "epilag-runtime";
const NET_TIMEOUT = 4000;
const SCOPE = new URL(self.registration.scope);

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(PRECACHE.map((p) => new Request(new URL(p, SCOPE), { cache: "reload" })))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k.startsWith("epilag-") && k !== CACHE && k !== RUNTIME).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

const put = async (name, req, res) => { if (res && res.ok && res.type !== "opaqueredirect") (await caches.open(name)).put(req, res.clone()); return res; };
const match = (req) => caches.match(req, { ignoreSearch: req.mode === "navigate" });

// After a failed or slow request, serve saved copies at once for a while instead of making every file wait out
// NET_TIMEOUT in turn (a page loads several data files one after another).
let slowUntil = 0;
const SLOW_FOR = 30000;

async function networkFirst(req) {
  const net = fetch(req).then((res) => { slowUntil = 0; return put(CACHE, req, res); });
  net.catch(() => { slowUntil = Date.now() + SLOW_FOR; });
  if (!self.navigator.onLine || Date.now() < slowUntil) {
    const saved = await match(req);
    if (saved) return saved; // the fetch above still refreshes the saved copy if the network comes back
  }
  const timer = new Promise((resolve) => setTimeout(resolve, NET_TIMEOUT));
  try {
    const res = await Promise.race([net, timer.then(() => null)]);
    if (res) return res;
    slowUntil = Date.now() + SLOW_FOR;
  } catch { /* offline: fall through to the saved copy */ }
  const saved = await match(req);
  if (saved) return saved;
  return net; // nothing saved: wait for the network (and its error)
}

async function cacheFirst(req) {
  return (await match(req)) || put(CACHE, req, await fetch(req));
}

async function staleWhileRevalidate(req) {
  const saved = await match(req);
  const net = fetch(req).then((res) => put(saved ? CACHE : RUNTIME, req, res)).catch(() => saved);
  return saved || net;
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || req.headers.has("range")) return;
  const url = new URL(req.url);
  const fonts = url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com";
  if (!fonts && (url.origin !== SCOPE.origin || !url.pathname.startsWith(SCOPE.pathname))) return;
  if (/\.(mp4|webm|mov|pdf|pptx)$/i.test(url.pathname)) return;
  if (req.mode === "navigate" || url.pathname.includes("/web/data/") || url.pathname.endsWith(".webmanifest")) e.respondWith(networkFirst(req));
  else if (url.pathname.includes("/assets/build/")) e.respondWith(cacheFirst(req));
  else e.respondWith(staleWhileRevalidate(req));
});
