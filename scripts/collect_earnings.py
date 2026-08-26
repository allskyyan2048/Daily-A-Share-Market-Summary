#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A股每日监测 - 财报数据一键采集

数据源: 东财 datacenter-web
  RPT_LICO_FN_CPD           业绩报表(中报/年报等正式披露, 按 NOTICE_DATE 过滤)
  RPT_PUBLIC_OP_NEWPREDICT  业绩预告

用法:
  python collect_earnings.py                          # 默认今天, 输出到 ./data
  python collect_earnings.py --date 2026-08-26 --out D:/work/data

输出:
  <out>/earnings_data.json
  <out>/earnings_log.txt

字段速查:
  SECURITY_NAME_ABBR 公司简称  PARENT_NETPROFIT 归母净利(元)
  SJLTZ 净利同比(%)           TOTAL_OPERATE_INCOME 营收(元)
  YSTZ 营收同比(%)             NOTICE_DATE 公告日期
"""
import argparse
import datetime
import json
import os
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
BASE = "https://datacenter-web.eastmoney.com/api/data/v1/get"


def dc_query(report_name, filter_str, page_size=100,
             sort_columns="PARENT_NETPROFIT", sort_types="-1"):
    params = {
        "reportName": report_name, "columns": "ALL",
        "filter": filter_str, "pageNumber": "1", "pageSize": str(page_size),
        "sortColumns": sort_columns, "sortTypes": sort_types,
        "source": "WEB", "client": "WEB",
    }
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, headers={"Referer": "https://data.eastmoney.com/", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as resp:
        d = json.loads(resp.read().decode("utf-8"))
    if d.get("result") and d["result"].get("data"):
        return d["result"]["data"], d["result"].get("count", 0)
    return [], 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat(),
                    help="公告日期 YYYY-MM-DD")
    ap.add_argument("--out", default="./data", help="输出目录")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    log_path = os.path.join(args.out, "earnings_log.txt")
    logf = open(log_path, "w", encoding="utf-8")

    def log(msg):
        print(msg)
        logf.write(msg + "\n")
        logf.flush()

    day = args.date
    result = {"notice_date": day}

    # 1. 正式业绩报表: 净利润 TOP200 (覆盖大公司)
    log("[1/5] 正式业绩报表 净利润降序 TOP200 ...")
    rows, cnt = dc_query("RPT_LICO_FN_CPD",
                         "(NOTICE_DATE='{}')".format(day),
                         page_size=200, sort_columns="PARENT_NETPROFIT")
    log("  今日披露 {} 家, 取 {}".format(cnt, len(rows)))
    result["profit_top"] = rows
    result["total_count"] = cnt
    time.sleep(1.2)

    # 2. 业绩预告
    log("[2/5] 业绩预告 ...")
    rows, cnt2 = dc_query("RPT_PUBLIC_OP_NEWPREDICT",
                          "(NOTICE_DATE='{}')".format(day),
                          page_size=200, sort_columns="PREDICT_AMT_LOWER")
    log("  今日披露业绩预告 {} 家".format(cnt2))
    result["forecasts"] = rows
    time.sleep(1.2)

    # 3. 高增长榜: 净利同比降序, 营收>10亿(避免小基数)
    log("[3/5] 高增长榜(净利同比降序, 营收>10亿) ...")
    rows, _ = dc_query("RPT_LICO_FN_CPD",
                       "(NOTICE_DATE='{}')(TOTAL_OPERATE_INCOME>1000000000)".format(day),
                       page_size=60, sort_columns="SJLTZ")
    log("  取 {}".format(len(rows)))
    result["growth_top"] = rows
    time.sleep(1.2)

    # 4. 亏损榜: 净利润升序
    log("[4/5] 亏损榜(净利润升序) ...")
    rows, _ = dc_query("RPT_LICO_FN_CPD",
                       "(NOTICE_DATE='{}')".format(day),
                       page_size=40, sort_columns="PARENT_NETPROFIT", sort_types="1")
    log("  取 {}".format(len(rows)))
    result["loss_top"] = rows
    time.sleep(1.2)

    # 5. 营收规模榜: 大市值公司覆盖
    log("[5/5] 营收规模榜(营收降序) ...")
    rows, _ = dc_query("RPT_LICO_FN_CPD",
                       "(NOTICE_DATE='{}')".format(day),
                       page_size=60, sort_columns="TOTAL_OPERATE_INCOME")
    log("  取 {}".format(len(rows)))
    result["revenue_top"] = rows

    out_path = os.path.join(args.out, "earnings_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    log("Saved -> " + out_path)
    log("=== DONE earnings_data ===")
    logf.close()


if __name__ == "__main__":
    main()
