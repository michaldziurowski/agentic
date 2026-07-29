#!/usr/bin/env python3
"""Write a reviewable commits.md per run, and mirror grading into run-1/ for the aggregator."""
import json
import os
import shutil
import subprocess
import sys

WS = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2:
    sys.exit("usage: prepare_review.py <iteration-name>")
ITER = sys.argv[1] if os.path.isabs(sys.argv[1]) else os.path.join(WS, sys.argv[1])

EVALS = [(f"eval-{e['id']}-{e['name']}", e["template"])
         for e in json.load(open(os.path.join(WS, "evals.json")))["evals"]]


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout


def run_dirs(cfg_dir):
    """Support both <cfg>/repo and <cfg>/run-N/repo layouts."""
    runs = sorted(d for d in os.listdir(cfg_dir) if d.startswith("run-")) \
        if os.path.isdir(cfg_dir) else []
    return [os.path.join(cfg_dir, r) for r in runs] or [cfg_dir]


for eval_dir, tpl in EVALS:
    base = git(os.path.join(WS, "fixtures", "templates", tpl), "rev-parse", "HEAD").strip()
    for cfg in ("with_skill", "without_skill"):
      for run in run_dirs(os.path.join(ITER, eval_dir, cfg)):
        repo = os.path.join(run, "repo")
        if not os.path.isdir(repo):
            continue

        shas = git(repo, "log", "--format=%H", f"{base}..HEAD").split()
        shas.reverse()

        lines = [f"# {eval_dir} — {cfg}", "",
                 f"**{len(shas)} commit(s)** created on top of `{base[:8]}`.", ""]
        for i, sha in enumerate(shas, 1):
            subject = git(repo, "log", "-1", "--format=%s", sha).strip()
            body = git(repo, "log", "-1", "--format=%b", sha).strip()
            stat = git(repo, "show", "--stat", "--format=", sha).strip()
            lines += [f"## Commit {i}: `{subject}`", ""]
            lines += ["```", subject, ""] + ([body, "```"] if body else ["(no body)", "```"])
            lines += ["", "Files:", "```", stat, "```", ""]

        dirty = git(repo, "status", "--porcelain").strip()
        lines += ["## Working tree after", "", "```",
                  dirty if dirty else "(clean)", "```", ""]

        with open(os.path.join(run, "outputs", "commits.md"), "w") as fh:
            fh.write("\n".join(lines))

        # flat layout only: mirror into run-1/ so the aggregator can find it
        if os.path.basename(run) != "repo" and not os.path.basename(run).startswith("run-"):
            r1 = os.path.join(run, "run-1")
            os.makedirs(r1, exist_ok=True)
            for name in ("grading.json", "timing.json"):
                src = os.path.join(run, name)
                if os.path.exists(src):
                    shutil.copy(src, os.path.join(r1, name))

        print(f"prepared {os.path.relpath(run, ITER)}: {len(shas)} commits")
