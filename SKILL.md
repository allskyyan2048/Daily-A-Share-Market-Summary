---
name: daily-a-share-market-summary
description: A股每日监测报告一键生成器。收盘后运行采集脚本抓取指数行情、涨跌分布、涨停/跌停/炸板池、行业与概念板块全量排行、主力资金、龙虎榜、两融、7x24快讯、当日披露财报（中报/年报/业绩预告），再整合当日重要财经新闻与A股大V/机构观点，产出单文件自包含 HTML 日报（ECharts 图表 + 图/表切换 + TLDR 结论卡）。适用于每个交易日收盘后做每日A股监测、每日复盘报告的场景。触发词：A股每日监测、每日监测报告、A股日报、收盘监测、每日监测。
---

# Daily A-Share Market Summary

## Overview

每个交易日收盘后（约 17:00 后）产出一份单文件 HTML 日报，涵盖：行情、板块与资金、涨停梯队与龙虎榜、当日重要财经新闻、当日披露财报、大V与机构观点、明日关注清单。数据采集由两个脚本完成（无需 akshare/mootdx），报告基于模板生成，交付前强制 JS 语法校验。

## 工作流（按序执行）

### Step 0 前置判断

- 确认当前时间已收盘（A股 15:00 收盘，建议 17:00 后跑，数据更稳）。盘前/盘中请求则提醒用户改为收盘后运行。
- 在用户工作区约定目录：数据 `data/`，报告 `daily-review/A股每日监测报告_YYYYMMDD.html`。若用户未指定 workspace，沿用 `C:\Users\Admin\WorkBuddy\A股每日监测\`。

### Step 1 数据采集（运行脚本，不要重写）

```powershell
$SKILL = "C:/Users/Admin/.workbuddy/skills/daily-a-share-market-summary"
# 交易日当天（默认今天，--date 可指定）
python "$SKILL/scripts/collect_market.py"   --date 2026-08-26 --out <workspace>/data
python "$SKILL/scripts/collect_earnings.py" --date 2026-08-26 --out <workspace>/data
```

- 脚本自带请求间隔、重试、多镜像切换与日志双写（`market_log.txt` / `earnings_log.txt`），跑完 Read 日志确认各数据块非空（尤其 `industry_all` 概念板块易因 502 失败）。
- 失败数据块：重跑一次；仍失败则在报告中标注缺失，不编造数据。
- Windows 下若 PowerShell 捕获不到 stdout，直接 Read 日志文件即可。
- 接口细节与坑点见 `references/api_endpoints.md`。

### Step 2 新闻与大V观点（WebSearch 补充）

采集脚本只提供 7x24 快讯原始流（`news_flash`），新闻与大V观点需用 WebSearch 二次加工：

- 新闻：从 `news_flash` 筛选重要条目，早间宏观新闻用 WebSearch 补（东财 sortEnd 分页无效）；按「宏观与政策 / 市场与海外 / 公司要闻」三类各取 5~10 条，每条含关键数字。
- 大V与机构观点：WebSearch 当日复盘类内容（检索词如"A股 复盘 8月26日"、"券商 研报 A股 观点"），取 8~12 条，每条标注倾向标签（tag-bull 偏多 / tag-neutral 中性 / tag-bear 偏空），并归纳三句话共识。若 REDFOX_API_KEY 已配置可改用 gzh-astock-top 技能取原始公众号数据。
- 财报季（4月底/8月底/10月底前两周）：`total_count` 可能上千家，重点抓行业脉络而非逐家罗列。

### Step 3 生成报告（基于模板）

复制 `assets/report_template.html` 到 `daily-review/A股每日监测报告_YYYYMMDD.html`，按模板内注释替换所有 `{{PLACEHOLDER}}`：

**结构（固定 7 章 + TLDR）**：TLDR 结论卡 → 一、市场概览 → 二、板块与资金 → 三、涨停梯队与龙虎榜 → 四、当日重要财经新闻 → 五、财报聚焦 → 六、大V与机构观点 → 七、明日关注清单。

**硬性规范**：
- 单文件自包含，ECharts 用 CDN `https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js`，浅色主题。
- A股配色：红涨 `#dc2626`、绿跌 `#16a34a`；`class="up"`=涨、`class="down"`=跌，绝不混用。
- TLDR 卡必须含：一句话定性、6~10 个 KPI、条件→操作→止损三段式。
- 框架 JS（`toggleVT` / `window.chartsMap` / resize 监听）保持模板原样，只填数据数组。
- 图表必须有对应的表格视图（图/表切换按钮），5 张图：指数涨跌幅、涨跌分布、行业板块涨跌 TOP、主力资金、财报净利润 TOP15。
- 每个观点/结论须有数据支撑（来自采集 JSON 或检索结果），不编造数字。
- 页脚保留「以上分析基于公开数据，不构成投资建议」风险提示与数据口径说明。

### Step 4 校验（交付前强制）

```powershell
python "$SKILL/scripts/validate_report_js.py" <workspace>/daily-review/A股每日监测报告_YYYYMMDD.html
```

必须输出 `node --check PASS` 才可交付；FAIL 则修到通过为止。

### Step 5 交付

- 用 present_files 展示 HTML 报告。
- 聊天中只给：一句话当日摘要 + 报告文件路径 + 数据缺失说明（如有）。不放长文。

## 数据字典速查

`market_data.json`：`indices`(10指数) `zd_fenbu`(涨跌分布) `limit_up_pool`/`limit_down_pool`/`broken_pool` `industry_all`(~496行业) `concept_all`(~504概念) `ths_hot`(强势股归因) `dragon_tiger`(龙虎榜) `margin`(两融) `news_flash`(快讯)。

`earnings_data.json`：`total_count`(披露总数) `profit_top`(净利TOP200) `forecasts`(业绩预告) `growth_top`(高增长) `loss_top`(亏损) `revenue_top`(营收榜)。

## 常见坑

1. `push2.eastmoney.com` 板块接口 502 → 脚本已自动切 `push2delay` 镜像，无需处理。
2. 板块列表 pz 上限 100 → 脚本已分页全量。
3. 东财 7x24 快讯 sortEnd 分页无效 → 早间新闻用 WebSearch 补。
4. 节假日/非交易日：池和快讯为空属正常，报告改为「休市日」简报或提示用户。
5. 财报季单日上千家披露：优先按行业脉络归纳 + TOP 榜展示，不逐家罗列。
