# -*- coding: utf-8 -*-
"""Generate zh/index.html from the (already picture-ised) English index.html."""
import io, json, os, re

SITE = r"G:/handcut-landing"
EN = os.path.join(SITE, "index.html")
ZH = os.path.join(SITE, "zh", "index.html")
DOMAIN = "https://www.artmosaicfactory.com"

MAN = json.load(open(next(p for p in (os.path.join(SITE, "tools", "artmurals-manifest.json"),
                             os.path.join(SITE, "images", "artmurals", "manifest.json"))
                    if os.path.exists(p)), encoding="utf-8"))
M = {m["file"]: m for m in MAN}

# ------------------------------------------------ filename -> Chinese alt text
ALT_BY_FILE = {
 "gallery/handcut_01.jpg": "青花花卉与飞鸟手工镶嵌壁画",
 "gallery/handcut_02.jpg": "欧洲运河风景手工镶嵌壁画",
 "gallery/handcut_03.jpg": "豪华客厅壁炉上方灰冠鹤与植物丛树手工镶嵌壁画",
 "gallery/handcut_04.jpg": "金心白花手工镶嵌壁画",
 "gallery/handcut_05.jpg": "海滨风格客厅沙发上方深蓝、绿松石与金色海浪玻璃马赛克墙",
 "gallery/handcut_06.jpg": "马赛克匠人用钳子手工剪裁金色玻璃颗粒、拼装放射状图案",
 "gallery/handcut_07.jpg": "独立浴缸上方中式风格蓝灰凤头鹦鹉栖于花枝马赛克壁画",
 "gallery/handcut_08.jpg": "豪华 SPA 浴室金琥珀与米色玻璃竹叶马赛克墙",
 "gallery/handcut_09.jpg": "桃色中式风格花树、飞鸟与牡丹马赛克画板",
 "gallery/handcut_10.jpg": "现代浴室雕塑感大理石浴缸后方超大白色雏菊马赛克主题墙",
 "gallery/handcut_11.jpg": "深色豪华酒吧内黑底白色玉兰花马赛克壁画",
 "gallery/handcut_12.jpg": "豪华浴室独立浴缸上方蓝、青绿与金色孔雀马赛克艺术墙",
 "gallery/handcut_14.jpg": "华丽客厅热带植物玻璃马赛克壁画，配鹦鹉与丛林叶片",
 "gallery/handcut_15.jpg": "豪华客厅装饰艺术风格黑金白豹行进马赛克壁画",
 "gallery/handcut_16.jpg": "中式风格客厅林中湖面双白天鹅手工镶嵌壁画",
 "gallery/handcut_17.jpg": "热带火烈鸟马赛克会议室主题墙",
 "gallery/handcut_18.jpg": "阳光走廊热带植物马赛克",
 "backsplash/bs_01_tropical.jpg": "热带叶片马赛克主题墙",
 "backsplash/bs_02_peacock.jpg": "白孔雀与玉兰马赛克墙",
 "backsplash/bs_03_lotus.jpg": "荷塘与飞鸟马赛克壁画",
 "backsplash/bs_04_rose.jpg": "经典玫瑰马赛克 backsplash",
 "backsplash/bs_05_leopard.jpg": "花间花豹马赛克艺术",
 "backsplash/bs_06_phoenix.jpg": "凤凰马赛克主题墙",
 "backsplash/bs_07_artnouveau.jpg": "新艺术风格马赛克卫浴空间",
 "backsplash/bs_08_mothereofpearl.jpg": "贝母植物马赛克",
 "backsplash/bs_09_scaleblue.jpg": "鳞纹蓝色马赛克浴缸墙",
 "backsplash/bs_10_whitearc.jpg": "白色花卉拱形马赛克墙",
 "proj1.jpg": "酒店中庭热带叶片马赛克主题墙",
 "proj2.jpg": "凤凰马赛克客厅背景墙",
 "proj3.jpg": "新艺术风格藤蔓马赛克卫浴空间",
 "proj4.jpg": "贝母植物马赛克古典会客厅",
 "hero.jpg": "手工镶嵌马赛克艺术壁画",
}
ZH_DESC = {
 1:"金底拜占庭圣像镶嵌画板",2:"餐桌后的锦鲤马赛克壁画",3:"蓝白花卉马赛克浴室主题墙",
 4:"圆形花鸟马赛克",6:"牡丹与丛林枝叶间的花豹",7:"圣心虔诚主题马赛克画板",
 8:"灰底蓝色与黑色蝴蝶",9:"大宅会客厅凤凰马赛克壁画",10:"浴缸后的褐调植物马赛克墙",
 11:"热带阔叶与天堂鸟马赛克画板",12:"客厅拱形花枝马赛克壁画",13:"石榴枝头与两只小鸟",
 14:"风格化人物主题马赛克墙",15:"摩洛哥 zellige 马赛克水景墙",
 16:"黄铜框弧形热带叶马赛克艺术墙",17:"穹顶长廊几何拼花地面",
 18:"大理石地面古典人物马赛克徽章",19:"热带棕榈风景马赛克壁画板",
 20:"超大白色百合马赛克艺术墙",21:"蓝底白色玉兰拱形马赛克",22:"红冠双鸡与红色花枝",
}
for _m in MAN:
    ALT_BY_FILE["artmurals/" + _m["file"]] = ZH_DESC[_m["idx"]] + " — Art Mosaic Factory 手工镶嵌艺术壁画"

