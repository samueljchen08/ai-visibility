"""Project Out of the Woods' AI-search visibility after the recommended changes.

The model is deliberately simple and fully traceable to the audit data:

1. Every non-brand answer is classified by what the engine built it from:
   a Houzz town list, a firm's own site (town or service page), or Google
   Business Profile cards (Google AI Mode builds every answer from those).
2. Each answer is tagged with the earliest scenario in which Out of the Woods
   would have the asset the engine used ("reachable"):
     s1  profiles fixed (Houzz filed under Waltham, Google Business Profile
         verified) and the first reviews in; reaches Houzz- and Google-built
         answers for Waltham and the towns that border it.
     s2  plus town pages for Newton, Wellesley, Needham, Lexington, Waltham,
         retitled service pages, the quotable about paragraph, structured data;
         reaches answers built from firms' own pages in those five towns.
     s3  plus the remaining town pages, the MetroWest page, the FAQ with cost
         ranges, the awards page, Angi, and 25 Google plus 25 Houzz reviews;
         reaches firm-page and Houzz-built answers in all twelve towns.
   Answers built only from curated listicles (bostonarchitects.org and the like)
   are never counted as reachable, because nothing in the plan controls them.
3. Being reachable is not being named. The share of reachable answers in which
   a firm that has the asset actually gets named is taken from the competitors
   in this audit: firms with a large review base and no town pages (Molla,
   Steveworks) were named in 21 to 23% of all 48 answers; firms with town pages
   and reviews (NEDC, Feinmann, Morse, Refined Renovations, JM Construction,
   RemodelWerks) in 19 to 62%, median 24%. The projection applies half of the
   benchmark as the low end (new pages, fewer reviews, no history) and the
   benchmark as the high end, with a higher band for the home town, where
   Google AI Mode listed firms with as few as 12 reviews.

Writes report/projection.json. Usage: python scripts/project.py
"""
import json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aggregate import load_records  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

NEAR_WALTHAM = {"Waltham", "Newton", "Lexington", "Belmont", "Arlington", "Weston", "Watertown"}
FIRST_TOWN_PAGES = {"Waltham", "Newton", "Wellesley", "Needham", "Lexington"}
ALL_TOWNS = FIRST_TOWN_PAGES | {"Reading", "Arlington", "Belmont", "Weston", "Concord", "MetroWest"}

# Directories, listicles, aggregators, and cost guides: not a firm's own site.
NOT_FIRM = ("houzz.com", "yelp.com", "angi.com", "bbb.org", "thumbtack.com", "homeadvisor.com",
            "buildzoom.com", "guildquality.com", "generalcontractors.org", "bostonarchitects.org",
            "homebuilderdigest.com", "chrysalisawards.com", "bostonmagazine.com", "pro-ne.org",
            "coohom.com", "blockrenovation.com", "homeyou.com", "homeblue.com", "nextdoor.com",
            "birdeye.com", "outofthewoodsconstruction.com", "google.com", "facebook.com",
            "instagram.com", "porch.com", "nari.org", "maldenbathrooms.com")

AREAS = [
    ("waltham", "Waltham (home town)", {"Waltham"}),
    ("core4", "Newton, Wellesley, Needham, Lexington", {"Newton", "Wellesley", "Needham", "Lexington"}),
    ("ring", "Reading, Arlington, Belmont, Concord, Weston", {"Reading", "Arlington", "Belmont", "Concord", "Weston"}),
    ("metro", "Boston and MetroWest", {"Boston", "MetroWest"}),
]

# (low, high) share of reachable answers in which the firm is actually named.
CONVERSION = {
    "s1": {"home": (0.40, 0.70), "other": (0.10, 0.22)},
    "s2": {"home": (0.50, 0.80), "other": (0.12, 0.25)},
    "s3": {"home": (0.60, 0.90), "other": (0.15, 0.30)},
}
SCENARIOS = [
    ("now", "Today (baseline, 2026-10-28)"),
    ("s1", "After profiles and first reviews (work: days 1 to 30)"),
    ("s2", "After five town pages, retitled service pages, structured data (days 31 to 60)"),
    ("s3", "After all town pages, FAQ, awards page, 25+25 reviews (days 61 to 90)"),
]

def area_of(geo):
    for key, _, towns in AREAS:
        if geo in towns:
            return key
    return "brand"

def _domain(url):
    return url.split("//")[-1].split("/")[0].replace("www.", "").lower()

