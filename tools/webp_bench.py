#!/usr/bin/env python3
"""量化图片优化空间：把仓库里的图转成 WebP（不覆盖原文件），对比总体积。

用法：python tools/webp_bench.py [--quality 80] [--max-width 1400]
输出：每张图的 原体积 → WebP 体积，以及全站合计与节省比例（写报告用）。
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXTS = (".jpg", ".jpeg", ".png")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quality", type=int, default=80)
    ap.add_argument("--max-width", type=int, default=1400)
    ap.add_argument("--detail", action="store_true")
    args = ap.parse_args()

    files = sorted([p for p in ROOT.rglob("*") if p.suffix.lower() in EXTS and "tools" not in p.parts])
    before = after = 0
    rows = []
    avif_ok = "AVIF" in Image.registered_extensions().values() if True else False
    try:
        Image.init()
        fmt_ok = "AVIF" in Image.OPEN or "AVIF" in getattr(Image, "SAVE", {})
    except Exception:  # noqa: BLE001
        fmt_ok = False

    for path in files:
        size_before = path.stat().st_size
        with Image.open(path) as im:
            im = im.convert("RGB")
            if im.width > args.max_width:
                ratio = args.max_width / im.width
                im = im.resize((args.max_width, int(im.height * ratio)), Image.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, format="WEBP", quality=args.quality, method=6)
            size_after = buf.tell()
        before += size_before
        after += size_after
        rows.append((path.relative_to(ROOT).as_posix(), size_before, size_after))

    rows.sort(key=lambda r: -(r[1] - r[2]))
    if args.detail:
        print(f"{'文件':<46}{'原始KB':>9}{'WebP KB':>9}{'省':>8}")
        for name, b, a in rows:
            print(f"{name:<46}{b/1024:>9.0f}{a/1024:>9.0f}{(1 - a / b) * 100:>7.0f}%")
    print(f"\n合计：{before/1024/1024:.2f} MB → {after/1024/1024:.2f} MB "
          f"（省 {(1 - after / before) * 100:.0f}%，质量 q={args.quality}，宽 ≤{args.max_width}px）")
    print(f"AVIF 可用：{fmt_ok}（Pillow 默认不带 AVIF，需要 pillow-avif-plugin 或 11.x）")
    print("说明：文件总数 %d，仅统计仓库内图片；未修改任何原文件。" % len(files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