# ------------------------------------------------ caption text EN -> ZH
CAPS = [
 ("Blue-White Floral &amp; Birds","青花花卉与飞鸟"),("European Canal Scene","欧洲运河风景"),
 ("Crowned Cranes &amp; Trees","灰冠鹤与丛树"),("White Blossom &amp; Gold","白花与金"),
 ("Ocean Waves","海浪"),("Hands at Work","匠人之手"),
 ("Cockatoos &amp; Blossoms","凤头鹦鹉与花枝"),("Golden Bamboo","金色竹影"),
 ("Blossom Tree &amp; Birds","花树与飞鸟"),("White Daisies","白色雏菊"),
 ("Magnolia Noir","墨底玉兰"),("Peacocks in Blue &amp; Gold","蓝金孔雀"),
 ("Tropical Jungle","热带丛林"),("Art Deco Leopard","装饰艺术花豹"),
 ("Swans on the Lake","湖上双鹅"),("Tropical Leaves","热带叶片"),
 ("White Peacock &amp; Magnolia","白孔雀与玉兰"),("Lotus Pond &amp; Birds","荷塘与飞鸟"),
 ("Classic Roses","经典玫瑰"),("Leopard Among Flowers","花间花豹"),
 ("Phoenix Mural","凤凰壁画"),("Art Nouveau Powder Room","新艺术风格卫浴"),
 ("Mother-of-Pearl Botanicals","贝母植物纹样"),("Scale-Blue Backsplash","鳞纹蓝墙面拼花"),
 ("White Blossom Arch","白色花卉拱形"),("Flamingo Meeting Room","火烈鸟会议室"),
 ("Botanical Sunlit Hallway","阳光走廊植物墙"),
 # existing projects section captions
 ("Hotel Atrium Feature Wall","酒店中庭主题墙"),
 ("Tropical leaf mosaic with reflective pool, resort lobby","热带叶片马赛克与镜面水池，度假酒店大堂"),
 ("Living Room Backdrop","客厅背景墙"),
 ("Grand phoenix mural, luxury residence","凤凰主题大幅壁画，高端住宅"),
 ("Powder Room","卫浴空间"),
 ("Art Nouveau vine mosaic, boutique hotel","新艺术风格藤蔓马赛克，精品酒店"),
 ("Classical Lounge","古典会客厅"),
 ("Mother-of-pearl botanicals, French-style salon","贝母植物纹样，法式沙龙"),
]
for _m in MAN:
    CAPS.append((_m["en"], _m["zh"]))
    CAPS.append((_m["desc_en"], ZH_DESC[_m["idx"]]))

