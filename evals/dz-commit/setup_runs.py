#!/usr/bin/env python3
"""Create the run matrix for one model's sweep.

Usage: setup_runs.py <iteration-name> [runs-per-config]

Builds <iteration-name>/eval-<id>-<name>/<config>/run-N/{repo,outputs} from the
fixture templates, and writes an eval_metadata.json beside each run so the
skill-creator viewer can label it.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "fixtures", "templates")

if len(sys.argv) < 2:
    sys.exit(__doc__)

ITER = os.path.join(HERE, sys.argv[1])
NRUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 3

if not os.path.isdir(TEMPLATES):
    sys.exit(f"missing {TEMPLATES}\nrun: bash fixtures/make_fixtures.sh fixtures/templates")

for ev in json.load(open(os.path.join(HERE, "evals.json")))["evals"]:
    eval_dir = f"eval-{ev['id']}-{ev['name']}"
    meta = {"eval_id": ev["id"], "eval_name": ev["name"],
            "prompt": ev["prompt"], "assertions": ev["expectations"]}

    os.makedirs(os.path.join(ITER, eval_dir), exist_ok=True)
    with open(os.path.join(ITER, eval_dir, "eval_metadata.json"), "w") as fh:
        json.dump(meta, fh, indent=2)

    for cfg in ("with_skill", "without_skill"):
        for n in range(1, NRUNS + 1):
            run = os.path.join(ITER, eval_dir, cfg, f"run-{n}")
            os.makedirs(os.path.join(run, "outputs"), exist_ok=True)
            repo = os.path.join(run, "repo")
            if os.path.isdir(repo):
                shutil.rmtree(repo)
            shutil.copytree(os.path.join(TEMPLATES, ev["template"]), repo)
            with open(os.path.join(run, "eval_metadata.json"), "w") as fh:
                json.dump(meta, fh, indent=2)
            print(run)
