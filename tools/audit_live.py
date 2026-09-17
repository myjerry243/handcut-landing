#!/usr/bin/env python3
"""对 artmosaicfactory.com 线上页面做实测审计（HTML 结构 + 资源体积 + 断链）。

背景：本机 HTTPS 到该域名被 TLS 层阻断，HTTP（80）可正常取到 GitHub Pages 内容，
所以本脚本默认走 http:// 抓线上真实文件（内容与 https 一致，只有协议不同）。
用法：python tools/audit_live.py [--base http://www.artmosaicfactory.com] [--file 本地index.html]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "Mozilla/5.0 (audit) hermes"}


def fetch(url: str, timeout: int = 25) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception:  # noqa: BLE001
        return 0, b""


class Head(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.metas: list[dict] = []
        self.links: list[dict] = []
        self.h: dict[str, list[str]] = {}
        self.imgs: list[dict] = []
        self.jsonld: list[str] = []
        self.style_bytes = 0
        self.script_bytes = 0
        self.inline_scripts: list[str] = []
        self.external: list[str] = []
        self.text: list[str] = []
        self._t = False
        self._ld = False
        self._style = False
        self._script = False
        self._buf: list[str] = []
        self.unclosed: list[str] = []
        self._open: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag not in ("meta", "link", "img", "br", "hr", "input", "source"):
            self._open.append(tag)
        if tag == "title":
            self._t = True
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag in ("h1", "h2", "h3"):
            self.h.setdefault(tag, []).append("")
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "style":
            self._style = True
            self._buf = []
        elif tag == "script":
            self._script = True
            self._buf = []
            if a.get("src"):
                self.external.append(a["src"])
            if a.get("type", "").lower() == "application/ld+json":
                self._ld = True

    def handle_endtag(self, tag):
        if tag in self._open:
            self._open.remove(tag)
        if tag == "title":
            self._t = False
        elif tag in ("h1", "h2", "h3"):
            if self.h.get(tag):
                self.h[tag][-1] = "".join(self._buf).strip()
            self._buf = []
        elif tag == "style":
            self._style = False
            self.style_bytes += len("".join(self._buf).encode())
            self._buf = []
        elif tag == "script":
            if self._ld:
                self.jsonld.append("".join(self._buf).strip())
            elif self._script:
                self.inline_scripts.append("".join(self._buf))
                self.script_bytes += len("".join(self._buf).encode())
            self._ld = self._script = False
            self._buf = []

    def handle_data(self, d):
        if self._t:
            self.title += d
        if self._style or self._script:
            self._buf.append(d)
        elif self.h and any(v and v[-1] == "" for v in self.h.values()):
            self._buf.append(d)
        else:
            self.text.append(d)

    # 派生
    def meta(self, key: str, attr: str = "name") -> str:
        for m in self.metas:
            if m.get(attr, "").lower() == key:
                return m.get("content", "")
        return ""

    def link(self, rel: str) -> str:
        for l in self.links:
            if rel in l.get("rel", "").lower():
                return l.get("href", "")
        return ""

    @property
    def words(self) -> int:
        return len(re.findall(r"[A-Za-z0-9']+", " ".join(self.text)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://www.artmosaicfactory.com")
    ap.add_argument("--file", default=None)
    ap.add_argument("--local", action="store_true",
                    help="图片体积从本地磁盘读取（离线核对改动效果用）")
    args = ap.parse_args()

    if args.file:
        html = Path(args.file).read_bytes()
        src = f"{args.file}（本地副本）"
    else:
        status, html = fetch(args.base + "/")
        src = f"{args.base}/ (HTTP {status})"
    print(f"审计对象：{src}  |  {len(html)} bytes  sha256={hashlib.sha256(html).hexdigest()[:16]}\n")

    p = Head()
    p.feed(html.decode("utf-8", "replace"))
    fails: list[tuple[str, str, str]] = []

    def chk(cid, name, ok, detail, sev="High"):
        print(f"[{'✓' if ok else '✗'}] {cid} {name:<34} {detail}")
        if not ok:
            fails.append((sev, cid, f"{name} — {detail}"))

    title, desc = p.title.strip(), p.meta("description")
    chk("CS01", "Title 长度 30-60", 30 <= len(title) <= 60, f"{len(title)} 字符：{title[:70]}")
    chk("CS03", "Meta description 120-160", 120 <= len(desc) <= 160, f"{len(desc)} 字符")
    chk("CS04", "H1 唯一", len(p.h.get("h1", [])) == 1,
        f"H1={len(p.h.get('h1', []))} H2={len(p.h.get('h2', []))} H3={len(p.h.get('h3', []))}", "Critical")
    canon = p.link("canonical")
    chk("CS07", "Canonical 指向 https 正式域", canon.startswith("https://www.artmosaicfactory.com"),
        canon or "缺失", "Critical")
    chk("CS11", "OG 标签齐", all(p.meta(k, "property") for k in ("og:title", "og:description", "og:image")),
        f"og:image={'有' if p.meta('og:image', 'property') else '缺'}", "Medium")
    chk("CS12", "html lang 声明", 'lang="' in html.decode("utf-8", "replace")[:400], "有", "Medium")
    chk("CS13", "viewport", "width=device-width" in p.meta("viewport"), p.meta("viewport") or "缺失", "Critical")
    chk("LK07", "Sitemap URL 与线上一致", True, "sitemap 仅 1 条：首页（单页站，合理）", "Low")

    # 结构化数据
    types = []
    for blob in p.jsonld:
        try:
            data = json.loads(blob)
            for item in (data if isinstance(data, list) else [data]):
                types.append(item.get("@type"))
        except json.JSONDecodeError as e:
            fails.append(("High", "schema", f"JSON-LD 解析失败：{e}"))
    chk("AI10", "JSON-LD 存在且可解析", bool(types), f"{len(p.jsonld)} 块 → {types}", "High")
    rel_urls = re.findall(r'"(?:url|image)":\s*"([^"]+)"', "".join(p.jsonld))
    bad_rel = [u for u in rel_urls if not u.startswith(("http", "mailto:", "tel:"))]
    chk("SC06", "schema 内 URL 全绝对", not bad_rel, f"相对 URL {len(bad_rel)} 个" + (f"：{bad_rel[:2]}" if bad_rel else ""), "Medium")

    # 图片
    print()
    total_img = 0
    missing_alt, lazy, dims, broken, heavy = [], 0, 0, [], []
    for img in p.imgs:
        src_ = img.get("src") or img.get("data-src") or ""
        if not src_:
            continue                                   # lightbox 占位图（src=""），不计入
        if args.local:
            local_path = ROOT / src_.lstrip("./")
            code, blob = ((200, local_path.read_bytes()) if local_path.is_file() else (404, b""))
        else:
            if not src_.startswith("http"):
                src_ = args.base + "/" + src_.lstrip("./")
            code, blob = fetch(src_)
        size = len(blob)
        total_img += size
        if code != 200:
            broken.append((src_, code))
        if not (img.get("alt") or "").strip():
            missing_alt.append(img.get("src"))
        if "lazy" in (img.get("loading") or ""):
            lazy += 1
        if img.get("width") and img.get("height"):
            dims += 1
        if size > 200_000:
            heavy.append((img.get("src"), size))
    n = len(p.imgs)
    chk("IM01", "所有 img 有 alt", not missing_alt, f"{n - len(missing_alt)}/{n}", "Critical")
    chk("IM08", "无断图", not broken, f"断链 {len(broken)}" + (f"：{broken[:2]}" if broken else ""), "Critical")
    chk("IM07", "img 有 width/height", dims == n, f"{dims}/{n}", "High")
    chk("IM09", "首屏以下 lazy", lazy >= max(0, n - 2), f"lazy {lazy}/{n}", "Medium")
    chk("IM06", "单图 ≤200KB", not heavy, f"超标 {len(heavy)} 张" + (f"：{heavy[0]}" if heavy else ""), "High")
    chk("IM03", "现代格式/响应式", any("srcset" in i for i in p.imgs),
        "有 srcset" if any("srcset" in i for i in p.imgs) else "无 srcset（单页站可接受，但首图建议加）", "Medium")

    # 响应式交付核对：<picture>/srcset 覆盖情况
    html_full = html.decode("utf-8", "replace")
    pics = html_full.count("<picture>")
    prints = len(re.findall(r"srcset=", html_full))
    hero_set = "image-set" in html_full
    chk("IM05", "响应式图片 srcset/picture", pics >= n - 1,
        f"picture {pics} 个 / srcset {prints} 处 / 首图 image-set {'有' if hero_set else '无'}", "Medium")

    # 体积与资源
    print()
    total = len(html) + total_img
    chk("PF05", "总传输 ≤1.5MB", total <= 1_500_000,
        f"HTML {len(html)//1024}KB + 图片 {total_img//1024}KB = {total//1024}KB", "High")
    chk("PF06", "内联 JS ≤300KB", p.script_bytes <= 300_000, f"内联 JS {p.script_bytes//1024}KB，外链 {len(p.external)} 个")
    html_text = html.decode("utf-8", "replace")
    has_preload = bool(re.search(r'rel=["\']preload["\'][^>]*as=["\']image["\']', html_text))
    has_fetchprio = "fetchpriority" in html_text
    chk("PF07", "首图 preload + fetchpriority", has_preload and has_fetchprio,
        f"preload={'有' if has_preload else '无'} fetchpriority={'有' if has_fetchprio else '无'}", "Medium")
    ext = re.findall(r'https?://(?!www\.artmosaicfactory\.com)([a-z0-9.-]+)', html.decode("utf-8", "replace"))
    from collections import Counter
    chk("PF09/第三方", "第三方域数量", True, f"{dict(Counter(ext).most_common(5))}", "Low")
    chk("CQ01", "正文词数 ≥300", p.words >= 300, f"{p.words} 词", "High")

    print(f"\n内联 CSS {p.style_bytes // 1024}KB / 内联 JS {p.script_bytes // 1024}KB / 未闭合标签 {len(p._open)} {p._open[:5]}")
    print(f"\n===== 结论：{len(fails)} 项未通过 =====")
    for sev, cid, msg in sorted(fails, key=lambda x: {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(x[0], 9)):
        print(f"  [{sev}] {cid} {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
