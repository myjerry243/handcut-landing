#!/usr/bin/env python3
"""本地改前/改后对比：用 Lighthouse 跑 file:// 上的基线版与当前版，输出移动端指标与溢出审计。

基线版来自 `git show HEAD:index.html`（写成 _baseline.html 放仓库根目录，相对路径才能解析）。
用法：python tools/lh_local.py [--chrome "C:/Program Files/Google/Chrome/Application/chrome.exe"]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "_baseline.html"
REPORTS = ROOT / "reports"
AUDITS = ["content-width", "largest-contentful-paint", "total-blocking-time",
          "cumulative-layout-shift", "speed-index", "total-byte-weight",
          "unminified-css", "uses-responsive-images"]


def run_lighthouse(target: Path, out: Path, chrome: str, base: str | None = None) -> dict:
    url = f"{base}/{target.name}" if base else target.resolve().as_uri()
    env = dict(os.environ, CHROME_PATH=chrome)
    npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx.cmd"
    cmd = [npx, "-y", "lighthouse", url, "--output=json", f"--output-path={out}",
           "--only-categories=performance,best-practices,accessibility,seo",
           "--form-factor=mobile", "--screenEmulation.mobile=true", "--quiet",
           "--chrome-flags=--headless=new --no-sandbox --disable-gpu"]
    print(f"  跑 Lighthouse：{target.name} …")
    subprocess.run(cmd, env=env, timeout=420, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    data = json.loads(out.read_text(encoding="utf-8"))
    scores = {k: round((v.get("score") or 0) * 100) for k, v in data["categories"].items()}
    metrics = {a: (data["audits"].get(a) or {}).get("displayValue") for a in AUDITS}
    cw = data["audits"].get("content-width") or {}
    # 用 Lighthouse 抓到的最终视口宽推断是否溢出（它给出 "Content is not sized correctly"）
    return {"url": url, "scores": scores, "metrics": metrics,
            "content_width_ok": bool(cw.get("score", 1) == 1),
            "content_width_msg": cw.get("displayValue") or cw.get("title")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chrome", default="C:/Program Files/Google/Chrome/Application/chrome.exe")
    ap.add_argument("--base", default="http://127.0.0.1:8899",
                    help="本地静态服务地址；file:// 下 Lighthouse 无法采集")
    args = ap.parse_args()
    REPORTS.mkdir(exist_ok=True)

    subprocess.run(["git", "show", "HEAD:index.html"], cwd=ROOT, stdout=BASELINE.open("wb"),
                   check=True)
    print("基线已导出：_baseline.html（来自 HEAD）")
    try:
        before = run_lighthouse(BASELINE, REPORTS / "lh-local-before.json", args.chrome, args.base)
        after = run_lighthouse(ROOT / "index.html", REPORTS / "lh-local-after.json", args.chrome, args.base)
    finally:
        BASELINE.unlink(missing_ok=True)

    for label, res in (("BEFORE", before), ("AFTER", after)):
        print(f"\n== {label} ==  得分 {res['scores']}")
        for k, v in res["metrics"].items():
            print(f"   {k:<28} {v}")
        print(f"   content-width 合规: {res['content_width_ok']}  ({res['content_width_msg']})")
    print("\n== 对比 ==")
    for k in sorted(set(before["scores"]) | set(after["scores"])):
        b, a = before["scores"].get(k), after["scores"].get(k)
        if b is not None and a is not None:
            print(f"  {k:<16} {b} → {a}  ({a - b:+d})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
