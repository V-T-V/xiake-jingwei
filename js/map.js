/* ═══════════ 霞客经纬 · 舆图（游线渲染器） ═══════════
   43 条游程折线（分色可开关，gx/kr 双底本） · 日锚点 · 悬停详情 · 点击开程
   当前阅读锚点朱点高亮 */

const XKMAP = (() => {
  let map, tileLayer = null, tileMode = "physical", tileErrs = 0;
  const lineLayer = L.layerGroup();
  const dotLayer = L.layerGroup();
  const curLayer = L.layerGroup();      // 当前游程高亮 + 阅读锚
  const hidden = new Set();             // 已隐藏游程 id
  let selId = null;
  let curDayIdx = -1;
  let onSelect = null;
  let onDayClick = null;

  function init() {
    map = L.map("map", {
      attributionControl: false, zoomControl: true,
      center: [27.5, 113.5], zoom: 5,
      maxBounds: XXK_CONF.bounds, maxBoundsViscosity: .6,
    });
    setBasemap("physical");
    lineLayer.addTo(map);
    dotLayer.addTo(map);
    curLayer.addTo(map);
  }

  function setBasemap(mode) {
    if (tileLayer) map.removeLayer(tileLayer);
    tileMode = mode; tileErrs = 0;
    const conf = BASEMAPS[mode];
    tileLayer = L.tileLayer(conf.url, { maxZoom: conf.maxZoom, maxNativeZoom: conf.maxNative }).addTo(map);
    tileLayer.on("tileerror", () => {
      if (++tileErrs > 6 && tileMode !== "physical") setBasemap("physical");  // 瓦片兜底
    });
  }

  /* ── 游程折线 ─────────────────────────────────────── */
  function render() {
    lineLayer.clearLayers(); dotLayer.clearLayers();
    XXK.trips.forEach(t => {
      if (hidden.has(t.id) || !t.path || t.path.length < 2) return;
      const sel = t.id === selId;
      const line = L.polyline(t.path, {
        className: "tripline", smoothFactor: 0,
        color: sel ? "#b23a2e" : t.color,
        weight: sel ? 5 : 3.2,
        opacity: sel ? 1 : .78,
        dashArray: t.stats.days > 40 ? null : null,
      });
      line.on("click", () => { select(t.id, { fly: false }); onSelect && onSelect(t); });
      line.bindTooltip(
        `${t.title} · ${t.year} · ${t.stats.days} 日 · ${t.stats.km.toLocaleString()} km`,
        { direction: "top", opacity: .95, className: "ftip" });
      line.addTo(lineLayer);
      // 起点·终点
      const head = t.path[0], tail = t.path[t.path.length - 1];
      L.circleMarker(head, {
        radius: 4.5, color: "#f6f3e6", weight: 1.5, fillColor: sel ? "#b23a2e" : t.color, fillOpacity: 1,
      }).bindTooltip(`${t.title} · 起点`, { direction: "top" }).addTo(lineLayer);
      L.circleMarker(tail, {
        radius: 3.2, color: "#f6f3e6", weight: 1.2, fillColor: "#8e2b22", fillOpacity: .95,
      }).bindTooltip(`${t.title} · 末锚`, { direction: "top" }).addTo(lineLayer);
    });
  }

  /* ── 选中游程：锚点层 + 视角 ─────────────────────── */
  function select(id, opt = {}) {
    selId = id;
    render();
    const t = XXK.trips.find(x => x.id === id);
    if (t && t.path.length > 1 && opt.fly !== false) {
      map.fitBounds(L.latLngBounds(t.path).pad(.25), { animate: true, duration: 1.1 });
    }
    renderDots(t);
    if (opt.day != null) markDay(t, opt.day, false);
  }

  function renderDots(t) {
    curLayer.clearLayers();
    if (!t) return;
    t.days.forEach((d, i) => {
      if (!d.anchor) return;
      const dot = L.circleMarker(d.anchor.pos, {
        radius: d.jump ? 5.5 : 4,
        color: "#f6f3e6", weight: 1.4, fillColor: "#24495a", fillOpacity: 1,
      });
      const dt = d.y && d.m && d.d ? `${d.y}年${d.m}月${d.d}日` : (d.h || "");
      dot.bindTooltip(
        `${dt} · ${d.anchor.name}${d.anchor.conf === "推" ? "（推）" : ""}${d.jump ? " ⚠跳段" : ""}`,
        { direction: "top", opacity: .95 });
      dot.on("click", () => onDayClick && onDayClick(t, i));
      dot.addTo(curLayer);
    });
  }

  /* 阅读高亮：当前日锚朱点大标 */
  function markDay(t, i, fly = true) {
    curDayIdx = i;
    curLayer.eachLayer(() => {});   // no-op 保持层引用
    renderDots(t);
    const d = t.days[i];
    if (d && d.anchor) {
      L.circleMarker(d.anchor.pos, {
        radius: 8, color: "#b23a2e", weight: 3, fillColor: "#b23a2e", fillOpacity: .35,
      }).bindTooltip(`◈ ${d.h} · ${d.anchor.name}`, { direction: "top" }).addTo(curLayer);
      /* 先停在途动画（fitBounds/flyTo 竞态会使 Leaflet 内部投影 NaN 抛
         "Invalid LatLng object"——书签「回到」与开程并发触发即中）；
         后台标签 Chromium 暂不布局 → 容器 0 尺寸 → project 除零 NaN，
         故加尺寸守卫（0 尺寸跳过飞行，回前台后随日导航再飞） */
      if (fly && map.getSize().x > 0) {
        map.stop();
        map.flyTo(d.anchor.pos, Math.max(map.getZoom(), 7), { duration: 1.0 });
      }
    }
  }

  function toggleTrip(id) {
    if (hidden.has(id)) hidden.delete(id);
    else hidden.add(id);
    render();
    return !hidden.has(id);
  }

  function flyTo(pos, zoom = 8) {
    map.flyTo(pos, zoom, { duration: 1.0 });
  }

  return {
    init, render, select, markDay, toggleTrip, flyTo, setBasemap,
    get map() { return map; },
    set onSelect(fn) { onSelect = fn; },
    set onDayClick(fn) { onDayClick = fn; },
    get selected() { return selId; },
    get hidden() { return hidden; },
    get curDay() { return curDayIdx; },
  };
})();
window.XKMAP = XKMAP;
