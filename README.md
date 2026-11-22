# 霞客经纬 · Xiake Jingwei

[![CI](https://github.com/V-T-V/xiake-jingwei/actions/workflows/ci.yml/badge.svg)](https://github.com/V-T-V/xiake-jingwei/actions/workflows/ci.yml)

明·徐弘祖《徐霞客游记》数字人文平台——方舆经纬（[D:\W_A_W\HHH](../HHH)，点·府治）与
水道经纬（[D:\W_A_W\SDJW](../SDJW)，线·水道）的姊妹项目。
同一套方法论，第三种空间诗学：**线（游程）× 时序（日记日）**——
**三源全编**：国学导航本 22 篇（gx）+ 文渊阁四库楊名時本滇黔补编 21 篇（kr）+
维基文库系通行本附编 9 篇（ws），合计五十二篇、九百六十九日条，自天台雁宕而嵩华恒岱，
尽浙赣楚桂之遥，更溯黔滇以抵腾越——盘江考、溯江纪源两附编俱得，全书主体至此无缺。

```
霞客经纬/
  index.html · 3d.html    # 四模式舆图 + 三维形胜（MapLibre 地形 · 沿游线飞览）
  data/trip_data.js       # 52 篇游程（日锚/折线/里程/置信/source 三源）· 管线生成
  data/read/000..051.js   # 循程阅读层（逐日条目 · 懒加载 · 编者注淡显）
  data/text/p01..p52.js   # 全文检索层（注释已剔 · 懒加载 · Worker 扫描）
  data_raw/kr/ data_raw/ws/ # 四库本 mandoku 原档 + ws 附编原档（存档不复算）
  data/stats.js           # 计量层（build_stats.py 产物，前端只读脚本数字）
  tools/                  # 管线：抓取 → 解析 → 地名 → 构建 → lint → 计量
  tests/                  # 断言页（数据 · 循程 · 书签回到竞态回归，iframe 驱动）
  docs/stats.json · ANALYSIS.md   # 数字存档与文本计量（同一口径）
```

## 快速开始

```bash
python -m http.server 9400 &       # 起本地服务
python tools/fetch_text.py         # Phase 0a 抓取 gx 底本（断点续抓，已有则跳过）
python tools/fetch_kr.py           # Phase 0b 抓取 kr 四库本（重试 5 次指数退避）
python tools/fetch_ws.py           # Phase 0c 抓取 ws 附编（盘江考自 TTS 语料切出验真）
python tools/parse_kr.py           # 滇黔补编：mandoku→21 篇卷切分（简体化·阙文注化）
python tools/parse_ws.py           # 附编收官：ws 9 篇（脚注剔除·简体化·零锚）
python tools/parse_trips.py        # Phase 1 三源篇章 → 969 日条
python tools/build_trip_data.py    # Phase 2 锚点/游线/里程 + 前端产物
python tools/build_stats.py        # 计量（data/stats.js · docs/stats.json · ANALYSIS.md）
python tools/build_paper_pdf.py    # P2 论文 PDF（ANALYSIS.md 改后必重跑，lint 哨兵联动）
python tools/export_data.py        # P2 古今对照三格式导出（docs/export/）
python tools/build_xref_fy.py      # P2 方舆互查桥（读 HHH site_data.js，HHH 只读绝不写入）
python run_tests.py                # lint + 数据断言（含 PDF 哨兵/互查桥/导出口径）+ 断言页
```

### 站际互查桥用法（相对深链约定）

「方舆」页签与样例的 ↗方舆 深链为**相对兄弟路径** `../HHH/#mode=舆图&p=<省id>&fu=<府名>`——
需**父目录同根服务**：在 `D:\W_A_W` 下 `python -m http.server 8000` 后，
`/XXK/`（本站）与 `/HHH/`（方舆经纬）同源可达，点击即跳；仅起本站 9400 服务时该链接不可达（属预期）。
桥数据由 `tools/build_xref_fy.py` 生成（`data/xref_fy.js`），HHH 目录一律只读。

## 核心体验

| # | 功能 | 入口 |
|---|---|---|
| 1 | **舆图**——52 篇分色折线，悬停篇名/年/里程，点击开程；纲目眼睛开关单线显隐 | 默认 |
| 2 | **循程而读**——滚动日记，地图沿游线飞行、朱点标记当日锚；Alt+↑↓ 日导航 | 点任一游程 / `#trip=t01&d=3` |
| 3 | **深链**——`#trip=xxx&d=n`（循程）/ `#t=xxx`（详情）/ `#m=stats`（模式），刷新可复原 | 自动写回 |
| 4 | **全文检索**——Worker 纯数据扫描 52 懒加载分片（编者注已剔，搜的是霞客原文） | 顶栏 |
| 5 | **霞客计量**——字频六十 / 游程长短 / 词汇场 / 游年分布（凡数字出自脚本） | 底栏「△ 计量」 |
| 6 | **三维形胜**——MapLibre 真地形上沿游线飞览（40 段渐近，DEM 失联自动降级） | 底栏「⛰ 形胜」 |
| 7 | TTS 循程听书 · 夜读墨色 · PWA 三级缓存离线 | 循程条「▷ 朗读」/ 底栏 |
| 8 | **☆ 书签收藏**（P1 尾项）——日条 ☆ 收藏，localStorage 持久化（上限 30），管理/删除/一键回到，深链 `#trip=xxx&d=n` 复原 | 循程条「☆ 收藏」/ 底栏「☆ 书签」 |
| 9 | **古今对照导出**（P2）——498 锚行 CSV（带 BOM，Excel 直开）/KML（Google Earth）/GeoJSON，字段 地名/所属篇/日条/坐标/今名/依据/置信(确\|推)/src；管线复算 `python tools/export_data.py`（与前端同口径） | 计量面板「古今对照 · 名录导出」 |
| 10 | **方舆互查桥**（P2）——霞客锚点 × 《读史方舆纪要》明府县（HHH 数据**只读**）：同名+今名匹配、同名异地省域消歧（最近府治定省 + ≤250km 距离闸），匹配不上如实计无对应；↗方舆深链直达对应府 | 顶栏「方舆」/ `#m=fy` |
| 11 | **论文 PDF**（P2）——`docs/霞客经纬-论文.pdf` 由 `python tools/build_paper_pdf.py` 排印，数字全出自 `docs/stats.json`；lint 哨兵：ANALYSIS.md 改动而 PDF 未重排即红 | docs/ |

## 数据边界（诚实口径 · 三源）

- **底本一 gx**：国学导航本（GB18030，HTTP 直抓 22 页），通行「前半部」——止于粤西游日记二。
  维基文库 zh.wikisource.org 于建站网络不可达（TLS 握手超时，curl/WebFetch 双证），
  guwendao 需登录、guoxuedashi 域名改投——数据源探测记录见 `tools/fetch_text.py` 头注。
- **底本二 kr**：kanripo **KR2k0135** 文渊阁四库全书本·楊名時重编订十二卷（mandoku 格式，
  raw.githubusercontent 直抓 13 文件，`tools/fetch_kr.py` 重试 5 次指数退避）。滇黔补编 21 篇：
  粤游三四（四库「西南游日记五六」）、黔游一二（七八）、滇游十四篇（九至廿二）、附记三篇
  （记游太华山·记滇中花木·记游颜洞）。提要自言「所缺者一篇而已」，卷内自注多处阙文
  （南宁段脱/武定后缺十九日/月终俱阙/永昌缺十日/卷尾「以下阙」）；
  **四库本有讳改删节风险**（抽样实证：天台篇同句同文率 89%（俱/并有喜态级异文），
  粤西游二全篇仅 gx 之 40%）——站内简体化呈现、罕字以 □ 存疑，每篇 source 字段（gx/kr）标注底本。
- **底本三 ws**：维基文库系通行本（季梦良/李介系口径）——michiboo/Classical_Chinese_Wikisource 镜像
  （溯江纪源 + 杂著七）+ raylexlee TTS 语料 030.txt（**盘江考自其中切出验真**：篇题行 +
  「南北两盘江，余于粤西已睹其下流」起「类一丘之貉也夫」止，2,525 字）。附编 9 篇：盘江考·溯江纪源
  （含馄土仁付梓叙，随原文保留）·永昌志略·法王缘起·近腾诸彝说略·鸡山志略一二·鸡山志目·丽江纪略。
  **考体文/志略零锚设计**（提及性地名皆叙事引称不占锚）；系年从权（附编无确年，暂系 1639）。
- **语料完备度（如实）**：三源合计后游记主体与两附编俱在；kr 阙段以编者注淡显（不入统计检索）；
  ws 与 kr 有版本源流之别（通行本 vs 四库），异文未逐篇校勘（抽样见 ANALYSIS）。
- **字数**：原文 469,749 字（gx 233,664 + kr 227,926 + ws 8,159）+ 编者注 27,702 字（分离，不入统计与检索）。
- **日条**：行首日期标记（干支纪年/闰月/晦朔/廿X日）→ 969 条（ws 9 篇为单块「篇首」，考体文无日条）；
  gx 另以句末标点后日号分段，kr 四库本每日自起一段（同行多日仅 0.2%，多为叙述性引日期，不切以免伪日条）。
  编年 1613（癸丑·天台）—1639（己卯·滇西）。纪年以干支推（版内公元注有误者已正）。
- **地名**：386 条人工地名表（tools/gazetteer.py），**篇内 scope 消歧**（玉女峰·武夷/华山、
  建昌·九江/南城 等 40+ 组；滇黔新增同名异地消歧：镇远（桂土州≠黔镇远府）/临安（滇建水≠浙临安）/
  太华山（滇碧鸡≠陕华山）/石屏（多作石屏风）/独山（山名≠州名）；泛词陷阱不收：三里=里程/木公=人名）；
  逐日首现法取锚，坐标今地常识定位，全部 `src:"derived"`，置信 确 360 / 推 138，日锚覆盖 51.4%（ws 附编零锚）。
- **里程**：锚点折线 haversine 累计 24,631 km（>400km 跳段标 ⚠ 不计入，现 2 处；含同地往返——
  粤西期为静闻病情数度折返，折线如实反映文本行踪，**非人行实距**）；滇黔补编贡献 9,554 km；ws 附编零里程（考体文）。
- **已知误锚风险**：文本提及而未亲历之地可能占锚（如楚游述及安福、滇一盘江叙事回指弥勒）——
  scope 表已尽力消歧，存疑处 conf=推 + ⚠ 双重标示。

## 架构

- JS 模块：`config → map → tripnav → reader → search → stats → bookmarks → xref → app`（defer 链严格有序，
  核心/特性分层；Worker 纯数据无 DOM；核心模块以 typeof 守卫引用特性模块（reader→XKBM））
- 禁止清单（承方舆经纬）：`map.fire("click")` / `innerHTML.indexOf()` 验证 / `window._闭包量` /
  `git mv -q` / Worker 引 DOM / 核心模块硬引特性模块 DOM / 版本号手列清单 bump / `|| true` 兜底
- 版本：`python tools/bump_version.py OLD NEW`——全站 `?v=` 一步到位（lint 校验一致性）

## 复用与致谢

基建承姊妹站（方舆经纬八件兵器 · 水道经纬循线范式）：PWA 三级缓存 · 检索 Worker ·
底图兜底 · 深链/分享 · MapLibre 地形竞态规避。底图 Esri World Physical / Imagery。
文本源：国学导航（guoxue123.com）。

学术引用：[CITATION.cff](CITATION.cff)（CFF 1.2.0 · dataset）——构建产物指纹账本另见 [SHA256SUMS](SHA256SUMS)，`python tools/build_sums.py` 重算、`run_tests.py` 对账。
