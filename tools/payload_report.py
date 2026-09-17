#!/usr/bin/env python3
"""按真实视口算"用户到底要下多少图片字节"：解析 <picture>/srcset/sizes 选档后求和。

用法：
    python tools/payload_report.py            # 本地文件 + 本地体积
    python tools/payload_report.py --live     # 从线上按 src 抓体积（改造前对比用）
"""

from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = [("mobile 390@2x", 390, 2), ("tablet 820@2x", 820, 2), ("desktop 1440@1x", 1440, 1)]


def pick(sizes: str, viewport: int) -> tuple[str, float]:
    """返回 (模式, 有效像素宽)：命中的 media 条件 + 该条件下需要的宽度。"""
    parts = [p.strip() for p in sizes.split(",")]
    for part in parts[:-1]:
        m = re.match(r"\(max-width:\s*(\d+)px\)\s*(.+)", part)
        if m and viewport <= int(m.group(1)):
            factor = m.group(2).strip()
            if factor.endswith("vw"):
                return factor, viewport * float(factor[:-2]) / 100
            return factor, float(factor.replace("px", ""))
    last = parts[-1]
    if last.endswith("vw"):
        return last, viewport * float(last[:-2]) / 100
    return last, float(last.replace("px", ""))


def choose(srcset: str, need_px: float) -> tuple[str, int]:
    cands = []
    for item in srcset.split(","):
        m = re.match(r"\s*(\S+)\s+(\d+)w", item)
        if m:
            cands.append((m.group(1), int(m.group(2))))
    cands.sort(key=lambda c: c[1])
    for url, w in cands:
        if w >= need_px:
            return url, w
    return cands[-1]


def size_of(url: str, local: bool, base: str) -> int:
    if local:
        p = ROOT / url
        return p.stat().st_size if p.is_file() else 0
    try:
        req = urllib.request.Request(base + "/" + url.lstrip("./"),
                                     headers={"User-Agent": "Mozilla/5.0 audit"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return len(r.read())
    except Exception:  # noqa: BLE001
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--base", default="http://www.artmosaicfactory.com")
    ap.add_argument("--file", default=str(ROOT / "index.html"))
    args = ap.parse_args()

    html = Path(args.file).read_text(encoding="utf-8")
    local = not args.live
    items: list[dict] = []
    picture_spans = [(m.start(), m.end()) for m in re.finditer(r"<picture>.*?</picture>", html, re.S)]

    for m in re.finditer(r"<picture>(.*?)</picture>", html, re.S):
        block = m.group(1)
        src_m = re.search(r"<img[^>]*src=\"([^\"]+)\"", block)
        # 模拟现代浏览器：优先 AVIF，其次 WebP，都没有才用 <img> 的 JPEG
        sources = re.findall(r'<source[^>]*type="([^"]+)"[^>]*srcset="([^"]+)"[^>]*sizes="([^"]+)"',
                             block)
        chosen = None
        for pref in ("image/avif", "image/webp"):
            for typ, srcset, sizes in sources:
                if typ == pref:
                    chosen = (srcset, sizes)
                    break
            if chosen:
                break
        for vp_name, vw, dpr in VIEWPORTS:
            pick_url = None
            if chosen:
                srcset, sizes = chosen
                _mode, need = pick(sizes, vw)
                pick_url, _w = choose(srcset, need * dpr)
            elif src_m:
                pick_url = src_m.group(1)
            items.append({"vp": vp_name, "url": pick_url,
                          "bytes": size_of(pick_url, local, args.base)})

    # 没有 <picture> 的裸图（例如 lightbox/背景）
    for m in re.finditer(r"<img(?![^>]*src=\"\")[^>]*src=\"(images/[^\"]+)\"[^>]*>", html):
        if any(a <= m.start() < b for a, b in picture_spans):
            continue                                   # 已在 <picture> 里，前面已统计过
        for vp_name, _vw, _dpr in VIEWPORTS:
            items.append({"vp": vp_name, "url": m.group(1),
                          "bytes": size_of(m.group(1), local, args.base)})

    def hero_bytes_for(_mobile: bool) -> int:
        """CSS 里 image-set 两档都声明为 1x → 支持 AVIF 的浏览器直接命中第一个（hero-900.avif）。"""
        for rel in ("images/webp/hero-900.avif", "images/webp/hero-900.webp", "images/hero.jpg"):
            pth = ROOT / rel
            if pth.is_file():
                return pth.stat().st_size
        return 0

    html_bytes = len(Path(args.file).read_bytes())

    print(f"图片元素 {len({i['url'] for i in items})} 个 | HTML {html_bytes//1024} KB | "
          f"来源：{'本地文件' if local else '线上 ' + args.base}")
    for vp_name, _vw, _dpr in VIEWPORTS:
        seen: dict[str, int] = {}
        for r in items:
            if r["vp"] == vp_name and r["url"]:
                seen[r["url"]] = r["bytes"]        # 同一文件只算一次（浏览器有缓存）
        total = sum(seen.values())
        hero = hero_bytes_for("mobile" in vp_name or "tablet" in vp_name) if local else 0
        print(f"  {vp_name:<18} 图片 {total/1024/1024:5.2f} MB"
              f"{f' + 首图 {hero//1024} KB' if hero else ''}"
              f" → 总计约 {(total + hero)/1024/1024:.2f} MB")
    print("\n注：<picture> 场景只计 WebP 变体；--live 模式按改造后的 HTML 抓线上体积（改造前不可用）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