def classify(record, query):
    sources = record.get("sources_cited", []) or []
    doms = [_domain(u) for u in sources]
    return {
        "houzz": any(d.endswith("houzz.com") for d in doms),
        "firm_page": any(not d.endswith(NOT_FIRM) for d in doms),
        "gbp": record.get("engine") == "google-ai-mode",
        "geo": query.get("geo"), "intent": query.get("intent"),
    }

def reachable(c, query):
    """Earliest scenario (1, 2, 3) in which OOTW has the asset this answer was built from, else None."""
    geo = query.get("geo")
    list_built = c["houzz"] or c["gbp"]
    if list_built and geo in NEAR_WALTHAM:
        return 1
    if geo in FIRST_TOWN_PAGES and (c["firm_page"] or list_built):
        return 2
    if geo in ALL_TOWNS and (c["firm_page"] or list_built):
        return 3
    if geo == "Boston" and c["houzz"]:
        return 3
    return None

def _expected(answers, scenario):
    """answers: list of (area_key, reach_level). Returns reachable, low, high for a scenario."""
    level = {"now": 0, "s1": 1, "s2": 2, "s3": 3}[scenario]
    n_reach, low, high = 0, 0.0, 0.0
    for area, r in answers:
        if r is None or r > level:
            continue
        n_reach += 1
        lo, hi = CONVERSION[scenario]["home" if area == "waltham" else "other"]
        low += lo; high += hi
    return n_reach, low, high

def project(records, queries):
    qmap = {q["id"]: q for q in queries}
    tagged = []
    for r in records:
        q = qmap.get(r["query_id"])
        if not q or r.get("status", "ok") != "ok" or q.get("intent") == "brand":
            continue
        c = classify(r, q)
        tagged.append({"query_id": r["query_id"], "engine": r["engine"], "area": area_of(q["geo"]),
                       "geo": q["geo"], "service": q["service"], "intent": q["intent"],
                       "built_from": [k for k in ("houzz", "firm_page", "gbp") if c[k]],
                       "reach": reachable(c, q), "mentioned": bool(r.get("ootw_mentioned"))})
    answers = [(t["area"], t["reach"]) for t in tagged]
    n = len(tagged)
    scenarios = []
    for key, label in SCENARIOS:
        if key == "now":
            m = sum(1 for t in tagged if t["mentioned"])
            scenarios.append({"key": key, "label": label, "reachable": 0, "low": m, "high": m,
                              "low_rate": m / n if n else 0, "high_rate": m / n if n else 0})
            continue
        nr, lo, hi = _expected(answers, key)
        scenarios.append({"key": key, "label": label, "reachable": nr, "low": round(lo), "high": round(hi),
                          "low_rate": lo / n if n else 0, "high_rate": hi / n if n else 0})
    areas = []
    for key, label, _ in AREAS:
        sub = [(a, r) for a, r in answers if a == key]
        row = {"key": key, "label": label, "n": len(sub),
               "now": sum(1 for t in tagged if t["area"] == key and t["mentioned"])}
        for s in ("s1", "s2", "s3"):
            nr, lo, hi = _expected(sub, s)
            row[s] = {"reachable": nr, "low": round(lo), "high": round(hi)}
        areas.append(row)
    built = defaultdict(int)
    for t in tagged:
        for b in t["built_from"]:
            built[b] += 1
    return {"overall": {"n": n, "mentioned": sum(1 for t in tagged if t["mentioned"])},
            "built_from": dict(built), "scenarios": scenarios, "areas": areas,
            "conversion": CONVERSION, "answers": tagged}

def main(out="report/projection.json"):
    with open(os.path.join(ROOT, "queries.json")) as f:
        queries = json.load(f)["queries"]
    records = load_records(os.path.join(ROOT, "results"))
    out_path = os.path.join(ROOT, out)
    result = project(records, queries)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"wrote {out_path}")
    for s in result["scenarios"]:
        print(f"  {s['key']:4s} reachable={s['reachable']:2d}  expected {s['low']}-{s['high']} of {result['overall']['n']}  ({100*s['low_rate']:.0f}-{100*s['high_rate']:.0f}%)  {s['label']}")
    for a in result["areas"]:
        print(f"  {a['label']:45s} n={a['n']:2d} now={a['now']} " + "  ".join(f"{s}:{a[s]['low']}-{a[s]['high']}/{a[s]['reachable']}" for s in ("s1", "s2", "s3")))

if __name__ == "__main__":
    main(*sys.argv[1:])