REPL = [
 ('<title>Handcut Mosaic Art Murals | Art Mosaic Factory, Foshan China</title>',
  '<title>手工镶嵌艺术壁画 | Art Mosaic Factory 佛山马赛克工厂</title>'),
 ('Custom mosaic wall art and handcut mosaic murals from our Foshan factory. Send a photo, painting or logo — master craftsmen turn it into bespoke wall art.',
  '来自佛山工厂的定制马赛克艺术墙与手工镶嵌壁画。提供照片、画作或 Logo，由资深匠人手工剪料、逐颗贴片，做成独一无二的定制墙面艺术。'),
 ('Handcut Mosaic Art Murals | Art Mosaic Factory','手工镶嵌艺术壁画 | Art Mosaic Factory'),
 ('Custom mosaic wall art and handcut mosaic murals — every tessera hand-cut and placed by master craftsmen.',
  '定制马赛克艺术墙与手工镶嵌壁画 — 每一颗马赛克均由资深匠人手工剪料、逐颗贴片。'),
 ('<li><a href="#gallery">Gallery</a></li>','<li><a href="#gallery">作品图库</a></li>'),
 ('<li><a href="#artmurals">Art Murals</a></li>','<li><a href="#artmurals">艺术壁画</a></li>'),
 ('<li><a href="#craft">Craft</a></li>','<li><a href="#craft">工艺</a></li>'),
 ('<li><a href="#makingof">Making of</a></li>','<li><a href="#makingof">制作过程</a></li>'),
 ('<li><a href="#projects">Projects</a></li>','<li><a href="#projects">工程案例</a></li>'),
 ('<li><a href="#process">Process</a></li>','<li><a href="#process">定制流程</a></li>'),
 ('<a class="nav-cta" href="#quote">Commission a Mural</a>','<a class="nav-cta" href="#quote">定制壁画</a>'),
 ('<em>Foshan E-Tile · Handcut Art</em>','<em>佛山宜瓷砖 · 手工镶嵌</em>'),
 ('<em>Foshan E-Tile · Mosaic</em>','<em>佛山宜瓷砖 · 马赛克</em>'),
 ('<span class="eyebrow">Handcrafted Mosaic Art</span>','<span class="eyebrow">手工镶嵌艺术</span>'),
 ('<h1>Mosaic Art,<br>Cut &amp; Set <em>by Hand</em></h1>','<h1>手工镶嵌艺术<br>一凿一贴，<em>全凭手艺</em></h1>'),
 ('<a class="btn btn-gold" href="#gallery">View Gallery ↓</a>','<a class="btn btn-gold" href="#gallery">浏览图库 ↓</a>'),
 ('<p>Custom mosaic wall art, handcrafted to order. Every tessera of your bespoke handcut mosaic mural is cut and placed by master craftsmen — send a photo, painting or logo, and we turn it into a one-of-a-kind mosaic art installation for your wall.</p>',
  '<p>按单定制的手工镶嵌艺术墙。您专属壁画上的每一颗马赛克，都由资深匠人手工剪料、逐颗贴片完成——只需提供一张照片、一幅画作或一个 Logo，我们就能把它变成您墙面上一件独一无二的镶嵌艺术作品。</p>'),
 ('<p>Handcut mosaic art in every style — classical blue-and-white, impressionist landscapes, florals, bespoke mosaic murals, backsplash and feature-wall designs. Each custom mosaic is a unique handcrafted work, scaled to your wall.</p>',
  '<p>涵盖各种风格的手工镶嵌艺术——古典青花、写意风景、花卉植物，以及按需定制的壁画、厨卫 backsplash 与主题墙设计。每一幅定制马赛克都是独此一件的手工作品，尺寸按您的墙面量身定做。</p>'),
 ('<a class="btn btn-ghost" href="#quote">Commission a Mural</a>','<a class="btn btn-ghost" href="#quote">定制壁画</a>'),
 ('<div class="hero-scroll">Scroll</div>','<div class="hero-scroll">向下滚动</div>'),
 ('<span>Years of Mosaic Craftsmanship</span>','<span>年镶嵌工艺积淀</span>'),
 ('<span>Hand-Cut &amp; Hand-Placed</span>','<span>手工剪料 · 手工贴片</span>'),
 ('<span>Tiles in a Single Mural</span>','<span>单幅壁画马赛克颗粒数</span>'),
 ('<span>Countries Delivered</span>','<span>出口国家与地区</span>'),
 ('<div class="kicker">The Collection</div>','<div class="kicker">作品系列</div>'),
 ('<h2>Handcut Mosaic Art Collection</h2>','<h2>手工镶嵌艺术壁画系列</h2>'),
 ('<div class="kicker">Art Mural Collection</div>','<div class="kicker">艺术壁画系列</div>'),
 ('<h2>Art Murals, Made to Order</h2>','<h2>艺术壁画 · 按单定制</h2>'),
 ('<p>Handmade mosaic artwork from our studio — classical icons, botanical panels, floral roundels and bold graphic pieces. Each one is produced to your size, palette and subject, either as a framed panel or set directly into your wall.</p>',
  '<p>来自我们工作室的手工镶嵌艺术作品——古典圣像、植物画板、圆形花卉与醒目图形题材。每一件都按您的尺寸、配色与题材定制，可做成独立装框画板，也可直接镶嵌上墙。</p>'),
 ('<p class="gal-note"><b>Have a wall in mind?</b> Send us the artwork and the wall size — we return a free layout and quotation within 24 hours.</p>',
  '<p class="gal-note"><b>心里已经有一面墙了？</b>把画面和墙面尺寸发给我们——24 小时内给您免费的排版方案与报价。</p>'),
 ('<div class="kicker">Why Handcut</div>','<div class="kicker">为什么选手工</div>'),
 ('<h2>The Craft Behind the Wall</h2>','<h2>墙面背后的手艺</h2>'),
 ('<p>Machine mosaics repeat; handcut art breathes. Here is what sets an Art Mosaic Factory mural apart.</p>',
  '<p>机器马赛克只能重复，手工镶嵌才有呼吸感。以下是 Art Mosaic Factory 壁画的与众不同之处。</p>'),
 ('<h3>Genuinely Handcrafted</h3>','<h3>真手工制作</h3>'),
 ('<p>Every tessera is cut and placed by hand — subtle variation, depth and life that no machine can copy.</p>',
  '<p>每一颗马赛克都由手工剪料与贴片——细微的差异、层次与生命力，机器无法复制。</p>'),
 ('<h3>Any Image, Any Size</h3>','<h3>任意画面 · 任意尺寸</h3>'),
 ('<p>Turn a photo, painting or logo into custom mosaic wall art — mapped to your exact wall dimensions, from backsplash to lobby.</p>',
  '<p>把照片、画作或 Logo 变成定制马赛克艺术墙——按您的实际墙面尺寸排版，小到厨卫 backsplash，大到酒店大堂。</p>'),
 ('<h3>Mixed Materials</h3>','<h3>多种材质混搭</h3>'),
 ('<p>Glass, stone, shell and gold accents blended in one artwork for texture and light play.</p>',
  '<p>玻璃、石材、贝壳与金箔点缀融于同一幅作品，带来丰富的质感与光影变化。</p>'),
 ('<h3>Precision Mapping</h3>','<h3>精准排版</h3>'),
 ('<p>CAD layout, colour plan and quantity sheet delivered before production — no surprises.</p>',
  '<p>生产前提供 CAD 排版图、配色方案与用量清单——杜绝任何意外。</p>'),
 ('<h3>Installer Friendly</h3>','<h3>方便施工安装</h3>'),
 ('<p>Mesh-backed sheets and a numbered installation map make professional installation straightforward.</p>',
  '<p>网背拼板 + 编号安装图，让专业施工变得简单直接。</p>'),
 ('<h3>Export-Ready Packing</h3>','<h3>出口级包装</h3>'),
 ('<p>Secure crating and anti-vibration protection for worldwide shipping.</p>','<p>牢固木箱 + 防震保护，可全球发运。</p>'),
 ('<div class="kicker">In the Workshop</div>','<div class="kicker">车间现场</div>'),
 ('<h2>How a Mosaic Work Is Created</h2>','<h2>一幅马赛克壁画如何诞生</h2>'),
 ('<b>01 · Cutting by Hand</b>','<b>01 · 手工剪料</b>'),
 ("<span>Each tessera is selected and nipped to shape — the artisan's eye guides every cut.</span>",
  '<span>每一颗马赛克都要挑选并用钳子剪裁成形——全凭匠人的眼力把控每一刀。</span>'),
 ('<b>02 · Placing Piece by Piece</b>','<b>02 · 逐颗贴片</b>'),
 ('<span>Colour by colour, tessera by tessera — the artwork grows across the worktable.</span>',
  '<span>一个颜色接一个颜色，一颗马赛克接一颗马赛克——画面在操作台上逐渐成形。</span>'),
 ('<b>03 · Setting &amp; Finishing</b>','<b>03 · 铺贴与修整</b>'),
 ('<span>Pieces bed into adhesive and grout — a permanent, seamless work of art.</span>',
  '<span>颗粒嵌入粘结剂与填缝，最终成为一幅永久、无缝的艺术作品。</span>'),
 ('<div class="kicker">In Situ</div>','<div class="kicker">落地实景</div>'),
 ('<h2>Murals That Transform Spaces</h2>','<h2>让空间改头换面的壁画</h2>'),
 ('<div class="kicker">How It Works</div>','<div class="kicker">合作流程</div>'),
 ('<h2>From Artwork to Installed Mural</h2>','<h2>从一张图到上墙成品</h2>'),
 ('<h3>Share Your Artwork</h3>','<h3>提供画面</h3>'),
 ('<p>Send a photo, painting, logo or design idea, plus your wall dimensions.</p>',
  '<p>发送照片、画作、Logo 或设计想法，并告知您的墙面尺寸。</p>'),
 ('<h3>Free Design Plan</h3>','<h3>免费设计方案</h3>'),
 ('<p>Our art team maps every tile, material and colour — free CAD preview.</p>',
  '<p>我方设计团队逐块排版，确定材质与配色——免费提供 CAD 效果预览。</p>'),
 ('<h3>Handcraft Production</h3>','<h3>手工生产</h3>'),
 ('<p>Master craftsmen cut and set each tessera, sheet by numbered sheet.</p>',
  '<p>资深匠人按编号逐板剪料、贴片，完成整幅作品。</p>'),
 ('<h3>Global Delivery</h3>','<h3>全球发运</h3>'),
 ('<h2>Commission Your Mosaic Wall Art</h2>','<h2>定制您的手工镶嵌壁画</h2>'),
 ('placeholder="Your Name *"','placeholder="您的姓名 *"'),
 ('placeholder="Email *"','placeholder="邮箱 *"'),
 ('placeholder="Country / Region"','placeholder="国家 / 地区"'),
 ('placeholder="Describe your artwork — subject, style, materials, colour preference..."',
  'placeholder="请描述您的画面 — 题材、风格、材质、色彩偏好……"'),
 ('placeholder="Wall Size (e.g. 3m × 2.4m)"','placeholder="墙面尺寸（如 3m × 2.4m）"'),
 ('<button type="submit" class="btn btn-gold">Send Inquiry</button>','<button type="submit" class="btn btn-gold">提交询盘</button>'),
 ('<div class="f-ok" id="fOk">✅ Inquiry sent! We will reply within 24 hours.</div>',
  '<div class="f-ok" id="fOk">✅ 询盘已提交！我们将在 24 小时内回复您。</div>'),
 ('<div class="f-err" id="fErr">⚠️ Submission failed — your email app has been opened with the inquiry pre-filled. Just press send, or chat with us on WhatsApp.</div>',
  '<div class="f-err" id="fErr">⚠️ 提交失败——已为您打开邮件客户端并预填询盘内容，直接点发送即可，或通过 WhatsApp 联系我们。</div>'),
 ('<h4>Products</h4>','<h4>产品</h4>'),
 ('<li><a href="#gallery">Handcut Collection</a></li>','<li><a href="#gallery">手工镶嵌系列</a></li>'),
 ('<li><a href="#projects">Project Gallery</a></li>','<li><a href="#projects">工程案例</a></li>'),
 ('<li><a href="#process">Commission Service</a></li>','<li><a href="#process">定制服务</a></li>'),
 ('>Pool Mosaic Landing</a>','>泳池马赛克落地页</a>'),
 ('<h4>Contact</h4>','<h4>联系方式</h4>'),
 ('<li>Foshan, Guangdong, China</li>','<li>中国 广东省 佛山市</li>'),
 ('<li><a href="#quote">Commission a Mural →</a></li>','<li><a href="#quote">定制壁画 →</a></li>'),
 ('aria-label="Menu"','aria-label="菜单"'),
 ('alt="Enlarged view"','alt="放大查看"'),
 ('Your browser does not support the video tag.','您的浏览器不支持视频播放。'),
]

