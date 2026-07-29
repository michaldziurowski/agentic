#!/usr/bin/env python3
"""Cross-model comparison of the dz-commit eval sweep."""
import json
import os
import sys
from collections import defaultdict

WS = os.path.dirname(os.path.abspath(__file__))


def discover():
    """Every directory under here that holds a benchmark.json, deepest label wins."""
    found = []
    for root, dirs, files in os.walk(WS):
        dirs[:] = [d for d in dirs if d not in {".git", "fixtures", "__pycache__"}]
        if "benchmark.json" in files and root != WS:
            found.append(os.path.relpath(root, WS))
    return sorted(found)


# Each argument is a directory holding one model's sweep (containing a
# benchmark.json). With no arguments, every such directory is compared.
MODELS = [(d, d) for d in (sys.argv[1:] or discover())]
if not MODELS:
    sys.exit(f"no directories with a benchmark.json found under {WS}")

EVAL_NAMES = {e["id"]: e["name"][:18]
              for e in json.load(open(os.path.join(WS, "evals.json")))["evals"]}


def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


rows, fails = [], defaultdict(list)
for label, d in MODELS:
    path = os.path.join(WS, d, "benchmark.json")
    if not os.path.exists(path):
        continue
    bench = json.load(open(path))
    by = defaultdict(lambda: defaultdict(list))
    tok = defaultdict(list)
    sec = defaultdict(list)
    for r in bench["runs"]:
        eid, cfg = r.get("eval_id"), r["configuration"]
        by[eid][cfg].append(r["result"]["pass_rate"])
        for e in r.get("expectations", []):
            if not e["passed"]:
                fails[(label, cfg)].append(f"[{EVAL_NAMES.get(eid, eid)}] {e['text']}")

    # the aggregator drops tokens, so read timing.json directly. Only count dirs
    # that hold an actual run (a repo/), which skips the mirrored run-1/ copies.
    for root, dirs, files in os.walk(os.path.join(WS, d)):
        if "timing.json" not in files or "repo" not in dirs:
            continue
        cfg = "with_skill" if "with_skill" in root else \
              "without_skill" if "without_skill" in root else None
        if cfg:
            t = json.load(open(os.path.join(root, "timing.json")))
            tok[cfg].append(t.get("total_tokens", 0))
            sec[cfg].append(t.get("total_duration_seconds", 0))
    rows.append((label, by, tok, sec, bench))

print("=" * 96)
print("PASS RATE BY MODEL AND EVAL   (with_skill / without_skill)")
print("=" * 96)
hdr = f"{'model':<22}" + "".join(f"{EVAL_NAMES[e]:>24}" for e in sorted(EVAL_NAMES)) + f"{'OVERALL':>16}"
print(hdr)
for label, by, tok, sec, bench in rows:
    cells = ""
    allw, allo = [], []
    for e in sorted(EVAL_NAMES):
        w, o = mean(by[e]["with_skill"]), mean(by[e]["without_skill"])
        allw += by[e]["with_skill"]
        allo += by[e]["without_skill"]
        cells += f"{w*100:>10.0f}% /{o*100:>5.0f}%   "
    d = mean(allw) - mean(allo)
    print(f"{label:<22}{cells}{mean(allw)*100:>6.1f}% /{mean(allo)*100:>5.1f}%  ({d:+.2f})")

print()
print("=" * 96)
print("COST  (mean per run)")
print("=" * 96)

# Timing lives in the run directories, so archived results have none. Report
# that rather than printing rows of zeros, which read as "this was free".
timed = [r for r in rows if r[2]["with_skill"] or r[2]["without_skill"]]
for label, *_ in rows:
    if label not in [t[0] for t in timed]:
        print(f"{label:<22}  no timing data (run dirs not retained)")

print(f"{'model':<22}{'tokens w/':>12}{'tokens w/o':>12}{'sec w/':>10}{'sec w/o':>10}{'token overhead':>18}")
for label, by, tok, sec, bench in timed:
    tw, to = mean(tok["with_skill"]), mean(tok["without_skill"])
    ov = (tw / to - 1) * 100 if to else 0
    print(f"{label:<22}{tw:>12,.0f}{to:>12,.0f}{mean(sec['with_skill']):>10.1f}"
          f"{mean(sec['without_skill']):>10.1f}{ov:>17.0f}%")

print()
print("=" * 96)
print("FAILED ASSERTIONS")
print("=" * 96)
for label, _ in MODELS:
    for cfg in ("with_skill", "without_skill"):
        f = fails.get((label, cfg), [])
        if not f:
            continue
        counts = defaultdict(int)
        for x in f:
            counts[x] += 1
        print(f"\n{label} — {cfg}:")
        for text, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"   {n}x  {text}")
if not fails:
    print("none")
