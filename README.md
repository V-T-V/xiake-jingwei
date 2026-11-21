# 霞客经纬 · Xiake Jingwei

明·徐弘祖《徐霞客游记》数字人文平台——方舆经纬（[D:\W_A_W\HHH](../HHH)，点·府治）与
水道经纬（[D:\W_A_W\SDJW](../SDJW)，线·水道）的姊妹项目。
同一套方法论，第三种空间诗学：**线（游程）× 时序（日记日）**——
廿二程、五百零六日条，自天台雁宕而嵩华恒岱，尽浙赣楚桂之遥。

```
霞客经纬/
  index.html · 3d.html    # 四模式舆图 + 三维形胜（MapLibre 地形 · 沿游线飞览）
  data/trip_data.js       # 22 游程（日锚/折线/里程/置信）· 管线生成
  data/read/000..021.js   # 循程阅读层（逐日条目 · 懒加载 · 编者注淡显）
  data/text/p01..p22.js   # 全文检索层（注释已剔 · 懒加载 · Worker 扫描）
  data/stats.js           # 计量层（build_stats.py 产物，前端只读脚本数字）
  tools/                  # 管线：抓取 → 解析 → 地名 → 构建 → lint → 计量
  tests/                  # 断言页（数据 14 项 · 循程 12 项）
  docs/stats.json · ANALYSIS.md   # 数字存档与文本计量（同一口径）
```

## 快速开始

```bash
python -m http.server 9400 &       # 起本地服务
python tools/fetch_text.py         # Phase 0 抓取（断点续抓，已有则跳过）
python tools/parse_trips.py        # Phase 1 篇章 → 506 日条
python tools/build_trip_data.py    # Phase 2 锚点/游线/里程 + 前端产物
python tools/build_stats.py        # 计量（data/stats.js · docs/stats.json · ANALYSIS.md）
python run_tests.py                # lint 142 项 + 数据断言 + 断言页
```

## 核心体验

| # | 功能 | 入口 |
|---|---|---|
| 1 | **舆图**——22 游程分色折线，悬停篇名/年/里程，点击开程；纲目眼睛开关单线显隐 | 默认 |
| 2 | **循程而读**——滚动日记，地图沿游线飞行、朱点标记当日锚；Alt+↑↓ 日导航 | 点任一游程 / `#trip=t01&d=3` |
| 3 | **深链**——`#trip=xxx&d=n`（循程）/ `#t=xxx`（详情）/ `#m=stats`（模式），刷新可复原 | 自动写回 |
| 4 | **全文检索**——Worker 纯数据扫描 22 懒加载分片（编者注已剔，搜的是霞客原文） | 顶栏 |
| 5 | **霞客计量**——字频六十 / 游程长短 / 词汇场 / 游年分布（凡数字出自脚本） | 底栏「△ 计量」 |
| 6 | **三维形胜**——MapLibre 真地形上沿游线飞览（40 段渐近，DEM 失联自动降级） | 底栏「⛰ 形胜」 |
| 7 | TTS 循程听书 · 夜读墨色 · PWA 三级缓存离线 | 循程条「▷ 朗读」/ 底栏 |

## 数据边界（诚实口径）

- **文本**：国学导航本（GB18030，HTTP 直抓 22 页），通行「前半部」——
  **止于粤西游日记二**。缺：粤西游日记三四、黔游日记、滇游日记十三、盘江考/溯江纪源等附编。
  维基文库 zh.wikisource.org 在本建站网络不可达（TLS 握手超时，curl/WebFetch 双证），
  guwendao 需登录、guoxuedashi 域名改投——数据源探测记录见 `tools/fetch_text.py` 头注。
  缺就是缺，不以节选冒充全书。
- **字数**：原文 233,664 字 + 编者括号注 22,305 字（题解/音注分离，不入统计与检索）。
- **日条**：行首日期标记（干支纪年/闰月/晦朔/廿X日）+ 句末标点后日号分段 → 506 条；
  编年 1613（癸丑·天台）—1637（丁丑·粤西）。纪年以干支推（版内公元注有误，如 002「丙辰岁
  （1618年）」实为 1616，已正）。
- **地名**：294 条人工地名表（tools/gazetteer.py），**篇内 scope 消歧**（玉女峰·武夷/华山、
  建昌·九江/南城 等 40+ 组）；逐日首现法取锚，坐标今地常识定位，全部 `src:"derived"`，
  置信 确 246 / 推 54，日锚覆盖 59.3%。
- **里程**：锚点折线 haversine 累计 15,077 km（>400km 跳段标 ⚠ 不计入；含同地往返——
  粤西期为静闻病情数度折返，折线如实反映文本行踪，**非人行实距**）。
- **已知误锚风险**：文本提及而未亲历之地可能占锚（如楚游述及安福）——scope 表已尽力消歧，
  存疑处 conf=推 + ⚠ 双重标示。

## 架构

- JS 模块：`config → map → tripnav → reader → search → stats → app`（defer 链严格有序，
  核心/特性分层；Worker 纯数据无 DOM）
- 禁止清单（承方舆经纬）：`map.fire("click")` / `innerHTML.indexOf()` 验证 / `window._闭包量` /
  `git mv -q` / Worker 引 DOM / 核心模块硬引特性模块 DOM / 版本号手列清单 bump / `|| true` 兜底
- 版本：`python tools/bump_version.py OLD NEW`——全站 `?v=` 一步到位（lint 校验一致性）

## 复用与致谢

基建承姊妹站（方舆经纬八件兵器 · 水道经纬循线范式）：PWA 三级缓存 · 检索 Worker ·
底图兜底 · 深链/分享 · MapLibre 地形竞态规避。底图 Esri World Physical / Imagery。
文本源：国学导航（guoxue123.com）。
