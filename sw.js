/* ═══════════ 霞客经纬 · Service Worker ═══════════
   三级缓存（承方舆/水道经纬）：SHELL 外壳预存 · TEXTS 全文懒存（首查后整本书离线）
                       TILES 瓦片限额存（stale-while-revalidate）
   VERSION 与 index.html 的 ?v 同步递增（当前 v1）。 */

const VERSION = "v13";
const SHELL = `xxk-${VERSION}-shell`;
const TEXTS = `xxk-${VERSION}-texts`;
const TILES = `xxk-${VERSION}-tiles`;
const TILE_CAP = 1200;

const SHELL_FILES = [
  "./", "./index.html", "./manifest.json",
  "./css/main.css?v=13",
  "./vendor/leaflet.js", "./vendor/leaflet.css",
  "./data/trip_data.js?v=13", "./data/stats.js?v=13", "./data/xref_fy.js?v=13",
  "./icons/icon-192.png", "./icons/icon-512.png",
  "./js/config.js?v=13", "./js/map.js?v=13", "./js/tripnav.js?v=13",
  "./js/reader.js?v=13", "./js/search.js?v=13",
  "./js/stats.js?v=13", "./js/bookmarks.js?v=13", "./js/xref.js?v=13",
  "./js/app.js?v=13", "./js/ftworker.js",
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(SHELL).then(c => c.addAll(SHELL_FILES)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => !k.endsWith(VERSION)).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET") return;

  // 瓦片：限额 stale-while-revalidate
  if (/arcgisonline\.com/.test(url.hostname)) {
    e.respondWith(
      caches.open(TILES).then(async c => {
        const hit = await c.match(e.request);
        const net = fetch(e.request).then(r => {
          c.put(e.request, r.clone());
          c.keys().then(ks => { if (ks.length > TILE_CAP) caches.delete(TILES); });
          return r;
        }).catch(() => hit);
        return hit || net;
      })
    );
    return;
  }

  // 全文（懒加载文本）：首查后存 TEXTS
  if (url.pathname.includes("/data/text/") || url.pathname.includes("/data/read/")) {
    e.respondWith(
      caches.open(TEXTS).then(async c => {
        const hit = await c.match(e.request);
        if (hit) return hit;
        const r = await fetch(e.request);
        if (r.ok) c.put(e.request, r.clone());
        return r;
      })
    );
    return;
  }

  // 同源其余：网络优先（页面与数据永不为旧）；仅版本化资源（?v=）随取随存
  if (url.origin === location.origin) {
    const versioned = url.search.includes("v=");
    e.respondWith(
      fetch(e.request).then(r => {
        if (versioned && r.ok) {
          const c = r.clone();
          caches.open(SHELL).then(sc => sc.put(e.request, c));
        }
        return r;
      }).catch(() =>
        caches.match(e.request).then(hit => hit || caches.match("./"))
      )
    );
  }
});
