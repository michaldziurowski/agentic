---
name: dz-commit
description: "Turn a working tree into a series of small, atomic commits with messages that explain what changed and why. Use whenever the user asks to commit, stage, or save work, wants changes split into separate commits, asks for a commit message, or is getting a branch ready for review — including bare requests like 'commit this' or 'commit my changes'."
---

# Commit

Based on GitHub's [Write better commits, build better projects](https://github.blog/developer-skills/github/write-better-commits-build-better-projects/).

The diff already records what changed. A commit's job is to make that change *reviewable on its own* and to record *why* it happened — for the reviewer today, and for `git blame`/`git bisect` two years from now.

## 1. Survey before you stage

```bash
git status
git diff                          # unstaged
git diff --cached                 # already staged
git log -15 --format='%s%n%n%b'   # house style
```

Match the style you find in the log: capitalization, `scope:` prefixes, Conventional Commits or plain prose. Consistency with the repo beats any external convention. If the log carries no tool or `Co-Authored-By` trailers, don't introduce one.

## 2. Group the work into a narrative

Split the working tree into the smallest set of commits that tell the story of the change, ordered so each one stands on what came before: prerequisite refactors and new helpers before the code that calls them, tests with the code they cover, pure renames and formatting on their own.

Tell the story as it *should* have happened, not the order you actually stumbled through it.

A commit is atomic when it does one thing, the repo still builds and passes tests at that commit without help from later ones, and a reviewer has everything needed to judge it without reading its neighbours.

Don't manufacture splits to look thorough — one coherent change is one commit. A narrative of one is a fine narrative.

## 3. Stage each unit precisely

Stage by path when the split is file-shaped — most splits are:

```bash
git add path/to/file.go path/to/other.go
```

When a single file holds two unrelated changes, don't hand-trim a patch. `git add -p` is interactive and unavailable here, and deleting hunks out of a `git diff` invalidates the line counts in the `@@` headers, so `git apply` rejects the result and you burn the next several minutes fighting it. Save the file, rewind it, and rebuild one commit at a time:

```bash
cp config.py /tmp/config.final       # keep the finished version
git checkout HEAD -- config.py       # rewind to the last commit
```

Re-apply just the first change as an ordinary edit and commit it, then bring the rest back:

```bash
git add config.py && git commit -F - <<'EOF'
raise default request timeout to 120s
...
EOF

cp /tmp/config.final config.py       # everything else returns
git add config.py && git commit -F - <<'EOF'
expand '~' in the configured output directory
...
EOF
```

Restoring from the saved copy is what makes this safe: the tree you finish on is byte-for-byte the one you started with, no matter how the intermediate edits went. Confirm it before you stop —

```bash
git diff <sha-before-your-first-commit> HEAD -- config.py
```

— which should reproduce the original working-tree diff exactly.

Avoid `git add -A` — sweeping everything in is how unrelated junk and secrets reach history. Read `git diff --cached` before each commit, and if the repo has a fast build or test command, run it; a commit that doesn't build breaks `git bisect` for everyone downstream.

## 4. Write the message

A good message answers four questions, in this order:

| | |
|---|---|
| **Intent** | what this accomplishes → the subject line |
| **Context** | why the code does what it does now |
| **Justification** | why this change is being made |
| **Implementation** | what you did to accomplish it |

Subject: imperative mood, roughly 50 characters, no trailing period — what the commit *accomplishes*, not which files you touched. Body: wrap near 72 characters; skip it only when the subject genuinely is the whole story.

Capitalization and any `scope:` or `type(scope):` prefix come from the log you read in step 1 — not from the examples on this page, which are deliberately inconsistent with each other. Reproduce whatever that repo does: if its subjects are lowercase, yours is lowercase.

Use a heredoc so the formatting survives:

```bash
# this project capitalizes its subjects; check yours before copying the shape
git commit -F - <<'EOF'
Add '--gray' option alias for '--grey'

Include '--gray' as an alternative name for '--grey' in the 'argparse'
definition so that users can specify either common spelling for the
option.
EOF
```

If the only "why" you have is "it was broken", say what was broken and how it surfaced. `Fix bug` and `Update code` are the messages that force a future reader to open the diff and guess.

## 5. Report

Print `git log --oneline` for the new commits and stop there. Don't push, branch, or open a PR unless asked.
