#!/usr/bin/env python3
"""图片清点：体积 + 像素尺寸 + HTML 里声明的显示宽高（判断"是不是按显示尺寸上传"）。

只读本地仓库文件；像素尺寸用纯 Python 解析 JPEG/PNG 头（不依赖 Pillow）。
用法：python tools/image_inventory.py [目录]
"""

from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def jpeg_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        if fh.read(2) != b"\xff\xd8":
            return None
        while True:
            b = fh.read(1)
            while b and b != b"\xff":
                b = fh.read(1)
            marker = fh.read(1)
            while marker == b"\xff":
                marker = fh.read(1)
            if not marker:
                return None
            if marker[0] in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
                fh.read(2)
                fh.read(1)
                h, w = struct.unpack(">HH", fh.read(4))
                return w, h
            seg = fh.read(2)
            if len(seg) < 2:
                return None
            fh.seek(struct.unpack(">H", seg)[0] - 2, 1)


def png_size(path: Path) -> tuple[int, int] | None:
    with path.open("rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def dims(path: Path) -> tuple[int, int] | None:
    return jpeg_size(path) or png_size(path)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT
    html = (root / "index.html").read_text(encoding="utf-8", errors="replace")
    declared = {}
    for m in re.finditer(r"<img[^>]*>", html):
        tag = m.group(0)
        src = re.search(r'src="([^"]+)"', tag)
        w = re.search(r'width="(\d+)"', tag)
        if src and w:
            declared[src.group(1).lstrip("./")] = int(w.group(1))

    files = sorted([p for p in root.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")],
                   key=lambda p: -p.stat().st_size)
    total = sum(p.stat().st_size for p in files)
    print(f"{'文件':<46}{'体积KB':>8}{'像素':>14}{'HTML显示宽':>12}{'建议上限':>12}")
    print("-" * 94)
    over = 0
    for p in files:
        size = p.stat().st_size
        d = dims(p)
        rel = p.relative_to(root).as_posix()
        disp = declared.get(rel) or declared.get(p.name)
        suggest = "—"
        if d and disp:
            ideal = disp * 2
            suggest = f"{ideal}px"
            if d[0] > ideal * 1.25:
                over += 1
                suggest += " ⚠超发"
        elif d:
            suggest = "900px（内容图）"
            if p.stat().st_size > 200_000:
                over += 1
                suggest += " ⚠"
        print(f"{rel:<46}{size/1024:>8.0f}{(str(d[0]) + 'x' + str(d[1])) if d else '?':>14}"
              f"{str(disp) + 'px' if disp else '未声明':>12}{suggest:>12}")
    print("-" * 94)
    print(f"合计 {len(files)} 个文件、{total/1024/1024:.2f} MB；超发/过大 {over} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
