# -*- coding: utf-8 -*-
"""Point the EN homepage at the new pages (nav + footer + a Collections section)
and pull in the shared subpage CSS. Idempotent: safe to re-run.
Reuses constants from tools/pages_build.py so the design stays one source of truth.
"""
import io, os, re, sys

SITE = r"G:/handcut-landing"
sys.path.insert(0, os.path.join(SITE, "tools"))

# pull the constants without running the generator: import as module would rebuild,
# so read and exec only the constant block we need.
src = io.open(os.path.join(SITE, "tools", "pages_build.py"), encoding="utf-8").read()
ns = {}
exec(compile(src.split("# --------------------------------------------------------------- read assets")[0],
             "consts", "exec"), ns)
EXTRA_CSS, NAV, FOOTER = ns["EXTRA_CSS"], ns["NAV"], ns["FOOTER"]

P = os.path.join(SITE, "index.html")
h = io.open(P, encoding="utf-8").read()
orig = len(h)

# 1) shared subpage CSS + absolute background paths
if "/* --- subpage components --- */" not in h:
    h = h.replace("</style>", EXTRA_CSS + "</style>", 1)

# 2) nav -> real pages
h = h.replace('<li><a href="#gallery">Gallery</a></li>',
              '<li><a href="/gallery/">Gallery</a></li>')
h = h.replace('<li><a href="#artmurals">Art Murals</a></li>',
              '<li><a href="/mosaic-murals/">Art Murals</a></li>')
h = h.replace('<li><a href="#makingof">Making of</a></li>',
              '<li><a href="/how-handcut-mosaic-murals-are-made/">Making of</a></li>\n'
              '        <li><a href="/mosaic-mural-cost/">Cost</a></li>')
h = h.replace('<li><a class="nav-cta" href="#quote">Commission a Mural</a></li>',
              '<li><a class="nav-cta" href="/contact/">Commission a Mural</a></li>')
h = h.replace('<a class="nav-lang" href="zh/"', '<a class="nav-lang" href="/zh/"')

# 3) Collections section before the footer
COLLS = [("handcut-mosaic-murals", "Handcut Mosaic Murals", "Every tessere cut and set by hand"),
         ("custom-mosaic-wall-art", "Custom Mosaic Wall Art", "Made to your exact wall size"),
         ("mosaic-from-photo", "Mosaic From Your Photo", "Portraits, pets, paintings, logos"),
         ("mosaic-feature-wall", "Mosaic Feature Walls", "Living rooms, stairwells, lobbies"),
         ("mosaic-backsplash", "Kitchen Backsplashes", "Heat-proof, grease-proof, handmade"),
         ("mosaic-bathroom-wall", "Bathroom Mosaics", "Wet-room artwork that lasts"),
         ("hotel-mosaic-art", "Hotel &amp; Hospitality", "Contract-grade FF&amp;E murals"),
         ("pool-mosaic-tiles", "Pool &amp; Spa Mosaics", "Frost-proof, chlorine-proof"),
         ("mosaic-mural-manufacturer", "Factory &amp; Wholesale", "Trade, private label, OEM"),
         ("mosaic-mural-cost", "What It Costs", "How the price is actually built"),
         ("how-handcut-mosaic-murals-are-made", "How They Are Made", "Six stages, start to finish"),
         ("faq", "Questions &amp; Answers", "Cost, lead times, shipping, care"),
         ("gallery", "Full Gallery", "36 handcut pieces")]
links = "\n".join('        <a href="/%s/">%s<span>%s</span></a>' % c for c in COLLS)
SECTION = ('<section class="section" style="background:var(--bg)"><div class="container">'
           '<div class="section-head"><div class="kicker">Explore</div>'
           '<h2>Mosaic Murals, Made to Order</h2>'
           '<p>Everything we make, and everything you need to know before commissioning it.</p></div>'
           '<div class="rel-links" style="grid-template-columns:repeat(3,1fr)">\n%s\n</div>'
           '</div></section>\n\n') % links
if 'class="rel-links"' not in h:
    h = h.replace('<footer class="footer">', SECTION + '<footer class="footer">', 1)

# 4) sitewide footer with real links
if 'footer-grid-4' not in h:
    h = re.sub(r'<footer class="footer">[\s\S]*?</footer>', FOOTER, h, count=1)

io.open(P, "w", encoding="utf-8", newline="\n").write(h)
print("index.html: %d -> %d bytes" % (orig, len(h)))
for probe in ['href="/gallery/"', 'href="/mosaic-murals/"', 'footer-grid-4',
              'rel-links', 'mosaic-mural-cost']:
    print("  %-24s %s" % (probe, "OK" if probe in h else "MISSING"))
