#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A股每日监测 - 报告内联 JS 语法校验

从 HTML 报告中提取所有内联 <script>(排除外链 src), 写入临时 .js,
调用 `node --check` 校验语法, 通过后自动删除临时文件.

用法:
  python validate_report_js.py <report.html>
退出码: 0 通过 / 1 语法错误 / 2 node 不可用
"""
import os
import re
import subprocess
import sys
import tempfile


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_report_js.py <report.html>")
        sys.exit(2)
    html_path = sys.argv[1]
    html = open(html_path, encoding="utf-8").read()

    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    body = "\n;\n".join(s for s in scripts
                        if s.strip() and "src=" not in s[:200])
    if not body.strip():
        print("[WARN] no inline script found")
        sys.exit(0)

    js_path = os.path.join(tempfile.gettempdir(), "_report_check.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(body)
    print("inline JS extracted: {} blocks, {} chars -> {}".format(
        len(scripts), len(body), js_path))

    try:
        r = subprocess.run(["node", "--check", js_path],
                           capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        print("[ERROR] node not found in PATH")
        os.remove(js_path)
        sys.exit(2)

    if r.returncode == 0:
        print("=== node --check PASS ===")
        os.remove(js_path)
        sys.exit(0)
    else:
        print("=== node --check FAIL ===")
        print(r.stderr or r.stdout)
        print("temp file kept for debugging: " + js_path)
        sys.exit(1)


if __name__ == "__main__":
    main()
