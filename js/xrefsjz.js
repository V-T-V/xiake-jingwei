/* ═══════════ 霞客经纬 × 水道经纬 · 互查桥页签（第六座桥） ═══════════
   渲染 data/xref_sjz.js（tools/build_xref_sjz.py 生成——SDJW 只读，凡计数出自脚本）
   4 计数卡 + 对读特辑（溯江纪源×江水注·岷山导江之辨）+ 水道表 + 消歧排除 +
   水经谱无对应（盘江水系 323 次——霞客正补千二百年之阙）+ 按篇分组样例 +
   ↗循水深链 ../SDJW/#r=<水道id>（相对兄弟路径，父目录同根服务时可达） */

const XKSJZ = (() => {
  const DEPTH = location.pathname.split("/").filter(Boolean).length - 1;
  const BASE = "../".repeat(DEPTH);
  let loading = null;

  function ensureData() {
    if (window.XXK_SJZ) return Promise.resolve();
    if (loading) return loading;
    loading = new Promise((ok, bad) => {
      const s = document.createElement("script");
      s.src = `${BASE}data/xref_sjz.js?v=15`;
      s.onload = ok;
      s.onerror = () => bad(new Error("data/xref_sjz.js 加载失败"));
      document.head.appendChild(s);
    });
    return loading;
  }

  const esc = t => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  function open() {
    XKAPP.setMode("sjz");
    document.getElementById("vname").textContent = "水经互查";
    document.getElementById("vseal").textContent = "渡";
    document.getElementById("pmeta").innerHTML =
      `<span>霞客语料 × 《水经注》112 水道 · SDJW 数据只读</span>`;
    const body = document.getElementById("pbody");
    body.className = "";
    body.innerHTML = "<p class='kv'>加载互查数据…</p>";
    document.getElementById("panel").classList.add("open");
    document.getElementById("readerbar").classList.add("hidden");
    ensureData().then(() => render(body)).catch(() => {
      body.innerHTML = "<p class='kv'>互查数据未载（data/xref_sjz.js）——重跑 tools/build_xref_sjz.py。</p>";
    });
    location.hash = "#m=sjz";
  }

  function render(body) {
    const X = window.XXK_SJZ;
    const t = X.totals;
    let html = `<div class="xrgrid">` +
      `<div class="xrcard"><b>${t.waterMentions}</b><span>水道提及（计入）</span></div>` +
      `<div class="xrcard"><b>${t.watersMatched}</b><span>水经水道命中</span></div>` +
      `<div class="xrcard"><b>${t.noCorr}</b><span>水经谱无对应（如实）</span></div>` +
      `<div class="xrcard"><b>${t.pairs}</b><span>对读特辑（岷山之辨）</span></div>` +
      `</div>`;

    /* 对读特辑：溯江纪源 × 江水注 */
    const F = X.feature;
    html += `<div class="sect"><h3>特辑 · ${esc(F.title)}</h3>`;
    F.pairs.forEach(p => {
      html += `<div class="sjzpair">` +
        `<div class="spk">【${esc(p.topic)}】</div>` +
        `<div class="spline xk"><i>霞客</i>${esc(p.xk)}</div>` +
        `<div class="spline sjz"><i>郦注</i>${esc(p.sjz)} ` +
        `<a href="${p.sjzHref}" target="_blank" rel="noopener">↗循水</a></div>` +
        `</div>`;
    });
    html += `<p class="kv" style="margin-top:6px">郦道元（卒 527）奉「岷山导江」为四渎之首——
一千一百余年后徐霞客行至金沙江畔，遂断「推江源者必当以金沙为首」。
对读句皆脚本截取，选题唯三：岷山 · 禹贡 · 导江。</p></div>`;

    /* 水道命中表 */
    html += `<div class="sect"><h3>水道提及 · ${t.watersMatched} 水 ${t.waterMentions} 次</h3>`;
    X.waters.forEach(w => {
      html += `<div class="xrtrip"><div class="xrh"><b>${esc(w.name)}</b>` +
        `<span>${w.n} 次 · ${w.pieces} 篇 · ${w.vols.join("/")}</span>` +
        `<a href="${w.href}" target="_blank" rel="noopener" title="于水道经纬打开此水">↗循水</a></div>` +
        w.samples.map(s => `<div class="xr_ex"><span class="nm">${esc(s.form)}</span>（${esc(s.piece)}）${esc(s.ctx)}</div>`).join("") +
        (w.note ? `<div class="xr_ex" style="border-left-color:rgba(142,43,34,.35)">注：${esc(w.note)}</div>` : "") +
        `</div>`;
    });
    html += `</div>`;

    /* 消歧排除 + 无对应 */
    html += `<div class="sect"><h3>消歧与无对应（如实）</h3><p class="kv">` +
      `· 排除 ${X.excluded.length} 名：` +
      X.excluded.map(e => `<b>${esc(e.name)}</b>×${e.n}（${esc(e.why)}）`).join("；") + `<br>` +
      `· 水经谱无对应 ${t.noCorr} 次：` +
      X.noCorrespondence.map(w => `<b>${esc(w.name)}</b>×${w.n}`).join(" · ") +
      `——水经注未及西南盘江诸水（成书早千二百年），霞客《盘江考》《溯江纪源》正补其阙</p></div>`;

    /* 按篇分组 */
    const hitTrips = X.byTrip.filter(b => b.n > 0);
    html += `<div class="sect"><h3>按篇分组 · ${hitTrips.length} 篇有水名命中</h3>`;
    hitTrips.forEach(b => {
      html += `<div class="xrtrip" data-tid="${b.id}">` +
        `<div class="xrh"><b>${esc(b.title)}</b><span>${b.year || ""} ${b.source}</span>` +
        `<span>水名命中 ${b.n} 次</span></div>` +
        b.hits.map(h => `<div class="xr_ex">${esc(h.ctx)}<span class="nm">〔${esc(h.water)}·${esc(h.form)}〕</span>` +
          `<a href="${h.href}" target="_blank" rel="noopener">↗循水</a></div>`).join("") +
        `</div>`;
    });
    html += `</div>`;

    body.innerHTML = html;
    body.querySelectorAll(".xrtrip[data-tid] .xrh").forEach(el =>
      el.addEventListener("click", () =>
        XKAPP.openTrip(el.closest(".xrtrip").dataset.tid, false)));
  }

  return { open };
})();
window.XKSJZ = XKSJZ;
