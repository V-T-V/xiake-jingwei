/* ═══════════ 霞客经纬 · 全文检索 ═══════════
   Worker 子串检索（js/ftworker.js）· 篇文本懒加载（data/text/pNN.js）
   结果：篇名 + 上下文高亮 + 定位（开该程循读） */

const XKSEARCH = (() => {
  const input = document.getElementById("search");
  const box = document.getElementById("sresults");
  /* 路径基（tests/ 等子目录下打开时回退一级） */
  const DEPTH = location.pathname.split("/").filter(Boolean).length - 1;
  const BASE = "../".repeat(DEPTH);   // 页面距站根深度（index=0 · tests/=1）
  let worker = null, loaded = new Set(), lastResults = [];

  function init() {
    try {
      worker = new Worker(BASE + "js/ftworker.js");
      worker.onmessage = e => {
        lastResults = (e.data.hits || []).slice();
        render();
      };
    } catch (_e) { worker = null; }   // file:// 下 Worker 可能被拒——退化主线程
    let timer = null;
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(run, 260);
    });
    input.addEventListener("keydown", e => {
      if (e.key === "Escape") { box.style.display = "none"; input.blur(); }
    });
    document.addEventListener("click", e => {
      if (!e.target.closest("#searchwrap")) box.style.display = "none";
    });
  }

  function ensurePieces() {
    const n = XXK.trips.length;
    for (let i = 1; i <= n; i++) {
      if (loaded.has(i)) continue;
      loaded.add(i);
      const s = document.createElement("script");
      s.src = `${BASE}data/text/p${String(i).padStart(2, "0")}.js?v=7`;
      document.head.appendChild(s);
    }
  }

  function run() {
    const q = input.value.trim();
    if (q.length < 2) { box.style.display = "none"; return; }
    ensurePieces();
    lastResults = [];
    box.style.display = "block";
    const t0 = performance.now();
    const go = () => {
      if (input.value.trim() !== q) return;
      const n = window.XXKTEXT ? Object.keys(XXKTEXT).length : 0;
      if (n < XXK.trips.length) {
        box.innerHTML = `<div class="sr"><span class="where">检索</span>全书加载中 ${n}/${XXK.trips.length} ……</div>`;
        if (performance.now() - t0 > 15000) return;
        return requestAnimationFrame(go);
      }
      if (worker) {
        worker.postMessage({ q, texts: window.XXKTEXT, seq: 1 });
      } else {
        for (let v = 1; v <= XXK.trips.length; v++) lastResults.push(...mainHits(q, v));
        render();
      }
    };
    go();
  }

  function mainHits(q, v) {
    const t = window.XXKTEXT[v] || "";
    const hits = [];
    let i = t.indexOf(q);
    while (i >= 0 && hits.length < 4) {
      hits.push({ vol: v, ctx: t.slice(Math.max(0, i - 22), i + q.length + 30) });
      i = t.indexOf(q, i + q.length);
    }
    return hits;
  }

  function render() {
    const q = input.value.trim();
    const hits = lastResults.slice(0, 60);
    if (!hits.length) {
      box.innerHTML = `<div class="sr"><span class="where">无得</span>全书未见「${q}」</div>`;
      box.style.display = "block";
      return;
    }
    box.innerHTML = hits.map((h, i) => {
      const ctx = h.ctx.replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(q, `<mark>${q}</mark>`);
      const trip = XXK.trips[h.vol - 1];
      return `<div class="sr" data-i="${i}"><span class="where">${trip ? trip.title : "篇" + h.vol}</span>${ctx}</div>`;
    }).join("");
    box.style.display = "block";
    box.querySelectorAll(".sr").forEach(el =>
      el.addEventListener("click", () => locate(hits[+el.dataset.i], q)));
  }

  /* 定位：打开该篇循程阅读 */
  function locate(hit, q) {
    box.style.display = "none";
    const trip = XXK.trips[hit.vol - 1];
    if (trip) XKREADER.open(trip.id, 0);
  }

  return { init, run };
})();
window.XKSEARCH = XKSEARCH;
