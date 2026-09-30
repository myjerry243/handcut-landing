# -*- coding: utf-8 -*-
"""Expand artmosaicfactory.com from 2 pages into a multi-page SEO site.

Reuses index.html's <style> block (single source of truth for design) and
generates:
  * 16 authored topic pages  (money pages / info pages / hubs)
  * 21 artwork detail pages  (from images/artmurals/manifest.json)
Regenerates sitemap.xml (with image entries) and robots.txt.
Run:  python tools/pages_build.py
"""
import io, json, os, re, html, hashlib, datetime

SITE   = r"G:/handcut-landing"
DOMAIN = "https://www.artmosaicfactory.com"
TODAY  = datetime.date.today().isoformat()

# ---------------------------------------------------------------- brand bits
WA   = "https://wa.me/8613827780690"
WA_T = WA + "?text=Hello%20Art%20Mosaic%20Factory%2C%20I%27d%20like%20to%20commission%20a%20handcut%20mosaic%20mural."
MAIL = "tinafs618@gmail.com"

NAV = """<header class="nav">
  <div class="container nav-inner">
    <a class="brand" href="/">
      <span class="brand-mark"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span>
      <span class="brand-name">Art Mosaic Factory<em>Foshan E-Tile &middot; Handcut Art</em></span>
    </a>
    <button class="nav-toggle" aria-label="Menu">&#9776;</button>
    <nav>
      <ul class="nav-links" id="navLinks">
        <li><a href="/gallery/">Gallery</a></li>
        <li><a href="/mosaic-murals/">Art Murals</a></li>
        <li><a href="/how-handcut-mosaic-murals-are-made/">Making of</a></li>
        <li><a href="/mosaic-mural-cost/">Cost</a></li>
        <li><a class="nav-cta" href="/contact/">Commission a Mural</a></li>
        <li><a class="nav-lang" href="/zh/" hreflang="zh-CN" lang="zh-CN">&#20013;&#25991;</a></li>
      </ul>
    </nav>
  </div>
</header>"""

FOOT_COLS = [
    ("Commissions", [
        ("/handcut-mosaic-murals/", "Handcut Mosaic Murals"),
        ("/custom-mosaic-wall-art/", "Custom Mosaic Wall Art"),
        ("/mosaic-from-photo/", "Mosaic From Your Photo"),
        ("/mosaic-feature-wall/", "Mosaic Feature Walls"),
        ("/mosaic-backsplash/", "Mosaic Backsplashes"),
        ("/mosaic-bathroom-wall/", "Bathroom Mosaics"),
        ("/hotel-mosaic-art/", "Hotel &amp; Hospitality"),
        ("/pool-mosaic-tiles/", "Pool Mosaics"),
    ]),
    ("Learn", [
        ("/how-handcut-mosaic-murals-are-made/", "How They Are Made"),
        ("/mosaic-mural-cost/", "What It Costs"),
        ("/mosaic-installation-guide/", "Installation Guide"),
        ("/faq/", "FAQ"),
        ("/gallery/", "Full Gallery"),
        ("/about/", "About the Factory"),
    ]),
]

FOOTER = """<footer class="footer">
  <div class="container">
    <div class="footer-grid footer-grid-4">
      <div>
        <a class="brand" href="/">
          <span class="brand-mark"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span>
          <span class="brand-name">Art Mosaic Factory<em>Foshan E-Tile &middot; Mosaic</em></span>
        </a>
        <p style="margin-top:14px">14+ years of mosaic R&amp;D and production. Handcut mosaic art murals, custom mosaic wall art, feature walls, pool mosaics and engineering murals for worldwide projects.</p>
      </div>
%s
      <div>
        <h4>Contact</h4>
        <ul>
          <li>Foshan E-Tile Building Material Co., Ltd.</li>
          <li>Foshan, Guangdong, China</li>
          <li><a href="mailto:%s">%s</a></li>
          <li><a href="%s" target="_blank" rel="noopener">WhatsApp: +86 138 2778 0690</a></li>
          <li><a href="/contact/">Request a Quote &rarr;</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">&copy; 2026 Foshan E-Tile Building Material Co., Ltd. &middot; Art Mosaic Factory &middot; Handcut Mosaic Art &middot; <a href="/sitemap.xml">Sitemap</a></div>
  </div>
</footer>""" % ("\n".join(
    '      <div>\n        <h4>%s</h4>\n        <ul>\n%s\n        </ul>\n      </div>'
    % (t, "\n".join('          <li><a href="%s">%s</a></li>' % (u, l) for u, l in items))
    for t, items in FOOT_COLS), MAIL, MAIL, WA)

QUOTE = """<section class="cta" id="quote">
  <div class="cta-bg"></div>
  <div class="cta-inner container">
    <h2>Commission Your Mosaic Wall Art</h2>
    <p>Send us your artwork and wall size &mdash; get a free custom mosaic design plan and quotation within 24 hours.</p>
    <form class="quote-form" id="quoteForm">
      <div class="f-row">
        <input type="text" name="name" placeholder="Your Name *" required>
        <input type="email" name="email" placeholder="Email *" required>
      </div>
      <div class="f-row">
        <input type="text" name="country" placeholder="Country / Region">
        <input type="text" name="wall" placeholder="Wall Size (e.g. 3m x 2.4m)">
      </div>
      <textarea name="message" rows="4" placeholder="Describe your artwork &mdash; subject, style, materials, colour preference..."></textarea>
      <div class="f-actions">
        <button type="submit" class="btn btn-gold">Send Inquiry</button>
        <a class="btn btn-wa" href="%s" target="_blank" rel="noopener">WhatsApp +86 138 2778 0690</a>
      </div>
      <div class="f-ok" id="fOk">&#9989; Inquiry sent! We will reply within 24 hours.</div>
      <div class="f-err" id="fErr">&#9888;&#65039; Submission failed &mdash; your email app has been opened with the inquiry pre-filled. Just press send, or chat with us on WhatsApp.</div>
      <p class="f-note">Submitting sends your inquiry straight to our inbox &mdash; or chat with us instantly on WhatsApp.</p>
    </form>
  </div>
</section>""" % WA_T

SCRIPT = """<div class="lightbox" id="lightbox"><img id="lightboxImg" src="" alt="Enlarged view"></div>
<script>
document.querySelector('.nav-toggle').addEventListener('click', function(){
  document.getElementById('navLinks').classList.toggle('open');
});
document.querySelectorAll('#navLinks a').forEach(function(a){
  a.addEventListener('click', function(){ document.getElementById('navLinks').classList.remove('open'); });
});
function openLightbox(src){
  document.getElementById('lightboxImg').src = src;
  document.getElementById('lightbox').classList.add('open');
}
document.querySelectorAll('.gal-card, .proj-card').forEach(function(card){
  card.addEventListener('click', function(){
    var im = card.querySelector('img');
    if (im) openLightbox(im.src);
  });
});
var lb = document.getElementById('lightbox');
lb.addEventListener('click', function(){ this.classList.remove('open'); });
document.addEventListener('keydown', function(e){
  if(e.key === 'Escape'){ lb.classList.remove('open'); }
});
var qf = document.getElementById('quoteForm');
if (qf) qf.addEventListener('submit', function(e){
  e.preventDefault();
  var f = this;
  var ok = document.getElementById('fOk');
  var err = document.getElementById('fErr');
  ok.style.display = 'none'; err.style.display = 'none';
  var data = {
    name: f.name.value.trim(),
    email: f.email.value.trim(),
    country: f.country.value.trim(),
    wall: f.wall.value.trim(),
    message: f.message.value.trim()
  };
  var fd = new FormData();
  Object.keys(data).forEach(function(k){ fd.append(k, data[k]); });
  fd.append('_subject', 'Handcut Mural Inquiry - ' + (data.name || 'New Lead'));
  fd.append('_captcha', 'false');
  fetch('https://formsubmit.co/ajax/%s', { method: 'POST', body: fd })
    .then(function(r){ return r.json(); })
    .then(function(j){
      if (j.success) { ok.style.display = 'block'; f.reset(); }
      else { mailtoFallback(data); err.style.display = 'block'; }
    })
    .catch(function(){ mailtoFallback(data); err.style.display = 'block'; });
});
function mailtoFallback(data){
  var subject = encodeURIComponent('Handcut Mural Inquiry - ' + (data.name || 'New Lead'));
  var body = encodeURIComponent(
    'Name: ' + data.name + '\\n' + 'Email: ' + data.email + '\\n' +
    'Country: ' + data.country + '\\n' + 'Wall Size: ' + data.wall + '\\n' +
    'Artwork Idea:\\n' + data.message
  );
  window.location.href = 'mailto:%s?subject=' + subject + '&body=' + body;
}
</script>""" % (MAIL, MAIL)

# ------------------------------------------------------------------ extra CSS
EXTRA_CSS = """
/* --- subpage components --- */
a.gal-card{display:block}
.hero-bg{background:url('/images/hero.jpg') center/cover no-repeat;
  background-image:image-set(url('/images/webp/hero-900.webp') 1x,url('/images/webp/hero-1600.webp') 2x);
  background-image:image-set(url('/images/webp/hero-900.avif') type('image/avif') 1x,url('/images/webp/hero-900.webp') 1x,url('/images/webp/hero-1600.webp') 2x)}
.cta-bg{background:url('/images/backsplash/bs_02_peacock.jpg') center/cover no-repeat}
.page-hero{position:relative;background:linear-gradient(150deg,#0b1f3a 0%,#0e2a4f 55%,#12345f 100%);color:#fff;padding:132px 0 58px}
.page-hero::after{content:"";position:absolute;inset:0;background:radial-gradient(760px 340px at 88% 0%,rgba(201,162,39,.13),transparent 62%);pointer-events:none}
.page-hero .container{position:relative;z-index:2}
.crumbs{font-size:12.5px;letter-spacing:.4px;color:rgba(255,255,255,.62);margin-bottom:16px}
.crumbs a{color:rgba(255,255,255,.62)}
.crumbs a:hover{color:var(--gold-2)}
.crumbs span{margin:0 8px;opacity:.5}
.page-hero h1{font-family:var(--serif);font-weight:700;font-size:clamp(30px,4.4vw,48px);line-height:1.14;letter-spacing:-.4px;margin-bottom:16px;max-width:900px}
.page-hero .lede{font-size:clamp(15.5px,1.7vw,18px);color:rgba(255,255,255,.86);max-width:760px}
.page-hero .hero-ctas{margin-top:28px}
.prose{max-width:850px}
.prose h2{font-family:var(--serif);font-size:clamp(24px,3vw,32px);line-height:1.2;color:var(--navy);margin:44px 0 16px}
.prose h2:first-child{margin-top:0}
.prose h3{font-size:18px;font-weight:700;color:var(--navy);margin:28px 0 10px}
.prose p{color:#33415a;font-size:16px;margin-bottom:16px}
.prose ul,.prose ol{margin:0 0 20px 22px}
.prose li{color:#33415a;font-size:15.5px;margin-bottom:9px}
.prose a{color:#8a6d1a;font-weight:600;border-bottom:1px solid rgba(201,162,39,.45)}
.prose a:hover{border-bottom-color:var(--gold)}
.prose .callout{background:var(--bg);border-left:3px solid var(--gold);border-radius:0 12px 12px 0;padding:20px 24px;margin:26px 0}
.prose .callout p:last-child{margin-bottom:0}
.prose table{width:100%;border-collapse:collapse;font-size:14.5px;margin:8px 0 24px}
.prose th,.prose td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}
.prose th{background:var(--bg);color:var(--navy);font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:.6px}
.prose td:first-child{font-weight:600;color:var(--navy);white-space:nowrap}
.split{display:grid;grid-template-columns:1.05fr .95fr;gap:44px;align-items:center}
.split.rev .split-media{order:2}
.split-media img{width:100%;border-radius:var(--radius);box-shadow:var(--shadow)}
.split-media figcaption{font-size:13px;color:var(--muted);margin-top:10px}
.faq-list{max-width:850px}
.faq-item{background:#fff;border:1px solid var(--line);border-radius:var(--radius);padding:24px 26px;margin-bottom:14px}
.faq-item h3{font-size:16.5px;font-weight:700;color:var(--navy);margin-bottom:9px}
.faq-item p{color:#41506b;font-size:15px;margin:0}
.rel-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.rel-card{display:block;border-radius:var(--radius);overflow:hidden;background:var(--navy);box-shadow:var(--shadow);aspect-ratio:4/5;position:relative}
.rel-card img{width:100%;height:100%;object-fit:cover;transition:transform .5s}
.rel-card:hover img{transform:scale(1.06)}
.rel-card figcaption{position:absolute;inset:auto 0 0;padding:30px 13px 12px;background:linear-gradient(transparent,rgba(7,20,40,.82));color:#fff;font-size:12.5px;font-weight:600}
.rel-links{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.rel-links a{display:block;background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:18px 20px;font-weight:600;color:var(--navy);font-size:15px;transition:.2s}
.rel-links a:hover{border-color:var(--gold);transform:translateY(-2px)}
.rel-links span{display:block;font-weight:400;font-size:13px;color:var(--muted);margin-top:5px}
.footer-grid-4{grid-template-columns:1.7fr 1fr 1fr 1fr}
@media(max-width:960px){
  .split{grid-template-columns:1fr;gap:26px}
  .split.rev .split-media{order:0}
  .rel-grid{grid-template-columns:repeat(2,1fr)}
  .rel-links{grid-template-columns:1fr}
  .footer-grid-4{grid-template-columns:1fr 1fr}
  .page-hero{padding:112px 0 46px}
}
@media(max-width:640px){
  .footer-grid-4{grid-template-columns:1fr}
  .prose table{font-size:13px}
  .prose th,.prose td{padding:9px 8px}
}
"""

