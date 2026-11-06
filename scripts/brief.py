"""Build the 4-page executive brief (report/brief-4page.html + report/brief-4page.pdf) from audit data."""
import json, os, subprocess, sys, datetime, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TOWNS = ["Waltham", "Newton", "Wellesley", "Needham", "Lexington", "Reading",
         "Arlington", "Belmont", "Weston", "Concord", "Boston", "MetroWest"]

def load(path):
    with open(os.path.join(ROOT, path)) as f:
        return json.load(f)

def esc(s):
    return html.escape(str(s))

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
@page { size: Letter; margin: 0; }
:root {
  --paper: #faf8f3; --ink: #1b1a17; --ink-2: #4f4c45; --ink-3: #7d7970; --rule: #dedad1;
  --forest: #1f4a36; --forest-ink: #163726; --accent: #1f8f55; --accent-soft: #e4f1e9; --bar-gray: #cfcbc1;
}
* { box-sizing: border-box; }
html, body { margin: 0; background: var(--paper); color: var(--ink); }
body { font: 10.4pt/1.42 "IBM Plex Sans", "Helvetica Neue", Arial, sans-serif; font-feature-settings: "tnum" 1, "cv11" 1; }
::selection { background: var(--accent-soft); }
.page { width: 8.5in; height: 11in; padding: 0.62in 0.7in 0.6in; page-break-after: always; position: relative; overflow: hidden; display: flex; flex-direction: column; }
.page:last-child { page-break-after: auto; }
h1, h2, h3 { font-family: "Newsreader", Georgia, "Times New Roman", serif; font-weight: 600; letter-spacing: -0.015em; margin: 0; color: var(--forest-ink); text-wrap: balance; }
h1 { font-size: 30pt; line-height: 1.08; }
h2 { font-size: 19pt; line-height: 1.15; margin-bottom: 10pt; }
h3 { font-size: 12.5pt; line-height: 1.2; margin: 0 0 4pt; }
p { margin: 0 0 7pt; max-width: 70ch; }
.lede { font-size: 12pt; line-height: 1.45; color: var(--ink); max-width: 62ch; }
.muted { color: var(--ink-2); }
.small { font-size: 9pt; line-height: 1.4; color: var(--ink-2); }
.rule { border: 0; border-top: 1px solid var(--rule); margin: 12pt 0; }

/* masthead */
.mast { display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 18pt; padding-bottom: 12pt; border-bottom: 2px solid var(--forest); margin-bottom: 16pt; }
.mast .meta { text-align: right; font-size: 9pt; line-height: 1.5; color: var(--ink-2); }
.mast .meta strong { color: var(--ink); font-weight: 600; }
.mast .sub { font-size: 11pt; color: var(--ink-2); margin-top: 6pt; }

/* hero */
.hero { display: grid; grid-template-columns: 2.55in 1fr; gap: 20pt; align-items: center; margin: 4pt 0 14pt; padding: 14pt 0; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); }
.hero .num { font-family: "Newsreader", Georgia, serif; font-weight: 500; font-size: 58pt; line-height: 0.95; letter-spacing: -0.03em; color: var(--forest-ink); }
.hero .num span { font-size: 24pt; color: var(--ink-3); letter-spacing: -0.01em; }
.hero .what { font-size: 10.5pt; line-height: 1.4; color: var(--ink); max-width: 36ch; }
.stats { display: flex; gap: 0; margin-top: 10pt; }
.stats div { padding: 0 14pt 0 0; margin-right: 14pt; border-right: 1px solid var(--rule); }
.stats div:last-child { border: 0; }
.stats b { display: block; font-family: "Newsreader", Georgia, serif; font-weight: 600; font-size: 17pt; line-height: 1.1; color: var(--forest-ink); }
.stats span { font-size: 8.6pt; color: var(--ink-2); line-height: 1.3; display: block; max-width: 18ch; }

/* two column */
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 22pt; }
.cols-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16pt; }

