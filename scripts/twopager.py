"""Build the two-page report (report/report.html + report/report.pdf).

Page 1: where Out of the Woods stands today, by key area, and why.
Page 2: the changes, the projected visibility after each wave, and the checklist.
Reads report/summary.json, report/projection.json, results/, queries.json.
"""
import json, os, subprocess, sys, datetime, html
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aggregate import load_records, is_ootw  # noqa: E402
from project import AREAS, area_of  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REPO = "github.com/samueljchen08/ai-visibility"

def load(path):
    with open(os.path.join(ROOT, path)) as f:
        return json.load(f)

def esc(s):
    return html.escape(str(s))

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
@page { size: Letter; margin: 0; }
:root { --paper:#faf8f3; --ink:#1b1a17; --ink-2:#4f4c45; --ink-3:#7d7970; --rule:#dedad1;
  --forest:#1f4a36; --forest-ink:#163726; --accent:#1f8f55; --accent-soft:#e4f1e9; --accent-mid:#9fd3b6; --bar-gray:#cfcbc1; --warn:#b4541a; }
* { box-sizing: border-box; }
html, body { margin:0; background:var(--paper); color:var(--ink); }
body { font: 8.8pt/1.36 "IBM Plex Sans","Helvetica Neue",Arial,sans-serif; font-feature-settings:"tnum" 1; }
.page { width:8.5in; height:11in; padding:0.42in 0.55in 0.38in; page-break-after:always; position:relative; overflow:hidden; display:flex; flex-direction:column; }
.page:last-child { page-break-after:auto; }
h1,h2,h3 { font-family:"Newsreader",Georgia,serif; font-weight:600; letter-spacing:-0.015em; margin:0; color:var(--forest-ink); }
h1 { font-size:22pt; line-height:1.06; }
h2 { font-size:15.5pt; line-height:1.15; }
h3 { font-size:11pt; line-height:1.2; margin:0 0 4pt; }
p { margin:0 0 5pt; }
.muted { color:var(--ink-2); }
.small { font-size:8.1pt; line-height:1.36; color:var(--ink-2); }
.mast { display:grid; grid-template-columns:1fr auto; align-items:end; gap:14pt; padding-bottom:8pt; border-bottom:2px solid var(--forest); margin-bottom:9pt; }
.mast .sub { font-size:9.6pt; color:var(--ink-2); margin-top:4pt; }
.mast .meta { text-align:right; font-size:8.3pt; line-height:1.45; color:var(--ink-2); }
.mast .meta strong { color:var(--ink); }
.lede { font-size:10pt; line-height:1.4; max-width:80ch; margin-bottom:7pt; }
.hero { display:grid; grid-template-columns:1fr 1fr 1fr; gap:0; margin:4pt 0 10pt; border-top:1px solid var(--rule); border-bottom:1px solid var(--rule); }
.hero > div { padding:6pt 12pt 6pt 0; margin-right:12pt; border-right:1px solid var(--rule); }
.hero > div:last-child { border:0; margin:0; }
.hero b { display:block; font-family:"Newsreader",Georgia,serif; font-weight:500; font-size:23pt; line-height:1; letter-spacing:-0.02em; color:var(--forest-ink); }
.hero b small { font-size:12pt; color:var(--ink-3); letter-spacing:0; }
.hero span { display:block; font-size:8.3pt; color:var(--ink-2); line-height:1.3; margin-top:3pt; }
.hero .proj b { color:var(--accent); }
.sec { margin-bottom:7pt; }
.sec h2 { padding-bottom:3pt; border-bottom:1px solid var(--forest); margin-bottom:6pt; }
.cols { display:grid; grid-template-columns:1fr 1fr; gap:16pt; }
.cols-3 { display:grid; grid-template-columns:1fr 1fr 1fr; gap:12pt; }
table { border-collapse:collapse; width:100%; font-size:8.5pt; }
th { text-align:left; font-weight:600; font-size:7.6pt; letter-spacing:0.03em; text-transform:uppercase; color:var(--ink-3); padding:0 6pt 3pt 0; border-bottom:1px solid var(--forest); }
td { padding:3pt 6pt 3pt 0; border-bottom:1px solid var(--rule); vertical-align:top; }
td.num, th.num { text-align:right; padding-right:8pt; white-space:nowrap; }
td.zero { color:var(--warn); font-weight:600; }
td.good { color:var(--accent); font-weight:600; }
tr.total td { font-weight:600; color:var(--forest-ink); background:var(--accent-soft); }
tr.total td:first-child { padding-left:4pt; }
.chart .cap { font-size:7.9pt; color:var(--ink-2); margin-bottom:5pt; }
.bars { display:grid; grid-template-columns:16em 1fr; row-gap:3pt; column-gap:6pt; align-items:center; font-size:8.3pt; }
.bars .lbl { text-align:right; color:var(--ink-2); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bars .bar { display:flex; align-items:center; gap:5pt; }
.bars .fill { height:9pt; background:var(--bar-gray); border-radius:0 3pt 3pt 0; }
.bars .val { color:var(--ink); font-weight:500; }
.bars .me .lbl, .bars .me .val { color:var(--forest-ink); font-weight:600; }
.bars .me .fill { background:var(--accent); min-width:2pt; }
.findings .f { display:grid; grid-template-columns:16pt 1fr; gap:5pt; margin-bottom:5pt; }
.findings .n { font-family:"Newsreader",Georgia,serif; font-size:13pt; font-weight:500; color:var(--accent); line-height:1.05; }
.findings p { margin:0; font-size:8.6pt; }
.findings b { color:var(--forest-ink); }
.rec { display:grid; grid-template-columns:15pt 1fr; gap:5pt; margin-bottom:4pt; }
.rec .n { font-family:"Newsreader",Georgia,serif; font-size:13pt; font-weight:500; color:var(--accent); line-height:1.05; }
.rec h3 { font-size:9.6pt; margin:0 0 1pt; }
.rec h3 small { font-family:"IBM Plex Sans",sans-serif; font-size:7.4pt; font-weight:600; color:var(--ink-3); text-transform:uppercase; letter-spacing:0.03em; margin-left:5pt; }
.rec p { margin:0; font-size:8.4pt; }
.range { display:flex; align-items:center; gap:5pt; }
.range .track { position:relative; flex:none; width:54pt; height:8pt; background:#ece9e1; border-radius:2pt; }
.range .band { position:absolute; top:0; height:100%; background:var(--accent-mid); border-radius:2pt; }
.range .lo { position:absolute; top:0; width:2pt; height:100%; background:var(--accent); }
.range .txt { white-space:nowrap; font-weight:500; }
.check ul { margin:0; padding:0; list-style:none; }
.check li { position:relative; padding-left:13pt; margin-bottom:2.5pt; font-size:8.3pt; line-height:1.32; }
.check li::before { content:""; position:absolute; left:0; top:2pt; width:7.5pt; height:7.5pt; border:1.2px solid var(--forest); border-radius:1.5pt; }
.check li b { color:var(--forest-ink); }
.check h3 { font-size:9.8pt; padding-bottom:3pt; border-bottom:1.5px solid var(--forest); margin-bottom:5pt; }
.check h3 small { font-family:"IBM Plex Sans",sans-serif; font-size:7.4pt; font-weight:500; color:var(--ink-3); margin-left:5pt; }
.note { font-size:7.9pt; color:var(--ink-2); line-height:1.35; margin-top:5pt; }
footer { margin-top:auto; padding-top:5pt; border-top:1px solid var(--rule); font-size:7.6pt; color:var(--ink-3); display:flex; justify-content:space-between; gap:12pt; }
footer span:last-child { white-space:nowrap; }
"""

def area_winners(records, queries, k=3):
    qmap = {q["id"]: q for q in queries}
    counts = defaultdict(lambda: defaultdict(int))
    for r in records:
        q = qmap.get(r["query_id"])
        if not q or r.get("status", "ok") != "ok" or q["intent"] == "brand":
            continue
        a = area_of(q["geo"])
        for f in r["firms_named"]:
            if not is_ootw(f):
                counts[a][f.strip().replace(", Inc.", "").replace(" LLC", "")] += 1
    out = {}
    for a, d in counts.items():
        top = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:k]
        out[a] = ", ".join(f"{n} ({c})" for n, c in top)
    return out

def service_stats(summary):
    order = ["kitchen", "bath", "addition", "design-build", "cabinetry"]
    names = {"kitchen": "Kitchens", "bath": "Baths", "addition": "Additions", "design-build": "Design-build", "cabinetry": "Cabinetry"}
    cells = []
    for s in order:
        v = summary["by_service"].get(s)
        if v:
            cells.append(f'<div><b>{v["mentioned"]} of {v["n"]}</b><span>{names[s]}</span></div>')
    return "".join(cells)

def bars_chart(leaderboard, n=7):
    rows = leaderboard[:n]
    mx = max(r["mentions"] for r in rows)
    out = ['<div class="chart"><h3>Firms the engines named most</h3>',
           '<div class="cap">Times named across the 48 service-and-town answers.</div><div class="bars">']
    for r in rows:
        out.append(f'<div class="lbl">{esc(r["firm"])}</div><div class="bar"><div class="fill" style="width:{100*r["mentions"]/mx:.1f}%"></div><span class="val">{r["mentions"]}</span></div>')
    out.append('<div class="lbl" style="color:var(--forest-ink);font-weight:600">Out of the Woods</div><div class="bar me"><div class="fill" style="width:0.5%"></div><span class="val">0</span></div>')
    out.append('</div></div>')
    return "\n".join(out)

def range_cell(lo, hi, n, max_n):
    if n == 0:
        return '<td class="num">-</td>'
    band_l = 100 * lo / n; band_w = 100 * (hi - lo) / n
    txt = f"{lo}&ndash;{hi} of {n}" if lo != hi else f"{lo} of {n}"
    return (f'<td><div class="range"><div class="track">'
            f'<div class="band" style="left:{band_l:.1f}%;width:{max(band_w,1):.1f}%"></div>'
            f'<div class="lo" style="left:{band_l:.1f}%"></div></div><span class="txt">{txt}</span></div></td>')

def build(report_date=None):
    s = load("report/summary.json"); pj = load("report/projection.json")
    queries = load("queries.json")["queries"]
    records = load_records(os.path.join(ROOT, "results"))
    winners = area_winners(records, queries)
    lb = [r for r in s["leaderboard"] if not is_ootw(r["firm"])]
    n_nb = pj["overall"]["n"]; brand_n = s["by_intent"]["brand"]["n"]
    sc = {x["key"]: x for x in pj["scenarios"]}
    bf = pj["built_from"]
    date = (report_date or datetime.date.today()).strftime("%B %-d, %Y")
    measured = "October 28, 2026"
    gam = s["by_engine"]["google-ai-mode"]; px = s["by_engine"]["perplexity"]; sim = s["by_engine"]["simulated"]

    area_rows = ""
    for a in pj["areas"]:
        area_rows += (f'<tr><td>{esc(a["label"])}</td><td class="num">{a["n"]}</td>'
                      f'<td class="num zero">{a["now"]}</td><td class="small">{esc(winners.get(a["key"], ""))}</td></tr>')
    area_rows += (f'<tr><td>Brand-name searches ("Out of the Woods Construction reviews")</td><td class="num">{brand_n}</td>'
                  f'<td class="num good">{brand_n}</td><td class="small">Named first every time, but engines call the review footprint "small and mixed" and surface the 2014 one-star Yelp review.</td></tr>')

    page1 = f"""
<section class="page">
  <div class="mast">
    <div><h1>AI-Search Visibility: Where You Stand, What to Change</h1>
      <div class="sub">Out of the Woods Construction &amp; Cabinetry, Waltham MA &middot; Two-page brief</div></div>
    <div class="meta"><strong>Prepared for Dave</strong><br>{date}<br>Baseline measured {measured}</div>
  </div>
  <p class="lede">When a homeowner asks ChatGPT, Perplexity, or Google AI Mode who should remodel their kitchen in Newton or build an addition in Needham, Out of the Woods is not in the answer. It appears only when someone already searches its name. Nothing technical is in the way: the firms that do get named have a current review base, a correct Houzz and Google listing, and a page for each town they serve. Page 2 lists the fixes and what they should do to these numbers.</p>
  <div class="hero">
    <div><b>0 <small>of {n_nb}</small></b><span>service-and-town answers that named Out of the Woods, across three AI engines and 12 towns</span></div>
    <div><b>{brand_n} <small>of {brand_n}</small></b><span>brand-name searches that found the firm and described it accurately</span></div>
    <div class="proj"><b>{sc['s3']['low']}&ndash;{sc['s3']['high']} <small>of {n_nb}</small></b><span>projected after the 90-day plan on page 2, which is where Morse Constructions and JM Construction sit today</span></div>
  </div>
  <div class="sec">
    <h2>Current visibility by key area</h2>
    <table>
      <tr><th>Area</th><th class="num">AI answers</th><th class="num">Named OOTW</th><th>Who the engines name instead (times named)</th></tr>
      {area_rows}
    </table>
    <p class="small" style="margin-top:6pt"><b>By service</b> (answers naming OOTW): kitchens {s['by_service']['kitchen']['mentioned']} of {s['by_service']['kitchen']['n']}, baths {s['by_service']['bath']['mentioned']} of {s['by_service']['bath']['n']}, additions {s['by_service']['addition']['mentioned']} of {s['by_service']['addition']['n']}, design-build {s['by_service']['design-build']['mentioned']} of {s['by_service']['design-build']['n']}, cabinetry {s['by_service']['cabinetry']['mentioned']} of {s['by_service']['cabinetry']['n']}, even though "Cabinetry" is in the company name. <b>By engine</b>: Google AI Mode {gam['mentioned']} of {gam['n']}, Perplexity {px['mentioned']} of {px['n']}, simulated engine {sim['mentioned']} of {sim['n']}; every hit was a brand query. ChatGPT needs a signed-in account and should be spot-checked.</p>
  </div>
  <div class="cols">
    {bars_chart(lb)}
    <div class="findings">
      <h3>Why the engines skip Out of the Woods</h3>
      <div class="f"><div class="n">1</div><p><b>Engines shortlist from three sources.</b> Of the {n_nb} answers, {bf['houzz']} drew on a Houzz town list, {bf['firm_page']} cited a firm's own town or service page, and all {bf['gbp']} Google AI Mode answers were built from Google Business Profile cards with star ratings and review counts.</p></div>
      <div class="f"><div class="n">2</div><p><b>Out of the Woods is absent from all three.</b> Its Houzz profile is filed under Acton with 3 reviews, the newest from 2017, so it is not on the Houzz Waltham list. Google shows 2 to 3 reviews. The website has no town pages and names only Waltham, Boston, and Arlington. Google AI Mode's Waltham answer listed six firms with 4 to 40 reviews; OOTW was not one.</p></div>
      <div class="f"><div class="n">3</div><p><b>Listings disagree with each other.</b> Four addresses are live: 260 Bear Hill Rd (website), 1347 Main St (BBB, Google-synced Birdeye), Nagog Hill Rd, Acton (BuildZoom, MasterBrand), and Ryder St, Arlington (unclaimed Nextdoor duplicate). Engines read that as different businesses. Crawling is fine: robots.txt allows every AI crawler and all 17 pages fetched cleanly.</p></div>
    </div>
  </div>
  <footer><span>Captured {measured}: 40 simulated, 8 Google AI Mode, and 3 Perplexity answers, plus site and directory pages. Detail: report-full.pdf.</span><span>1 / 2</span></footer>
</section>"""

    max_n = max(a["n"] for a in pj["areas"])
    proj_rows = ""
    for a in pj["areas"]:
        proj_rows += f'<tr><td>{esc(a["label"])}</td><td class="num zero">{a["now"]} of {a["n"]}</td>'
        for k in ("s1", "s2", "s3"):
            proj_rows += range_cell(a[k]["low"], a[k]["high"], a["n"], max_n)
        proj_rows += "</tr>"
    proj_rows += f'<tr class="total"><td>All service-and-town answers</td><td class="num">0 of {n_nb}</td>'
    for k in ("s1", "s2", "s3"):
        x = sc[k]
        proj_rows += f'<td class="num">{x["low"]}&ndash;{x["high"]} of {n_nb} <span class="muted" style="font-weight:400">({100*x["low_rate"]:.0f}&ndash;{100*x["high_rate"]:.0f}%)</span></td>'
    proj_rows += "</tr>"

    page2 = f"""
<section class="page">
  <div class="sec">
    <h2>What to change, in priority order</h2>
    <div class="cols" style="margin-top:2pt">
      <div>
        <div class="rec"><div class="n">1</div><div><h3>Fix Houzz and Google Business Profile<small>Hours &middot; Office</small></h3><p>Houzz: location from Acton to Waltham, service area set to all twelve towns, services and photos refreshed. Google: address, phone, categories, and hours verified; services and towns in the description. These two listings feed every Google AI Mode answer and {bf['houzz']} of {n_nb} answers here.</p></div></div>
        <div class="rec"><div class="n">2</div><div><h3>Reach 25 Google and 25 Houzz reviews in 90 days<small>Ongoing &middot; Dave</small></h3><p>Start with the nine clients on the testimonials page, then every client from the last three years. Ask for the town and project in the review ("our Newton kitchen"). Reply to the 2014 Yelp review so a 3.0 from two reviews stops being the headline. Molla Builders ranks region-wide on 60 Houzz reviews and a four-page website.</p></div></div>
        <div class="rec"><div class="n">3</div><div><h3>Make every listing say the same address<small>Hours &middot; Office</small></h3><p>260 Bear Hill Rd, Suite 201, Waltham on BBB, BuildZoom (fix the phone too), MasterBrand, Alignable, MapQuest, Cylex. Claim and merge the Arlington Nextdoor page. Create the missing Angi profile; complete the PRO New England and NARI member pages, which engines cited for competitors.</p></div></div>
      </div>
      <div>
        <div class="rec"><div class="n">4</div><div><h3>Publish one page per town, five first<small>Weeks &middot; Web</small></h3><p>Newton, Wellesley, Needham, Lexington, Waltham; then Reading, Arlington, Belmont, Weston, Concord, and MetroWest. Each: 400 to 600 words, two or three real projects from that town with photos, the local housing stock, links to each service page. The top eight competitors average more than fifteen town pages. Fifty words with the town name swapped will not be cited.</p></div></div>
        <div class="rec"><div class="n">5</div><div><h3>Retitle service pages; add a quotable "about" paragraph and an FAQ<small>Days &middot; Web</small></h3><p>Today: "Kitchen Remodeling Portfolio | Massachusetts". Retitle kitchens, baths, additions, and cabinetry as "Design-Build Kitchen Remodeling in Waltham, Newton, Wellesley &amp; Needham MA" and lead with the service and towns. Add one plain homepage paragraph: what the firm is, where it is, which towns it serves, that it has its own cabinet shop. Add an FAQ with real cost ranges and timelines; cost guides answered 6 of the 8 cost and "who should I hire" queries.</p></div></div>
        <div class="rec"><div class="n">6</div><div><h3>Add structured data<small>Hours &middot; Web</small></h3><p>One HomeAndConstructionBusiness block site-wide via Squarespace code injection: Waltham address, phone, founded 1992, links to the Houzz, Google, Facebook, and Nextdoor profiles, the twelve towns as areaServed. A Service entity per service page; FAQPage markup once the FAQ exists.</p></div></div>
      </div>
    </div>
  </div>
  <div class="sec">
    <h2>Projected visibility after each wave of changes</h2>
    <table style="margin-top:2pt">
      <tr><th>Area</th><th class="num">Today</th><th>After wave 1: profiles and first reviews</th><th>After wave 2: five town pages, retitles, schema</th><th>After wave 3: all pages, FAQ, 25+25 reviews</th></tr>
      {proj_rows}
    </table>
    <p class="note">How the projection is built. Each of the {n_nb} answers was tagged with the source the engine used (Houzz list, firm's own town page, Google Business Profile card) and the wave in which Out of the Woods gains that asset: wave 1 reaches {sc['s1']['reachable']} answers, wave 2 {sc['s2']['reachable']}, wave 3 {sc['s3']['reachable']}. Having the asset is not being named, so the conversion rate comes from competitors in this audit: firms with reviews but no town pages were named in 21 to 23% of answers, firms with both in 19 to 62% (median 24%). The low end applies half of that, the high end all of it, with a higher band for the home town. Two Boston answers built only from curated lists are treated as unreachable. A day-90 re-run of the 40 queries replaces this projection with a measurement.</p>
  </div>
  <div class="sec check">
    <h2>Checklist</h2>
    <div class="cols-3" style="margin-top:2pt">
      <div><h3>This week<small>owner: office</small></h3><ul>
        <li><b>Houzz:</b> location to Waltham, service area set to twelve towns, photos refreshed.</li>
        <li><b>Google Business Profile:</b> address, phone, categories, hours verified; description names services and towns.</li>
        <li><b>Yelp</b> owner reply posted; <b>review asks</b> sent to the nine testimonial clients with Google and Houzz links. Dave's missing-items list shared.</li></ul></div>
      <div><h3>This month<small>owner: web + office</small></h3><ul>
        <li><b>Directories corrected:</b> BBB, BuildZoom, MasterBrand, Alignable, MapQuest, Cylex; Arlington Nextdoor claimed and merged.</li>
        <li><b>Four service pages retitled;</b> "about" paragraph live; structured data injected and validated.</li>
        <li><b>Review asks</b> to every client from the last three years; 10 Google and 10 Houzz by day 30.</li></ul></div>
      <div><h3>This quarter<small>owner: web + Dave</small></h3><ul>
        <li><b>Town pages live:</b> Newton, Wellesley, Needham, Lexington, Waltham by day 60; the other five plus MetroWest by day 90.</li>
        <li><b>FAQ page</b> with cost ranges; cabinetry page rewritten around the shop; awards page; Angi, PRO New England, and NARI profiles completed.</li>
        <li><b>Day-90 re-run</b> of the same 40 queries; compare to 0 of {n_nb}.</li></ul></div>
    </div>
  </div>
  <footer><span>40 queries answered by a web-searching AI agent; 8 also run on Google AI Mode and Perplexity. Code: {REPO}</span><span>2 / 2</span></footer>
</section>"""

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>AI-Search Visibility Brief: Out of the Woods Construction</title><style>{CSS}</style></head><body>{page1}{page2}</body></html>"""

def main(out_html="report/report.html", out_pdf="report/report.pdf"):
    out_html = os.path.join(ROOT, out_html); out_pdf = os.path.join(ROOT, out_pdf)
    with open(out_html, "w") as f:
        f.write(build())
    cmd = [CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
           f"--print-to-pdf={out_pdf}", "file://" + out_html]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    print(f"wrote {out_html} and {out_pdf} ({os.path.getsize(out_pdf)} bytes)")

if __name__ == "__main__":
    main(*sys.argv[1:])
