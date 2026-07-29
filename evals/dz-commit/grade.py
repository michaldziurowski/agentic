#!/usr/bin/env python3
"""Grade dz-commit eval runs programmatically from the resulting git history."""
import json
import os
import re
import subprocess
import sys

WS = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) < 2:
    sys.exit("usage: grade.py <iteration-name>")
ITER = sys.argv[1] if os.path.isabs(sys.argv[1]) else os.path.join(WS, sys.argv[1])

# (run-dir name, fixture template, eval id) — graders below are keyed by id
EVALS = [(f"eval-{e['id']}-{e['name']}", e["template"], e["id"])
         for e in json.load(open(os.path.join(WS, "evals.json")))["evals"]]

CC_RE = re.compile(r"^(feat|fix|docs|chore|refactor|test|style|perf|build|ci|revert)(\([^)]+\))?!?: .+")
TRAILER_RE = re.compile(r"co-authored-by|generated with|noreply@anthropic|🤖", re.I)


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout


def commits_since(repo, base):
    shas = git(repo, "log", "--format=%H", f"{base}..HEAD").split()
    shas.reverse()
    out = []
    for sha in shas:
        subject = git(repo, "log", "-1", "--format=%s", sha).strip()
        body = git(repo, "log", "-1", "--format=%b", sha).strip()
        files = [f for f in git(repo, "show", "--name-only", "--format=", sha).split("\n") if f.strip()]
        patch = git(repo, "show", "--format=", sha)
        out.append({"sha": sha[:8], "subject": subject, "body": body, "files": files, "patch": patch})
    return out


def check(text, passed, evidence):
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def common_checks(cs, repo):
    long_subj = [c["subject"] for c in cs if len(c["subject"]) > 72]
    trailers = [c["sha"] for c in cs if TRAILER_RE.search(c["body"]) or TRAILER_RE.search(c["subject"])]
    dirty = git(repo, "status", "--porcelain").strip()
    return [
        check("All commit subjects are 72 characters or fewer",
              not long_subj,
              "all subjects within 72 chars" if not long_subj else f"over-length: {long_subj}"),
        check("No Co-Authored-By or tool-attribution trailer was added",
              not trailers,
              "no trailers found" if not trailers else f"trailer in commits {trailers}"),
        check("Working tree is clean afterwards",
              not dirty,
              "git status --porcelain is empty" if not dirty else f"uncommitted remains:\n{dirty}"),
    ]


def has_body(cs, minlen=30):
    bodied = [c for c in cs if len(c["body"]) >= minlen]
    return check("At least one commit body explains why the change was made, not just what changed",
                 bodied,
                 f"{len(bodied)}/{len(cs)} commits have a body of >={minlen} chars"
                 + (f"; e.g. {bodied[0]['sha']}: {bodied[0]['body'][:120]!r}" if bodied else ""))


def grade_eval0(cs, repo):
    readme_only = [c for c in cs if set(c["files"]) == {"README.md"}]
    mixed = [c for c in cs if any("store.go" in f for f in c["files"]) and any("export/csv.go" in f for f in c["files"])]
    together = [c for c in cs if any("export/csv.go" in f for f in c["files"]) and any("cmd/root.go" in f for f in c["files"])]
    bad_style = [c["subject"] for c in cs if CC_RE.match(c["subject"]) or (c["subject"][:1].isupper())]
    return [
        check("Splits the work into at least 3 commits rather than one lump",
              len(cs) >= 3, f"{len(cs)} commits: {[c['subject'] for c in cs]}"),
        check("The README typo fix is isolated in a commit that touches nothing else",
              readme_only, f"README-only commits: {[c['sha'] for c in readme_only]}"
              or "README.md never appeared alone"),
        check("The store.go bug fix is not mixed into the CSV export feature commit",
              not mixed, "store.go and export/csv.go never share a commit" if not mixed
              else f"mixed in {[c['sha'] for c in mixed]}"),
        check("The new export package and the cmd/root.go call site that uses it land in the same commit",
              together, f"together in {[c['sha'] for c in together]}" if together
              else "export/csv.go and cmd/root.go were committed separately"),
        check("Commit subjects follow the repo's lowercase plain-prose style, not Conventional Commits",
              not bad_style, "all subjects lowercase plain prose" if not bad_style
              else f"off-style subjects: {bad_style}"),
        has_body(cs),
        *common_checks(cs, repo),
    ]


