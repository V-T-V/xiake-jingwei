/* ═══════════ 霞客经纬 · 书签收藏（P1 尾项） ═══════════
   游程/日条 ☆ 收藏 · localStorage 持久化 · 上限 30（学方舆经纬 BM 模式）
   深链可复原：书签存 {tid, day}，点击 → XKREADER.open(tid, day)（#trip=&d= 自动写回） */

const XKBM = (() => {
  const KEY = "xxkbm", MAX = 30;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; }
  }
  function save(a) {
    try { localStorage.setItem(KEY, JSON.stringify(a.slice(0, MAX))); } catch (e) {}
  }
  function has(tid, day) {
    return load().some(b => b.tid === tid && b.day === day);
  }
  /* 游程级书签（day=-1：回到篇首）；日条级（day=n） */
  function toggle(tid, day, meta) {
    let a = load();
    const i = a.findIndex(b => b.tid === tid && b.day === day);
    if (i >= 0) {
      a.splice(i, 1);
      save(a);
      return false;                       // 已移除
    }
    a.unshift({ tid, day, title: meta.title, dayLabel: meta.dayLabel || "", place: meta.place || "", ts: Date.now() });
    save(a);
    return true;                          // 新增
  }
  function remove(tid, day) {
    save(load().filter(b => !(b.tid === tid && b.day === day)));
  }
  function count() { return load().length; }

  /* ── 管理面板（总叙）：列出 / 删除 / 一键回到 ── */
  function openPanel() {
    XKAPP.setMode("map");
    document.getElementById("vname").textContent = "书签收藏";
    document.getElementById("vseal").textContent = "藏";
    document.getElementById("pmeta").innerHTML =
      `<span>本机 localStorage 持久化 · 上限 ${MAX} 条</span>`;
    const body = document.getElementById("pbody");
    body.className = "";
    render(body);
    document.getElementById("panel").classList.add("open");
    document.getElementById("readerbar").classList.add("hidden");
    location.hash = "#m=bm";
  }

  function render(body) {
    const a = load();
    let html = `<div class="sect"><h3>☆ 收藏 (${a.length}/${MAX})</h3>`;
    if (!a.length) {
      html += `<p class="kv">尚无书签——循程阅读中点 <b>☆</b> 收藏当前日条；深链 #trip=xxx&d=n 刷新可复原。</p></div>`;
    } else {
      html += `<div class="bmlist">` + a.map((b, i) =>
        `<div class="bmrow" data-i="${i}">` +
        `<span class="bmstar" data-del="${i}" title="移除此书签">★</span>` +
        `<span class="bmmain"><b>${b.title}</b>` +
        (b.day >= 0 ? `<i>${b.dayLabel}${b.place ? " · ◈ " + b.place : ""}</i>` : `<i>篇首 · 整程收藏</i>`) +
        `</span>` +
        `<span class="bmgo" title="回到此程此日">▸ 回到</span>` +
        `</div>`).join("") + `</div>` +
        `</div><p class="kv">点击行或「回到」即循程而读复原（${"#trip="}xxx&d=n 深链）。</p>`;
    }
    body.innerHTML = html;
    body.querySelectorAll(".bmrow").forEach(el =>
      el.addEventListener("click", e => {
        const b = load()[+el.dataset.i];
        if (!b) return;
        if (e.target.dataset.del !== undefined) {
          remove(b.tid, b.day);
          render(body);
          updateBadge();
          return;
        }
        XKREADER.open(b.tid, Math.max(0, b.day));
      }));
  }

  /* 底栏计数徽标 + 阅读条 ☆ 状态（由 app/reader 调） */
  function updateBadge() {
    const el = document.getElementById("bmcount");
    if (el) el.textContent = count() ? `(${count()})` : "";
  }
  function updateStar() {
    const btn = document.getElementById("rbm");
    if (!btn || !XKREADER.current) return;
    const on = has(XKREADER.current, XKREADER.day);
    btn.textContent = on ? "★ 已藏" : "☆ 收藏";
    btn.classList.toggle("on", on);
  }

  return { load, has, toggle, remove, count, openPanel, updateBadge, updateStar, MAX };
})();
window.XKBM = XKBM;
