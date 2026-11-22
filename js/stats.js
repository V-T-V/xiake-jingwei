/* ═══════════ 霞客经纬 · 计量面板 ═══════════
   渲染 data/stats.js（build_stats.py 产物）——前端只读脚本数字
   P2：古今对照名录导出（CSV-BOM / KML / GeoJSON，与 tools/export_data.py 同口径） */

/* 行构造（与 tools/export_data.py 同口径：t01→t22 · 逐日 · 锚点行）
   字段：地名/所属篇/日条/坐标/今名/依据/置信(确|推)/src */
function xrefRows() {
  const rows = [];
  XXK.trips.forEach(t => t.days.forEach((d, i) => {
    if (!d.anchor) return;
    rows.push({
      name: d.anchor.name,
      piece: t.title,
      day: (d.y && d.m) ? `${d.y}.${String(d.m).padStart(2, "0")}.${String(d.d || "").padStart(2, "0")}` : "篇首",
      lat: d.anchor.pos[0], lng: d.anchor.pos[1],
      today: d.anchor.today, basis: d.anchor.basis,
      conf: d.anchor.conf, src: d.anchor.src, di: i, tid: t.id,
    });
  }));
  return rows;
}

function dlFile(content, mime, fname) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([content], { type: mime }));
  a.download = fname;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 3000);
}

