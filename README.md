# Daily A-Share Market Summary

一键生成 A 股每日监测报告（自包含 HTML，内置 ECharts 图表 + 图/表切换 + TLDR 结论卡）。

## 📦 什么是这个 skill？

这是一个 WorkBuddy skill，能够在每个交易日收盘后自动完成：

1. **行情采集**：指数、涨跌分布、涨停/跌停/炸板池、行业与概念板块全量排行、龙虎榜、两融、7x24 快讯。
2. **财报采集**：当日披露的中报/年报/业绩预告，生成净利润/高增长/亏损/营收榜单。
3. **新闻与观点**：结合 7x24 快讯和 WebSearch（或 REDFOX_API_KEY）整理重要财经新闻和大V/机构观点。
4. **报告生成**：基于模板生成单文件自包含 HTML 报告（含 5 张 ECharts 图表，图/表可切换）。
5. **强制校验**：交付前必须通过 `node --check` 对内联 JS 进行语法自检。
6. **轻量交付**：聊天中仅给出“一句话当日摘要 + 报告文件路径 + 数据缺失说明”。

> 本 skill 纯使用公开接口与标准库实现，无需 akshare/mootdx 等第三方依赖。

## 🚀 开始使用

### 前置条件

- Python 3.10+（推荐使用 WorkBuddy 自带的 managed python）
- Node.js 18+（用于 `node --check` 校验报告内联 JS；仅在交付前需要）
- 网络访问（需能访问腾讯财经、东方财富、同花顺等公开接口）

### 步骤

1. **获取 skill**（两种方式均可）

   - 直接从本仓库克隆/下载：
     ```bash
     git clone https://github.com/yourname/Daily-A-Share-Market-Summary.git
     # 或下载 ZIP 解压
     ```

   - 或将本目录 `daily-a-share-market-summary/` 复制到你的 WorkBuddy skills 目录：
     ```
     <workbuddy_root>/.workbuddy/skills/daily-a-share-market-summary/
     ```

2. **采集数据**（以交易日 2026-08-27 为例）

   ```powershell
   # 假设你已进入 skill 目录
   python scripts/collect_market.py   --date 2026-08-27 --out ./data
   python scripts/collect_earnings.py --date 2026-08-27 --out ./data
   ```

   - 脚本会在 `./data/` 目录下生成 `market_data.json`、`earnings_data.json` 以及日志文件。
   - 失败的数据块会在日志中标注，报告中会注明缺失。

3. **补充新闻与大V观点**（可选，但推荐）

   - 使用你偏好的搜索引擎或工具（WorkBuddy 自带的 WebSearch 技能、浏览器等），收集：
     - 当日重要财经新闻（宏观政策、市场海外、公司要闻，各 5~10 条）。
     - 当日大V/机构观点（可检索 “A股 复盘 YYYYMMDD”、“券商 研报 A股 观点”）。
   - 将观点以纯文本形式保存，稍后会手动填入报告模板（或自行改写脚本以自动读取）。

4. **生成报告**

   复制对应语言的模板到报告目录，然后手动填充数据（或编写小脚本自动替换 `{{PLACEHOLDER}}`）：

   ```powershell
   # 中文报告模板
   copy assets\report_template.html daily-report\A股每日监测报告_20260827.html
   # 英文报告模板
   copy assets\report_template_en.html daily-report\A股每日监测报告_20260827_en.html
   # 法文报告模板
   copy assets\report_template_fr.html daily-report\A股每日监测报告_20260827_fr.html
   ```

   > 注意：报告文件名中的日期须与采集日期一致（`YYYYMMDD` 格式）。

   用文本编辑器打开 HTML 文件，替换所有 `{{PLACEHOLDER}}` 为对应数据（市场概览表格、涨停梯队列表、财报榜单、新闻列表、大V观点等）。

5. **交付前强制 JS 校验**

   ```powershell
   python scripts/validate_report_js.py daily-report\A股每日监测报告_20260827.html
   ```

   必须看到输出 `=== node --check PASS ===`（退出码 0）才能交付。若失败，请根据提示修正内联 JS（一般为模板填充后遗留的语法错误），再次校验直至通过。

6. **展示报告**

   在 WorkBuddy 中使用 `present_files` 展示 HTML 报告，或直接在浏览器中打开。

   聊天中只需输出：
   - 一句话当日市场摘要（例如：`8月27日 A股放量长阳（上证 3956.57 +1.13%），成交 2.14 万亿，放量 3191 亿`）。
   - 报告文件路径（例如：`daily-report\A股每日监测报告_20260827.html`）。
   - 如有数据缺失，简要说明（例如：`注：概念板块采集失败，暂无数据`）。

## 📂 目录结构

```
daily-a-share-market-summary/
├── SKILL.md                 # Skill 使用说明（本文件的精简版）
├── README.md                # 你正在阅读的文件
├── LICENSE                  # MIT 许可证
├── .gitignore               # Git 忽略文件
├── requirements.txt         # 空文件（纯标准库，无外部依赖）
├── assets/
│   ├── report_template.html     # 中文报告模板
│   ├── report_template_en.html  # 英文报告模板
│   ├── report_template_fr.html  # 法文报告模板
├── references/
│   └── api_endpoints.md         # 接口细节与常见坑
└── scripts/
    ├── collect_market.py        # 行情数据采集
    ├── collect_earnings.py      # 财报数据采集
    └── validate_report_js.py    # 报告内联 JS 语法校验（node --check）
```

## 📄 数据来源与接口说明

详见 `references/api_endpoints.md`，包括：

- 指数行情：腾讯财经 `qt.gtimg.cn`
- 涨跌分布 / 涨停池：东方财富 `push2ex.eastmoney.com`
- 行业/概念板块：东方财富 `push2delay.eastmoney.com`（主站易 502，脚本已自动切换）
- 强势股题材归因：同花顺 `zx.10jqka.com.cn`
- 龙虎榜 / 两融：东方财富数据中心 `datacenter-web.eastmoney.com`
- 7x24 全球快讯：东方财富 `np-weblist.eastmoney.com`

## ⚠️ 常见问题

1. **板块接口 502 Bad Gateway**  
   → 脚本内部已配置多镜像 fallback（`push2delay` 优先），无需人工干预。

2. **板块列表只能拿到 100 条**  
   → 脚本已实现分页全量（`pn=1..14, pz=100`，自动累计直到 `total`）。

3. **7x24 快讯 sortEnd 分页无效**  
   → 早间宏观新闻请自行用 WebSearch 补齐。

4. **Windows PowerShell 捕获不到子进程 stdout**  
   → 本脚本同时写日志文件（`market_log.txt`、`earnings_log.txt`），建议直接阅读日志。

5. **节假日/非交易日**  
   → 池和快讯为空属正常，报告会显示“休市日”或提示用户。

6. **财报季单日上千家披露**  
   → 建议仅展示行业脉络 + 净利润 TOP 前 15、高增长榜、亏损榜、营收榜，不逐家罗列。

## 🛡️ 风险提示

> 以上分析基于公开数据，不构成投资建议。市场有风险，投资需谨慎。

## 📄 许可证

本 skill 采用 [MIT 许可证](./LICENSE)，欢迎自由使用、修改和分发。

## 🙋‍♂️ 贡献

欢迎提交 Issue 或 Pull Request 来改进此 skill！

- 发现数据接口失效？请在 Issues 中报告。
- 有更好的报告模板或额外指标？请提交 PR。
- 让这个 skill 对更多 A 股爱好者有用！

---
*由 WorkBuddy 生成并维护。*  
*最后更新：2026-08-27*