#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A股每日监测 - 行情数据一键采集

数据源:
  腾讯财经 qt.gtimg.cn        指数行情(GBK, 不封IP)
  东财 push2ex                涨跌分布 / 涨停池 / 跌停池 / 炸板池
  东财 push2delay              行业+概念板块排行(分页全量; push2 主站易502, 必用 delay 镜像)
  同花顺 zx.10jqka.com.cn     当日强势股题材归因
  东财 datacenter-web          龙虎榜 / 两融余额
  东财 np-weblist              7x24 全球快讯

用法:
  python collect_market.py                          # 默认今天, 输出到 ./data
  python collect_market.py --date 2026-08-26 --out D:/work/data

输出:
  <out>/market_data.json
  <out>/market_log.txt   (采集日志, 便于排查)

Windows 注意: PowerShell 可能捕获不到子进程 stdout, 本脚本同时写日志文件,
重定向运行亦可:  python collect_market.py ... *> run.log
"""
import argparse
import datetime
import json
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

INDEX_CODES = [
    "sh000001", "sz399001", "sz399006", "sh000688", "sh000016",
    "sh000300", "sh000852", "sh000905", "sh000922", "bj899050",
]


# ── 通用 HTTP ─────────────────────────────────────────────────
def http_get(url, headers=None, timeout=15, retries=2, log=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            if i == retries:
                if log:
                    log("[WARN] GET failed {}: {}".format(url[:80], e))
                return None
            time.sleep(1.5)
    return None


def http_get_json(url, headers=None, timeout=15, log=None):
    raw = http_get(url, headers, timeout, log=log)
    if raw is None:
        return None
    for enc in ("utf-8", "gbk"):
        try:
            return json.loads(raw.decode(enc))
        except Exception:
            continue
    if log:
        log("[WARN] JSON parse failed: " + url[:80])
    return None


# ── 1. 腾讯指数行情 ───────────────────────────────────────────
def tencent_quotes(codes):
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    raw = http_get(url, timeout=10)
    if raw is None:
        return {}
    data = raw.decode("gbk", errors="ignore")
    out = {}
    for line in data.strip().split(";"):
        line = line.strip()
        if "=" not in line or '"' not in line:
            continue
        key = line.split("=")[0].split("_")[-1]
        vals = line.split('"')[1].split("~")
        if len(vals) < 53:
            continue

        def f(idx):
            try:
                return float(vals[idx]) if vals[idx] else 0.0
            except Exception:
                return 0.0

        out[key] = {
            "name": vals[1], "price": f(3), "last_close": f(4), "open": f(5),
            "change_amt": f(31), "change_pct": f(32), "high": f(33), "low": f(34),
            "amount_wan": f(37), "turnover_pct": f(38), "pe_ttm": f(39),
            "amplitude_pct": f(43), "mcap_yi": f(44), "pb": f(46),
        }
    return out


# ── 2. 涨跌分布 ───────────────────────────────────────────────
def zd_fenbu():
    url = ("https://push2ex.eastmoney.com/getTopicZDFenBu?"
           "ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt")
    d = http_get_json(url)
    return d.get("data") if d else None


# ── 3. 涨停/跌停/炸板池 ────────────────────────────────────────
def pool(pool_type, date_compact):
    url = ("https://push2ex.eastmoney.com/getTopic{}?"
           "ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt"
           "&Pageindex=0&pagesize=500&sort=fbt%3Aasc&date={}").format(pool_type, date_compact)
    d = http_get_json(url)
    if not d or not d.get("data"):
        return []
    rows = []
    for p in d["data"].get("pool", []):
        rows.append({
            "code": p.get("c"), "name": p.get("n"),
            "change_pct": round(p.get("zdp", 0), 2),
            "seal_amount": p.get("fund", 0),
            "first_seal_time": str(p.get("fbt", "")),
            "last_seal_time": str(p.get("lbt", "")),
            "open_count": p.get("zbc", 0),
            "turnover": p.get("hs", 0),
            "free_mcap": p.get("ltsz", 0),
            "reason": p.get("hybk", ""),
        })
    return rows


# ── 4. 板块排行(分页全量, push2delay) ──────────────────────────
SECTOR_FIELDS = "f2,f3,f4,f8,f12,f14,f62,f66,f104,f105,f128,f136,f140,f184"
SECTOR_HOSTS = [
    "https://push2delay.eastmoney.com/api/qt/clist/get",
    "https://push2.eastmoney.com/api/qt/clist/get",
]


def sector_page(host, fs_code, pn):
    params = {
        "pn": str(pn), "pz": "100", "po": "1", "np": "1",
        "fltt": "2", "invt": "2", "fid": "f3", "fs": fs_code,
        "fields": SECTOR_FIELDS,
    }
    url = host + "?" + urllib.parse.urlencode(params)
    return http_get_json(url, headers={"Referer": "https://quote.eastmoney.com/"})


def sector_all(fs_code, log=None):
    for host in SECTOR_HOSTS:
        all_rows, total = [], None
        for pn in range(1, 15):
            try:
                d = sector_page(host, fs_code, pn)
            except Exception as e:
                if log:
                    log("[WARN] page {} fail: {}".format(pn, e))
                time.sleep(2)
                continue
            if not d or not d.get("data") or not d["data"].get("diff"):
                break
            total = d["data"].get("total")
            for item in d["data"]["diff"]:
                def sf(v, nd=2):
                    try:
                        return round(float(v), nd) if v not in (None, "", "-") else None
                    except Exception:
                        return None
                all_rows.append({
                    "name": item.get("f14"), "code": item.get("f12"),
                    "change_pct": sf(item.get("f3")),
                    "up_count": item.get("f104"), "down_count": item.get("f105"),
                    "leader": item.get("f140"), "leader_change": sf(item.get("f136")),
                    "main_net_yi": (round(item.get("f62", 0) / 1e8, 2)
                                    if item.get("f62") not in (None, "", "-") else None),
                })
            if total and len(all_rows) >= total:
                break
            time.sleep(1.2)
        if all_rows:
            return sorted(all_rows,
                          key=lambda x: (x["change_pct"] if x["change_pct"] is not None else -99),
                          reverse=True)
        if log:
            log("[WARN] host {} returned nothing, trying next".format(host))
    return []


# ── 5. 同花顺强势股题材归因 ───────────────────────────────────
def ths_hot(date):
    url = ("http://zx.10jqka.com.cn/event/api/getharden/date/{}/"
           "orderby/date/orderway/desc/charset/GBK/").format(date)
    d = http_get_json(url)
    if not d or d.get("errocode", 0) != 0:
        return []
    out = []
    for r in d.get("data") or []:
        try:
            out.append({
                "code": r.get("code"), "name": r.get("name"),
                "reason": r.get("reason", ""),
                "change_pct": float(r.get("zhangfu", 0) or 0),
                "turnover": float(r.get("huanshou", 0) or 0),
                "amount": r.get("chengjiaoe", 0),
                "market": r.get("market", ""),
            })
        except Exception:
            continue
    return out


# ── 6/7. 东财数据中心(龙虎榜/两融) ─────────────────────────────
def dc_query(report_name, filter_str="", page_size=100,
             sort_columns="", sort_types="-1"):
    url = ("https://datacenter-web.eastmoney.com/api/data/v1/get?"
           "reportName=" + report_name + "&columns=ALL&filter=" +
           urllib.parse.quote(filter_str) +
           "&pageNumber=1&pageSize={}&sortColumns={}&sortTypes={}"
           "&source=WEB&client=WEB").format(page_size, sort_columns, sort_types)
    d = http_get_json(url, headers={"Referer": "https://data.eastmoney.com/"}, timeout=15)
    if d and d.get("result") and d["result"].get("data"):
        return d["result"]["data"]
    return []


def dragon_tiger(trade_date):
    data = dc_query(
        "RPT_DAILYBILLBOARD_DETAILSNEW",
        "(TRADE_DATE>='{}')(TRADE_DATE<='{}')".format(trade_date, trade_date),
        page_size=200, sort_columns="BILLBOARD_NET_AMT")
    stocks = {}
    for row in data:
        code = row.get("SECURITY_CODE", "")
        if code not in stocks:
            stocks[code] = {
                "code": code, "name": row.get("SECURITY_NAME_ABBR", ""),
                "reason": row.get("EXPLANATION", ""),
                "close": row.get("CLOSE_PRICE") or 0,
                "change_pct": round(float(row.get("CHANGE_RATE") or 0), 2),
                "net_buy_wan": round((row.get("BILLBOARD_NET_AMT") or 0) / 10000, 1),
                "buy_wan": round((row.get("BILLBOARD_BUY_AMT") or 0) / 10000, 1),
                "sell_wan": round((row.get("BILLBOARD_SELL_AMT") or 0) / 10000, 1),
                "turnover_pct": round(float(row.get("TURNOVERRATE") or 0), 2),
            }
    return list(stocks.values())


def margin_market():
    rows = []
    for row in dc_query("RPTA_RZRQ_LSHJ", "", page_size=10,
                        sort_columns="dim_date"):
        rows.append({
            "date": str(row.get("DIM_DATE", ""))[:10],
            "rzye": row.get("RZYE", 0), "rqye": row.get("RQYE", 0),
            "rzrqye": row.get("RZRQYE", 0), "rzmre": row.get("RZMRE", 0),
        })
    return rows


# ── 8. 7x24 快讯 ─────────────────────────────────────────────
def news_flash(page_size=100):
    import uuid
    url = ("https://np-weblist.eastmoney.com/comm/web/getFastNewsList?"
           "client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize={}"
           "&req_trace={}").format(page_size, uuid.uuid4())
    d = http_get_json(url, headers={"Referer": "https://kuaixun.eastmoney.com/"})
    rows = []
    for item in (d.get("data") or {}).get("fastNewsList", []):
        rows.append({
            "title": item.get("title", ""),
            "summary": (item.get("summary", "") or "")[:300],
            "time": item.get("showTime", ""),
        })
    return rows


# ── 主流程 ───────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat(),
                    help="交易日期 YYYY-MM-DD")
    ap.add_argument("--out", default="./data", help="输出目录")
    args = ap.parse_args()

    import os
    os.makedirs(args.out, exist_ok=True)
    date_compact = args.date.replace("-", "")
    log_path = os.path.join(args.out, "market_log.txt")
    logf = open(log_path, "w", encoding="utf-8")

    def log(msg):
        print(msg)
        logf.write(msg + "\n")
        logf.flush()

    result = {"trade_date": args.date}

    log("[1/8] 指数行情(腾讯)...")
    result["indices"] = tencent_quotes(INDEX_CODES)
    log("  {} 个指数".format(len(result["indices"])))
    time.sleep(0.5)

    log("[2/8] 涨跌分布...")
    result["zd_fenbu"] = zd_fenbu()
    log("  {}".format("OK" if result["zd_fenbu"] else "FAIL"))
    time.sleep(1.0)

    log("[3/8] 涨停/跌停/炸板池...")
    result["limit_up_pool"] = pool("ZTPool", date_compact)
    log("  涨停 {} 只".format(len(result["limit_up_pool"])))
    time.sleep(1.0)
    result["limit_down_pool"] = pool("DTPool", date_compact)
    log("  跌停 {} 只".format(len(result["limit_down_pool"])))
    time.sleep(1.0)
    result["broken_pool"] = pool("ZBPool", date_compact)
    log("  炸板 {} 只".format(len(result["broken_pool"])))
    time.sleep(1.0)

    log("[4/8] 行业板块全量(分页)...")
    result["industry_all"] = sector_all("m:90+t:2", log)
    log("  {} 个行业".format(len(result["industry_all"])))
    time.sleep(1.5)
    log("[4/8] 概念板块全量(分页)...")
    result["concept_all"] = sector_all("m:90+t:3", log)
    log("  {} 个概念".format(len(result["concept_all"])))

    log("[5/8] 同花顺强势股题材归因...")
    result["ths_hot"] = ths_hot(args.date)
    log("  {} 只".format(len(result["ths_hot"])))
    time.sleep(1.0)

    log("[6/8] 龙虎榜...")
    result["dragon_tiger"] = dragon_tiger(args.date)
    log("  {} 只".format(len(result["dragon_tiger"])))
    time.sleep(1.0)

    log("[7/8] 两融余额...")
    result["margin"] = margin_market()
    log("  {} 条".format(len(result["margin"])))
    time.sleep(1.0)

    log("[8/8] 7x24 快讯...")
    result["news_flash"] = news_flash()
    log("  {} 条".format(len(result["news_flash"])))

    out_path = os.path.join(args.out, "market_data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    log("Saved -> " + out_path)
    log("=== DONE market_data ===")
    logf.close()


if __name__ == "__main__":
    main()
