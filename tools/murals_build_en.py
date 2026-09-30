# -*- coding: utf-8 -*-
"""Rebuild index.html on top of upstream 08d1b43:
   - add Art Murals section  -> the 7 FLAT artwork photos (gal-card)
   - extend Projects section -> the 14 ROOM/decor scene photos (proj-card)
   - nav item + lang switcher + hreflang + section CSS
Run:  python.exe rebuild_en.py
"""
import io, json, os, subprocess

SITE = r"G:/handcut-landing"
BASE_REV = "08d1b43"
DOMAIN = "https://www.artmosaicfactory.com"

MAN = json.load(open(next(p for p in (os.path.join(SITE, "tools", "artmurals-manifest.json"),
                             os.path.join(SITE, "images", "artmurals", "manifest.json"))
                    if os.path.exists(p)), encoding="utf-8"))
BY_FILE = {m["file"]: m for m in MAN}

# ROOM = mosaic shown inside a decorated interior scene  -> Projects
ROOM = {"am_02", "am_03", "am_08", "am_09", "am_11", "am_13", "am_14",
        "am_15", "am_16", "am_17", "am_18", "am_19", "am_20", "am_21"}
FLAT = {m["slug"] for m in MAN}  # placeholder, replaced below
FLAT = set()
for m in MAN:
    stem = m["file"][:-4]
    if stem not in ROOM:
        FLAT.add(stem)
flat_files = [m["file"] for m in MAN if m["file"][:-4] in FLAT]
room_files = [m["file"] for m in MAN if m["file"][:-4] in ROOM]
print(f"FLAT {len(flat_files)}: {flat_files}")
print(f"ROOM {len(room_files)}: {room_files}")
assert len(flat_files) + len(room_files) == 21

def gal_card(m, prefix=""):
    alt = m["desc_en"] + " — custom mosaic wall art by Art Mosaic Factory"
    return (f'      <figure class="gal-card"><img src="{prefix}images/artmurals/{m["file"]}"'
            f' width="{m["w"]}" height="{m["h"]}" alt="{alt}" loading="lazy">'
            f'<figcaption>{m["en"]}</figcaption></figure>')

def proj_card(m, prefix=""):
    alt = m["desc_en"] + " — custom mosaic wall art by Art Mosaic Factory"
    return (f'      <figure class="proj-card"><img src="{prefix}images/artmurals/{m["file"]}"'
            f' width="{m["w"]}" height="{m["h"]}" alt="{alt}" loading="lazy">'
            f'<figcaption><b>{m["en"]}</b><span>{m["desc_en"]}</span></figcaption></figure>')

html = subprocess.run(["git", "show", f"{BASE_REV}:index.html"], cwd=SITE,
                      capture_output=True, text=True, encoding="utf-8").stdout
assert "id=\"artmurals\"" not in html, "base already has the section"
assert html.count('<div class="proj-grid">') == 1

# ---- 1. CSS
html = html.replace("</style>",
                    ".artmurals{background:#fff;border-top:1px solid var(--line)}\n"
                    ".nav-lang{border:1px solid rgba(255,255,255,.35);border-radius:6px;"
                    "padding:6px 11px!important;font-size:13px!important}\n</style>", 1)

# ---- 2. nav item + language switcher
nav = '<li><a href="#gallery">Gallery</a></li>'
assert nav in html
html = html.replace(nav, nav + '\n        <li><a href="#artmurals">Art Murals</a></li>', 1)
html = html.replace(
    '<a class="nav-cta" href="#quote">Commission a Mural</a></li>',
    '<a class="nav-cta" href="#quote">Commission a Mural</a></li>\n'
    '        <li><a class="nav-lang" href="zh/" hreflang="zh-CN" lang="zh-CN">中文</a></li>', 1)

# ---- 3. hreflang
html = html.replace(
    '<meta property="og:type" content="website">',
    '<link rel="alternate" hreflang="en" href="%s/">\n'
    '<link rel="alternate" hreflang="zh-CN" href="%s/zh/">\n'
    '<link rel="alternate" hreflang="x-default" href="%s/">\n'
    '<meta property="og:type" content="website">' % (DOMAIN, DOMAIN, DOMAIN), 1)

# ---- 4. extend Projects with the 14 room-scene photos
grid_open = html.index('<div class="proj-grid">')
grid_close = html.index("\n    </div>", grid_open)
cards = "".join("\n" + proj_card(BY_FILE[f]) for f in room_files)
html = html[:grid_close] + cards + html[grid_close:]
print("projects cards now:", html.count('class="proj-card"'))

# ---- 5. new Art Murals section with the 7 flat artworks
SEC = ('\n<section class="section artmurals" id="artmurals">\n'
       '  <div class="container">\n'
       '    <div class="section-head">\n'
       '      <div class="kicker">Art Mural Collection</div>\n'
       '      <h2>Art Murals, Made to Order</h2>\n'
       '      <p>Handmade mosaic artwork from our studio — classical icons, botanical panels, '
       'floral roundels and bold graphic pieces. Each one is produced to your size, palette and '
       'subject, either as a framed panel or set directly into your wall.</p>\n'
       '    </div>\n'
       '    <div class="gal-grid">\n'
       + "\n".join(gal_card(BY_FILE[f]) for f in flat_files) + "\n"
       '    </div>\n'
       '    <p class="gal-note"><b>Have a wall in mind?</b> Send us the artwork and the wall size — '
       'we return a free layout and quotation within 24 hours.</p>\n'
       '  </div>\n'
       '</section>\n\n')

craft = '<section class="section craft" id="craft">'
assert craft in html
html = html.replace(craft, SEC + craft, 1)

io.open(os.path.join(SITE, "index.html"), "w", encoding="utf-8", newline="\n").write(html)
print(f"index.html written: {len(html)} bytes")
print("gal-card:", html.count('class="gal-card"'), " proj-card:", html.count('class="proj-card"'))