# long paragraph / list texts captured by a second pass on distinctive fragments
FRAG = [
 ('<p>Custom mosaic wall art, handcrafted to order.', None),  # handled by full-string below
 ('Watch master craftsmen bring a mural to life — every tessera cut, placed and finished by hand in our Foshan studio.',
  '看资深匠人如何让一幅壁画活起来——在佛山工作室里，每一颗马赛克都经过手工剪料、贴片与修整。'),
 ('Real production footage from the Art Mosaic Factory workshop —',
  'Art Mosaic Factory 车间实拍生产影像 —'),
 ('<b>send us your image and watch your own mural being made</b>',
  '<b>把图片发给我们，您就能看到自己的壁画如何被制作出来</b>'),
 ('<b>Dreaming of a different scene?</b>','<b>想要不一样的画面？</b>'),
 ('Send us any image — a family portrait, brand logo or masterpiece — and we will handcraft it into mosaic art.',
  '把任何图片发给我们——全家福、品牌 Logo 或名画名作——我们都能把它手工镶嵌成一幅马赛克艺术品。'),
 ('Hotel atriums, living rooms, powder rooms and classical salons — bespoke mosaic murals from Art Mosaic Factory, installed in spaces worldwide.',
  '酒店中庭、客厅、卫浴空间到古典沙龙——Art Mosaic Factory 的定制马赛克壁画，落地于全球各地的空间。'),
 ('Four clear steps — you share the artwork, master craftsmen do the rest.',
  '四步清晰流程——您提供画面，其余交给我们的匠人。'),
 ('<p>Cratted and shipped worldwide with installation map and support.</p>',
  '<p>木箱包装发往全球，随附安装图纸与技术支持。</p>'),
 ('<p>Send us your artwork and wall size — get a free custom mosaic design plan and quotation within 24 hours.</p>',
  '<p>把画面与墙面尺寸发给我们——24 小时内获得免费的定制马赛克设计方案与报价。</p>'),
 ('<p class="f-note">Submitting sends your inquiry straight to our inbox — or chat with us instantly on WhatsApp.</p>',
  '<p class="f-note">提交后询盘将直接进入我们的邮箱——也可通过 WhatsApp 即时沟通。</p>'),
 ('<p style="margin-top:14px">14+ years of mosaic R&amp;D and production.',
  '<p style="margin-top:14px">14 年以上马赛克研发与生产经验。'),
 (' Handcut mosaic art murals, custom mosaic wall art, feature walls, pool mosaics and engineering murals for worldwide projects.',
  '手工镶嵌艺术壁画、定制马赛克艺术墙、主题背景墙、泳池马赛克及工程壁画，服务全球项目。'),
 ('<div class="footer-bottom">© 2026 Foshan E-Tile Building Material Co., Ltd. · Art Mosaic Factory · Handcut Mosaic Art</div>',
  '<div class="footer-bottom">© 2026 Foshan E-Tile Building Material Co., Ltd. · Art Mosaic Factory · 手工镶嵌艺术壁画</div>'),
 ('Handcut Mural Inquiry - ','手工镶嵌壁画询盘 - '),
 ("'Artwork Idea:\\n'","'画面想法:\\n'"),
 ("'Wall Size: '","'墙面尺寸: '"),
 ("'Country: '","'国家: '"),
 ("'Email: '","'邮箱: '"),
 ("'Name: '","'姓名: '"),
]

