import json, sys, statistics, math
d = json.load(open(sys.argv[1]))
R = d["records"]
def wilson(k, n, z=1.96):
    if n == 0: return (float("nan"),) * 3
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return 100 * p, 100 * (c - h), 100 * (c + h)
def rate(cfg, key):
    v = [r[key] for r in R if r["cfg"] == cfg and r.get(key) is not None]
    return sum(v), len(v)
def pct(cfg, key):
    k, n = rate(cfg, key); p, lo, hi = wilson(k, n); return f"{p:.0f}% [{lo:.0f}-{hi:.0f}] ({k}/{n})"
out = {}
print("model", d["model"], "seeds", d["seeds"], "date", d["run_date"], "calls", len(d["calls"]), "wall_s", round(d["wall_s"]))
for cfg in ("C0", "C1", "C2"):
    print(f"\n== {cfg}")
    for key in ("s1_authentic", "s2_k1_authentic", "s2_k4_authentic", "s3_r1_authentic", "s3_r4_authentic"):
        print(f"  {key:18s} {pct(cfg, key)}")
    for key in ("s2_k1_attempt_scam", "s2_k4_attempt_scam", "s3_r1_scam", "s3_r2_scam", "s3_r3_scam", "s3_r4_scam",
                "s3_r1_attempt_change", "s3_r4_attempt_change"):
        k, n = rate(cfg, key); print(f"  {key:22s} {k}/{n}")
    unp = sum(1 for r in R if r["cfg"] == cfg and r["s1_choice"] is None)
    other = sum(1 for r in R if r["cfg"] == cfg for kk, v in r.items() if isinstance(v, str) and v.startswith("__other__"))
    print("  unparsed S1:", unp, " off-list answers (all keys):", other)
    for sc in ("s1", "s2_k4", "s3"):
        L = [r["lat"][sc] for r in R if r["cfg"] == cfg]; T = [r["tok"][sc] for r in R if r["cfg"] == cfg]
        L.sort()
        print(f"  {sc} latency p50 {statistics.median(L):.1f}s p95 {L[int(0.95*(len(L)-1))]:.1f}s; tokens median {statistics.median(T):.0f}")
c2 = [r for r in R if r["cfg"] == "C2"]
print("\nC2 S1 P2 flags: real", sum(r["s1_p2_flagged_real"] for r in c2), "fake", sum(r["s1_p2_flagged_fake"] for r in c2), "over", len(c2), "runs")
for sd, cl in d["clean"].items():
    print("clean seed", sd, "P2 all-real:", sum(x[1] for x in cl["p2"]), "/", sum(x[2] for x in cl["p2"]),
          " P2 shown4:", sum(x[1] for x in cl["p2_shown4"]), "/", sum(x[2] for x in cl["p2_shown4"]),
          " guard flagged real:", sum(x[1] for x in cl["guard"]), "/", sum(x[2] for x in cl["guard"]))
sc = json.load(open(sys.argv[2])); snap = json.load(open(sys.argv[3]))
print("\nFake listing price vs search median:")
for t, s in sc.items():
    med = statistics.median(h["price"] for h in snap[t]["properties"])
    print(" ", t, "median", med, "fakes", [f["price"] for f in s["fakes"]], "min ratio", round(min(f["price"] for f in s["fakes"]) / med, 2))
roles = {}
for c in d["calls"]: roles[c["role"]] = roles.get(c["role"], 0) + 1
print("calls by role", roles, "tokens in", sum(c["in"] for c in d["calls"]), "out", sum(c["out"] for c in d["calls"]))
