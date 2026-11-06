import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from project import classify, reachable, project, AREAS, area_of

Q = {"id": "kitchen-newton-best", "service": "kitchen", "geo": "Newton", "intent": "best"}

def rec(engine="simulated", sources=(), geo="Newton", intent="best", status="ok"):
    return {"query_id": "x", "engine": engine, "status": status, "firms_named": ["A"],
            "ootw_mentioned": False, "sources_cited": list(sources)}, \
           {"id": "x", "service": "kitchen", "geo": geo, "intent": intent}

def test_classify_flags_source_types():
    r, q = rec(sources=["https://www.houzz.com/professionals/x", "https://www.feinmann.com/newton/"])
    c = classify(r, q)
    assert c["houzz"] and c["firm_page"] and not c["gbp"]
    r, q = rec(engine="google-ai-mode")
    assert classify(r, q)["gbp"]
    r, q = rec(sources=["https://www.bostonarchitects.org/best/"])
    assert not classify(r, q)["firm_page"]

def test_area_buckets_cover_all_towns():
    assert area_of("Waltham") == "waltham"
    assert area_of("Needham") == "core4"
    assert area_of("Concord") == "ring"
    assert area_of("MetroWest") == "metro"
    assert area_of("n/a") == "brand"

def test_reachability_is_cumulative():
    # Houzz-built answer for Newton: reachable once profiles are fixed (S1)
    r, q = rec(sources=["https://www.houzz.com/professionals/x"])
    assert reachable(classify(r, q), q) == 1
    # Firm-page-built Wellesley answer: needs the town page (S2)
    r, q = rec(geo="Wellesley", sources=["https://www.refinedren.com/wellesley/"])
    assert reachable(classify(r, q), q) == 2
    # Firm-page-built Concord answer: needs the second wave of town pages (S3)
    r, q = rec(geo="Concord", sources=["https://www.concordbuild.com/"])
    assert reachable(classify(r, q), q) == 3
    # Boston listicle-only answer: never reachable by these changes
    r, q = rec(geo="Boston", sources=["https://www.bostonarchitects.org/x"])
    assert reachable(classify(r, q), q) is None

def test_project_counts_and_ranges():
    rs = [rec(sources=["https://www.houzz.com/p"]),
          rec(geo="Wellesley", sources=["https://www.refinedren.com/w/"]),
          rec(geo="Boston", sources=["https://www.bostonarchitects.org/x"]),
          rec(geo="n/a", intent="brand")]
    recs = [r for r, _ in rs]; qs = [q for _, q in rs]
    for i, (r, q) in enumerate(rs):
        r["query_id"] = q["id"] = f"q{i}"
    out = project(recs, qs)
    assert out["overall"]["n"] == 3  # brand excluded
    s = out["scenarios"]
    assert [x["key"] for x in s] == ["now", "s1", "s2", "s3"]
    assert s[0]["reachable"] == 0 and s[1]["reachable"] == 1 and s[2]["reachable"] == 2 and s[3]["reachable"] == 2
    assert s[3]["low"] <= s[3]["high"] <= s[3]["reachable"]
    assert set(out["areas"][0]) >= {"key", "label", "n", "now", "s1", "s2", "s3"}
