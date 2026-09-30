# -*- coding: utf-8 -*-
"""Preprocess Art Mural Collection images for handcut-landing.
- drops AI-generated source
- crops off supplier/brand watermarks + phone-screenshot UI + size annotations
- auto-orients, converts to sRGB, resizes (long side <=1400), optimises JPEG
- writes images/artmurals/am_NN.jpg + manifest.json
"""
import glob, json, os
from PIL import Image, ImageOps

SRC = r"C:/Users/Administrator/Desktop/Art Mural Collection"
DST = r"G:/handcut-landing/images/artmurals"
os.makedirs(DST, exist_ok=True)

files = sorted(glob.glob(os.path.join(SRC, "*")))
assert len(files) == 22, len(files)

# 1-based sorted index -> metadata
# crop = (top_pct, bottom_pct, left_pct, right_pct) fraction to REMOVE from each edge
PLAN = {
    1:  dict(slug="byzantine-icon",        en="Byzantine Icon Mosaic",          zh="拜占庭圣像马赛克",   desc_en="Gold-ground Byzantine icon mosaic panel"),
    2:  dict(slug="koi-dining",            en="Koi Fish Mural",                 zh="锦鲤壁画",           desc_en="Koi fish mosaic mural behind a dining table"),
    3:  dict(slug="blue-floral-bath",      en="Blue Floral Bathroom Wall",      zh="蓝色花卉浴室墙",     desc_en="Blue and white floral mosaic bathroom feature wall", crop=(0,0.07,0,0)),
    4:  dict(slug="floral-bird-roundel",   en="Floral Bird Roundel",            zh="圆形花鸟马赛克",     desc_en="Circular mosaic roundel with a bird among blossoms"),
    5:  None,  # AI-generated (Doubao watermark) - dropped
    6:  dict(slug="leopard-peonies",       en="Leopard &amp; Peonies",          zh="花豹与牡丹",         desc_en="Leopard among peonies and jungle foliage"),
    7:  dict(slug="sacred-heart",          en="Sacred Heart Panel",             zh="圣心马赛克板",       desc_en="Sacred Heart devotional mosaic panel"),
    8:  dict(slug="butterfly-field",       en="Butterfly Field",                zh="蝶舞",               desc_en="Blue and black butterflies on a textured grey field"),
    9:  dict(slug="phoenix-grand-salon",   en="Phoenix in the Grand Salon",     zh="大宅凤凰",           desc_en="Large phoenix mosaic mural in a grand salon"),
    10: dict(slug="sepia-botanical-bath",  en="Sepia Botanical Bath",           zh="褐调植物浴室",       desc_en="Sepia botanical mosaic wall behind a bathtub"),
    11: dict(slug="tropical-foliage",      en="Tropical Foliage Panel",         zh="热带阔叶马赛克板",   desc_en="Tropical foliage and bird-of-paradise mosaic panel"),
    12: dict(slug="arched-blossom",        en="Arched Blossom Mural",           zh="拱形花枝壁画",       desc_en="Arched blossom tree mosaic mural in a living room"),
    13: dict(slug="pomegranate-birds",     en="Pomegranate Branch &amp; Birds", zh="石榴枝头双鸟",       desc_en="Pomegranate branch with two birds", crop=(0,0.09,0,0)),
    14: dict(slug="portrait-feature-wall", en="Portrait Feature Wall",          zh="人物主题墙",         desc_en="Stylised portrait mosaic feature wall"),
    15: dict(slug="zellige-fountain",      en="Zellige Fountain Wall",          zh="摩洛哥马赛克水景墙", desc_en="Moroccan zellige mosaic wall fountain", crop=(0.12,0.07,0,0)),
    16: dict(slug="curved-tropical-panels",en="Curved Tropical Leaf Panels",    zh="弧形热带叶艺术墙",   desc_en="Curved tropical leaf mosaic panels with brass frames"),
    17: dict(slug="geometric-floor-hall",  en="Geometric Floor Hall",           zh="几何拼花长廊",       desc_en="Geometric mosaic floor in a coffered hall"),
    18: dict(slug="classical-medallion",   en="Classical Floor Medallion",      zh="古典地面徽章",       desc_en="Classical figure mosaic medallion in marble floor", crop=(0,0.05,0,0)),
    19: dict(slug="tropical-landscape",    en="Tropical Landscape Mural",       zh="热带风景壁画",       desc_en="Tropical palm landscape mosaic mural panel"),
    20: dict(slug="white-lily-panel",      en="White Lily Wall Panel",          zh="白色百合艺术墙",     desc_en="Oversized white lily mosaic wall panel"),
    21: dict(slug="magnolia-blue",         en="Magnolia on Blue",               zh="蓝底玉兰",           desc_en="White magnolia blossom arched mosaic on blue"),
    22: dict(slug="roosters-blossoms",     en="Roosters &amp; Blossoms",        zh="双鸡花枝",           desc_en="Two roosters with red blossom branches"),
}

LONG_SIDE = 1400
manifest = []
n = 0
for i in range(1, 23):
    info = PLAN[i]
    src = files[i - 1]
    if info is None:
        print(f"[{i:02d}] DROPPED  {os.path.basename(src)}  (AI-generated)")
        continue
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert("RGB")
    W0, H0 = im.size
    t, b, l, r = info.get("crop", (0, 0, 0, 0))
    if any((t, b, l, r)):
        box = (int(W0 * l), int(H0 * t), int(W0 * (1 - r)), int(H0 * (1 - b)))
        im = im.crop(box)
    if max(im.size) > LONG_SIDE:
        sc = LONG_SIDE / max(im.size)
        im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
    n += 1
    name = f"am_{n:02d}.jpg"
    out = os.path.join(DST, name)
    im.save(out, "JPEG", quality=82, optimize=True, progressive=True)
    kb = os.path.getsize(out) // 1024
    manifest.append(dict(
        idx=i, file=name, src=os.path.basename(src), slug=info["slug"],
        w=im.width, h=im.height, en=info["en"], zh=info["zh"], desc_en=info["desc_en"],
        cropped=bool(any((t, b, l, r))), kb=kb, src_size=[W0, H0],
    ))
    print(f"[{i:02d}] {name:10s} {W0}x{H0} -> {im.width}x{im.height}  {kb}KB  {info['slug']}"
          + ("   (cropped)" if any((t, b, l, r)) else ""))
    # alt text per language
    manifest[-1]["alt_en"] = f"{info['desc_en']} — custom mosaic wall art by Art Mosaic Factory"
    manifest[-1]["alt_zh"] = f"{info['desc_en']} — 众岩联手工镶嵌艺术壁画"

with open(os.path.join(DST, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
tot = sum(m["kb"] for m in manifest)
print(f"\n{n} images written, total {tot} KB ({tot/1024:.2f} MB), avg {tot//n} KB")
print("DIR", DST)
