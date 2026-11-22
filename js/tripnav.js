/* ═══════════ 霞客经纬 · 游程纲目（左列） ═══════════
   43 程按编年列（gx/kr 双底本）；眼睛开关单线显隐；点击开程 */

const XKNAV = (() => {
  function build() {
    const host = document.getElementById("raillist");
    host.innerHTML = "";
    const trips = [...XXK.trips].sort((a, b) => a.year0 - b.year0 || a.id.localeCompare(b.id));
    let lastYear = null;
    trips.forEach(t => {
      if (t.year0 !== lastYear) {
        lastYear = t.year0;
        const yr = document.createElement("div");
        yr.className = "ryear";
        yr.textContent = `—— ${t.year0} ——`;
        host.appendChild(yr);
      }
      host.appendChild(row(t));
    });
  }

  function row(t) {
    const el = document.createElement("div");
    el.className = "trow" + (XKMAP.selected === t.id ? " cur" : "");
    el.dataset.tid = t.id;
    const eye = XKMAP.hidden.has(t.id) ? "◌" : "●";
    el.innerHTML =
      `<span class="tglyph" data-eye="1" title="图上显/隐此游线">${eye}</span>` +
      `<span class="tname">${t.title}</span>` +
      `<span class="tchars">${t.stats.days}日</span>` +
      `<span class="tdot" style="background:${t.color}"></span>`;
    el.addEventListener("click", e => {
      if (e.target.dataset.eye) {
        const on = XKMAP.toggleTrip(t.id);
        e.target.textContent = on ? "●" : "◌";
        return;
      }
      XKAPP.openTrip(t.id, false);
    });
    return el;
  }

  function highlight(tid) {
    document.querySelectorAll("#raillist .trow").forEach(r =>
      r.classList.toggle("cur", r.dataset.tid === tid));
  }

  return { build, highlight };
})();
window.XKNAV = XKNAV;
