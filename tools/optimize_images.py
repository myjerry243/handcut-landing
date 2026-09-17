#!/usr/bin/env python3
"""把 index.html 的图片改造成"按视口给不同尺寸"的响应式 WebP（幂等，可重复运行）。

做三件事：
  1. 为每张内容图生成 400w / 800w 两档 WebP（首图另出 900w / 1600w），放在 images/webp/
  2. 把 <img> 包成 <picture>（WebP source + 原 JPEG 作 fallback），并按卡片类型给真实 sizes
  3. 首图（CSS 背景）改用 image-set，preload 补 imagesrcset

只改 index.html 与新增 images/webp/*；不删任何原图（JPEG 仍作为 fallback 在用）。
用法：
    python tools/optimize_images.py            # 生成 + 改写
    python tools/optimize_images.py --dry-run  # 只看会生成什么、省多少字节
"""

from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

from PIL import Image

try:                                  # AVIF 编码依赖 pillow-avif-plugin（只影响能不能出 AVIF 档）
    import pillow_avif  # noqa: F401
    HAVE_AVIF = True
except ImportError:
    HAVE_AVIF = False

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
WEBP_DIR = ROOT / "images" / "webp"

SIZES = {
    "gal-card": "(max-width:640px) 92vw, (max-width:960px) 45vw, 380px",
    "proj-card": "(max-width:960px) 92vw, 560px",
}
DEFAULT_SIZES = "(max-width:960px) 92vw, 800px"
CONTENT_WIDTHS = (400, 720, 1000)    # 内容图三档（覆盖手机 92vw@2x、平板 45vw@2x、桌面卡片@2x）
HERO_WIDTHS = (900, 1600)            # 首图（全屏背景）
AVIF_WIDTHS = (400, 720)             # AVIF 只出最省字节的两档（现代浏览器 >93%，优先命中）
QUALITY = 80
AVIF_QUALITY = 62                    # AVIF 同视觉质量下更低字节


def card_type(html: str, pos: int) -> str:
    """根据图片前方最近的卡片 class 判断它属于哪种布局。"""
    before = html[:pos]
    gal = before.rfind('class="gal-card')
    proj = before.rfind('class="proj-card')
    if gal == -1 and proj == -1:
        return "default"
    return "gal-card" if gal > proj else "proj-card"