# ------------------------------------------------------------------- helpers
def esc(s):
    return html.escape(s, quote=False)

def page(slug, title, desc, h1, lede, body, schema_extra=None, hero_cta=True):
    url = DOMAIN + "/" + (slug.strip("/") + "/" if slug.strip("/") else "")
    if slug.strip("/") == "":
        url = DOMAIN + "/"
    crumbs = "".join(
        '<a href="%s">%s</a><span>/</span>' % (u, t) for u, t in CRUMBS.get(slug, [])
    ) + "<b>%s</b>" % esc(h1)
    cta = ('<div class="hero-ctas">'
           '<a class="btn btn-gold" href="#quote">Request a Quote</a>'
           '<a class="btn btn-ghost" href="/gallery/">See the Gallery</a></div>') if hero_cta else ""
    ld = [{
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u}
            for i, (u, n) in enumerate(CRUMBS.get(slug, []))
        ] + [{"@type": "ListItem", "position": len(CRUMBS.get(slug, [])) + 1, "name": h1, "item": url}],
    }]
    if schema_extra:
        ld.extend(schema_extra if isinstance(schema_extra, list) else [schema_extra])

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<meta name="description" content="%s">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="%s">
<link rel="alternate" hreflang="en" href="%s">
<link rel="alternate" hreflang="x-default" href="%s">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Art Mosaic Factory">
<meta property="og:title" content="%s">
<meta property="og:description" content="%s">
<meta property="og:url" content="%s">
<meta property="og:image" content="%s/images/og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%s">
<meta name="twitter:description" content="%s">
<meta name="twitter:image" content="%s/images/og.jpg">
<link rel="icon" href="data:image/svg+xml,%%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%%3E%%3Crect width='32' height='32' rx='6' fill='%%230d1b2a'/%%3E%%3Cpath d='M4 4h8v8H4zM12 4h8v8h-8zM20 4h8v8h-8zM4 12h8v8H4zM12 12h8v8h-8zM20 12h8v8h-8zM4 20h8v8H4zM12 20h8v8h-8zM20 20h8v8h-8z' fill='%%23c9a227'/%%3E%%3C/svg%%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap" rel="stylesheet">
<style>%s%s</style>
%s
</head>
<body>

%s

<section class="page-hero">
  <div class="container">
    <nav class="crumbs" aria-label="Breadcrumb">%s</nav>
    <h1>%s</h1>
    <p class="lede">%s</p>
    %s
  </div>
</section>

%s

%s

%s

