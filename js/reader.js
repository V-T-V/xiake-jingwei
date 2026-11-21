/* ═══════════ 霞客经纬 · 循程阅读器（核心体验） ═══════════
   右幅 = 该程日记逐日条目（日期锚头 + 正文，注释（…）淡显）
   滚动文本 → 地图飞至当前日锚；前/后日按钮；跳段朱示警
   深链 #trip=t01&d=n 由 app.js 写回 */

const XKREADER = (() => {
  let curId = null, curDay = -1;
  const pbody = () => document.getElementById("pbody");
  /* 路径基（tests/ 等子目录下打开时回退一级） */
  const DEPTH = location.pathname.split("/").filter(Boolean).length - 1;
  const BASE = "../".repeat(DEPTH);   // 页面距站根深度（index=0 · tests/=1）

  /* 懒加载该程文本（data/read/NN.js） */
  function ensureRead(num) {
    if (window.XXK_READ && XXK_READ[num]) return Promise.resolve();
    if (ensureRead._p && ensureRead._p.num === num) return ensureRead._p.p;
    const p = new Promise((ok, bad) => {
      const s = document.createElement("script");
      s.src = `${BASE}data/read/${num}.js?v=10`;
      s.onload = ok;
      s.onerror = () => bad(new Error(`read/${num}.js 加载失败`));
      document.head.appendChild(s);
    });
    ensureRead._p = { num, p };
    return p;
  }

  /* 正文段落：括号注释 → 淡色小注 */
  function fmtPara(t) {
    const esc = t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return esc.replace(/[（(]([^（）()]{1,60})[）)]/g, '<span class="nz">（$1）</span>');
  }

  async function open(id, day = 0) {
    curId = id;
    const t = XXK.trips.find(x => x.id === id);
    if (!t) return;
    try { await ensureRead(t.num); } catch (e) { /* 正文暂缺——骨架仍可展示 */ }
    XKAPP.setMode("read");
    XKMAP.select(id, { fly: true, day });
    XKNAV.highlight(id);
    document.getElementById("vname").textContent = t.title;
    document.getElementById("vseal").textContent = "游";
    document.getElementById("pmeta").innerHTML = metaHTML(t);
    renderBody(t);
    document.getElementById("panel").classList.add("open");
    document.getElementById("readerbar").classList.remove("hidden");
    gotoDay(day, true);
    XKAPP.writeHash(id, curDay);
  }

  function metaHTML(t) {
    return `<span>万历崇祯间 · ${t.year}</span>` +
      `<span>${t.stats.days} 日条</span>` +
      `<span>锚点 ${t.stats.anchored}</span>` +
      `<span>${t.stats.km.toLocaleString()} km</span>` +
      `<span>${t.stats.chars.toLocaleString()} 字</span>`;
  }

  function renderBody(t) {
    const rd = (window.XXK_READ && XXK_READ[t.num]) || null;
    const host = pbody();
    host.className = "";
    if (!rd) { host.innerHTML = "<p class='kv'>此程文本未载。</p>"; return; }
    // 题解（编者）
    let html = "";
    if (rd.intro && rd.intro.length) {
      html += `<div class="termcard">编者题解 · ${rd.intro[0].replace(/^[（(]|[）)]$/g, "").slice(0, 60)}…</div>`;
    }
    rd.days.forEach((d, i) => {
      const meta = t.days[i] || {};
      const a = meta.anchor;
      const dateLabel = d.h === "篇首" ? "篇首引子" : d.h;
      const dt = meta.y && meta.m ? `${meta.y}.${String(meta.m).padStart(2, "0")}.${String(meta.d || "").padStart(2, "0")}` : "";
      html += `<div class="dayblk" data-i="${i}">` +
        `<div class="dayhead"><span class="dnum">${dateLabel}</span>` +
        (a ? `<span class="dplace" data-i="${i}">◈ ${a.name}${a.conf === "推" ? "（推）" : ""}</span>` : "") +
        (meta.km != null && meta.km > 0 ? `<span class="dkm">${meta.km.toLocaleString()} km</span>` : "") +
        (meta.jump ? `<span class="djump">⚠ 跳段</span>` : "") +
        `</div>` +
        d.paras.map(p => `<p class="you">${fmtPara(p)}</p>`).join("") +
        (meta.places && meta.places.length > (a ? 1 : 0)
          ? `<div class="kv">是日历地：${meta.places.slice(0, 8).map(x => `<span class="pl">${x}</span>`).join("")}</div>` : "") +
        `</div>`;
    });
    html += `<div class="termcard">◆ ${t.title} 终 · ${t.year}</div>`;
    host.innerHTML = html;
    // 交互：点日头跳锚
    host.querySelectorAll(".dplace").forEach(el =>
      el.addEventListener("click", () => gotoDay(+el.dataset.i, true)));
    attachFollow();
  }

  /* ── 日导航与地图跟随 ─────────────────────────────── */
  function dayBlocks() { return [...pbody().querySelectorAll(".dayblk")]; }

  /* 程序跳转期解除滚动跟随（v0.4 竞态：平滑滚动在途时 onScroll 防抖尾班按旧视口
     判定日号，书签回到 d=n 高亮偶落 d=0——同 Leaflet 动画先 stop() 之理：
     跳转即令牌作废在途判定 + 摘监听，滚动收尾后重挂并手动确认日号） */
  let jumpSeq = 0;
  let followOn = false;

  function attachFollow() {
    if (followOn) return;
    pbody().addEventListener("scroll", onScroll, { passive: true });
    followOn = true;
  }
  function detachFollow() {
    if (!followOn) return;
    pbody().removeEventListener("scroll", onScroll);
    followOn = false;
  }

  function waitForScrollEnd(done) {
    const host = pbody();
    let fin = false;
    const finish = () => {
      if (fin) return;
      fin = true;
      host.removeEventListener("scrollend", finish);
      clearTimeout(timer);
      done();
    };
    const timer = setTimeout(finish, 900);       // 无 scrollend/长惯性兜底（含已在位无滚动）
    host.addEventListener("scrollend", finish);
  }

  function gotoDay(i, fly) {
    const t = XXK.trips.find(x => x.id === curId);
    if (!t) return;
    const blocks = dayBlocks();
    if (!blocks.length) return;
    i = Math.max(0, Math.min(i, blocks.length - 1));
    curDay = i;
    blocks.forEach((b, k) => b.classList.toggle("cur", k === i));
    const my = ++jumpSeq;                         // 作废此前在途判定与收尾回调
    detachFollow();
    blocks[i].scrollIntoView({ block: "start", behavior: "smooth" });
    waitForScrollEnd(() => {
      if (my !== jumpSeq) return;                 // 已有更新跳转/open——由它收尾
      attachFollow();
      confirmDay(t, i);                           // 收尾手动钉日号，不再按视口猜
    });
    if (fly !== false) XKMAP.markDay(t, i, true);
    else XKMAP.markDay(t, i, false);
    updateProg(t, i, blocks.length);
    XKAPP.writeHash(curId, i);
    if (typeof XKBM !== "undefined") XKBM.updateStar();   // 书签☆随日同步（守卫：核心不硬赖特性）
  }

  /* 跳转收尾确认：滚动动画完成后再钉一次高亮/进度/深链（幂等） */
  function confirmDay(t, i) {
    dayBlocks().forEach((b, k) => b.classList.toggle("cur", k === i));
    updateProg(t, i, dayBlocks().length);
    XKAPP.writeHash(curId, i);
  }

  function updateProg(t, i, total) {
    const d = t.days[i] || {};
    const a = d.anchor;
    const pct = total > 1 ? Math.round(i / (total - 1) * 100) : 100;
    const km = d.km != null ? ` · 累计 ${d.km.toLocaleString()} km` : "";
    document.getElementById("rprog").textContent =
      `${t.title.slice(0, 6)} · ${pct}%${a ? " · " + a.name : ""}${km}`;
  }

  /* 滚动跟随：可视判读线（host 视口顶 + 90px）以下最近日块即当前日。
     rect 基准修 v0.4 偏差——原 offsetTop 相对 #panel（最近定位祖），
     与 scrollTop 不同坐标系；程序跳转期 followOn=false，防抖尾班不判定 */
  let scrollTimer = null;
  function onScroll() {
    if (scrollTimer) return;
    scrollTimer = setTimeout(() => {
      scrollTimer = null;
      if (!followOn) return;                      // 跳转在途——旧视口判定作废
      const host = pbody();
      const line = host.getBoundingClientRect().top + 90;
      let best = 0;
      dayBlocks().forEach((b, k) => { if (b.getBoundingClientRect().top <= line) best = k; });
      if (best !== curDay) {
        curDay = best;
        dayBlocks().forEach((b, k) => b.classList.toggle("cur", k === best));
        const t = XXK.trips.find(x => x.id === curId);
        if (t) {
          const d = t.days[best];
          if (d && d.anchor) XKMAP.markDay(t, best, true);
          else XKMAP.markDay(t, best, false);
          updateProg(t, best, dayBlocks().length);
          XKAPP.writeHash(curId, best);
          if (typeof XKBM !== "undefined") XKBM.updateStar();
        }
      }
    }, 240);
  }

  /* ── TTS 朗读：自当前日起读（循程听书） ─────────── */
  const tts = { queue: [], idx: 0, on: false };
  function collectFrom(i) {
    const blocks = dayBlocks();
    const b = blocks[i];
    if (!b) return [];
    const items = [b.querySelector(".dnum").textContent];
    b.querySelectorAll("p.you").forEach(p => items.push(p.textContent));
    return items;
  }
  function ttsNext() {
    if (!tts.on || tts.idx >= tts.queue.length) { ttsStop(); return; }
    const u = new SpeechSynthesisUtterance(tts.queue[tts.idx++]);
    u.lang = "zh-CN";
    u.rate = 0.95;
    const v = speechSynthesis.getVoices().find(x => x.lang && x.lang.startsWith("zh"));
    if (v) u.voice = v;
    u.onend = () => setTimeout(ttsNext, 260);
    speechSynthesis.speak(u);
  }
  function ttsToggle() {
    if (tts.on) { ttsStop(); return; }
    if (typeof speechSynthesis === "undefined") return;
    tts.queue = collectFrom(curDay < 0 ? 0 : curDay);
    if (!tts.queue.length) return;
    tts.on = true; tts.idx = 0;
    const b = document.getElementById("rtts");
    if (b) b.textContent = "■ 停读";
    ttsNext();
  }
  function ttsStop() {
    tts.on = false;
    try { speechSynthesis.cancel(); } catch (e) {}
    const b = document.getElementById("rtts");
    if (b) b.textContent = "▷ 朗读";
  }

  function close() {
    ttsStop();
    detachFollow();
    curId = null;
    document.getElementById("readerbar").classList.add("hidden");
  }

  return { open, close, gotoDay, ttsToggle, get current() { return curId; },
           get day() { return curDay; } };
})();
window.XKREADER = XKREADER;