def write_variant(src: Path, out: Path, width: int, dry: bool,
                  fmt: str = "WEBP") -> tuple[int, int]:
    """返回 (原字节, 新字节)；已存在则直接读现有大小。fmt: WEBP | AVIF"""
    original = src.stat().st_size
    if out.exists() and not dry:
        return original, out.stat().st_size
    with Image.open(src) as im:
        if im.mode != "RGB":
            im = im.convert("RGB")
        if im.width > width:
            im = im.resize((width, max(1, round(im.height * width / im.width))), Image.LANCZOS)
        buf = io.BytesIO()
        if fmt == "AVIF":
            im.save(buf, format="AVIF", quality=AVIF_QUALITY, speed=6)
        else:
            im.save(buf, format="WEBP", quality=QUALITY, method=6)
        data = buf.getvalue()
    if not dry:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    return original, len(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    html = INDEX.read_text(encoding="utf-8")
    if '<picture>' in html:
        print("注意：index.html 里已存在 <picture>，脚本会跳过已处理的图片（幂等）")

    stats = {"imgs": 0, "variants": 0, "orig_bytes": 0, "bytes": 0}
    replaced: list[tuple[str, str]] = []

    def build_picture(match: re.Match) -> str:
        tag = match.group(0)
        if 'src=""' in tag or "data-src" in tag:
            return tag                                    # lightbox 占位图不动
        # 幂等：已经处在 <picture> 内部的 img 直接跳过（防重复包裹成嵌套 picture）
        head = html[:match.start()]
        if head.count("<picture>") > head.count("</picture>"):
            return tag
        src_m = re.search(r'src="([^"]+)"', tag)
        if not src_m:
            return tag
        rel = src_m.group(1)
        path = ROOT / rel
        if not path.exists():
            print(f"  ! 找不到文件，跳过：{rel}")
            return tag
        kind = card_type(html, match.start())
        webp_pairs, avif_pairs = [], []
        for w in CONTENT_WIDTHS:
            out = WEBP_DIR / f"{path.stem}-{w}.webp"
            before, after = write_variant(path, out, w, args.dry_run, "WEBP")
            webp_pairs.append((f"images/webp/{out.name}", w, after))
            stats["orig_bytes"] += before
            stats["bytes"] += after
            stats["variants"] += 1
        for w in (AVIF_WIDTHS if HAVE_AVIF else ()):
            out = WEBP_DIR / f"{path.stem}-{w}.avif"
            before, after = write_variant(path, out, w, args.dry_run, "AVIF")
            avif_pairs.append((f"images/webp/{out.name}", w, after))
            stats["bytes"] += after
            stats["variants"] += 1
        stats["imgs"] += 1
        sizes = SIZES.get(kind, DEFAULT_SIZES)
        webp_srcset = ", ".join(f"{u} {w}w" for u, w, _ in webp_pairs)
        avif_srcset = ", ".join(f"{u} {w}w" for u, w, _ in avif_pairs)
        avif_source = (f'<source type="image/avif" srcset="{avif_srcset}" sizes="{sizes}">'
                       if avif_srcset else "")
        picture = (f'<picture>{avif_source}'
                   f'<source type="image/webp" srcset="{webp_srcset}" sizes="{sizes}">'
                   f'{tag}</picture>')
        replaced.append((rel, f"{kind} → AVIF {len(avif_pairs)} 档 / WebP {len(webp_pairs)} 档"))
        return picture

    new_html = re.sub(r"<img[^>]*>", build_picture, html)

    # 首图：CSS 背景 → image-set（WebP 优先，JPEG 兜底）；preload 补 imagesrcset
    hero = ROOT / "images" / "hero.jpg"
    hero_pairs = []
    for w in HERO_WIDTHS:
        out = WEBP_DIR / f"hero-{w}.webp"
        before, after = write_variant(hero, out, w, args.dry_run, "WEBP")
        hero_pairs.append((f"images/webp/{out.name}", w, after))
        stats["orig_bytes"] += before
        stats["bytes"] += after
        stats["variants"] += 1
    if HAVE_AVIF:
        hero_avif = WEBP_DIR / "hero-900.avif"
        _, hero_avif_bytes = write_variant(hero, hero_avif, 900, args.dry_run, "AVIF")
        stats["bytes"] += hero_avif_bytes
        stats["variants"] += 1
    hero_srcset = ", ".join(f"{u} {w}w" for u, w, _ in hero_pairs)
    old_bg = "background:url('images/hero.jpg') center/cover no-repeat"
    avif_first = (f"url('images/webp/hero-900.avif') type('image/avif') 1x,"
                  if HAVE_AVIF else "")
    new_bg = ("background:url('images/hero.jpg') center/cover no-repeat;"
              "background-image:image-set(" + avif_first +
              "url('images/webp/hero-900.webp') 1x,"
              "url('images/webp/hero-1600.webp') 2x)")
    if old_bg in new_html:
        new_html = new_html.replace(old_bg, new_bg)
    preload_old = re.search(r'<link[^>]*rel="preload"[^>]*as="image"[^>]*>', new_html)
    if preload_old and "imagesrcset" not in preload_old.group(0):
        tag = preload_old.group(0)
        tag_new = re.sub(r'\shref="[^"]*"', ' href="images/webp/hero-1600.webp"', tag)
        tag_new = tag_new[:-1] + f' imagesrcset="{hero_srcset}" imagesizes="100vw">'
        new_html = new_html.replace(tag, tag_new)

    if not args.dry_run:
        INDEX.write_text(new_html, encoding="utf-8")

    print(f"\n处理图片 {stats['imgs']} 张，生成 WebP 变体 {stats['variants']} 个")
    print(f"参与统计的原图合计 {stats['orig_bytes']/1024/1024:.2f} MB "
          f"→ 变体合计 {stats['bytes']/1024/1024:.2f} MB（多档并存，实际每次只传一档）")
    print("单视口的真实负载用 tools/payload_report.py 看")
    for rel, note in replaced[:40]:
        print(f"  {rel:<46} {note}")
    if args.dry_run:
        print("\n[dry-run] 未写入任何文件")
    else:
        print(f"\n已写入 {INDEX}（原文件可通过 git diff 回退）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