</body>
</html>
""" % (esc(title), esc(desc), url, url, url,
       esc(title), esc(desc), url, DOMAIN,
       esc(title), esc(desc), DOMAIN,
       BASE_CSS, EXTRA_CSS,
       "\n".join('<script type="application/ld+json">%s</script>' % json.dumps(x, ensure_ascii=False, indent=2) for x in ld),
       NAV, crumbs, esc(h1), lede, cta, body, QUOTE, FOOTER + "\n" + SCRIPT)


def sec(title, *paras):
    out = ['<section class="section"><div class="container prose">']
    if title:
        out.append("<h2>%s</h2>" % title)
    for p in paras:
        out.append(p)
    out.append("</div></section>")
    return "\n".join(out)


def sec_bg(title, *paras):
    return sec(title, *paras).replace('<section class="section">', '<section class="section" style="background:var(--bg)">')


def gal_section(title, kicker, imgs, note=""):
    cards = "\n".join(
        '<figure class="gal-card"><img src="%s" alt="%s" loading="lazy" width="%d" height="%d">'
        '<figcaption>%s</figcaption></figure>' % (src, esc(alt), w, h, esc(cap))
        for src, alt, cap, w, h in imgs
    )
    return ('<section class="section" style="background:var(--bg)"><div class="container">'
            '<div class="section-head"><div class="kicker">%s</div><h2>%s</h2></div>'
            '<div class="gal-grid">%s</div>%s</div></section>') % (
        kicker, title, cards,
        '<p class="gal-note">%s</p>' % note if note else "")


def faq_section(title, items, intro=None):
    body = "\n".join('<div class="faq-item"><h3>%s</h3><p>%s</p></div>' % (q, a) for q, a in items)
    head = ('<div class="section-head"><div class="kicker">FAQ</div><h2>%s</h2>%s</div>'
            % (title, '<p>%s</p>' % intro if intro else ""))
    return ('<section class="section"><div class="container">%s'
            '<div class="faq-list" style="margin:0 auto">%s</div></div></section>') % (head, body)


def rel_section(title, links, intro=None):
    items = "\n".join('<a href="%s">%s<span>%s</span></a>' % (u, t, d) for u, t, d in links)
    head = ('<div class="section-head"><div class="kicker">Related</div><h2>%s</h2>%s</div>'
            % (title, '<p>%s</p>' % intro if intro else ""))
    return ('<section class="section" style="background:var(--bg)"><div class="container">%s'
            '<div class="rel-links">%s</div></div></section>') % (head, items)


FAQ_SCHEMA = lambda items: {
    "@context": "https://schema.org", "@type": "FAQPage",
    "mainEntity": [{"@type": "Question", "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}}
                   for q, a in items],
}

SERVICE_SCHEMA = lambda name, desc, url, img: {
    "@context": "https://schema.org", "@type": "Service",
    "name": name, "description": desc, "serviceType": "Handcut mosaic mural production",
    "url": url, "image": img,
    "provider": {"@type": "Organization", "@id": DOMAIN + "/#organization",
                 "name": "Art Mosaic Factory"},
    "areaServed": {"@type": "Place", "name": "Worldwide"},
}

# --------------------------------------------------------------- read assets
BASE_CSS = re.search(r"<style>([\s\S]*?)</style>",
                     io.open(os.path.join(SITE, "index.html"), encoding="utf-8").read()).group(1)

MAN = json.load(io.open(os.path.join(SITE, "images", "artmurals", "manifest.json"), encoding="utf-8"))

def mi(prefix):
    """manifest entry -> (src, alt, caption, w, h)"""
    return ("/images/artmurals/" + prefix["file"],
            prefix.get("alt_en") or prefix["desc_en"], prefix["en"], prefix["w"], prefix["h"])

AM = {m["slug"]: m for m in MAN}
print("manifest:", len(MAN), "artworks |", len(BASE_CSS), "css bytes")

# ------------------------------------------------------------- image dims
D = {
 "handcut_01":(700,1244),"handcut_02":(700,466),"handcut_03":(612,840),"handcut_04":(700,1048),
 "handcut_05":(666,827),"handcut_06":(700,1243),"handcut_07":(576,835),"handcut_08":(700,1514),
 "handcut_09":(585,769),"handcut_10":(621,814),"handcut_11":(700,700),"handcut_12":(665,838),
 "handcut_14":(700,933),"handcut_15":(667,830),"handcut_16":(700,1263),"handcut_17":(1400,644),
 "handcut_18":(1000,1129),
 "bs_01_tropical":(900,900),"bs_02_peacock":(1400,1050),"bs_03_lotus":(900,1600),
 "bs_04_rose":(800,1600),"bs_05_leopard":(900,1171),"bs_06_phoenix":(900,1200),
 "bs_07_artnouveau":(900,1080),"bs_08_mothereofpearl":(900,1200),"bs_09_scaleblue":(900,1200),
 "bs_10_whitearc":(678,959),
 "insitu-01-spa-wave-mural":(1400,840),"insitu-02-water-lily-floor":(560,314),
 "insitu-03-lotus-pool-floor":(1068,800),"insitu-04-curved-wave-feature":(1200,788),
 "insitu-05-coral-reef-floor":(1200,788),"insitu-06-indoor-lotus-medallion":(1200,788),
 "insitu-07-water-lily-lap-pool":(1200,788),"insitu-08-lily-pool-floor":(1200,788),
 "insitu-09-garden-leaf-scroll":(1200,788),"insitu-10-illuminated-infinity":(1200,788),
 "insitu-11-indoor-wave-currents":(597,840),"insitu-12-blue-white-floral":(612,840),
 "insitu-13-luxury-spa-medallion":(864,840),"insitu-14-freeform-backyard":(1200,788),
}
def G(stem, alt, cap, folder="gallery"):
    return ("/images/%s/%s.jpg" % (folder, stem),
            alt + " &mdash; handcut mosaic art by Art Mosaic Factory", cap,
            D[stem][0], D[stem][1])

def AMIMG(slug):
    m = AM[slug]
    return ("/images/artmurals/" + m["file"], m.get("alt_en") or m["desc_en"], m["en"], m["w"], m["h"])

# ------------------------------------------------------------------- crumbs
HC = (DOMAIN + "/", "Home")
def cr(*names):
    """build breadcrumb trail: [('Home','/'), ...] -> [(url,name)]"""
    return [(DOMAIN + "/", "Home")]

CRUMBS = {}

# ============================================================ 1. hubs / money
CRUMBS["handcut-mosaic-murals"] = [(DOMAIN + "/", "Home")]
CRUMBS["custom-mosaic-wall-art"] = [(DOMAIN + "/", "Home")]
CRUMBS["mosaic-from-photo"] = [(DOMAIN + "/", "Home")]
CRUMBS["mosaic-feature-wall"] = [(DOMAIN + "/", "Home")]
CRUMBS["mosaic-backsplash"] = [(DOMAIN + "/", "Home")]
CRUMBS["mosaic-bathroom-wall"] = [(DOMAIN + "/", "Home")]
CRUMBS["hotel-mosaic-art"] = [(DOMAIN + "/", "Home")]
CRUMBS["pool-mosaic-tiles"] = [(DOMAIN + "/", "Home")]
CRUMBS["mosaic-mural-cost"] = [(DOMAIN + "/", "Home")]
CRUMBS["how-handcut-mosaic-murals-are-made"] = [(DOMAIN + "/", "Home")]
CRUMBS["mosaic-installation-guide"] = [(DOMAIN + "/", "Home")]
CRUMBS["faq"] = [(DOMAIN + "/", "Home")]
CRUMBS["about"] = [(DOMAIN + "/", "Home")]
CRUMBS["contact"] = [(DOMAIN + "/", "Home")]
CRUMBS["gallery"] = [(DOMAIN + "/", "Home")]
CRUMBS["mosaic-murals"] = [(DOMAIN + "/", "Home")]

PAGES = []

# ---- /mosaic-murals/  (collection hub, links every artwork page)
PAGES.append(dict(
 slug="mosaic-murals",
 title="Mosaic Murals Collection &mdash; 21 Handcut Designs | Art Mosaic Factory",
 desc="Browse our handcut mosaic mural collection: chinoiserie, botanical, Byzantine, landscape and animal designs. Every piece can be re-composed to your wall size.",
 h1="The Mosaic Murals Collection",
 lede="Twenty-one handcut designs from our studio &mdash; from gold-ground Byzantine icon panels to glass peacock backsplashes. Each one is a starting point: we re-cut, re-scale and re-colour any design to fit your wall.",
 body=(sec("Choose a design, or send us your own",
   "<p>Everything below was cut and set by hand in our Foshan workshop. Browse by subject, or use them as a reference for the style you want &mdash; most of our commissions start from a customer's own artwork, photograph or interior scheme rather than from a catalogue piece.</p>",
   "<p>Each artwork page lists the materials used, the setting, the sizes we can produce and what it costs to adapt. If a design is close but not quite right, tell us what to change: subject, palette, proportions or format.</p>")
  + rel_section("Browse by category", [
      ("/mosaic-murals/", "All Handcut Murals", "21 designs, every subject"),
      ("/handcut-mosaic-murals/", "What Handcut Means", "Why hand-cut beats printed"),
      ("/mosaic-backsplash/", "Backsplash Mosaics", "Kitchen &amp; bar feature panels"),
      ("/mosaic-bathroom-wall/", "Bathroom Mosaics", "Humidity-proof wall art"),
      ("/hotel-mosaic-art/", "Hotel &amp; Hospitality", "Lobby and atrium murals"),
      ("/mosaic-from-photo/", "From Your Photo", "Turn an image into mosaic"),
    ])
  + gal_section("The collection", "21 designs", [AMIMG(m["slug"]) for m in MAN]),
 ),
 schema_extra=[],
))

# ---- linked gallery helper (hub/gallery pages need crawlable links)
def gal_linked(imgs_with_url):
    cards = "\n".join(
        '<a class="gal-card" href="%s"><img src="%s" alt="%s" loading="lazy" width="%d" height="%d">'
        '<figcaption>%s</figcaption></a>' % (u, src, esc(alt), w, h, esc(cap))
        for u, src, alt, cap, w, h in imgs_with_url
    )
    return ('<section class="section" style="background:var(--bg)"><div class="container">'
            '<div class="gal-grid">%s</div></div></section>') % cards

AU = lambda m: "/mosaic-murals/%s/" % m["slug"]

# ======================================================== 2. flagship service
PAGES.append(dict(
 slug="handcut-mosaic-murals",
 title="Handcut Mosaic Murals &mdash; Custom Made to Order | Art Mosaic Factory",
 desc="Handcut mosaic murals, made to order in our Foshan studio. Vitreous glass, smalti and gold tesserae, cut and set by hand. Send artwork or a photo for a free quote.",
 h1="Handcut Mosaic Murals",
 lede="A handcut mosaic mural is built one tessera at a time &mdash; no printed film, no digital tile image, no shortcuts. Send us your artwork or photograph and we will cut, set and ship a mosaic that holds its detail for <em>decades outdoors</em> as well as indoors.",
 body=(sec("What &ldquo;handcut&rdquo; actually means",
   "<p>In a handcut mural, every single piece of glass or stone is scored and cut individually, then placed by hand into the design. A 3&nbsp;m &times; 2.4&nbsp;m mural typically needs 12,000&ndash;18,000 tesserae, and each one is positioned with the grain of the artwork in mind.</p>",
   "<p>That is the difference that matters. Machine-cut mosaics use uniform squares in a fixed grid, so curves, eyelids, petals and lettering break apart into visible steps. Printed &ldquo;mosaic effect&rdquo; tiles are worse still: from three metres away they look convincing, but they have no surface relief, they fade, and they cannot be repaired. A handcut mural has real depth, real light play, and any damaged area can be re-cut and re-set.</p>",
   '<div class="callout"><p><b>The test that separates the two:</b> run your eye along a diagonal in the design. In a handcut mural the tesserae follow the line and the angle changes gradually. In a machine-cut or printed version, the diagonal breaks into a staircase.</p></div>')
  + rel_section("Why clients choose it", [
      ("/custom-mosaic-wall-art/", "Bespoke to Your Wall", "Cut to the exact millimetre"),
      ("/mosaic-from-photo/", "From a Photograph", "Portraits and family images"),
      ("/mosaic-mural-cost/", "Price Guidance", "How cost is actually built up"),
      ("/how-handcut-mosaic-murals-are-made/", "Inside the Workshop", "Six stages, start to finish"),
    ])
  + gal_section("Recent handcut work", "From the studio",
      [AMIMG("byzantine-icon"), AMIMG("floral-bird-roundel"), G("handcut_03","Blue and white floral mosaic mural","Blue and white floral mural"),
       AMIMG("pomegranate-birds"), G("handcut_09","Chinoiserie mosaic panel with blossom and birds","Chinoiserie blossom panel"),
       AMIMG("white-lily-panel")])
  + sec_bg("Materials we cut",
   "<table><tr><th>Material</th><th>Where it is the right choice</th><th>Notes</th></tr>"
   "<tr><td>Vitreous glass (smalto)</td><td>Most indoor and outdoor murals, wet rooms, pools</td><td>Non-porous, frost-proof, UV-stable. The everyday workhorse.</td></tr>"
   "<tr><td>Gold &amp; silver leaf glass</td><td>Halos, jewellery, borders, feature highlights</td><td>Real leaf between glass layers &mdash; will not tarnish. Adds a genuine shimmer that photographs poorly but reads beautifully in a room.</td></tr>"
   "<tr><td>Smalti</td><td>Fine painterly detail, landscape and portrait</td><td>Hand-poured Italian glass, irregular cut. Gives the richest colour range.</td></tr>"
   "<tr><td>Marble &amp; natural stone</td><td>Floors, medallions, exterior facades, high-traffic areas</td><td>Honest, heavy, timeless. Best for geometric and classical work.</td></tr>"
   "<tr><td>Mother of pearl</td><td>Skies, water, feathers, soft highlights</td><td>Iridescent and directional &mdash; it shifts as you walk past.</td></tr></table>",
   "<h2>Sizes, formats and where they go</h2>",
   "<p>We work to your wall, not to a fixed product size. Murals are supplied in numbered sections that join invisibly, so a 6&nbsp;m &times; 3&nbsp;m hotel atrium wall arrives in manageable panels with a setting-out drawing.</p>",
   "<ul>"
   "<li><b>Full-wall panels</b> &mdash; living rooms, atriums, stairwells, restaurants</li>"
   "<li><b>Roundels and medallions</b> &mdash; a circular or oval mosaic set into plaster, stone or a plain wall</li>"
   "<li><b>Borders, dados and friezes</b> &mdash; a mosaic band that frames a room without taking the whole wall</li>"
   "<li><b>Feature niches</b> &mdash; showers, alcoves, bar fronts, headboard walls</li></ul>",
   "<p>For pool floors, wet zones and exterior facades, see the material notes above and our <a href=\"/pool-mosaic-tiles/\">pool mosaic</a> and <a href=\"/mosaic-installation-guide/\">installation guide</a> pages.</p>")
  + faq_section("Handcut mosaic questions", [
    ("Is a handcut mosaic mural waterproof?",
     "Yes, when it is built with vitreous glass and installed with the correct cementitious or epoxy adhesive plus grout. Glass tesserae are non-porous and frost-proof, which is why the same material is used in swimming pools. We supply pool-grade specification for wet areas and exterior use."),
    ("How long does a bespoke mural take?",
     "Typically four to seven weeks from approved proof to shipping, depending on size and detail. A small roundel can be faster; a multi-panel atrium mural with gold leaf runs longer. We give you a dated production schedule with the quotation."),
    ("Can you match an existing mosaic or repair a damaged one?",
     "In most cases yes. Send clear photographs of the damaged area with a ruler or coin in frame, and tell us the approximate age. We can match colour and tesserae size closely; exact matches on heavily weathered historic work are best discussed first."),
    ("What file do you need for a quotation?",
     "Your artwork, a photograph, or simply a reference image plus the wall dimensions and the height it will be viewed from. A phone photograph of a painting is usually enough to quote. Higher resolution is only needed later for production."),
  ], "Straight answers to the questions we are asked most often.")
 ),
 schema_extra=[SERVICE_SCHEMA("Handcut Mosaic Murals", "Bespoke handcut mosaic murals in vitreous glass, smalti, gold leaf and stone, produced in Foshan and shipped worldwide.",
   DOMAIN + "/handcut-mosaic-murals/", DOMAIN + "/images/artmurals/am_01.jpg")],
))

# ---------------------------------------------------- 3. custom wall art
PAGES.append(dict(
 slug="custom-mosaic-wall-art",
 title="Custom Mosaic Wall Art &mdash; Made to Your Size | Art Mosaic Factory",
 desc="Custom mosaic wall art built to your exact wall dimensions. Send a photo, painting or logo and we produce a proof, then hand-cut and ship the finished mosaic.",
 h1="Custom Mosaic Wall Art",
 lede="Wall art made to fit &mdash; not a print, not a poster, not a standard panel. You send the image and the wall measurements; we return a proof, then cut and set the mosaic to the millimetre.",
 body=(sec("How a custom commission works",
   "<p>Most clients come to us with one of four things: a photograph they love, a painting they own, a brand mark they need reproduced, or a colour scheme and a mood. Any of those is enough to start.</p>",
   "<ol>"
   "<li><b>Send the source.</b> A photograph, scan, sketch or even a screenshot. Tell us the wall width and height in millimetres or inches.</li>"
   "<li><b>We return a proof.</b> A mosaic-aware rendering that shows how the image survives translation into tesserae &mdash; where detail will hold and where it will simplify.</li>"
   "<li><b>You approve, we cut.</b> Tesserae are cut and set by hand, then the mural is sectioned, labelled and packed.</li>"
   "<li><b>It ships with a setting-out plan.</b> Numbered sections, a layout drawing and adhesive guidance for your installer.</li></ol>",
   '<div class="callout"><p><b>One honest caveat.</b> Mosaic is not a printer. Fine detail below roughly 5&nbsp;mm cannot survive as a single tessera, so we sometimes advise adjusting an image &mdash; simplifying a background, strengthening a silhouette, or scaling the piece up. We will tell you before you commit, not after.</p></div>')
  + sec_bg("What works well, and what needs care",
   "<table><tr><th>Source image</th><th>Result in mosaic</th></tr>"
   "<tr><td>Bold subjects, strong silhouette, few colours</td><td>Excellent. Big shapes and clear edges are what mosaic does best.</td></tr>"
   "<tr><td>Landscape and botanical work</td><td>Very good. Gradual tonal shifts map naturally onto smalti colour runs.</td></tr>"
   "<tr><td>Portraits</td><td>Good at 1&nbsp;m+ height. Small faces need the mosaic enlarged or simplified.</td></tr>"
   "<tr><td>Photographs with fine texture (fabric, foliage detail)</td><td>Needs simplification. We will propose an edited version.</td></tr>"
   "<tr><td>Logos and lettering</td><td>Good if letterforms are bold. Thin serifs and hairlines need re-drawing heavier.</td></tr>"
   "<tr><td>Line drawings and maps</td><td>Excellent &mdash; strong lines read perfectly in cut tesserae.</td></tr></table>")
  + rel_section("Related services", [
      ("/handcut-mosaic-murals/", "Handcut Mosaic Murals", "The flagship service"),
      ("/mosaic-from-photo/", "Mosaic From Photo", "Portraits and personal images"),
      ("/mosaic-feature-wall/", "Mosaic Feature Walls", "Interior design language"),
      ("/mosaic-mural-cost/", "Cost Guide", "Sizes, materials, budgets"),
    ])
  + faq_section("Custom mosaic questions", [
    ("Do you work from a photograph or do I need artwork?",
     "A photograph is fine &mdash; that is how most commissions begin. Send the highest resolution you have and we will tell you honestly how it will translate."),
    ("Can you match a specific paint colour or brand palette?",
     "We match to a Pantone, RAL or paint reference wherever the palette allows. Glass colour is achieved through the body of the material, not a surface coating, so it does not fade or rub off."),
    ("Is there a minimum order?",
     "No formal minimum, but the economics favour pieces of roughly 1&nbsp;m across or larger. Below that, our smallest roundels still deliver a fully handmade piece."),
  ]),
 ),
 schema_extra=[SERVICE_SCHEMA("Custom Mosaic Wall Art", "Bespoke mosaic wall art produced to exact wall dimensions from customer artwork, photographs or logos.",
   DOMAIN + "/custom-mosaic-wall-art/", DOMAIN + "/images/gallery/handcut_04.jpg")],
))

# ------------------------------------------------------- 4. from photo
PAGES.append(dict(
 slug="mosaic-from-photo",
 title="Mosaic From a Photo &mdash; Turn Your Image Into Mosaic Art | Art Mosaic Factory",
 desc="Turn a photograph, portrait or painting into a handcut mosaic. We proof the image, advise where detail will hold, then cut and set it in glass or stone.",
 h1="Mosaic From Your Photograph",
 lede="Send a photograph &mdash; a family portrait, a wedding picture, a house, a pet, a painting you own. We rebuild it in cut glass and stone so it survives on a wall for generations instead of fading in a frame.",
 body=(sec("What survives the translation, and what does not",
   "<p>Turning a photograph into mosaic is a translation, not a copy. The mosaicist decides where to keep detail and where to simplify, and that decision is what separates a good mosaic portrait from a pixelated one.</p>",
   "<p>The rule of thumb is <b>one tessera per meaningful feature</b>. For a face to read properly, the eye and the mouth need a handful of tesserae each &mdash; which means a portrait generally wants to be at least 60&ndash;80&nbsp;cm tall, and comfortable at 1&nbsp;m or more. Below that, we will suggest a tighter crop or a stronger silhouette.</p>",
   "<p>Images that work beautifully: figures against a plain ground, animals, boats and buildings with clear edges, silhouettes at sunset, line art, and any photograph where the subject is unambiguous. Images that need work: busy crowds, heavy foliage texture, and anything where the emotional content sits in fine facial detail.</p>")
  + sec_bg("Sending us an image",
   "<h2>What to send</h2>",
   "<p>An email with the photograph attached and three facts is enough for us to quote properly:</p>",
   "<ul>"
   "<li><b>The wall size</b> you have available, ideally in millimetres (width &times; height).</li>"
   "<li><b>How far away</b> people will usually stand &mdash; this determines how much detail is worth cutting.</li>"
   "<li><b>Indoors or outside</b>, and whether it is a wet area. This drives the material choice.</li></ul>",
   "<p>We reply with a proof rendering and a fixed price. There is no charge for the proof and no obligation.</p>",
   "<h2>Where photo mosaics usually go</h2>",
   "<p>Memorial walls and family portraits in homes; founder portraits and heritage walls in company receptions; wedding and anniversary gifts that are meant to last; pet portraits; and house or venue portraits commissioned as gifts.</p>")
  + gal_section("Portrait and figure work", "Selected pieces",
      [AMIMG("byzantine-icon"), AMIMG("portrait-feature-wall"), AMIMG("koi-dining"),
       G("handcut_06","Mosaic artist hand-cutting gold glass tesserae","Cutting glass by hand"),
       AMIMG("tropical-landscape"), AMIMG("sacred-heart")])
  + rel_section("Related", [
      ("/custom-mosaic-wall-art/", "Custom Mosaic Wall Art", "Any size, any subject"),
      ("/handcut-mosaic-murals/", "Handcut Murals", "How they are built"),
      ("/mosaic-mural-cost/", "Cost Guide", "What a portrait costs"),
      ("/faq/", "Full FAQ", "Every common question"),
    ])
  + faq_section("Photo mosaic questions", [
    ("How much detail can you keep from a photograph?",
     "Roughly one tessera per feature. As a guide, a well-lit head-and-shoulders portrait reads clearly from about 80&nbsp;cm tall; a full-length figure or group needs 1.5&nbsp;m or more. We will tell you the minimum size for your specific image before you order."),
    ("Will it look like the photograph?",
     "It will read as the photograph &mdash; the likeness, the pose, the mood, the dominant colours. It will not be photographically sharp, and it is not meant to be. Expect a mosaic: visible tesserae, real surface relief, colour that shifts with the light."),
    ("Can you work from an old or damaged photograph?",
     "Often yes. Send a scan at the highest resolution available. We can propose restoration and simplification as part of the proof so you can see exactly what will be lost."),
  ]),
 ),
 schema_extra=[SERVICE_SCHEMA("Mosaic From Photo", "Photograph-to-mosaic service producing handcut glass and stone mosaics from customer images.",
   DOMAIN + "/mosaic-from-photo/", DOMAIN + "/images/artmurals/am_06.jpg")],
))

# ------------------------------------------------------- 5. feature wall
PAGES.append(dict(
 slug="mosaic-feature-wall",
 title="Mosaic Feature Walls for Interiors | Art Mosaic Factory, Foshan",
 desc="Handcut mosaic feature walls for living rooms, stairwells, lobbies and restaurants. Made to your wall dimensions in glass, smalti and stone.",
 h1="Mosaic Feature Walls",
 lede="A single mosaic wall does the work of a whole scheme: it gives a room its focal point, its colour story and its sense of craftsmanship. We make them to measure, for designers and for homeowners.",
 body=(sec("The room&rsquo;s one wall that matters",
   "<p>Interior designers use mosaic where a room needs a signature surface but not a whole-surface treatment. One wall, done properly in cut tesserae, settles the palette for everything else in the space &mdash; and unlike a wallpaper or a paint finish, it is still there in thirty years.</p>",
   "<h2>Where a mosaic feature wall works hardest</h2>",
   "<ul>"
   "<li><b>Behind a sofa or bed</b> &mdash; a wide landscape-format panel, often 3&ndash;5&nbsp;m long and 1.2&ndash;1.8&nbsp;m high, sitting above furniture height.</li>"
   "<li><b>Stairwells and double-height voids</b> &mdash; the one place a tall portrait-format mural belongs. Mosaic holds up at distance, and gold tesserae catch light as you move.</li>"
   "<li><b>Dining and bar walls</b> &mdash; darker, richer palettes with gold or mother-of-pearl, deliberately low-lit.</li>"
   "<li><b>Entrance halls and reception walls</b> &mdash; the first thing a visitor sees, and the piece that says how the rest of the building will feel.</li>"
   "<li><b>Alcoves, niche walls and chimney breasts</b> &mdash; irregular openings are where a made-to-measure mosaic beats any standard product.</li></ul>",
   "<p>Get the proportion right and everything else follows. As a rule, a feature panel should occupy between one third and two thirds of the wall it sits on, with its dominant horizontal or vertical line aligning to a real architectural line in the room.</p>")
  + sec_bg("Design decisions that change the result",
   "<h2>Four choices worth thinking about early</h2>",
   "<table><tr><th>Decision</th><th>Effect</th></tr>"
   "<tr><td>Tessera size</td><td>Small tesserae (5&ndash;10&nbsp;mm) give fine colour blending and read as painterly. Large tesserae (20&nbsp;mm+) give a bolder, more architectural pattern and suit very large walls viewed from distance.</td></tr>"
   "<tr><td>Grout colour</td><td>A grout close to the surrounding tesserae makes the wall read as one continuous surface. A contrasting grout emphasises the grid and makes it read as a tiled pattern.</td></tr>"
   "<tr><td>Matt vs. gloss glass</td><td>Gloss vitreous glass throws light around and brightens a dark room; matt finishes give a flatter, more stone-like result and photograph better.</td></tr>"
   "<tr><td>Backlit or front-lit</td><td>Some murals are designed to be backlit through a translucent backing panel &mdash; dramatic, but the mosaic must be designed for it from the start. Tell us early.</td></tr></table>")
  + gal_section("Feature walls in situ", "Interiors",
      [G("handcut_01","Blue and white floral bird handcut mosaic mural","Floral bird feature wall"),
       G("handcut_08","Gold and cream glass mosaic wall of bamboo leaves","Gold bamboo wall"),
       G("handcut_17","Wide mosaic mural panel","Wide-format panel"),
       G("handcut_16","Mosaic mural in a living interior","Living room mural"),
       G("handcut_12","Mosaic wall art detail","Detail of cut tesserae"),
       G("handcut_18","Large format mosaic mural","Large format installation")])
  + rel_section("Related", [
      ("/handcut-mosaic-murals/", "Handcut Murals", "The full service"),
      ("/hotel-mosaic-art/", "Hotel &amp; Hospitality", "Contract-scale work"),
      ("/mosaic-bathroom-wall/", "Bathroom Mosaics", "Wet-area feature walls"),
      ("/mosaic-mural-cost/", "Cost Guide", "Sizing and budget"),
    ])
  + faq_section("Feature wall questions", [
    ("Can a mosaic be fitted over existing tiles or paint?",
     "In most cases yes, provided the substrate is sound, flat and clean. Painted plaster usually needs scoring or a bonding primer; glossy tiles need a degreasing and a suitable modified adhesive. Full guidance goes in the setting-out drawing we ship with the mosaic."),
    ("How thick is a finished mosaic wall?",
     "Between roughly 10&nbsp;mm and 25&nbsp;mm including the adhesive bed, depending on tesserae size and material. If you are working within a tight reveal or a door jamb, tell us the available depth and we will design to it."),
    ("Does mosaic work with underfloor heating or in a wet room?",
     "Yes. Mosaic handles thermal movement well because the tesserae are individually bedded &mdash; it is more tolerant than large-format tile in that respect. For wet rooms, use the pool-grade specification."),
  ]),
 ),
 schema_extra=[SERVICE_SCHEMA("Mosaic Feature Walls", "Made-to-measure handcut mosaic feature walls for residential and commercial interiors.",
   DOMAIN + "/mosaic-feature-wall/", DOMAIN + "/images/gallery/handcut_01.jpg")],
))

# ------------------------------------------------------- 6. backsplash
PAGES.append(dict(
 slug="mosaic-backsplash",
 title="Mosaic Kitchen Backsplash &mdash; Handcut Feature Panels | Art Mosaic Factory",
 desc="Handcut mosaic kitchen backsplashes and bar fronts. Heat-resistant vitreous glass, made to your exact run and splash height. Send a photo for a free proof.",
 h1="Mosaic Kitchen Backsplashes",
 lede="The backsplash is the one surface in a kitchen that is always in view and always being looked at. A handcut mosaic panel turns it into the room&rsquo;s artwork &mdash; and unlike a print, it wipes clean, takes heat, and never fades.",
 body=(sec("Why mosaic belongs behind a hob",
   "<p>Vitreous glass mosaic is genuinely suited to the hardest-working wall in the kitchen. It is non-porous, so grease and cooking splatter wipe off. It will not discolour. It handles the heat behind a hob where painted surfaces blister. And it can be scrubbed without fear, which is more than can be said for printed splashback panels and vinyl film.</p>",
   "<p>The practical specification matters though. Behind a hob, keep a clear zone of at least the hob width plus 100&nbsp;mm each side in a plain or simple mosaic, and let the artwork sit to one side or above. That way the piece stays visible instead of being hidden by pans.</p>",
   "<h2>Typical formats</h2>",
   "<ul>"
   "<li><b>Full-run splashback</b> &mdash; the whole wall between counter and upper cabinets, with the subject composed to fit the run.</li>"
   "<li><b>Insert panel</b> &mdash; a defined rectangular or arched panel centred behind the hob, with plain tile or stone around it.</li>"
   "<li><b>Bar front and island face</b> &mdash; a wider, lower horizontal composition, often geometric or repeating.</li>"
   "<li><b>Full-height wall</b> &mdash; the backsplash continuing up past the cabinets for a dramatic single surface.</li></ul>")
  + rel_section("Related", [
      ("/mosaic-bathroom-wall/", "Bathroom Mosaics", "Wet-area mosaic walls"),
      ("/handcut-mosaic-murals/", "Handcut Murals", "How the cutting works"),
      ("/mosaic-installation-guide/", "Installation Guide", "Adhesives, grout, sealing"),
      ("/mosaic-mural-cost/", "Cost Guide", "What drives the price"),
    ])
  + gal_section("Backsplash designs", "Kitchen &amp; bar",
      [G("bs_02_peacock","Peacock mosaic backsplash panel with flowing tail feathers","Peacock backsplash", "backsplash"),
       G("bs_01_tropical","Tropical foliage mosaic backsplash with birds of paradise","Tropical backsplash", "backsplash"),
       G("bs_03_lotus","Tall lotus mosaic backsplash panel","Lotus panel", "backsplash"),
       G("bs_05_leopard","Leopard mosaic feature panel for a kitchen wall","Leopard panel", "backsplash"),
       G("bs_06_phoenix","Phoenix bird mosaic backsplash in warm glass tones","Phoenix backsplash", "backsplash"),
       G("bs_07_artnouveau","Art Nouveau mosaic backsplash with flowing linework","Art Nouveau panel", "backsplash")],
      "All backsplash panels are cut to your run and splash height &mdash; nothing here is a fixed product size.")
  + faq_section("Backsplash questions", [
    ("Can a mosaic backsplash go directly behind a gas hob?",
     "Yes. Vitreous glass is fired at over 1,000&nbsp;&deg;C in manufacture and takes radiant heat far better than paint or laminate. The practical limit is the adhesive and grout, so we always specify a heat-rated cementitious or epoxy system for the hob zone."),
    ("How do I clean it?",
     "Warm water and a soft cloth for everyday cleaning; a mild non-abrasive cleaner for grease. Avoid aggressive acidic descalers and abrasive pads on gold-leaf glass, which can dull the surface. Grout can be sealed on installation for easier maintenance."),
    ("Can you match my existing kitchen colour scheme?",
     "Yes &mdash; send the cabinet and worktop details, or a paint reference, and we will build a glass palette against it. Since glass colour runs through the body of the material, the palette is stable and will not drift from the sample."),
  ]),
 ),
 schema_extra=[SERVICE_SCHEMA("Mosaic Kitchen Backsplash", "Handcut mosaic kitchen backsplash panels made to the customer's exact run and splash height.",
   DOMAIN + "/mosaic-backsplash/", DOMAIN + "/images/backsplash/bs_02_peacock.jpg")],
))

# ------------------------------------------------------- 7. bathroom
PAGES.append(dict(
 slug="mosaic-bathroom-wall",
 title="Mosaic Bathroom Wall Art &mdash; Waterproof Feature Walls | Art Mosaic Factory",
 desc="Handcut mosaic bathroom wall art and wet-room feature walls. Glass tesserae are non-porous and humidity-proof. Made to your wall size and shower dimensions.",
 h1="Mosaic Bathroom Walls",
 lede="A bathroom is the one room where you are alone with a surface for twenty minutes at a time. Mosaic belongs here more than anywhere: it is waterproof by nature, it handles steam, and it gives a small room a focal point that costs almost no floor area.",
 body=(sec("Built for wet rooms from the start",
   "<p>Vitreous glass mosaic is non-porous and dimensionally stable. Steam does not lift it, condensation does not stain it, and it tolerates the repeated wet-dry cycling of a shower far better than most decorative finishes. This is the same material family used in swimming pools, and it has been used in baths and hammams for two thousand years for exactly these reasons.</p>",
   "<h2>Where it works in a bathroom</h2>",
   "<ul>"
   "<li><b>Behind the basin</b> &mdash; a modest panel at eye level, the most-seen wall in the room.</li>"
   "<li><b>Shower wall or shower niche</b> &mdash; full-height panels, designed so the composition survives the fittings. We set out around the shower valve and rail positions.</li>"
   "<li><b>Feature wall beside the bath</b> &mdash; a tall composition that gives a narrow bathroom a vertical lift.</li>"
   "<li><b>Bath panel and surround</b> &mdash; a mosaic skirt around a freestanding tub, often a repeating motif rather than a picture.</li>"
   "<li><b>Complete room</b> &mdash; a single colour story carried across every wall, with the artwork concentrated on one.</li></ul>",
   '<div class="callout"><p><b>Plan the fittings first.</b> Give us the positions of the shower valve, handset rail, mirror, light fittings and towel rail before we compose the artwork. Reworking a mural around a fitting after it is cut is expensive; setting out around it at design stage costs nothing.</p></div>')
  + gal_section("Bathroom mosaics", "In situ",
      [AMIMG("blue-floral-bath"), AMIMG("sepia-botanical-bath"),
       G("handcut_10","Oversized white daisy mosaic feature wall","Oversized daisy wall"),
       G("handcut_04","White blossom with gold core handcut mosaic mural","Blossom with gold core"),
       AMIMG("magnolia-blue"), G("handcut_05","Ocean wave glass mosaic wall mural in blue turquoise and gold","Ocean wave mosaic")])
  + faq_section("Bathroom mosaic questions", [
    ("Is mosaic safe in a steam shower?",
     "Yes, provided the whole assembly is specified as a wet-room system: a suitable waterproof substrate or tanking membrane, a polymer-modified or epoxy adhesive, and an epoxy or sealed cementitious grout. The glass itself is unaffected by steam."),
    ("Will the grout go mouldy?",
     "Not if the correct grout is used and the room is ventilated. Epoxy grout is effectively non-porous and is our recommendation for shower zones. Cementitious grout should be sealed on installation and the seal maintained."),
    ("How do you handle a shower niche or an uneven wall?",
     "Send dimensions and photographs of the wall including the reveal depth around any niche. We cut sections to suit and mark the setting-out drawing so your installer knows exactly where each section lands."),
  ]),
 ),
 schema_extra=[SERVICE_SCHEMA("Mosaic Bathroom Wall Art", "Waterproof handcut mosaic wall art and wet-room feature walls for bathrooms and steam rooms.",
   DOMAIN + "/mosaic-bathroom-wall/", DOMAIN + "/images/artmurals/am_03.jpg")],
))

# ------------------------------------------------------- 8. hotel
PAGES.append(dict(
 slug="hotel-mosaic-art",
 title="Hotel &amp; Hospitality Mosaic Art &mdash; Contract Murals | Art Mosaic Factory",
 desc="Contract-grade mosaic art for hotels, resorts, restaurants and spas. Lobby and atrium murals, pool mosaics and FF&E panels, shipped worldwide from our Foshan factory.",
 h1="Hotel &amp; Hospitality Mosaic Art",
 lede="Hotel mosaic work is a different discipline from residential work: it is specified by designers, priced against a budget line, scheduled against a handover date, and judged by guests who will look at it every day for twenty years.",
 body=(sec("What hospitality projects need from a mosaic supplier",
   "<p>We work with interior designers, procurement agents and FF&amp;E contractors. That means the conversation starts with a specification and a programme, not a picture.</p>",
   "<ul>"
   "<li><b>Sample boards before commitment</b> &mdash; material and palette samples supplied for designer sign-off, so the client approves the actual glass rather than a screen image.</li>"
   "<li><b>A dated production programme</b> &mdash; issued with the quotation and revised if the design changes, so the mosaic is never the item that delays handover.</li>"
   "<li><b>Sectional delivery</b> &mdash; murals are cut into numbered sections sized to the access route, the lift, and the installer&rsquo;s working day. A 6&nbsp;m atrium wall that will not fit through the service lift is useless.</li>"
   "<li><b>Contract-grade materials</b> &mdash; pool-grade glass, epoxy bedding and grout for wet and exterior zones; slip-rated stone for floors; UV-stable glass for anything sunlit.</li>"
   "<li><b>Installation documentation</b> &mdash; setting-out drawings, section maps and adhesive specification issued for the site team, in a form that can be filed and referenced later.</li>"
   "<li><b>Repeatability</b> &mdash; if the brand rolls out to a second property, the palette and the design are documented and can be reproduced.</li></ul>")
  + sec_bg("Where mosaic earns its place in a hotel",
   "<table><tr><th>Location</th><th>Typical treatment</th><th>Why mosaic</th></tr>"
   "<tr><td>Lobby and reception</td><td>Large feature mural, 4&ndash;10&nbsp;m, often with gold or backlighting</td><td>Arrival moment; the single strongest visual asset in the building</td></tr>"
   "<tr><td>Atrium and lift core</td><td>Full-height portrait mural across several floors</td><td>Reads at distance; scale is limited only by the wall</td></tr>"
   "<tr><td>Restaurants and bars</td><td>Dining wall or bar front, richer palette, low lighting</td><td>Photographs well for the hotel&rsquo;s own marketing</td></tr>"
   "<tr><td>Pool deck and spa</td><td>Pool floor motifs, medallions, spa wall panels</td><td>Frost-proof and chlorine-resistant by material</td></tr>"
   "<tr><td>Guest bathrooms</td><td>Shower or vanity feature panel</td><td>Withstands industrial cleaning regimes</td></tr>"
   "<tr><td>Corridors</td><td>Repeating motif or a series of roundels</td><td>Repetition is cheap to produce and gives a long run a rhythm</td></tr></table>")
  + rel_section("Related", [
      ("/handcut-mosaic-murals/", "Handcut Murals", "Materials and formats"),
      ("/mosaic-feature-wall/", "Feature Walls", "Interior specification"),
      ("/pool-mosaic-tiles/", "Pool Mosaics", "Pool and spa work"),
      ("/about/", "About the Factory", "Capacity and history"),
    ])
  + faq_section("Hospitality project questions", [
    ("Can you supply against a designer's specification and sample schedule?",
     "Yes. Send the specification, the FF&amp;E schedule reference and the required delivery date. We return a quotation with a production programme, and supply physical material samples for design sign-off before production starts."),
    ("Do you ship internationally and handle export documentation?",
     "Yes &mdash; we ship worldwide from Foshan and have delivered to 30+ countries. Mosaics are crated with edge protection and section numbering. We can quote FOB, CIF or delivered, and provide the commercial documentation your freight forwarder needs."),
    ("What lead time should a hotel project plan for?",
     "For a typical bespoke mural, allow four to seven weeks from design approval to shipment, plus sea or air transit. Large multi-panel atrium schemes and projects requiring sample-board approval should allow longer. Give us the handover date and we will tell you the latest design-freeze date."),
    ("Can you match a palette across multiple properties?",
     "Yes. Once a palette is approved we document it, and it can be reproduced for later phases or sister properties. Glass colour is inherent to the material rather than a surface coating, so a re-order years later will match."),
  ]),
 ),
 schema_extra=[SERVICE_SCHEMA("Hotel and Hospitality Mosaic Art", "Contract-grade mosaic murals, pool mosaics and FF&E panels for hotels, resorts and restaurants.",
   DOMAIN + "/hotel-mosaic-art/", DOMAIN + "/images/artmurals/am_17.jpg")],
))

# ------------------------------------------------------- 9. pool
PAGES.append(dict(
 slug="pool-mosaic-tiles",
 title="Pool Mosaic Tiles &mdash; Handcut Pool Floor Art &amp; Murals | Art Mosaic Factory",
 desc="Handcut pool mosaic tiles and pool floor art. Frost-proof, chlorine-resistant vitreous glass, slip-rated for deck use, made to your pool dimensions.",
 h1="Pool Mosaic Tiles &amp; Pool Floor Art",
 lede="A pool is the one place where a mosaic is walked on, submerged in chlorinated water and left outside in the sun for decades. The material has to be right before the design is even discussed.",
 body=(sec("Material first, picture second",
   "<p>Vitreous glass mosaic has been the standard pool-lining material for over a century and for good reason. It does not absorb water, so it does not freeze and spall in winter. It is unaffected by chlorine, bromine or salt systems. It does not fade under UV. And because each tessera is bedded individually, it tolerates the thermal and structural movement of a pool shell better than large-format tile &mdash; the joints flex rather than crack.</p>",
   "<table><tr><th>Zone</th><th>Specification</th></tr>"
   "<tr><td>Pool interior &mdash; walls and floor</td><td>Vitreous glass tesserae, epoxy or pool-grade cementitious adhesive, epoxy grout</td></tr>"
   "<tr><td>Waterline band</td><td>Glass, typically in a contrasting colour; the most visually exposed metre of the pool</td></tr>"
   "<tr><td>Surround and deck</td><td>Slip-rated stone or glass mosaic (R11 or better) &mdash; do not use smooth gloss glass where people walk barefoot</td></tr>"
   "<tr><td>Exterior wall alongside the pool</td><td>Frost-proof glass or natural stone; the same detail work as an interior mural</td></tr></table>",
   '<div class="callout"><p><b>One safety point worth repeating:</b> polished glass is not a deck material. If the mosaic continues out of the water onto the surround, we specify a slip-rated finish or switch to stone for the walking surface.</p></div>')
  + sec_bg("Designing for water",
   "<h2>What reads well under water</h2>",
   "<p>Underwater distortion, refraction and the movement of the surface change how a design is read. Three practical rules:</p>",
   "<ul>"
   "<li><b>Work at a large scale.</b> Fine detail is lost. A motif that would be subtle on a wall can be doubled in size on a pool floor.</li>"
   "<li><b>Expect colour shift.</b> Water absorbs red first, so warm reds and oranges go dull and blue-green tones strengthen. We compensate in the palette when we know the design will be submerged.</li>"
   "<li><b>Account for the waterline.</b> The tile band at the waterline is where the eye rests. Treat it as a designed element, not a leftover.</li></ul>",
   "<p>Typical commissioned work includes water-lily and lotus floors, coral and reef scenes, wave and current motifs, illuminated infinity-edge features, spa medallions, and freeform backyard pools where the mosaic follows the shell&rsquo;s own shape.</p>")
  + gal_section("Pool and spa work", "In situ",
      [G("insitu-01-spa-wave-mural","Illuminated spa wave mosaic wall","Spa wave mural","pool"),
       G("insitu-03-lotus-pool-floor","Lotus mosaic pool floor","Lotus pool floor","pool"),
       G("insitu-04-curved-wave-feature","Curved glass wave mosaic feature","Curved wave feature","pool"),
       G("insitu-05-coral-reef-floor","Coral reef mosaic pool floor","Coral reef floor","pool"),
       G("insitu-13-luxury-spa-medallion","Luxury spa mosaic medallion","Spa medallion","pool"),
       G("insitu-14-freeform-backyard","Freeform backyard pool mosaic","Freeform pool","pool")])
  + faq_section("Pool mosaic questions", [
    ("Is your pool mosaic suitable for salt-water pools?",
     "Yes. Vitreous glass is unaffected by salt chlorination. The critical items are the adhesive and grout &mdash; both must be specified for the water chemistry, and we issue that specification with the mosaic."),
    ("Does pool mosaic survive freezing winters?",
     "Frost-proof glass mosaic does, provided the pool is correctly constructed with proper drainage and the shell is not subject to ground movement. This is the standard lining method for outdoor pools in cold climates."),
    ("Can you follow the shape of a freeform pool?",
     "Yes. Send a dimensioned plan of the shell, or a surveyed drawing. Freeform and kidney shapes are where a cut mosaic outperforms any modular system, because everything is cut to fit rather than cut to a grid."),
    ("Do you supply matching mosaic for the pool surround?",
     "Yes, and we will advise where to use glass and where to switch to a slip-rated stone. The aesthetic can be continuous while the friction underfoot changes with the zone."),
  ]),
 ),
 schema_extra=[SERVICE_SCHEMA("Pool Mosaic Tiles", "Frost-proof, chlorine-resistant handcut mosaic tiles and pool floor art.",
   DOMAIN + "/pool-mosaic-tiles/", DOMAIN + "/images/pool/insitu-03-lotus-pool-floor.jpg")],
))

# ------------------------------------------------------- 10. cost
PAGES.append(dict(
 slug="mosaic-mural-cost",
 title="What a Handcut Mosaic Mural Costs &mdash; Price Drivers Explained | Art Mosaic Factory",
 desc="How handcut mosaic mural pricing actually works: the six factors that set the price, how to reduce cost without losing impact, and how to get a fixed quote.",
 h1="What a Handcut Mosaic Mural Costs",
 lede="Mosaic is priced by hand-time, not by a price list. This page explains exactly what drives the number &mdash; so you can decide what to spend money on and what to leave out before you ask for a quote.",
 body=(sec("Honest pricing: why there is no price per square metre",
   "<p>You will find mosaic sold by the square metre, and for a repeating standard pattern that is a sensible way to buy. A commissioned picture mural is not that product. Two murals of identical size can differ several-fold in price, because the cost sits in the number of cuts, the material of the tesserae, and the amount of hand-setting &mdash; none of which scale with area alone.</p>",
   "<p>Anyone quoting a mural from a photograph without asking about tesserae size, material and detail density is guessing. We quote after looking at your actual design and your actual wall, and the number we give is fixed.</p>",
   "<h2>The six factors that set the price</h2>",
   "<table><tr><th>Factor</th><th>Why it changes the price</th></tr>"
   "<tr><td>Wall area</td><td>The baseline. Area drives material volume and setting time, and time rises faster than area because larger pieces are usually also more detailed.</td></tr>"
   "<tr><td>Tessera size</td><td>The single biggest variable. Halving tesserae size roughly quadruples the number of pieces to cut and set for the same wall. A 5&nbsp;mm mosaic can cost several times a 20&nbsp;mm mosaic of the same size.</td></tr>"
   "<tr><td>Material</td><td>Standard vitreous glass is the baseline. Smalti costs more. Real gold and silver leaf glass costs substantially more and is normally used selectively rather than across a whole design.</td></tr>"
   "<tr><td>Detail density</td><td>A portrait, a face or fine lettering takes far longer per square metre than a broad landscape or a simple geometric field.</td></tr>"
   "<tr><td>Shape and cutting</td><td>Straight rectangles and circles are cheapest. Arches, ovals, irregular openings and shaped panels need bespoke setting-out and edge cutting.</td></tr>"
   "<tr><td>Sectioning and documentation</td><td>Large murals must be cut into transportable sections sized to your access route, with a setting-out drawing. This is real work, and skipping it makes installation much more expensive on site.</td></tr></table>")
  + sec_bg("How to reduce cost without losing the effect",
   "<ul>"
   "<li><b>Enlarge the design and simplify the tessera size.</b> A bold mural at 15&nbsp;mm tesserae viewed from four metres will often read better than a fine one at 6&nbsp;mm &mdash; and costs a fraction as much.</li>"
   "<li><b>Use gold as an accent, not a field.</b> Gold leaf in a halo, a border or a few highlights gives the shimmer that people remember. Covering an entire background in gold is where budgets go.</li>"
   "<li><b>Concentrate the detail.</b> Keep the face or the focal subject at fine tessera size and let the background go coarse. This is how historic mosaics were built and it is still the most economical approach.</li>"
   "<li><b>Let us compose to a standard section size.</b> If the mural can be divided without wastage, you avoid the cost of bespoke section setting-out.</li>"
   "<li><b>Simplify the background.</b> Flat colour fields cost far less than textured foliage or busy skies, and usually look stronger.</li>"
   "<li><b>Fix the design before production.</b> Changes after cutting starts are the most expensive changes of all.</li></ul>",
   "<h2>What a quote from us includes</h2>",
   "<p>A proof rendering of your image in mosaic; material and palette specification; the sectional layout plan; a fixed price; and a dated production programme. If we believe a smaller or simpler version would serve you better at a lower cost, we will say so &mdash; a mural that reads well on the wall matters more to us than one extra square metre of invoice.</p>")
  + faq_section("Cost questions", [
    ("Can you give me a ballpark before I send a design?",
     "Roughly, yes &mdash; but only with caveats. Send the wall size and we will give you an indicative band and tell you which factors are still unknown. A firm fixed price needs the design."),
    ("Is a proof charged for?",
     "No. The proof rendering and the quotation are free and carry no obligation."),
    ("What payment terms do you use?",
     "Typically a deposit to start production and the balance before shipment, with milestone payments on larger contract work. Exact terms are confirmed in the quotation."),
    ("Do you price in USD or EUR?",
     "We can quote in USD, EUR or RMB depending on your preference. The currency is fixed at quotation, so a later exchange-rate move does not change your price."),
  ]),
 ),
 schema_extra=[],
))

# ------------------------------------------------------- 11. how made
PAGES.append(dict(
 slug="how-handcut-mosaic-murals-are-made",
 title="How Handcut Mosaic Murals Are Made &mdash; Six Stages | Art Mosaic Factory",
 desc="From artwork to installed mural: proofing the design, planning the tesserae, hand-cutting, setting, sectioning and documentation. Inside our Foshan mosaic workshop.",
 h1="How a Handcut Mosaic Mural Is Made",
 lede="Six stages, and the first three are the ones that decide whether the finished mural is worth looking at. Here is the whole process, including the parts most suppliers gloss over.",
 body=(sec("Stage 1 &mdash; Reading the artwork",
   "<p>Before anything is cut, we study the source image and decide how it will survive translation into tesserae. Where is the eye drawn? Which edges must stay crisp and which can soften? Which tonal transitions are gradual enough to be built from runs of colour, and which need a hard boundary?</p>",
   "<p>This is the stage where a good mosaicist earns their keep, and it is the stage most automated suppliers skip. If the design logic is wrong here, no amount of careful cutting will rescue it.</p>",
   "<h2>Stage 2 &mdash; Proofing</h2>",
   "<p>We render a mosaic-aware proof: the image redrawn as it will actually appear in tesserae, at the real wall size. You see the artwork as mosaic &mdash; not as a photograph &mdash; and approve it before production. Where the translation loses something important, we say so and propose a change.</p>",
   "<h2>Stage 3 &mdash; Planning tessera size and direction</h2>",
   "<p>Tessera size is decided per zone, not for the whole mural. A face might be built at 6&nbsp;mm and its background at 15&nbsp;mm. We also set the <em>andamento</em> &mdash; the direction of flow of the tesserae. Rows that follow a form make it read as three-dimensional; rows that march in a rectilinear grid flatten it. This single decision is what makes a mosaic look alive or look like tiles.</p>")
  + sec_bg("Stage 4 &mdash; Cutting",
   "<p>Glass is scored and cut by hand, tessera by tessera, using nippers and cutters. Colours are laid out in work-in-progress runs so tonal transitions can be judged on the work surface, not on a screen. A large detailed mural is many hundreds of hours of this.</p>",
   "<h2>Stage 5 &mdash; Setting</h2>",
   "<p>Tesserae are placed face-down onto a paper or film carrier in the reverse of the final image, or set directly, depending on the intended installation method. The reverse method is generally used for wall murals because it lets the whole design be assembled flat and inspected before it ever reaches the wall.</p>",
   "<h2>Stage 6 &mdash; Sectioning, documentation and packing</h2>",
   "<p>Finished work is divided into numbered sections sized to the access route at your site &mdash; the lift, the stairwell, the doorway. A setting-out drawing is produced showing exactly where each section lands on the wall, together with adhesive and grout specification. Sections are packed flat with edge protection and shipped.</p>",
   '<div class="callout"><p><b>Why the section plan matters more than it sounds.</b> A mural that arrives as one unmanageable sheet is a site problem; a mural that arrives as twenty numbered sections with a map is a morning&rsquo;s work for two installers. The documentation is not paperwork &mdash; it is what makes the price of installation predictable.</p></div>')
  + rel_section("Related", [
      ("/handcut-mosaic-murals/", "The Service", "Materials and formats"),
      ("/mosaic-installation-guide/", "Installation Guide", "Adhesives, grout, sequence"),
      ("/mosaic-mural-cost/", "Cost Drivers", "Where the money goes"),
      ("/about/", "About the Workshop", "People and capacity"),
    ])
  + faq_section("Process questions", [
    ("Do I see the mosaic before it ships?",
     "Yes. You approve a mosaic-aware proof before cutting starts, and we send progress photographs during cutting and setting. For contract work we can also supply a sample board of the actual materials before production."),
    ("What happens if I want to change the design after approving the proof?",
     "Changes are usually possible until cutting begins, and we will re-proof at no charge. Once tesserae are cut for a specific area, changes in that area become a rework cost. We flag which areas are committed at each milestone."),
    ("How is the mosaic delivered?",
     "Face-mounted on paper or film, in numbered sections, tesserae facing down where the method requires it, packed flat with edge protection and shipped on a pallet. The setting-out drawing and material specification are included."),
  ]),
 ),
 schema_extra=[{
   "@context": "https://schema.org", "@type": "HowTo",
   "name": "How a handcut mosaic mural is made",
   "description": "The six-stage process of turning customer artwork into a handcut mosaic mural.",
   "step": [{"@type": "HowToStep", "position": i + 1, "name": n, "text": t} for i, (n, t) in enumerate([
     ("Reading the artwork", "Studying the source image to decide what survives translation into tesserae."),
     ("Proofing", "Rendering the image as it will appear in mosaic at real wall size for approval."),
     ("Planning tessera size and direction", "Setting tessera size per zone and the direction of flow (andamento)."),
     ("Cutting", "Scoring and cutting each tessera by hand and laying out colour runs."),
     ("Setting", "Placing tesserae face-down on a carrier in the reverse of the final image."),
     ("Sectioning and documentation", "Dividing the work into numbered sections and producing the setting-out drawing."),
   ])],
 }],
))

# ------------------------------------------------------- 12. installation
PAGES.append(dict(
 slug="mosaic-installation-guide",
 title="Mosaic Installation Guide &mdash; Adhesives, Grout &amp; Sequence | Art Mosaic Factory",
 desc="How handcut mosaic murals are installed: substrate preparation, adhesive and grout selection, wet-area specification, section sequence and finish sealing.",
 h1="Mosaic Installation Guide",
 lede="A handcut mural is a permanent fixture, and the installation decides how long it lasts. This is the guidance we issue with every piece &mdash; substrate, adhesive, sequence and finishing, zone by zone.",
 body=(sec("Substrate: what the mosaic is happy to be fixed to",
   "<table><tr><th>Substrate</th><th>Preparation</th></tr>"
   "<tr><td>New plaster or render</td><td>Fully cured, sound, flat to within 3&nbsp;mm over 2&nbsp;m, dust-free, primed</td></tr>"
   "<tr><td>Painted plaster</td><td>Score or key the surface, remove loose or flaking paint, apply a bonding primer</td></tr>"
   "<tr><td>Existing ceramic tile</td><td>Degrease, abrade gloss tiles, use a modified adhesive rated for tiling onto tile</td></tr>"
   "<tr><td>Plasterboard / drywall</td><td>Only in dry areas; in wet areas use a tile backer board or tanking membrane</td></tr>"
   "<tr><td>Concrete</td><td>Fully cured, level, free of release agents and laitance</td></tr>"
   "<tr><td>Pool shell</td><td>Structurally sound, watertight, correct curing; epoxy or pool-grade cementitious system</td></tr></table>",
   "<h2>Adhesive and grout",
   "<p>For dry interior walls, a polymer-modified cementitious mosaic adhesive is normally correct. For wet rooms, exterior work and pools, we specify epoxy bedding and epoxy grout. Both are supplied to a specification issued with your mural, because the wrong adhesive is the most common cause of a mosaic failing.</p>",
   "<p>Grout colour is a design decision as much as a technical one. A grout matched to the surrounding tesserae closes the design up and makes it read as a continuous surface. A contrasting grout emphasises the grid. Tell us which effect you want and we will specify accordingly.</p>")
  + sec_bg("Installation sequence for a sectioned mural",
   "<ol>"
   "<li><b>Unpack and check.</b> Lay out the numbered sections and verify against the setting-out drawing before anything is fixed.</li>"
   "<li><b>Set out.</b> Establish the centreline and datum from the drawing. For a design with a dominant horizontal &mdash; a horizon, a waterline &mdash; the datum line is critical; get it right first.</li>"
   "<li><b>Start from the centre or the datum.</b> Work outward. This keeps any accumulated error at the edges where it can be trimmed, rather than in the middle of the design.</li>"
   "<li><b>Bed the sections.</b> Apply adhesive to the wall, press the section in, and check level and alignment continuously.</li>"
   "<li><b>Remove the carrier.</b> For face-mounted work, the paper or film is removed once the adhesive has set, following the method statement &mdash; usually a controlled soaking or a peel after a set interval.</li>"
   "<li><b>Clean carefully.</b> Remove adhesive residue from the face before it cures. Do not use acidic cleaners on glass or gold leaf.</li>"
   "<li><b>Grout and finish.</b> Grout after the tesserae have set, clean down, and seal cementitious grout where specified.</li></ol>",
   "<h2>Handling and storage before installation</h2>",
   "<p>Store sections flat, indoors, out of the sun. Face-mounted paper should not be wetted before installation. Do not stack heavy items on the sections. If the mural will sit on site for more than a few weeks, keep it dry and check it for movement before installation.</p>")
  + rel_section("Related", [
      ("/how-handcut-mosaic-murals-are-made/", "How They Are Made", "The production process"),
      ("/mosaic-bathroom-wall/", "Wet Areas", "Shower and steam specification"),
      ("/pool-mosaic-tiles/", "Pool Installation", "Submerged and deck zones"),
      ("/faq/", "Full FAQ", "All common questions"),
    ])
  + faq_section("Installation questions", [
    ("Can my own tiler install the mosaic?",
     "Yes, and most of our clients do exactly that. A competent tiler who follows the method statement and the setting-out drawing will achieve a good result. For very large or complex schemes we can advise on installation or help you select a specialist mosaic installer."),
    ("How long does installation take?",
     "A single-section panel takes a few hours. A large multi-section mural is usually one to three days for two installers, plus curing time before grouting and any sealing."),
    ("Do you provide the adhesive and grout?",
     "We supply the specification, and can supply the materials if you prefer &mdash; particularly the epoxy systems, which are harder to source locally in some markets."),
  ]),
 ),
 schema_extra=[],
))

# ------------------------------------------------------- 13. faq
FAQ_ALL = [
 ("What exactly is a handcut mosaic mural?",
  "A mural in which every tesserae &mdash; every individual piece of glass or stone &mdash; is cut by hand and placed by hand into the design. Nothing is printed, and no uniform machine-cut grid is used, so curves and fine detail hold instead of breaking into steps."),
 ("How much does a mosaic mural cost?",
  "It depends on four things above all: wall area, tesserae size, material and how much fine detail the design contains. Halving the tesserae size roughly quadruples the cutting and setting work for the same wall. We quote free and fixed once we have seen the design and the wall dimensions &mdash; see the <a href=\"/mosaic-mural-cost/\">cost guide</a>."),
 ("How long does an order take?",
  "Typically four to seven weeks from approved proof to shipping for a bespoke mural. Small roundels can be quicker. Large contract schemes with sample-board approval take longer. We issue a dated production programme with every quotation."),
 ("Do you ship internationally?",
  "Yes. We ship worldwide from Foshan and have delivered to over thirty countries. Mosaics travel flat, crated with edge protection and numbered sections, together with the setting-out drawing."),
 ("Can you work from my own photograph or painting?",
  "That is how most commissions start. Send the highest resolution image you have plus the wall size and we will return a free proof showing how it translates into mosaic."),
 ("Is a mosaic mural waterproof?",
  "The glass itself is non-porous and frost-proof, which is why the same material lines swimming pools. Waterproofing a wall depends on the full assembly &mdash; substrate, adhesive and grout &mdash; and we issue the wet-area specification with the mural."),
 ("Can mosaic be installed over existing tiles or paint?",
  "Usually yes, with the correct preparation: degreasing and abrading gloss tiles, or keying and priming painted plaster, and using an adhesive rated for the substrate. Full guidance is in our <a href=\"/mosaic-installation-guide/\">installation guide</a>."),
 ("How do I clean and maintain it?",
  "Warm water and a soft cloth for routine cleaning, a mild non-abrasive cleaner for grease. Avoid acidic descalers and abrasive pads, particularly on gold-leaf glass. Cementitious grout should be sealed on installation and the seal maintained."),
 ("Will the colours fade?",
  "No. Glass and stone colour runs through the body of the material rather than sitting on the surface as a coating, and vitreous glass is UV-stable. A mosaic in direct sun will still look the same colour in fifty years."),
 ("Can you repair a damaged mosaic?",
  "Often yes, including historic work. Send photographs of the damaged area with a scale reference and tell us the approximate age; we will tell you how closely we can match."),
 ("Do you have a minimum order?",
  "No formal minimum. In practice the economics favour pieces of roughly one metre across or larger, but our smallest roundels are still fully handmade."),
 ("Can I see physical samples before ordering?",
  "Yes &mdash; for contract and interior design projects we supply a physical sample board of the actual materials and palette for sign-off. For residential commissions, material photographs and the proof rendering are usually sufficient."),
 ("Do you supply ready-made designs or only bespoke work?",
  "Both. Our <a href=\"/mosaic-murals/\">collection of twenty-one designs</a> can be ordered broadly as shown, or adapted in scale, palette and format. Bespoke work from your own artwork is the larger part of what we do."),
 ("In what currency do you quote?",
  "USD, EUR or RMB, fixed at quotation, so a later exchange-rate movement does not change your price."),
]

PAGES.append(dict(
 slug="faq",
 title="Mosaic Mural FAQ &mdash; Cost, Lead Time, Shipping &amp; Care | Art Mosaic Factory",
 desc="Answers to the questions we are asked most: how handcut mosaic murals are priced, how long they take, shipping, waterproofing, cleaning, repairs and samples.",
 h1="Mosaic Mural FAQ",
 lede="Everything clients ask us before commissioning &mdash; cost, lead times, shipping, wet areas, installation, cleaning and repairs. No sales padding; if something depends on your project we say so.",
 body=faq_section("Common questions", FAQ_ALL,
   "Ask us anything that is not covered here and we will answer it directly."),
 schema_extra=[FAQ_SCHEMA([(q, re.sub(r"<[^>]+>", "", a)) for q, a in FAQ_ALL])],
))

# ------------------------------------------------------- 14. about
PAGES.append(dict(
 slug="about",
 title="About Art Mosaic Factory &mdash; Handcut Mosaic Studio, Foshan China",
 desc="Foshan E-Tile Building Material Co., Ltd. Fourteen years of mosaic production, handcut art murals and engineering mosaics shipped to over thirty countries.",
 h1="About the Workshop",
 lede="Art Mosaic Factory is the mosaic art studio of Foshan E-Tile Building Material Co., Ltd. &mdash; fourteen years of mosaic production in China&rsquo;s ceramics and stone capital, and a small workshop within it that does nothing but cut pictures by hand.",
 body=(sec("What we actually are",
   "<p>Foshan is where a large share of the world&rsquo;s tile and mosaic is made. Foshan E-Tile has been producing mosaic there for over fourteen years, supplying standard mosaic and engineered mosaic work to projects in more than thirty countries. Art Mosaic Factory is the part of that business that makes commissioned art &mdash; murals, portraits, roundels, feature walls and pool art, cut and set by hand.</p>",
   "<p>That combination is the reason this studio exists. A large production facility gives us material sourcing, quality control and export logistics that a small craft studio cannot match. A craft workshop gives us the hand-cutting and the design judgement that a production line cannot. Doing both under one roof means the artist and the factory are the same company.</p>",
   "<h2>What we make</h2>",
   "<ul>"
   "<li><b>Custom handcut art murals</b> from customer artwork, photography or paintings</li>"
   "<li><b>Feature walls</b> for residential, hospitality and commercial interiors</li>"
   "<li><b>Roundels, medallions and floor mosaics</b> in glass and natural stone</li>"
   "<li><b>Pool, spa and wet-area mosaics</b> to contract specification</li>"
   "<li><b>Engineering and standard mosaic</b> through Foshan E-Tile for large projects</li></ul>")
  + sec_bg("How we work",
   "<p>We are set up for people who specify rather than browse: interior designers, architects, FF&amp;E contractors, procurement agents and private clients commissioning a single piece. That means we answer specification questions properly, quote in writing with a fixed price and a dated programme, and supply the documentation a site team needs.</p>",
   "<p>We also try to be straight about limits. Mosaic is not a printer; fine detail has a floor. Some images need to be simplified, some walls need a different scale, and sometimes a smaller piece will look better than the one you asked for. We will tell you that at the proof stage rather than let you find out on site.</p>",
   "<h2>Contact</h2>",
   "<p>Foshan E-Tile Building Material Co., Ltd. &middot; Foshan, Guangdong, China<br>"
   "Email <a href=\"mailto:tinafs618@gmail.com\">tinafs618@gmail.com</a> &middot; "
   "WhatsApp <a href=\"https://wa.me/8613827780690\" target=\"_blank\" rel=\"noopener\">+86 138 2778 0690</a></p>")
  + rel_section("Start here", [
      ("/handcut-mosaic-murals/", "The Service", "What handcut means"),
      ("/gallery/", "The Gallery", "Everything we have made"),
      ("/mosaic-mural-cost/", "Cost Guide", "How pricing works"),
      ("/contact/", "Get a Quote", "Free proof in 24 hours"),
    ])
  + gal_section("From the workshop", "Selected work",
      [G("handcut_06","Mosaic artist hand-cutting gold glass tesserae","Hand-cutting gold glass"),
       G("handcut_12","Close detail of handcut mosaic tesserae","Tessera detail"),
       G("handcut_11","Mosaic panel under construction","Work in progress"),
       AMIMG("leopard-peonies"), AMIMG("phoenix-grand-salon"), AMIMG("butterfly-field")])
 ),
 schema_extra=[{
   "@context": "https://schema.org", "@type": "AboutPage",
   "name": "About Art Mosaic Factory",
   "mainEntity": {"@type": "Organization", "@id": DOMAIN + "/#organization",
                  "name": "Art Mosaic Factory",
                  "legalName": "Foshan E-Tile Building Material Co., Ltd.",
                  "foundingDate": "2012",
                  "address": {"@type": "PostalAddress", "addressLocality": "Foshan",
                              "addressRegion": "Guangdong", "addressCountry": "CN"},
                  "email": MAIL,
                  "telephone": "+8613827780690",
                  "areaServed": "Worldwide",
                  "knowsAbout": ["handcut mosaic", "mosaic murals", "mosaic wall art",
                                 "glass mosaic", "pool mosaic", "smalti"]},
 }],
))

# ------------------------------------------------------- 15. contact
PAGES.append(dict(
 slug="contact",
 title="Contact Art Mosaic Factory &mdash; Free Mosaic Proof &amp; Quote",
 desc="Send your artwork, photograph or wall dimensions for a free mosaic proof and a fixed quote. Foshan E-Tile Building Material Co., Ltd., Guangdong, China.",
 h1="Send Us Your Project",
 lede="Email a photograph, a drawing or simply your wall dimensions. You will get a mosaic proof and a fixed quotation &mdash; normally within 24 hours, and always free.",
 body=(sec("What to send us",
   "<ol>"
   "<li><b>Your image</b> &mdash; a photograph, painting, sketch, logo or a reference picture of something similar. A phone photograph is usually enough to quote.</li>"
   "<li><b>The wall size</b> &mdash; width and height, ideally in millimetres, and the available depth if there is a reveal or a jamb.</li>"
   "<li><b>Where it is going</b> &mdash; room type, indoors or out, wet area or dry, and how far away people will normally view it.</li>"
   "<li><b>Anything you already know</b> &mdash; colour scheme, deadline, budget range, or a designer&rsquo;s specification.</li></ol>",
   "<h2>Reach us directly</h2>",
   "<ul>"
   "<li><b>Email:</b> <a href=\"mailto:tinafs618@gmail.com\">tinafs618@gmail.com</a></li>"
   "<li><b>WhatsApp:</b> <a href=\"https://wa.me/8613827780690\" target=\"_blank\" rel=\"noopener\">+86 138 2778 0690</a> &mdash; fastest for sending images and short questions</li>"
   "<li><b>Factory:</b> Foshan E-Tile Building Material Co., Ltd., Foshan, Guangdong, China</li></ul>",
   "<p>Contract and interior design enquiries are welcome &mdash; send the specification and required delivery date and we will return a quotation with a production programme and material samples for sign-off.</p>")
  + rel_section("Before you write", [
      ("/mosaic-mural-cost/", "Cost Guide", "What drives the price"),
      ("/handcut-mosaic-murals/", "The Service", "Materials and formats"),
      ("/faq/", "FAQ", "Lead times, shipping, care"),
      ("/mosaic-murals/", "The Collection", "21 designs to start from"),
    ]),
 ),
 schema_extra=[{
   "@context": "https://schema.org", "@type": "ContactPage",
   "name": "Contact Art Mosaic Factory",
   "mainEntity": {"@type": "Organization", "@id": DOMAIN + "/#organization",
                  "name": "Art Mosaic Factory", "email": MAIL,
                  "telephone": "+8613827780690"},
 }],
))

# ------------------------------------------------------- 16. gallery hub
GAL_ITEMS = [(AU(m), "/images/artmurals/" + m["file"], m.get("alt_en") or m["desc_en"], m["en"], m["w"], m["h"]) for m in MAN]
GAL_ITEMS += [(u, src, alt, cap, w, h) for u, src, alt, cap, w, h in [
    ("/mosaic-backsplash/", *G("bs_02_peacock", "Peacock mosaic backsplash panel", "Peacock backsplash", "backsplash")),
    ("/mosaic-backsplash/", *G("bs_05_leopard", "Leopard mosaic kitchen panel", "Leopard panel", "backsplash")),
    ("/mosaic-backsplash/", *G("bs_06_phoenix", "Phoenix mosaic backsplash", "Phoenix backsplash", "backsplash")),
    ("/mosaic-feature-wall/", *G("handcut_01", "Blue and white floral bird mosaic mural", "Floral bird wall")),
    ("/mosaic-feature-wall/", *G("handcut_08", "Gold and cream glass bamboo mosaic wall", "Gold bamboo wall")),
    ("/mosaic-feature-wall/", *G("handcut_17", "Wide mosaic mural panel", "Wide panel")),
    ("/pool-mosaic-tiles/", *G("insitu-01-spa-wave-mural", "Illuminated spa wave mosaic", "Spa wave mural", "pool")),
    ("/pool-mosaic-tiles/", *G("insitu-03-lotus-pool-floor", "Lotus mosaic pool floor", "Lotus pool floor", "pool")),
    ("/pool-mosaic-tiles/", *G("insitu-13-luxury-spa-medallion", "Luxury spa mosaic medallion", "Spa medallion", "pool")),
]]

PAGES.append(dict(
 slug="gallery",
 title="Mosaic Gallery &mdash; 36 Handcut Murals, Panels &amp; Pool Art | Art Mosaic Factory",
 desc="The full Art Mosaic Factory gallery: handcut art murals, chinoiserie and botanical panels, kitchen backsplashes, pool mosaics and in-situ installations.",
 h1="Mosaic Gallery",
 lede="Every piece here was cut and set by hand in our Foshan workshop. Click any image to see the design, the materials and how it can be adapted to your wall.",
 body=(sec("Thirty-six pieces, and none of them a stock product",
   "<p>Some are studio pieces made as design studies; most were commissioned for a specific wall in a specific room. All of them can be re-composed &mdash; a different size, a different palette, a different format &mdash; because everything starts from a design drawing rather than a fixed mould.</p>",
   "<p>If you see something close to what you want, tell us what you would change. If you see nothing you like, send us your own image; that is how most of the work on this page started.</p>")
  + gal_linked(GAL_ITEMS)
  + rel_section("Browse by type", [
      ("/mosaic-murals/", "Art Murals", "21 handcut designs"),
      ("/mosaic-feature-wall/", "Feature Walls", "Interiors and stairwells"),
      ("/mosaic-backsplash/", "Backsplashes", "Kitchens and bars"),
      ("/mosaic-bathroom-wall/", "Bathrooms", "Wet-area artwork"),
      ("/hotel-mosaic-art/", "Hospitality", "Contract-scale work"),
      ("/pool-mosaic-tiles/", "Pools &amp; Spas", "Submerged and deck"),
    ]),
 ),
 schema_extra=[{
   "@context": "https://schema.org", "@type": "CollectionPage",
   "name": "Mosaic Gallery", "isPartOf": {"@id": DOMAIN + "/#website"},
 }],
))

# ==================================================== 17. artwork detail pages
APP = [
 (("bath", "bathroom"), "bathroom wall or a bathroom feature panel",
  "In a bathroom the mosaic has to cope with steam and cleaning products, so we build these with non-porous vitreous glass, epoxy bedding and epoxy grout."),
 (("dining", "table"), "dining room wall",
  "Positioned behind a dining table, this scale of work reads at seating distance, so fine detail is worth including."),
 (("living room",), "living room feature wall",
  "This is a full-height living room piece; the ceiling height usually allows a tall composition rather than a wide one."),
 (("pool", "spa"), "pool or spa area",
  "For submerged and wet-deck use we switch to pool-grade glass with epoxy bedding; for the surrounding walls the standard specification is unchanged."),
 (("floor", "medallion"), "floor or foyer medallion",
  "Floor work uses denser tesserae and a slip-rated surface where people walk on it. Send a surveyed plan if the shape is irregular."),
 (("hall", "salon", "atrium"), "hall, salon or atrium wall",
  "Designed to be read at distance, so tessera size is usually increased and fine detail deliberately reduced."),
 (("fountain", "zellige"), "wet feature wall or fountain surround",
  "Built for constant water contact with epoxy bedding and grout."),
]
def apply_for(desc):
    d = desc.lower()
    for keys, where, note in APP:
        if any(k in d for k in keys):
            return where, note
    return "feature wall in a dining room, bedroom, hallway or reception", \
           "The scale can be reduced for a smaller wall, though fine detail is lost below roughly one metre in height."

MATS = [
 ("Vitreous glass tesserae", "The main body of the design. Non-porous, frost-proof and UV-stable."),
 ("Smalti", "Hand-poured Italian glass used where the design needs a richer or more painterly colour run."),
 ("Gold-leaf glass", "Real gold leaf sealed between glass layers, used on highlights and borders. It will not tarnish."),
 ("Mother of pearl", "Used for skies, water and soft highlights; it shifts as you move past it."),
 ("Natural stone", "Used where the piece is intended for heavy wear, floors or exterior exposure."),
]

for idx, m in enumerate(MAN):
    slug = "mosaic-murals/" + m["slug"]
    CRUMBS[slug] = [(DOMAIN + "/", "Home"), (DOMAIN + "/mosaic-murals/", "Mosaic Murals")]
    where, note = apply_for(m["desc_en"])
    nxt = MAN[(idx + 1) % len(MAN)]
    prv = MAN[(idx - 1) % len(MAN)]
    orient = "portrait" if m["h"] > m["w"] * 1.15 else ("landscape" if m["w"] > m["h"] * 1.15 else "square")
    rel = [MAN[(idx + k) % len(MAN)] for k in (2, 5, 9, 13)]
    body = (
        gal_section(m["en"], "Artwork", [AMIMG(m["slug"])])
        + sec("About this design",
          "<p><b>%s.</b> %s</p>" % (m["en"], m["desc_en"]),
          "<p>This is a %s-format composition. It is intended for a %s. %s</p>" % (orient, where, note),
          "<p>The palette is built from glass tesserae rather than applied colour, so it is stable under UV and will not fade. Where the design needs a highlight that carries across a room, we use gold-leaf glass or mother of pearl at the focal point &mdash; these read as a genuine shimmer in person, which is exactly what photographs cannot capture.</p>")
        + sec_bg("Materials and how it can be adapted",
          "<h2>Materials in this piece</h2>",
          "<table><tr><th>Material</th><th>Role</th></tr>%s</table>"
              % "".join("<tr><td>%s</td><td>%s</td></tr>" % (a, b) for a, b in MATS),
          "<h2>Making it fit your wall</h2>",
          "<p>We re-compose this design to your wall rather than shipping it as a fixed size. That means:</p>",
          "<ul>"
          "<li><b>Re-scaling.</b> Both up and down, with tessera size adjusted so the piece reads correctly at the viewing distance you describe.</li>"
          "<li><b>Re-formatting.</b> The design can be extended, cropped or converted between portrait and landscape where the composition allows.</li>"
          "<li><b>Re-colouring.</b> The palette can be matched to a paint reference, a fabric or an existing interior scheme.</li>"
          "<li><b>Sectioning.</b> Dimensions taken from your access route so every section fits through the door and the lift.</li></ul>",
          "<p>If you would like this as a starting point, send us the wall size on the <a href=\"/contact/\">contact page</a> and we will return a proof of the adapted version.</p>")
        + rel_section("More from the collection", [
            (AU(nxt), nxt["en"], "Next design"),
            (AU(prv), prv["en"], "Previous design"),
            ("/mosaic-murals/", "The Full Collection", "All 21 designs"),
            ("/mosaic-mural-cost/", "What It Costs", "Price drivers explained"),
          ])
        + faq_section("Questions about this piece", [
          ("Can you make this design at a different size?",
           "Yes. We re-scale the composition and adjust the tessera size to suit your wall and viewing distance. Wall dimensions are all we need to quote an adapted version."),
          ("Can the colours be changed?",
           "Yes. The palette can be matched to a paint, fabric or stone reference. Glass colour runs through the body of the material, so a matched palette will not fade or drift."),
          ("How long would this take and what does it cost?",
           "Lead time is typically four to seven weeks from approved proof to shipping. Price depends on your final size, tessera size and material &mdash; send the wall dimensions and we will give you a fixed figure with the proof. See the <a href=\"/mosaic-mural-cost/\">cost guide</a> for how the number is built up."),
        ])
    )
    PAGES.append(dict(
        slug=slug,
        title="%s &mdash; Handcut Mosaic Mural | Art Mosaic Factory" % m["en"].replace("&amp;", "&"),
        desc="%s. Handcut in glass and stone, made to your wall dimensions. Free proof and fixed quote from our Foshan mosaic workshop." % m["desc_en"].replace("&amp;", "&")[:150],
        h1=m["en"],
        lede="%s &mdash; a handcut mosaic design from our collection, adaptable in size, format and palette to suit your wall." % m["desc_en"],
        body=body,
        schema_extra=[{
          "@context": "https://schema.org", "@type": "CreativeWork",
          "name": m["en"].replace("&amp;", "&"),
          "description": m["desc_en"].replace("&amp;", "&"),
          "image": DOMAIN + "/images/artmurals/" + m["file"],
          "creator": {"@type": "Organization", "@id": DOMAIN + "/#organization"},
          "isPartOf": {"@id": DOMAIN + "/mosaic-murals/"},
          "material": "Vitreous glass, smalti, gold leaf glass",
          "genre": "Handcut mosaic mural",
        }],
    ))

# =================================================================== BUILD
def write(rel, text):
    p = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return len(text)

def url_of(slug):
    s = slug.strip("/")
    return DOMAIN + "/" + (s + "/" if s else "")

total = 0
for pg in PAGES:
    n = write(pg["slug"] + "/index.html", page(
        pg["slug"], pg["title"], pg["desc"], pg["h1"], pg["lede"], pg["body"],
        pg.get("schema_extra")))
    total += n
print("wrote %d pages, %d bytes" % (len(PAGES), total))

# --------------------------------------------------------------- sitemap
PRIO = {"": "1.0", "handcut-mosaic-murals": "0.9", "custom-mosaic-wall-art": "0.9",
        "mosaic-from-photo": "0.9", "mosaic-feature-wall": "0.9", "mosaic-backsplash": "0.9",
        "mosaic-bathroom-wall": "0.9", "hotel-mosaic-art": "0.9", "pool-mosaic-tiles": "0.9",
        "mosaic-murals": "0.8", "gallery": "0.8", "mosaic-mural-cost": "0.8",
        "how-handcut-mosaic-murals-are-made": "0.7", "mosaic-installation-guide": "0.7",
        "faq": "0.7", "about": "0.6", "contact": "0.8"}
FREQ = {"": "weekly", "gallery": "weekly", "mosaic-murals": "weekly"}
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
      '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']

def img_block(src, cap):
    return ('    <image:image>\n      <image:loc>%s%s</image:loc>\n'
            '      <image:caption>%s</image:caption>\n    </image:image>'
            % (DOMAIN, src, esc(cap)))

def add(loc, prio, freq, imgs=()):
    sm.append("  <url>")
    sm.append("    <loc>%s</loc>" % loc)
    sm.append("    <lastmod>%s</lastmod>" % TODAY)
    sm.append("    <changefreq>%s</changefreq>" % freq)
    sm.append("    <priority>%s</priority>" % prio)
    for s, c in imgs:
        sm.append(img_block(s, c))
    sm.append("  </url>")

# homepage + a couple of its key image entries
home_imgs = [("/images/gallery/handcut_%s.jpg" % n, t) for n, t in [
 ("01", "Blue and white floral bird handcut mosaic mural"),
 ("03", "Grey crowned cranes and botanical trees mosaic mural"),
 ("04", "White blossom with gold core handcut mosaic mural"),
 ("05", "Ocean wave glass mosaic wall mural in blue turquoise and gold"),
 ("06", "Mosaic artist hand-cutting gold glass tesserae"),
 ("08", "Gold and cream glass mosaic wall of bamboo leaves"),
 ("17", "Wide handcut mosaic mural panel")]]
add(DOMAIN + "/", "1.0", "weekly", home_imgs)
add(DOMAIN + "/zh/", "0.8", "weekly")

for pg in PAGES:
    slug = pg["slug"]
    imgs = []
    if slug == "mosaic-murals" or slug == "gallery":
        imgs = [("/images/artmurals/" + m["file"], m["en"]) for m in MAN]
    elif slug.startswith("mosaic-murals/"):
        m = AM[slug.split("/", 1)[1]]
        imgs = [("/images/artmurals/" + m["file"], m["en"])]
    add(url_of(slug), PRIO.get(slug, "0.7" if "/" not in slug else "0.6"),
        FREQ.get(slug, "monthly"), imgs)

sm.append("</urlset>")
n = write("sitemap.xml", "\n".join(sm) + "\n")
print("sitemap: %d urls, %d bytes" % (len(PAGES) + 2, n))

# --------------------------------------------------------------- robots
write("robots.txt",
      "User-agent: *\nAllow: /\n\n"
      "User-agent: GPTBot\nAllow: /\n\n"
      "User-agent: PerplexityBot\nAllow: /\n\n"
      "User-agent: ClaudeBot\nAllow: /\n\n"
      "Sitemap: %s/sitemap.xml\n" % DOMAIN)

# --------------------------------------------------------------- IndexNow
KEY = "a7f3c9e21d84b6f05c3e9a7b4d18f26a"
write(KEY + ".txt", KEY + "\n")
io.open(os.path.join(SITE, "tools", "indexnow_key.txt"), "w").write(KEY)
print("indexnow key file:", KEY + ".txt")

# --------------------------------------------------------------- llms.txt
lines = ["# Art Mosaic Factory (Foshan E-Tile)", "",
 "> Handcut mosaic art studio and factory in Foshan, China. We turn customer artwork, photographs,",
 "> logos and paintings into bespoke hand-cut glass mosaic murals for residential and hospitality walls.", "",
 "## What we make",
 "- Custom handcut mosaic wall art and murals (photo, painting, logo or pattern as the source)",
 "- Mosaic feature walls for living rooms, hotel atriums, powder rooms, bathrooms, kitchen backsplashes",
 "- Chinoiserie, Art Deco, botanical, peacock, landscape and portrait subjects in glass tesserae",
 "- Pool, spa and wet-area mosaics to contract specification",
 "- Roundels, medallions and floor mosaics in glass and natural stone", "",
 "## How it works",
 "1. Send your artwork or photo and the wall size.",
 "2. We quote, then produce a digital proof for approval.",
 "3. Tesserae are hand-cut and placed by craftsmen; the mural ships in sections with installation guidance.", "",
 "## Key pages"]
for pg in PAGES:
    lines.append("- %s: %s" % (pg["h1"].replace("&amp;", "&"), url_of(pg["slug"])))
lines += ["- Homepage: %s/" % DOMAIN,
          "- Image sitemap: %s/sitemap.xml" % DOMAIN, "",
          "## Contact",
          "- Email: %s" % MAIL,
          "- WhatsApp: +86 138 2778 0690",
          "- Location: Foshan, Guangdong, China", ""]
write("llms.txt", "\n".join(lines))
print("llms.txt updated")




