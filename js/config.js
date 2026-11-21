/* ═══════════ 霞客经纬 · 配置（展示层） ═══════════
   数据在 data/trip_data.js（管线生成）；本文件为展示层配置。 */

const XXK_CONF = {
  bounds: [[20, 100], [42, 124]],
  version: "v1",
  port: 9400,
};

/* 底图：绢面地形 ↔ 卫星影像（与水道经纬同源瓦片） */
const BASEMAPS = {
  physical: {
    name: "地形",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
    maxNative: 8, maxZoom: 12,
  },
  imagery: {
    name: "影像",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    maxNative: 12, maxZoom: 12,
  },
};

/* 词表（计量层） */
const WORDLISTS = {
  landform: ["山", "峰", "岭", "崖", "岩", "洞", "石", "瀑", "溪", "涧", "潭", "泉"],
  motion: ["行", "登", "上", "下", "渡", "宿", "饭", "抵", "至", "入", "逾", "涉"],
  weather: ["雨", "雾", "云", "雪", "风", "霜", "日", "晴", "寒"],
  wonder: ["奇", "胜", "绝", "妙", "异", "灵", "秀", "险"],
};

/* 游程分色：五次大游段系（名山/浙/赣/楚/粤西）微调色相 */
const PHASE_TINT = {
  "名山": "#8a5a2b", "浙": "#446b35", "赣": "#2f5d70", "楚": "#5d4a7d", "粤西": "#8e2b22",
};

/* 深链语法：
   #trip=t01&d=3   循程而读（第 4 日锚）
   #t=t01          游程详情
   #m=map|read|stats|about   模式
*/
