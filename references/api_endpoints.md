# A股每日监测 - 数据接口参考

全部为公开 HTTP 接口, 无需鉴权. 频率限制宽松, 但建议请求间隔 ≥1s.
脚本 `collect_market.py` / `collect_earnings.py` 已封装以下全部接口.

## 1. 腾讯指数行情 (qt.gtimg.cn)

```
GET https://qt.gtimg.cn/q=sh000001,sz399001,sz399006,sh000688,sh000016,sh000300,sh000852,sh000905,sh000922,bj899050
```

- 响应为 GBK 文本, 多行 `v_sh000001="..."`; `~` 分隔字段
- 常用字段下标: `1`名称 `3`现价 `4`昨收 `5`今开 `31`涨跌额 `32`涨跌幅 `33`最高 `34`最低 `37`成交额(万) `38`换手率 `44`总市值(亿)
- 优点: 不封 IP, 可批量; 缺点: 仅快照无历史

指数代码速查:
| 代码 | 指数 | 代码 | 指数 |
|---|---|---|---|
| sh000001 | 上证指数 | sh000300 | 沪深300 |
| sz399001 | 深证成指 | sh000852 | 中证1000 |
| sz399006 | 创业板指 | sh000905 | 中证500 |
| sh000688 | 科创50 | sh000922 | 中证红利 |
| sh000016 | 上证50 | bj899050 | 北证50 |

## 2. 东财 push2ex (涨跌分布 / 涨跌停池)

```
GET https://push2ex.eastmoney.com/getTopicZDFenBu?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt
GET https://push2ex.eastmoney.com/getTopicZTPool? ut=...&dpt=wz.ztzt&Pageindex=0&pagesize=500&sort=fbt:asc&date=YYYYMMDD
GET https://push2ex.eastmoney.com/getTopicDTPool?...   # 跌停池
GET https://push2ex.eastmoney.com/getTopicZBPool?...   # 炸板池
```

- `ut=7eea3edcaed734bea9cbfc24409ed989` 为东财网页公开 token
- 池字段: `c`代码 `n`名称 `zdp`涨跌幅 `fund`封单资金(元) `fbt`首次封板时间 `zbc`炸板次数 `ltsz`流通市值 `hybk`行业板块
- 注意: date 参数为 `YYYYMMDD` 紧凑格式; 只能查最近若干交易日

## 3. 东财板块排行 (clist)

```
GET https://push2delay.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=...
```

**坑点(重要)**:
- `push2.eastmoney.com` 主站高频访问返回 502, **务必优先用 `push2delay.eastmoney.com` 镜像**
- `pz` 上限 100, 全量必须分页 `pn=1..N`, 以 `data.total` 为准 (行业约 496 个, 概念约 504 个)
- `fs=m:90+t:2` 行业板块, `fs=m:90+t:3` 概念板块
- fields: `f2`现价 `f3`涨跌幅 `f12`代码 `f14`名称 `f62`主力净额(元) `f104`上涨家数 `f105`下跌家数 `f140`领涨股名 `f136`领涨股涨幅
- 个股排行可换 fs: `m:0+t:6` 深A, `m:1+t:2` 沪A, `m:0+t:80+s:2048` 创业板

## 4. 同花顺强势股题材归因

```
GET http://zx.10jqka.com.cn/event/api/getharden/date/YYYY-MM-DD/orderby/date/orderway/desc/charset/GBK/
```

- 返回当日强势股 + 题材归因 `reason` 字段 (涨停原因一句话)
- `errocode=0` 为成功(注意拼写就是 errocode)

## 5. 东财数据中心 (datacenter-web)

```
GET https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=XXX&columns=ALL&filter=(...)&pageNumber=1&pageSize=200&sortColumns=YYY&sortTypes=-1&source=WEB&client=WEB
```

- filter 需 URL 编码; 多条件 `(A='x')(B='y')` 拼接

常用 reportName:

| reportName | 用途 | 关键过滤字段 |
|---|---|---|
| RPT_LICO_FN_CPD | 业绩报表(正式披露) | NOTICE_DATE 公告日 |
| RPT_PUBLIC_OP_NEWPREDICT | 业绩预告 | NOTICE_DATE |
| RPT_DAILYBILLBOARD_DETAILSNEW | 龙虎榜明细 | TRADE_DATE 交易日 |
| RPTA_RZRQ_LSHJ | 两融余额(全市场) | 按 dim_date 倒序取最新 |

RPT_LICO_FN_CPD 常用列:
- `SECURITY_NAME_ABBR` 简称, `PARENT_NETPROFIT` 归母净利(元), `SJLTZ` 净利同比%, `TOTAL_OPERATE_INCOME` 营收(元), `YSTZ` 营收同比%

排序技巧: 净利润榜 `sortColumns=PARENT_NETPROFIT`; 高增长榜 `sortColumns=SJLTZ` + filter 加 `(TOTAL_OPERATE_INCOME>1000000000)` 过滤小基数; 亏损榜 `sortTypes=1` 升序.

## 6. 东财 7x24 快讯

```
GET https://np-weblist.eastmoney.com/comm/web/getFastNewsList?client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize=100&req_trace=<uuid>
```

- `fastColumn=102` 重点栏目; 返回 `data.fastNewsList[]`: `title` / `summary` / `showTime`
- **坑点**: `sortEnd` 分页参数实际无效(总是返回最新一批), 早间新闻补不齐时改用 WebSearch

## 7. 已知局限与替代方案

| 需求 | 现状 | 替代 |
|---|---|---|
| 公众号大V榜单 | gzh-astock-top 依赖 REDFOX_API_KEY | WebSearch 检索大V观点 |
| 指数历史K线 | 腾讯仅快照 | mootdx/akshare(需安装) |
| 早间宏观新闻 | 7x24 sortEnd 失效 | WebSearch |

## 8. Windows 运行注意

- PowerShell 可能捕获不到子进程 stdout: 采集脚本已内置双写日志文件 (`market_log.txt` / `earnings_log.txt`), 直接 Read 日志即可
- 所有 Python 脚本内部强制 UTF-8 读写, 不依赖控制台编码
- 运行方式: `python <script> --date YYYY-MM-DD --out <dir>`