def apply(text, pairs, label):
    miss = []
    for en, zh in sorted([p for p in pairs if p[1]], key=lambda p: -len(p[0])):
        if en in text:
            text = text.replace(en, zh)
        else:
            miss.append(en[:65])
    print(f"  {label}: {len(miss)} not found")
    for m in miss:
        print("     -", m)
    return text

html = io.open(EN, encoding="utf-8").read()
html = apply(html, REPL, "REPL")
html = apply(html, FRAG, "FRAG")

# figcaptions + project card b/span
for en, zh in sorted(CAPS, key=lambda p: -len(p[0])):
    html = html.replace(f"<figcaption>{en}</figcaption>", f"<figcaption>{zh}</figcaption>")
    html = html.replace(f"<b>{en}</b>", f"<b>{zh}</b>")
    html = html.replace(f"<span>{en}</span>", f"<span>{zh}</span>")

# alt text keyed by image filename (robust against upstream alt rewrites)
unmapped, n_alt = set(), 0
def fix_alt(mo):
    global n_alt
    tag = mo.group(0)
    src = re.search(r'src="([^"]+)"', tag)
    if not src:
        return tag
    key = re.sub(r'^\.\./', '', src.group(1))
    key = re.sub(r'^images/', '', key)
    zh = ALT_BY_FILE.get(key)
    if not zh:
        unmapped.add(key)
        return tag
    n_alt += 1
    return re.sub(r'alt="[^"]*"', 'alt="' + zh + '"', tag)
