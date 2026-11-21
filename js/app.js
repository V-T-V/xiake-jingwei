/* ═══════════ 霞客经纬 · 应用装配（boot / 模式 / 深链 / PWA） ═══════════ */

const XKAPP = (() => {
  let mode = "map";
  const MODE_NOTE = {
    map: "廿二游程 · 万里足迹见于图",
    read: "循程而读 · 滚动日记，地图随行",
    stats: "霞客计量 · 字频 / 里程 / 游年",
    fy: "方舆互查 · 霞客行踪 × 明府县",
    about: "关于 · 数据与方法",
  };

  function boot() {
    XKMAP.init();
    XKMAP.onSelect = onTripClick;
    XKMAP.onDayClick = (t, i) => XKREADER.open(t.id, i);
    XKMAP.render();
    XKNAV.build();
    XKSEARCH.init();
    bindUI();
    document.querySelector("#boot .go").addEventListener("click", () => {
      document.getElementById("boot").classList.add("off");
      setTimeout(() => document.getElementById("boot").remove(), 700);
    });
    document.getElementById("bookstat").textContent =
      `${XXK.meta.pieces} 程 · ${XXK.meta.days} 日 · ${XXK.meta.kmTotal.toLocaleString()} km`;
    applyHash();
    window.addEventListener("hashchange", applyHash);
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("sw.js").then(() => {
        const el = document.getElementById("swstate");
        el.style.display = ""; el.textContent = "离线就绪";
      }).catch(() => {});
    }
  }

  function bindUI() {
    document.querySelectorAll("#modes .mode").forEach(b =>
      b.addEventListener("click", () => act(b.dataset.mode)));
    document.getElementById("pclose").addEventListener("click", closePanel);
    document.getElementById("wanderlink").addEventListener("click", () => {
      const ts = XXK.trips.filter(t => t.path.length > 2);
      openTrip(ts[Math.floor(Math.random() * ts.length)].id, true);
    });
    document.getElementById("statslink").addEventListener("click", () => XKSTATS.open());
    document.getElementById("tdlink").addEventListener("click", () => {
      location.href = "3d.html?v=10";
    });
    document.getElementById("rtts").addEventListener("click", () => XKREADER.ttsToggle());
    document.getElementById("rbm").addEventListener("click", () => {
      if (!XKREADER.current) return;
      const t = XXK.trips.find(x => x.id === XKREADER.current);
      const d = t.days[XKREADER.day] || {};
      const dateLabel = (d.h && d.h !== "篇首") ? d.h.slice(0, 12) : "篇首";
      XKBM.toggle(XKREADER.current, XKREADER.day, {
        title: t.title, dayLabel: dateLabel,
        place: d.anchor ? d.anchor.name : "",
      });
      XKBM.updateStar();
      XKBM.updateBadge();
    });
    document.getElementById("bmlink").addEventListener("click", () => XKBM.openPanel());
    XKBM.updateBadge();
    const nightBtn = document.getElementById("nightlink");
    const nightApply = on => {
      document.body.classList.toggle("night", on);
      nightBtn.textContent = on ? "☀ 昼" : "☾ 夜读";
      try { localStorage.setItem("xxkNight", on ? "1" : ""); } catch (e) {}
    };
    nightBtn.addEventListener("click", () =>
      nightApply(!document.body.classList.contains("night")));
    try { if (localStorage.getItem("xxkNight")) nightApply(true); } catch (e) {}
    document.getElementById("rprev").addEventListener("click", () =>
      XKREADER.gotoDay(Math.max(0, XKREADER.day - 1), true));
    document.getElementById("rnext").addEventListener("click", () =>
      XKREADER.gotoDay(XKREADER.day + 1, true));
    window.addEventListener("keydown", e => {
      if (e.key === "Escape") closePanel();
      if ((e.key === "ArrowDown" || e.key === "ArrowUp") && XKREADER.current && e.altKey) {
        e.preventDefault();
        XKREADER.gotoDay(XKREADER.day + (e.key === "ArrowDown" ? 1 : -1), true);
      }
    });
  }

  function onTripClick(t) {
    if (!t) return;
    if (mode === "map") openTrip(t.id, false);
    XKNAV.highlight(t.id);
  }

  function setMode(m) {
    mode = m;
    document.querySelectorAll("#modes .mode").forEach(b =>
      b.classList.toggle("active", b.dataset.mode === m));
    document.getElementById("modelabel").textContent =
      document.querySelector(`#modes .mode[data-mode="${m}"]`).textContent;
    document.getElementById("modenote").textContent = MODE_NOTE[m] || "";
  }

  function act(m) {
    if (m === "stats") return XKSTATS.open();
    if (m === "fy") return XKXREF.open();
    if (m === "about") return openAbout();
    setMode(m);
    if (m === "map") closePanel();
  }

  function openTrip(id, read = true) {
    const t = XXK.trips.find(x => x.id === id);
    if (!t) return;
    if (read) {
      XKREADER.open(id, 0);          // 循程而读（含详情）
    } else {
      XKMAP.select(id, { fly: true });
      XKNAV.highlight(id);
      showDetail(t);
    }
  }

  function showDetail(t) {
    XKAPP.setMode("map");
    document.getElementById("vname").textContent = t.title;
    document.getElementById("vseal").textContent = "游";
    document.getElementById("pmeta").innerHTML = metaOf(t);
    const body = document.getElementById("pbody");
    const anchors = t.days.filter(d => d.anchor);
    let html = "";
    if (anchors.length) {
      html += `<div class="sect"><h3>行程（${anchors.length} 锚）</h3><p class="kv">` +
        anchors.map(d => `<span class="pl" data-di="${t.days.indexOf(d)}">${d.anchor.name}</span>`).join(" → ") +
        `</p></div>`;
    }
    html += `<div class="sect"><h3>统计</h3><p class="kv">` +
      `日条 <b>${t.stats.days}</b> · 锚定 <b>${t.stats.anchored}</b> · ` +
      `里程 <b>${t.stats.km.toLocaleString()}</b> km · 原文 <b>${t.stats.chars.toLocaleString()}</b> 字<br>` +
      `纪年 <b>${t.year}</b>${t.stats.ganzhi ? "（" + t.stats.ganzhi + "）" : ""}</p></div>`;
    html += `<button class="ftool" id="goread" style="margin-top:6px">▸ 循程而读</button>`;
    body.innerHTML = html;
    body.className = "";
    body.querySelectorAll(".pl").forEach(el =>
      el.addEventListener("click", () => XKREADER.open(t.id, +el.dataset.di)));
    const gr = body.querySelector("#goread");
    if (gr) gr.addEventListener("click", () => openTrip(t.id, true));
    document.getElementById("panel").classList.add("open");
    document.getElementById("readerbar").classList.add("hidden");
    location.hash = "#t=" + t.id;
  }

  function metaOf(t) {
    return `<span>${t.year}</span><span>${t.stats.days} 日条</span>` +
      `<span>锚点 ${t.stats.anchored}</span><span>${t.stats.km.toLocaleString()} km</span>`;
  }

  /* 深链：#trip=t01&d=n · #t=t01 · #m=mode */
  function writeHash(tid, day) {
    location.hash = `trip=${tid}&d=${day}`;
  }

  /* 深链：#trip=t01&d=n · #t=t01 · #m=mode
     v0.4 修复：原 const [k,v]=h.split("=") 对 trip=t03&d=4 只取到 v="t03&d"
     （第二个 = 后的日号被解构丢弃）→ 日号恒 0，哈希写回触发 hashchange 又
     open(tid,0) 重开——书签/深链回到 d=n 高亮漂到 d=0 即此环。 */
  function applyHash() {
    const h = location.hash.slice(1);
    const k = h.split("=", 1)[0];
    const v = h.slice(k.length + 1);
    if (k === "trip") {
      const [tid, d] = (v || "").split("&");
      const day = d ? +d.split("=")[1] || 0 : 0;
      /* 已在此程此日则不重开（防 写hash→hashchange→open 反馈环：重渲染清滚动） */
      if (XKREADER.current === tid && XKREADER.day === day) return;
      XKREADER.open(tid, day);
    } else if (k === "t") {
      const t = XXK.trips.find(x => x.id === v);
      if (t) { XKMAP.select(v, { fly: true }); XKNAV.highlight(v); showDetail(t); }
    } else if (k === "m") {
      if (v === "stats") XKSTATS.open();
      else if (v === "fy") XKXREF.open();
      else if (v === "bm") XKBM.openPanel();
      else if (v === "about") openAbout();
      else setMode(v || "map");
    }
  }

  function openAbout() {
    const m = XXK.meta;
    setMode("about");
    document.getElementById("vname").textContent = "关于";
    document.getElementById("vseal").textContent = "叙";
    document.getElementById("pmeta").innerHTML = `<span>数据管线 · 方法与边界</span>`;
    const body = document.getElementById("pbody");
    body.className = "";
    body.innerHTML = `
<div class="sect"><h3>霞客经纬</h3>
<p class="kv">明·徐弘祖《徐霞客游记》数字人文平台。方舆经纬（点·府治）与水道经纬（线·水道）
的姊妹站——此以<b>游程（线）+时序（日记日）</b>为空间范式：廿二程、五百零六日条，
自天台雁宕而嵩华恒岱，尽浙赣楚桂之遥。</p></div>
<div class="sect"><h3>数据与方法</h3><p class="kv">
· 文本：国学导航本（GB18030 抓取，${m.charsOrig.toLocaleString()} 字原文 + ${m.charsNote.toLocaleString()} 字编者注）；
版本为通行「前半部」——<b>止于粤西游日记二</b>，缺粤游三四·黔游·滇游·附编（宁缺毋假）<br>
· 维基文库 zh.wikisource.org 于建站网络不可达（TLS 握手超时），故用国学导航本，见 README 数据源记录<br>
· 日条解析：行首日期标记（干支纪年·闰月·晦朔）→ ${m.days} 日条；句末标点后日号分段<br>
· 锚点：294 地名表（篇内 scope 消歧）逐日首现地名；坐标为今地常识定位（src=derived），
确 ${m.confQu} / 推 ${m.confTui}，覆盖 ${m.coverage}%<br>
· 里程：锚点折线 haversine 累计（${m.kmTotal.toLocaleString()} km，含同地往返，非人行实距）；
>400km 跳段标 ⚠ 不计入里程<br>
· 全文检索：Worker 懒加载分片（22 片，编者注已剔，搜的是霞客原文）</p></div>
<div class="sect"><h3>姊妹站</h3><p class="kv">
· 方舆经纬（读史方舆纪要·点织版图） · 水道经纬（水经注·线溯江河） · 霞客经纬（本站）<br>
· 基建承两站：PWA 三级缓存 · 全文检索 Worker · 底图兜底 · 深链/分享 · 循读飞行</p></div>
<div class="sect"><h3>路线图</h3><p class="kv">
滇黔游补全（待可达数据源）· 三维形胜（MapLibre 地形沿游线飞览）· 古今地名对照导出 · TTS 循程听书（已具）</p></div>`;
    document.getElementById("panel").classList.add("open");
    location.hash = "#m=about";
  }

  function closePanel() {
    document.getElementById("panel").classList.remove("open");
    if (XKREADER.current) XKREADER.close();
    location.hash = "#m=map";
  }

  document.addEventListener("DOMContentLoaded", boot);
  return { openTrip, setMode, writeHash, get mode() { return mode; } };
})();
window.XKAPP = XKAPP;
