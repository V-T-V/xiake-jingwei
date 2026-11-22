/* ═══════════ 霞客经纬 × 方舆经纬 · 互查桥页签（P2 站际桥） ═══════════
   渲染 data/xref_fy.js（tools/build_xref_fy.py 生成——HHH 只读，凡计数出自脚本）
   按篇分组计数 + 样例（霞客原文句 + 方舆对应府县）+ ↗方舆深链
   ../HHH/#mode=舆图&p=<省id>&fu=<府名>（相对兄弟路径，父目录同根服务时可达） */

const XKXREF = (() => {
  const DEPTH = location.pathname.split("/").filter(Boolean).length - 1;
  const BASE = "../".repeat(DEPTH);
  let loading = null;

  function ensureData() {
    if (window.XXK_FYXREF) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise((ok, bad) => {
      const s = document.createElement("script");
      s.src = `${BASE}data/xref_fy.js?v=14`;
      s.onload = ok;
      s.onerror = () => bad(new Error("data/xref_fy.js 加载失败"));
      document.head.appendChild(s);
    });
    return loading;
  }

  const esc = t => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  function open() {
    XKAPP.setMode("fy");
    document.getElementById("vname").textContent = "方舆互查";
    document.getElementById("vseal").textContent = "桥";
    document.getElementById("pmeta").innerHTML =
      `<span>霞客行踪 × 《读史方舆纪要》明府县 · HHH 数据只读</span>`;
    const body = document.getElementById("pbody");
    body.className = "";
    body.innerHTML = "<p class='kv'>加载互查数据…</p>";
    document.getElementById("panel").classList.add("open");
    document.getElementById("readerbar").classList.add("hidden");
    ensureData().then(() => render(body)).catch(() => {
      body.innerHTML = "<p class='kv'>互查数据未载（data/xref_fy.js）——重跑 tools/build_xref_fy.py。</p>";
    });
    location.hash = "#m=fy";
  }

  function render(body) {
    const X = window.XXK_FYXREF;
    let html = `<div class="xrgrid">` +
      `<div class="xrcard"><b>${X.total}</b><span>日条锚点</span></div>` +
      `<div class="xrcard"><b>${X.matched}</b><span>匹配方舆府县</span></div>` +
      `<div class="xrcard"><b>${X.unmatched}</b><span>无对应（如实）</span></div>` +
      `<div class="xrcard"><b>${X.uniqMatched}/${X.uniqNames}</b><span>唯一地名命中</span></div>` +
      `</div>`;

    html += `<div class="sect"><h3>桥 · 数据与口径</h3><p class="kv">` +
      `· 匹配法：同名（剥 府/州/县/卫 尾）+ 今名对照；同名异地以<b>省域消歧</b>（最近府治定省，` +
      `候选须距锚 ≤250km——如浙江宁海 vs 山东登州府宁海州即判无对应）<br>` +
      `· 方舆侧（HHH site_data.js 只读）：${X.hhh.provinces} 省 · ${X.hhh.fu} 府治 · 县名 ${X.hhh.counties} · 基名索引 ${X.hhh.names}<br>` +
      `· 无对应多为山寺岩潭（天台山·灵峰·石梁……）——霞客所游本非政区，缺就是缺<br>` +
      `· ↗方舆为相对兄弟路径 <code>../HHH/</code>：<b>父目录同根服务</b>（于 D:\\W_A_W 起 ` +
      `<code>python -m http.server</code>）后 /XXK/ 与 /HHH/ 同源可达，用法见 README</p></div>`;

    html += `<div class="sect"><h3>按篇分组</h3>`;
    X.byTrip.forEach(t => {
      const pct = t.matched + t.unmatched ? Math.round(t.matched / (t.matched + t.unmatched) * 100) : 0;
      html += `<div class="xrtrip" data-tid="${t.id}">` +
        `<div class="xrh"><b>${esc(t.title)}</b><span>${t.year}</span>` +
        `<span>匹配 ${t.matched} · 无对应 ${t.unmatched}（${pct}%）</span></div>`;
      t.examples.forEach(ex => {
        html += `<div class="xr_ex">` +
          (ex.ctx ? `「${esc(ex.ctx)}」` : `《${esc(t.title)}》`) +
          `　<span class="nm">${esc(ex.name)}</span> → ${esc(ex.fyProv)}·${esc(ex.fyFu)}（${ex.kind}·${esc(ex.how)}）` +
          `<a href="${ex.href}" target="_blank" rel="noopener" title="于方舆经纬打开此府">↗方舆</a></div>`;
      });
      if (t.misses.length)
        html += `<div class="xr_ex" style="border-left-color:rgba(142,43,34,.35)">无对应样例：` +
          t.misses.map(esc).join(" · ") + `</div>`;
      html += `</div>`;
    });
    html += `</div>`;

    body.innerHTML = html;
    body.querySelectorAll(".xrtrip .xrh").forEach(el =>
      el.addEventListener("click", () =>
        XKAPP.openTrip(el.closest(".xrtrip").dataset.tid, false)));
  }

  return { open };
})();
window.XKXREF = XKXREF;
