# dz-commit eval harness

Benchmarks `skills/dz-commit` by giving a model a messy working tree and grading
the git history it produces. Every assertion is checked programmatically from the
resulting commits, so a sweep is reproducible and needs no human grading.

## Fixtures

`fixtures/make_fixtures.sh` builds three throwaway git repos, each seeded with a
few commits (which establish a house style) plus uncommitted work:

| template | uncommitted work | correct answer |
|---|---|---|
| `mixed-concerns` | CSV export feature across 2 files, an unrelated `rows.Err()` bug fix, a README typo | 3 commits; the export package and its call site stay together |
| `two-in-one-file` | two unrelated edits in one file, far enough apart to be separate hunks | 2 commits, requiring sub-file staging |
| `single-change-conventional` | one coherent change plus its test; history uses Conventional Commits | 1 commit, `feat(scope):` style — tests that the skill does *not* over-split |

The templates are generated, not committed — regenerate them before a sweep.

## Running a sweep

```bash
cd evals/dz-commit
bash fixtures/make_fixtures.sh fixtures/templates
python3 setup_runs.py run-haiku 3          # 3 evals x 2 configs x 3 runs = 18 dirs
```

Then launch one subagent per run directory. Each gets the repo path and the eval's
`prompt` verbatim; `with_skill` runs are told to follow `skills/dz-commit/SKILL.md`,
`without_skill` runs are told to use no skill at all. Use the `Agent` tool's `model`
parameter to pick the model — the fixtures and grader are model-agnostic, so a
sweep is the same runs pointed somewhere else.

As each subagent finishes, its completion notification carries `total_tokens` and
`duration_ms`. That data exists nowhere else, so capture it immediately:

```bash
python3 record_timing.py run-haiku/eval-0-mixed-concerns/with_skill/run-1 23565 70657 17
```

## Grading and comparing

```bash
python3 grade.py run-haiku            # writes grading.json per run
python3 prepare_review.py run-haiku   # writes a reviewable commits.md per run
python3 compare_models.py             # cross-model table over every benchmark.json
```

For the skill-creator benchmark and browser viewer:

```bash
SC=~/.claude/plugins/cache/claude-plugins-official/skill-creator/unknown/skills/skill-creator
python3 -m scripts.aggregate_benchmark $PWD/run-haiku --skill-name dz-commit   # run from $SC
python3 $SC/eval-viewer/generate_review.py $PWD/run-haiku \
    --skill-name dz-commit --benchmark $PWD/run-haiku/benchmark.json
```

Note the two tools want different layouts: `aggregate_benchmark` looks for
`<eval>/<config>/run-N/grading.json`, while the viewer treats any directory
containing an `outputs/` as one run. The `run-N` layout satisfies both.

## Results so far

`results/` holds the archived `benchmark.json` from the first three-model sweep
against the original skill. Headline: the skill's value scales inversely with
model strength.

| model | with skill | without | delta |
|---|---|---|---|
| Opus 5 (max effort) | 100.0% | 100.0% | +0.00 |
| Sonnet 5 (medium) | 100.0% | 97.5% | +0.02 |
| Haiku 4.5 (medium) | 98.8% | 88.5% | +0.10 |

Nearly all the signal is in `mixed-concerns` (Haiku 96% vs 70%). Two subsequent
fixes — replacing the fragile `git apply --cached` recipe with rewind-and-replay,
and removing a capitalization bias — cut Sonnet's tool calls on `two-in-one-file`
from 22.7 to 7.7 and eliminated the house-style leak. Those runs are not archived
here; only the original sweep is.

## Known weaknesses

- `two-in-one-file` and `single-change-conventional` no longer discriminate — every
  model passes both with and without the skill. They work as regression guards but
  won't tell you whether a change is an improvement.
- "At least one commit body explains why" only checks for 30+ characters of body.
  Haiku passes it with prose that restates the diff. Measuring message *quality*
  needs an LLM-judged assertion, which this harness does not have.
- Model comparisons carry an effort confound unless every sweep runs at the same
  effort level. The archived Opus numbers were collected at max effort; the Sonnet
  and Haiku ones at medium.
- n=3 catches gross instability, not small differences.