html = re.sub(r'<img [^>]*>', fix_alt, html)

# ---- head rewrites
html = html.replace('<html lang="en">', '<html lang="zh-CN">', 1)
html = html.replace('<meta property="og:locale" content="en_US">',
                    '<meta property="og:locale" content="zh_CN">\n'
                    '<meta property="og:locale:alternate" content="en_US">', 1)
html = html.replace('<link rel="canonical" href="' + DOMAIN + '/">',
                    '<link rel="canonical" href="' + DOMAIN + '/zh/">')
html = html.replace('content="' + DOMAIN + '/"', 'content="' + DOMAIN + '/zh/"')
html = html.replace('"' + DOMAIN + '/#organization"', '"' + DOMAIN + '/zh/#organization"')
html = html.replace('"inLanguage": "en"', '"inLanguage": "zh-CN"')
html = html.replace('<li><a class="nav-lang" href="zh/" hreflang="zh-CN" lang="zh-CN">中文</a></li>',
                    '<li><a class="nav-lang" href="../" hreflang="en" lang="en">EN</a></li>')
# hreflang: en + x-default back to the site root
html = re.sub(r'(hreflang="(?:en|x-default)" href=")' + re.escape(DOMAIN) + r'/zh/"',
              r'\g<1>' + DOMAIN + '/"', html)

# ---- asset paths: ../ for the one-level-deep page
html = re.sub(r'(?<![\w/])images/', '../images/', html)
html = re.sub(r'(?<![\w/])videos/', '../videos/', html)
# srcset entries that follow a space (2nd+ candidate) were caught by the same rule

os.makedirs(os.path.dirname(ZH), exist_ok=True)
io.open(ZH, "w", encoding="utf-8", newline="\n").write(html)

print(f"\nalts localised: {n_alt}; unmapped srcs: {sorted(unmapped) or 'none'}")
print(f"zh written: {len(html)} chars")
print("residual bare paths:", [p for p in ['src="images/', 'srcset="images/', 'href="images/', "url('images/"] if p in html] or "none")
print("double-prefix bug:", "../../" in html)
for k in ("手工", 'hreflang="zh-CN" href="' + DOMAIN + '/zh/"', 'hreflang="en" href="' + DOMAIN + '/"'):
    print(f"  contains {k[:40]!r}: {k in html}")
