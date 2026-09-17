# www.artmosaicfactory.com 站点评估（2026-09-15 实测）

> 取证方式：本机 **HTTPS 到该域名被 TLS 层阻断**（curl 443 一律 000，`--resolve` 也失败），但 **HTTP(80) 可正常取到 GitHub Pages 内容**，
> 因此本次所有"线上实测"数据来自 `http://www.artmosaicfactory.com`（内容与 https 一致，仅协议不同）。
> 取到的线上首页 `sha256=e7935a0a9889906b`，37,242 bytes。

---

## 一、结论速览

| 维度 | 评价 | 关键证据 |
|---|---|---|
| 技术 SEO | **良好** | title 60 字符含主词+产地；meta description 154 字符；canonical 指 https 正式域；robots + sitemap 正确；viewport 有；lang=en |
| 结构化数据 | **良好** | 3 块 JSON-LD（Organization / WebSite / WebPage）全部可解析，URL 全绝对，无相对路径 |
| On-page | **良好** | H1 唯一（1 个 H1 / 6 个 H2 / 10 个 H3），正文 724 词，32 张图 **全部有 alt** 且描述具体 |
| 性能 | **中等偏弱** | 首图 `preload + fetchpriority` 已做；内联 CSS 11KB、内联 JS 2KB（很轻）；**但滚动到底共传 5.7MB 图片** |
| 图片交付 | **主要短板** | 单图尺寸其实合理（700/900/1400px，与显示宽度匹配），**问题是"一个尺寸发给所有设备"** |
| 可访问性/第三方 | **良好** | 无第三方脚本（仅 Google Fonts + schema.org + wa.me），字体用 preconnect + `display=swap` |
| 内容深度 | **受限** | 单页站，sitemap 仅 1 条 URL；关键词覆盖面天然有限 |

**一句话**：技术 SEO 底子扎实（上次那一轮没白做），**真正拖后腿的是移动端图片体积**；
另外有一个**必须先处理的工程风险**——本地 git 仓库落后于线上。

---

## 二、必须优先处理（P0）

### P0-1 本地仓库落后线上一个内容区块 ⚠️

| 项 | 结果 |
|---|---|
| 线上首页 | 37,242 bytes，含 `<section class="section makingof" id="makingof">`（"In the Workshop / How a Mosaic Work Is Created"） |
| 本地 `index.html` | 33,861 bytes，**`makingof` 出现 0 次**（线上 8 次） |

**风险**：现在如果从本地直接改完 push，线上那一节会被覆盖掉（等于删内容）。
**处置**：改版前先把线上版本取回仓库并对齐（或先 `git pull` 看是否有你直接在 GitHub 上提交的版本）。
本机已把线上版本下载到缓存，可直接作为对齐基准。

---

## 三、值得修（P1）

### P1-1 移动端图片体积：4.72MB → 1.11MB（省 76%）

实测（`tools/webp_bench.py` 与移动变体基准）：

| 资源 | 现状 | 移动端适配后 | 节省 |
|---|---|---|---|
| 画廊 17 张 | 2.40 MB | 400px WebP **0.65 MB** | −73% |
| 背景墙 10 张 | 2.32 MB | 400px WebP **0.46 MB** | −80% |
| **滚动全站图片** | **4.72 MB** | **1.11 MB** | **−76%** |
| 首图 hero.jpg | 331 KB（1600×1066） | 900px WebP **91 KB** | −72% |

**注意**：只做"全站转 WebP"收益有限——实测 33 张图仅省 **15%**（5.96→5.05MB），
因为单图尺寸本来就跟显示宽度匹配、且马赛克纹理压缩收益低（`bs_05_leopard` 仅省 1%）。
**真正的收益来自按设备给不同尺寸**（`<picture>` + `srcset/sizes`，移动端出 400px 变体）。

### P1-2 首图 LCP 优化

`hero.jpg` 已 `preload + fetchpriority=high`（好），但给移动端发的是 1600px 原图。
改成 `srcset`（900w / 1600w）+ `sizes` 后，移动端首屏图片从 331KB 降到 91KB。

---

## 四、可以排期（P2）

| 项 | 现象 | 建议 |
|---|---|---|
| HTTP 未跳 HTTPS | `http://` 直接返回 **200**（无 301 到 https），`Server: GitHub.com` | 疑似 GitHub Pages 的 *Enforce HTTPS* 未开启；请在浏览器无痕窗口开 `http://` 复核（本机 TLS 被阻断，验不了 https 侧） |
| `og.jpg` 166KB | 1200×630，偏大 | 压到 ~120KB（分享卡片足够） |
| 1 张图 alt 与画面不符 | `handcut_03` 的 alt 写 "Grey crowned **cranes** … **above a fireplace**"；实拍画面里**只有一只**灰冠鹤，且壁画是**铺满壁炉所在整面墙**、鹤在壁炉**右侧**，"above a fireplace" 不准确 | 改为："Handcut mosaic mural with botanical trees and a grey crowned crane covering the wall around a fireplace" |
| 单页站结构 | sitemap 仅 1 条 URL | 若目标是自然流量，建议拆分：产品/工艺页、应用场景页（酒店/住宅/浴室）、案例页、市场页；否则只能吃品牌词 |
| 无 `srcset` | 32 张图均为固定宽度 | 与 P1-1 合并处理 |

**alt 抽查结论**：抽查 2 张（`handcut_15`、`handcut_03`）——`handcut_15` 的 "Art Deco black and gold mosaic mural of a white leopard mid-stride in a luxury living room" 与画面**完全相符**；
`handcut_03` 有上述两处不符。整体 alt 质量高，属个别措辞问题。

---

## 五、本次测不了的部分（不编数字）

| 项 | 原因 | 怎么办 |
|---|---|---|
| Core Web Vitals 实测（LCP/INP/CLS 的 CrUX 75 分位） | 本机 TLS 到该域名被阻断；本地代理（127.0.0.1:7897）当前已停，PageSpeed Insights API 调不通 | 恢复代理后我用 PSI API 跑 mobile+desktop 并存 JSON；或你直接开 pagespeed.web.dev 贴截图给我 |
| GSC 收录与查询数据 | 需要你的 Google 账号授权（jerry888.xu@gmail.com） | 你确认后我走 GSC：URL Inspection + 页面/查询报告 + sitemap 状态 |
| 真实访客侧表现 | 同上 | 等 PSI/CrUX 数据 |

---

## 六、建议的下一步（三选一）

1. **先修工程风险 + 图片**：把线上版本对齐回仓库 → 生成 WebP + 移动端 400px 变体 → 加 `srcset`/`picture` → 改 `handcut_03` 的 alt → 本地自检 → push（预计滚动体积 4.72MB→1.11MB）
2. **先做内容扩张**：在单页基础上增加产品/应用/案例/市场子页（对自然流量影响最大，但工作量也最大）
3. **先看数据再动手**：恢复代理跑 PSI + 你授权 GSC，拿到真实 CWV 与查询词，再决定优先级

---

## 附：本次新增的可复用工具（在 `tools/` 下，只读，不改站点）

| 脚本 | 用途 |
|---|---|
| `tools/audit_live.py` | 线上/本地页面实测审计（80 条精简规则版）：head/结构化数据/图片/体积/第三方域，输出 P0-P2 结论 |
| `tools/image_inventory.py` | 图片清点：体积 + 像素尺寸 + HTML 声明显示宽，标出"超发"的图（纯 Python 解析 JPEG/PNG 头） |
| `tools/webp_bench.py` | 量化图片优化空间：全站转 WebP 的字节对比（不改原文件） |
