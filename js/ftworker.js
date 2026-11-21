/* 霞客经纬 · 全文检索 Worker（纯数据计算，无 DOM） */
onmessage = e => {
  const { q, texts, seq } = e.data;
  const hits = [];
  for (const v in texts) {
    const t = texts[v];
    if (!t) continue;
    let i = t.indexOf(q);
    let n = 0;
    while (i >= 0 && n < 4) {
      hits.push({ vol: +v, ctx: t.slice(Math.max(0, i - 22), i + q.length + 30) });
      n++;
      i = t.indexOf(q, i + q.length);
    }
    if (hits.length > 200) break;
  }
  hits.sort((a, b) => a.vol - b.vol);
  postMessage({ seq, hits });
};