function exportCSV() {
  const NL = "\n", BOM = String.fromCharCode(0xFEFF);
  const head = ["地名", "所属篇", "日条", "纬度", "经度", "今名", "依据", "置信", "src"];
  const q = s => /[",\n]/.test(s) ? `"${String(s).replace(/"/g, '""')}"` : String(s);
  const csv = BOM + head.join(",") + NL +
    xrefRows().map(r => [r.name, r.piece, r.day, r.lat, r.lng, r.today,
      r.basis, r.conf, r.src].map(q).join(",")).join(NL) + NL +
    `注：坐标全部为今地常识定位示意坐标（src=derived，确±3km级/推±10-25km级），非实测`;
  dlFile(csv, "text/csv;charset=utf-8", "霞客经纬-古今对照.csv");
}

function exportKML() {
  let pins = "";
  xrefRows().forEach(r => {
    const desc = `${r.piece} · ${r.day} · 今${r.today}（${r.basis}）· 置信${r.conf} · 示意坐标(derived)`;
    pins += `<Placemark><name>${r.name}</name><description>${desc}</description>` +
      `<Point><coordinates>${r.lng},${r.lat},0</coordinates></Point></Placemark>`;
  });
  const kml = `<?xml version="1.0" encoding="UTF-8"?>` +
    `<kml xmlns="http://www.opengis.net/kml/2.2"><Document>` +
    `<name>霞客经纬·古今对照锚点（示意坐标）</name>` + pins + `</Document></kml>`;
  dlFile(kml, "application/vnd.google-earth.kml+xml", "霞客经纬-古今对照.kml");
}

function exportGeoJSON() {
  const feats = xrefRows().map(r => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [r.lng, r.lat] },
    properties: {
      地名: r.name, 所属篇: r.piece, 日条: r.day, 今名: r.today,
      依据: r.basis, 置信: r.conf, src: r.src, 备注: "示意坐标（今地常识定位，非实测）",
    },
  }));
  const gj = JSON.stringify({ type: "FeatureCollection",
    note: "坐标全部为 src=derived 示意坐标（今地常识定位）", features: feats });
  dlFile(gj, "application/geo+json", "霞客经纬-古今对照.geojson");
}

const XKSTATS = (() => {
  function open() {
    XKAPP.setMode("stats");
    document.getElementById("vname").textContent = "霞客计量";
    document.getElementById("vseal").textContent = "数";
    document.getElementById("pmeta").innerHTML = `<span>凡数字必出自脚本 · tools/build_stats.py</span>`;
    /* data/stats.js 以顶层 const XXK_STATS 载入（词法全局，不上 window）——
       修 v0.4 遗留：原 window.XXK_STATS 恒 undefined，面板必显「未载」 */
    const S = typeof XXK_STATS !== "undefined" ? XXK_STATS : null;
    const body = document.getElementById("pbody");
    if (!S) { body.innerHTML = "<p class='kv'>data/stats.js 未载。</p>"; return; }
    const m = S.meta;
    body.className = "";
    let html = `<div class="statgrid">` +
      `<div class="statcard"><b>${m.pieces}</b><span>游程</span></div>` +
      `<div class="statcard"><b>${m.days}</b><span>日条</span></div>` +
      `<div class="statcard"><b>${m.charsOrig.toLocaleString()}</b><span>原文字数</span></div>` +
      `<div class="statcard"><b>${m.kmTotal.toLocaleString()}</b><span>里程 km</span></div>` +
      `<div class="statcard"><b>${m.anchored}</b><span>锚定日</span></div>` +
      `<div class="statcard"><b>${m.coverage}%</b><span>锚覆盖率</span></div>` +
      `</div>`;

    /* 游程长短图 */
    html += `<div class="sect"><h3>五十二篇 · 日数与里程</h3>`;
    const maxDays = Math.max(...S.trips.map(t => t.days));
    S.trips.forEach(t => {
      const wDays = Math.round(t.days / maxDays * 180);
      const wKm = Math.round(t.km / S.meta.kmMax * 180);
      html += `<div class="hbar"><span class="hn" data-tid="${t.id}" title="${t.title}">${t.title}</span>` +
        `<span class="hv" style="width:${Math.max(2, wDays)}px;background:${t.color}" title="${t.days} 日"></span>` +
        `<span class="hv hv2" style="width:${Math.max(2, wKm)}px" title="${t.km} km"></span>` +
        `<span class="hc">${t.days}日 / ${t.km.toLocaleString()}km</span></div>`;
    });
    html += `<p class="kv" style="margin-top:6px">深条=日数 · 浅条=折线里程（含返程往返，方法论见 README）</p></div>`;

    /* 字频 */
    html += `<div class="sect"><h3>字频 · 六十字</h3><p class="kv freqbox">` +
      S.freq.map(f => `<span class="fq"><b>${f[0]}</b><i>${f[1].toLocaleString()}</i></span>`).join("") +
      `</p></div>`;

    /* 词类 */
    html += `<div class="sect"><h3>词汇场</h3><p class="kv">` +
      Object.entries(S.wordlists).map(([k, v]) =>
        `<b>${v.label}</b> ${v.total.toLocaleString()} 次（${v.top.map(x => x[0] + " " + x[1]).join(" · ")}）<br>`).join("") +
      `</p></div>`;

    /* 年份分布 */
    html += `<div class="sect"><h3>游年分布</h3><p class="kv">` +
      S.years.map(y => `${y[0]}：${"▮".repeat(Math.max(1, Math.round(y[1] / 3)))} ${y[1]} 日条`).join("<br>") +
      `</p></div>`;

    html += `<div class="sect"><h3>数据边界</h3><p class="kv">` +
      `· 文本：<b>三源</b>——国学导航本 22 篇（止粤西游二）+ 四库楊名時本滇黔 21 篇 + 通行本附编 9 篇（盘江考·溯江纪源·杂著七，零锚）<br>` +
      `· 坐标：地文学常识定位（今地），确 ${m.confQu} / 推 ${m.confTui}，全部 src=derived<br>` +
      `· 锚点法：逐日文本地名首现；跳段（>400km）标 ⚠（现存 ${m.jumps} 处）<br>` +
      `· 里程为锚点折线长（含同地往返），非人行实距</p></div>`;

    /* P2 · 古今对照名录导出（CSV/KML/GeoJSON，与 tools/export_data.py 同口径） */
    const nrows = xrefRows().length;
    html += `<div class="sect"><h3>古今对照 · 名录导出</h3><p class="kv">` +
      `${nrows} 锚行（地名/所属篇/日条/坐标/今名/依据/置信 确|推）——同口径复算：` +
      `<code>python tools/export_data.py</code><br>` +
      `<button class="ftool" id="dlcsv" style="margin-top:6px">⤓ CSV（Excel 直开）</button> ` +
      `<button class="ftool" id="dlkml">⤓ KML（Google Earth）</button> ` +
      `<button class="ftool" id="dlgj">⤓ GeoJSON</button><br>` +
      `坐标均为 src=derived 示意坐标（今地常识定位，非实测），导出内已逐行注明</p></div>`;

    body.innerHTML = html;
    body.querySelectorAll(".hn").forEach(el =>
      el.addEventListener("click", () => XKAPP.openTrip(el.dataset.tid, false)));
    document.getElementById("dlcsv").addEventListener("click", exportCSV);
    document.getElementById("dlkml").addEventListener("click", exportKML);
    document.getElementById("dlgj").addEventListener("click", exportGeoJSON);
    document.getElementById("panel").classList.add("open");
    location.hash = "#m=stats";
  }

  return { open, rows: xrefRows };
})();
window.XKSTATS = XKSTATS;