def grade_eval1(cs, repo):
    timeout = [c for c in cs if "DEFAULT_TIMEOUT = 120" in c["patch"]]
    expand = [c for c in cs if "expanduser" in c["patch"]]
    separate = len(timeout) == 1 and len(expand) == 1 and timeout[0]["sha"] != expand[0]["sha"]
    isolated = separate and "expanduser" not in timeout[0]["patch"] and "DEFAULT_TIMEOUT = 120" not in expand[0]["patch"]
    return [
        check("Splits the single modified file into exactly 2 commits",
              len(cs) == 2, f"{len(cs)} commits: {[c['subject'] for c in cs]}"),
        check("The timeout bump and the expanduser fix are in different commits",
              separate,
              f"timeout in {[c['sha'] for c in timeout]}, expanduser in {[c['sha'] for c in expand]}"),
        check("Neither commit's diff carries the other commit's change",
              isolated,
              "each commit's diff contains only its own change" if isolated
              else "at least one commit's diff contains both changes"),
        has_body(cs),
        *common_checks(cs, repo),
    ]


def grade_eval2(cs, repo):
    both = [c for c in cs if any("rates.js" in f and "test" not in f for f in c["files"])
            and any("rates.test.js" in f for f in c["files"])]
    styled = [c["subject"] for c in cs if CC_RE.match(c["subject"])]
    return [
        check("Does not over-split: exactly one commit for one coherent change",
              len(cs) == 1, f"{len(cs)} commits: {[c['subject'] for c in cs]}"),
        check("Implementation and its test are committed together",
              both, f"together in {[c['sha'] for c in both]}" if both
              else "rates.js and rates.test.js were committed separately"),
        check("Subject matches the repo's Conventional Commits house style",
              len(styled) == len(cs) and cs,
              f"{len(styled)}/{len(cs)} subjects match feat|fix|docs(scope): — {[c['subject'] for c in cs]}"),
        *common_checks(cs, repo),
    ]


GRADERS = {0: grade_eval0, 1: grade_eval1, 2: grade_eval2}

def run_dirs(cfg_dir):
    """Support both <cfg>/repo and <cfg>/run-N/repo layouts."""
    runs = sorted(d for d in os.listdir(cfg_dir) if d.startswith("run-")) \
        if os.path.isdir(cfg_dir) else []
    return [os.path.join(cfg_dir, r) for r in runs] or [cfg_dir]


for eval_dir, tpl, eid in EVALS:
    base = git(os.path.join(WS, "fixtures", "templates", tpl), "rev-parse", "HEAD").strip()
    for cfg in ("with_skill", "without_skill"):
      for run in run_dirs(os.path.join(ITER, eval_dir, cfg)):
        repo = os.path.join(run, "repo")
        if not os.path.isdir(repo):
            continue
        cs = commits_since(repo, base)
        exps = GRADERS[eid](cs, repo)
        passed = sum(1 for e in exps if e["passed"])
        grading = {
            "expectations": exps,
            "summary": {"passed": passed, "failed": len(exps) - passed, "total": len(exps),
                        "pass_rate": round(passed / len(exps), 3)},
        }
        tpath = os.path.join(run, "timing.json")
        if os.path.exists(tpath):
            with open(tpath) as fh:
                grading["timing"] = json.load(fh)
        with open(os.path.join(run, "grading.json"), "w") as fh:
            json.dump(grading, fh, indent=2)
        print(f"{eval_dir:36s} {cfg:14s} {passed}/{len(exps)}  ({len(cs)} commits)")
        for c in cs:
            print(f"    {c['sha']}  {c['subject']}")