/* chart */
.chart h3 { margin-bottom: 2pt; }
.chart .cap { font-size: 8.8pt; color: var(--ink-2); margin-bottom: 8pt; }
.bars { display: grid; grid-template-columns: 17.5em 1fr; row-gap: 5pt; column-gap: 8pt; align-items: center; font-size: 9.3pt; }
.bars .lbl { text-align: right; color: var(--ink-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.bars .bar { display: flex; align-items: center; gap: 6pt; }
.bars .fill { height: 11pt; background: var(--bar-gray); border-radius: 0 3pt 3pt 0; }
.bars .val { font-variant-numeric: tabular-nums; color: var(--ink); font-weight: 500; }
.bars .me .lbl { color: var(--forest-ink); font-weight: 600; }
.bars .me .fill { background: var(--accent); min-width: 2pt; }
.bars .me .val { color: var(--forest-ink); font-weight: 600; }

/* findings */
.findings { counter-reset: f; }
.finding { display: grid; grid-template-columns: 22pt 1fr; gap: 8pt; margin-bottom: 9pt; }
.finding .n { font-family: "Newsreader", Georgia, serif; font-size: 16pt; font-weight: 500; color: var(--accent); line-height: 1.05; }
.finding p { margin: 0; }
.finding b { color: var(--forest-ink); }

/* tables */
table { border-collapse: collapse; width: 100%; font-size: 9.3pt; }
th { text-align: left; font-weight: 600; font-size: 8.4pt; letter-spacing: 0.02em; text-transform: uppercase; color: var(--ink-3); padding: 0 6pt 5pt 0; border-bottom: 1px solid var(--forest); }
td { padding: 4pt 6pt 4pt 0; border-bottom: 1px solid var(--rule); vertical-align: top; }
td.num, th.num { text-align: right; padding-right: 10pt; font-variant-numeric: tabular-nums; white-space: nowrap; }
td.num + td, th.num + th { padding-left: 6pt; }
td.me { color: var(--forest-ink); font-weight: 600; }
tr.me td { background: var(--accent-soft); }
tr.me td:first-child { padding-left: 5pt; border-radius: 3pt 0 0 3pt; }
tr.me td:last-child { padding-right: 5pt; border-radius: 0 3pt 3pt 0; }
.towns { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2pt 12pt; font-size: 9.1pt; margin-top: 6pt; }
.towns span:last-child { font-size: 8.3pt; white-space: nowrap; }
.towns div { display: flex; justify-content: space-between; padding: 3pt 0; border-bottom: 1px solid var(--rule); }
.towns .yes { color: var(--accent); font-weight: 600; }
.towns .no { color: var(--ink-3); }

/* recommendations */
.rec { margin-bottom: 9pt; padding-bottom: 8pt; border-bottom: 1px solid var(--rule); }
.rec:last-child { border: 0; }
.rec h3 { font-size: 11.5pt; display: flex; gap: 7pt; align-items: baseline; }
.rec h3 .k { font-family: "IBM Plex Sans", sans-serif; font-size: 8.4pt; font-weight: 600; color: var(--accent); letter-spacing: 0.02em; }
.rec p { margin: 0; font-size: 9.6pt; }
.rec p + p { margin-top: 3pt; }
blockquote { margin: 6pt 0 0; padding: 8pt 11pt; background: #fff; border: 1px solid var(--rule); border-radius: 4pt; font-family: "Newsreader", Georgia, serif; font-size: 9.9pt; line-height: 1.45; color: var(--ink); }
blockquote .t { font-family: "IBM Plex Sans", sans-serif; font-size: 8pt; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink-3); display: block; margin-bottom: 3pt; font-weight: 600; }

/* plan */
.plan h3 { font-size: 11pt; padding-bottom: 5pt; border-bottom: 2px solid var(--forest); margin-bottom: 7pt; }
.plan h3 small { font-family: "IBM Plex Sans", sans-serif; font-size: 8.4pt; font-weight: 500; color: var(--ink-3); margin-left: 6pt; }
.plan ul { margin: 0; padding-left: 13pt; font-size: 9.4pt; }
.plan li { margin-bottom: 5pt; }

footer { margin-top: auto; padding-top: 8pt; border-top: 1px solid var(--rule); font-size: 8.2pt; color: var(--ink-3); display: flex; justify-content: space-between; gap: 16pt; }
footer span:last-child { white-space: nowrap; }
"""

def bars_chart(leaderboard, n=8):
    rows = leaderboard[:n]
    mx = max(r["mentions"] for r in rows)
    out = ['<div class="chart"><h3>Firms the AI engines recommended most</h3>',
           '<div class="cap">Times named across 48 service-and-town answers. Out of the Woods is shown for comparison.</div>',
           '<div class="bars">']
    for r in rows:
        w = 100 * r["mentions"] / mx
        out.append(f'<div class="lbl">{esc(r["firm"])}</div><div class="bar"><div class="fill" style="width:{w:.1f}%"></div><span class="val">{r["mentions"]}</span></div>')
    out.append('<div class="lbl" style="color:var(--forest-ink);font-weight:600">Out of the Woods</div><div class="bar me"><div class="fill" style="width:0.5%"></div><span class="val">0</span></div>')
    out.append('</div></div>')
    return "\n".join(out)

def build():
    s = load("report/summary.json"); site = load("results/audit/site.json")
    lb = [r for r in s["leaderboard"] if "out of the woods" not in r["firm"].lower()]
    o = s["overall"]
    nonbrand_n = sum(v["n"] for k, v in s["by_intent"].items() if k != "brand")
    brand_n = s["by_intent"].get("brand", {"n": 0})["n"]
    towns_on_site = set(site["coverage"]["towns_anywhere"])
    date = datetime.date(2026, 10, 28).strftime("%B %-d, %Y")
    repo = "github.com/samueljchen08/ootw-ai-visibility"

    page1 = f"""
<section class="page">
  <div class="mast">
    <div><h1>AI-Search Visibility Audit</h1><div class="sub">Out of the Woods Construction &amp; Cabinetry · Boston-area and MetroWest design-build remodeling</div></div>
    <div class="meta"><strong>Prepared for Dave</strong><br>{date}<br>Baseline measurement</div>
  </div>
  <p class="lede">When a homeowner asks ChatGPT, Perplexity, or Google's AI Mode who should remodel their kitchen in Newton or build an addition in Needham, Out of the Woods is not in the answer. Not once. The company only surfaces when someone already knows its name. Nothing technical is in the way, and the fix is a focused set of website, review, and directory changes that the firms winning these answers have already made.</p>
  <div class="hero">
    <div><div class="num">0<span> of {nonbrand_n}</span></div></div>
    <div><div class="what">service-and-town questions where any AI engine named Out of the Woods, across the simulated engine, Perplexity, and Google AI Mode.</div>
      <div class="stats">
        <div><b>{o['n']}</b><span>AI answers captured and read</span></div>
        <div><b>{brand_n} of {brand_n}</b><span>brand-name searches did find the firm</span></div>
        <div><b>12</b><span>Route 128 and MetroWest towns tested</span></div>
      </div></div>
  </div>
  <div class="cols">
    {bars_chart(lb)}
    <div class="findings">
      <h3 style="margin-bottom:8pt">Why the engines skip Out of the Woods</h3>
      <div class="finding"><div class="n">1</div><p><b>Engines shortlist from Houzz town lists and firms' own town pages.</b> Houzz was cited in 31 of 40 simulated answers and a firm's town or service-area page in 37 of 40. Google AI Mode built every answer from Google Business Profile cards with star ratings and review counts.</p></div>
      <div class="finding"><div class="n">2</div><p><b>Out of the Woods is missing from all three sources.</b> The Houzz profile is filed under Acton with 3 reviews, the newest from 2017, so it never appears in the Houzz Waltham list. Google shows 2 reviews. The website has no town pages and names only Waltham, Boston, and Arlington.</p></div>
      <div class="finding"><div class="n">3</div><p><b>The crawl is fine.</b> robots.txt allows GPTBot, ClaudeBot, PerplexityBot, and Google-Extended; the sitemap works; all 17 pages fetched cleanly. This is a content, reviews, and consistency problem, which means it is fixable in weeks.</p></div>
    </div>
  </div>
  <footer><span>Out of the Woods Construction &amp; Cabinetry · AI-search visibility audit</span><span>1 / 4</span></footer>
</section>"""

    town_cells = "".join(
        f'<div><span>{t}</span><span class="{"yes" if t in towns_on_site else "no"}">{"named" if t in towns_on_site else "not named"}</span></div>'
        for t in TOWNS)

    page2 = f"""
<section class="page">
  <h2>What the winning firms have that Out of the Woods doesn't</h2>
  <p class="muted" style="max-width:76ch">The eight firms named most often share two traits: a network of town-specific pages on their own site, and a large, current review base on Houzz and Google. Either one gets a firm onto the lists AI engines read. Out of the Woods has neither yet.</p>
  <table style="margin-top:4pt;font-size:9pt">
    <tr><th>Firm</th><th>Based in</th><th class="num">Named in answers</th><th class="num">Town pages</th><th>Review base</th></tr>
    <tr><td>New England Design &amp; Construction</td><td>Lexington</td><td class="num">30</td><td class="num">16</td><td>47 Houzz reviews, 5.0, 19× Best of Houzz</td></tr>
    <tr><td>Feinmann, Inc.</td><td>Lexington</td><td class="num">16</td><td class="num">~23</td><td>81 Houzz reviews, 4.9, awards and press page</td></tr>
    <tr><td>Morse Constructions</td><td>Woburn</td><td class="num">12</td><td class="num">10+</td><td>53 Houzz reviews, 4.8</td></tr>
    <tr><td>Refined Renovations</td><td>Wilmington / Wellesley</td><td class="num">12</td><td class="num">35+</td><td>53 Houzz reviews, 5.0</td></tr>
    <tr><td>Steveworks LLC</td><td>Newton</td><td class="num">11</td><td class="num">0</td><td>69 Houzz reviews, 5.0, GuildQuality surveys</td></tr>
    <tr><td>JM Construction</td><td>Framingham</td><td class="num">11</td><td class="num">yes</td><td>42 GuildQuality surveys, 4.9</td></tr>
    <tr><td>Molla Builders LLC</td><td>North Reading</td><td class="num">10</td><td class="num">0</td><td>60 Houzz reviews, 5.0, with a four-page website</td></tr>
    <tr class="me"><td>Out of the Woods</td><td>Waltham</td><td class="num">0</td><td class="num">0</td><td>3 Houzz (2017, filed under Acton) · 2 Google · Yelp 3.0 from 2 reviews</td></tr>
  </table>
  <div class="cols" style="margin-top:12pt">
    <div>
      <h3>Towns tested, and whether your site names them</h3>
      <p class="small">Engines match "kitchen remodel in Newton" to pages that say Newton. Three of twelve scope towns appear anywhere on the site; none has its own page.</p>
      <div class="towns">{town_cells}</div>
    </div>
    <div>
      <h3>Where your listings disagree with each other</h3>
      <p class="small">Four addresses are live online. Engines read inconsistent name, address, and phone as different businesses.</p>
      <table style="font-size:8.6pt">
        <tr><th>Source</th><th>Address shown</th></tr>
        <tr><td>Website, Yelp, Nextdoor (Waltham page)</td><td>260 Bear Hill Rd, Suite 201, Waltham</td></tr>
        <tr><td>BBB, Birdeye (Google-synced)</td><td>1347 Main St, Waltham</td></tr>
        <tr><td>Houzz</td><td>260 Bear Hill Rd, "Acton, MA 01720"</td></tr>
        <tr><td>BuildZoom, MasterBrand, Alignable</td><td>312 Nagog Hill Rd, Acton (BuildZoom also lists a different phone)</td></tr>
        <tr><td>Nextdoor duplicate, MapQuest, Cylex</td><td>15 or 33 Ryder St, Arlington</td></tr>
      </table>
      <p class="small" style="margin-top:6pt">Already right: crawlers allowed, sitemap present, phone consistent everywhere but BuildZoom, and brand-name searches describe the company accurately.</p>
    </div>
  </div>
  <footer><span>Sources: 40 simulated answers, 8 Google AI Mode answers, 3 Perplexity answers, site crawl, and directory pages, captured {date}.</span><span>2 / 4</span></footer>
</section>"""

    page3 = f"""
<section class="page">
  <h2>What to change</h2>
  <p class="muted" style="max-width:76ch">Six changes, in priority order. The first two take hours and move the Google and Houzz lists that engines read directly. The rest build the pages engines cite.</p>
  <div class="cols" style="margin-top:8pt">
    <div>
      <div class="rec"><h3><span class="k">1 · HOUZZ AND GOOGLE</span>Fix the two profiles engines read first</h3>
        <p>Change the Houzz location from Acton to Waltham and refresh its services and photos. Verify the Google Business Profile address, categories, and hours, and add the service list and the twelve towns to its description. Molla Builders ranks across the region on Houzz reviews alone.</p></div>
      <div class="rec"><h3><span class="k">2 · REVIEWS</span>Get to 25 Google and 25 Houzz reviews in 90 days</h3>
        <p>The nine clients on the testimonials page already said yes once. Ask them, plus every client from the last three years, for a Google and a Houzz review that names the town and the project ("our Newton kitchen"). Post an owner reply to the 2014 Yelp review so the 3.0 stops being the headline.</p></div>
      <div class="rec"><h3><span class="k">3 · TOWN PAGES</span>Publish one page per town, five first</h3>
        <p>Newton, Wellesley, Needham, Lexington, Waltham, then the rest. Each needs 400 to 600 words, two or three real projects from that town with photos, the local housing stock (Newton Victorians, Needham capes), and links to each service page. Fifty words with the town name swapped will not be cited.</p></div>
      <div class="rec"><h3><span class="k">6 · STRUCTURED DATA</span>Tell engines what and where you are</h3>
        <p>Add one HomeAndConstructionBusiness block site-wide with the Waltham address, phone, founding date, links to the Houzz, Google, Facebook, and Nextdoor profiles, and the twelve towns as the service area. Add a Service entity per service page and FAQ markup once the cost and timeline questions are answered on the site. Squarespace code injection handles all of it.</p></div>
    </div>
    <div>
      <div class="rec"><h3><span class="k">4 · SERVICE PAGES</span>Say the service and the towns in the title</h3>
        <p>Today: "Kitchen Remodeling Portfolio | Massachusetts". Engines matched competitor pages that say "design-build kitchen remodeling in Newton, Wellesley and Needham". Retitle the kitchen, bath, additions, and cabinetry pages, rewrite the first paragraph, and move the portfolio below it.</p></div>
      <div class="rec"><h3><span class="k">5 · ABOUT COPY</span>Give engines one paragraph they can quote</h3>
        <blockquote><span class="t">Draft for the homepage and team page</span>Out of the Woods Construction &amp; Cabinetry is a design-build residential remodeling firm in Waltham, Massachusetts, founded in 1992. We remodel kitchens and bathrooms, build additions, and renovate whole houses for homeowners along Route 128 and in MetroWest, from Reading to Needham, Wellesley, and Newton. Our in-house woodworking shop builds custom cabinetry and reproduces period millwork for older homes. Over 90% of our work comes from repeat clients and referrals.</blockquote></div>
      
    </div>
  </div>
  <footer><span>Full detail, draft titles, and page-by-page audit: report-full.pdf</span><span>3 / 4</span></footer>
</section>"""

    page4 = f"""
<section class="page">
  <h2>The next 90 days</h2>
  <div class="cols-3 plan" style="margin-top:6pt">
    <div><h3>First 30 days<small>hours of work</small></h3><ul>
      <li>Houzz location to Waltham; services and photos refreshed.</li>
      <li>Google Business Profile verified: address, phone, categories, hours, description with towns.</li>
      <li>Claim the Arlington Nextdoor page and merge it; correct BuildZoom, BBB, MasterBrand, Alignable, MapQuest.</li>
      <li>Reply to the 2014 Yelp review; three fresh Yelp and Google reviews.</li>
      <li>"About" paragraph live on homepage and team page; structured data block injected site-wide.</li>
      <li>Four service pages retitled.</li></ul></div>
    <div><h3>Days 31 to 60<small>content</small></h3><ul>
      <li>Service-area hub plus town pages for Newton, Wellesley, Needham, Lexington, Waltham.</li>
      <li>FAQ page answering cost ranges, timelines, and "what is design-build", with FAQ markup.</li>
      <li>Cabinetry page rewritten around the in-house shop and period millwork.</li>
      <li>Review campaign to all clients from the last three years.</li></ul></div>
    <div><h3>Days 61 to 90<small>depth and measurement</small></h3><ul>
      <li>Town pages for Belmont, Arlington, Weston, Concord, Reading, plus MetroWest.</li>
      <li>Awards and press page; one-sentence workmanship warranty on the process page.</li>
      <li>Angi profile created; PRO New England and NARI member profiles completed.</li>
      <li>Re-run the same 40 queries and compare to this baseline of 0 of 48.</li></ul></div>
  </div>
  <hr class="rule" style="margin-top:18pt">
  <div class="cols">
    <div>
      <h3>How this was measured</h3>
      <p class="small">Forty queries were built from a grid of five services, twelve towns, and four intents ("best", "who should I hire", cost, and brand name). Each was answered by a simulated engine: an AI agent that searches the live web and composes an answer the way Perplexity or ChatGPT search does. Eight core queries were then run in a real browser on Google AI Mode (all eight answered) and Perplexity (three answered before it required sign-in). Every answer was read and recorded: firms named in order, whether Out of the Woods appeared, how it was described, and which pages were cited. The website was crawled from its sitemap, and review and directory profiles were checked by hand.</p>
    </div>
    <div>
      <h3>What was not tested</h3>
      <p class="small">ChatGPT requires a signed-in session and was not run; it should be spot-checked from a logged-in account. Five Perplexity queries hit a sign-up wall on two attempts. Dave's own audit and missing-items list had not been received by the report date; when it arrives, each item can be mapped onto the six changes on page 3. The simulated results show how often the open web gives an AI a reason to name the firm, which is exactly what the changes here are designed to move.</p>
      <p class="small" style="margin-top:8pt">All queries, answers, sources, and the page-by-page site audit are in <b>report-full.pdf</b>. Code and data: {repo}.</p>
    </div>
  </div>
  <footer><span>Prepared {date}. Re-run the same 40 queries after the 90-day plan to measure change.</span><span>4 / 4</span></footer>
</section>"""

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>AI-Search Visibility Audit: Out of the Woods Construction</title><style>{CSS}</style></head><body>{page1}{page2}{page3}{page4}</body></html>"""

def main(out_html="report/brief-4page.html", out_pdf="report/brief-4page.pdf"):
    out_html = os.path.join(ROOT, out_html); out_pdf = os.path.join(ROOT, out_pdf)
    with open(out_html, "w") as f:
        f.write(build())
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
           f"--print-to-pdf={out_pdf}", "file://" + out_html]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    print(f"wrote {out_html} and {out_pdf} ({os.path.getsize(out_pdf)} bytes)")

if __name__ == "__main__":
    main(*sys.argv[1:])
