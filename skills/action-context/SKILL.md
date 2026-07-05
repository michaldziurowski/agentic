---
name: action-context
description: |
  Build a short orientation brief ("context") for an action item in actions/ and write it
  inline into the action file, so the user can start digging into the work. Use whenever the
  user wants to build/prep/gather context for an action, get oriented on a task on their plate,
  or "start working on" / "dig into" a specific action item. Produces a skimmable launchpad —
  the crux, a minimal mental model, where to dig, current state, and open questions — NOT a full
  design doc. Trigger when the user names an action file or says things like "build context for
  <action>", "prep this action", "help me start on <action>", "orient me on <action>".
---

# Action Context — Orientation Brief for an Action Item

Build a **launchpad**, not a dossier. Actions in `actions/` are the user's "what's on my plate"
queue. The point of a context brief is to load the topic into the user's head fast and point them
at the right threads to pull — *enough to start digging, no more.* Once they're working they'll
ask questions and go deeper; the brief doesn't try to answer everything up front.

Two consequences shape everything below:

- **Short and skimmable wins.** A brief someone reads in ~30 seconds and then starts working beats
  a thorough one they skip. Cut anything that isn't needed to *start*.
- **The brief is orientation, not durable knowledge.** Don't turn it into reference documentation.
  Any genuinely durable domain fact uncovered while researching belongs in the owning entity's
  `knowledge/` as an atomic note (per the vault rules) — the brief can link to it. The brief itself
  is ephemeral; it can go stale and that's fine.

## The altitude test (the hard part)

The one judgment that makes or breaks the brief: **what vs. why-it's-hard.**

- A detail that explains **what** the problem is and **where it lives** → orientation. Keep it.
- A detail that explains **why it's hard to fix** — edge-case event sequences, internal mechanics,
  corner cases — → digging-depth. Leave it out. The user will hit it naturally once they start, and
  it's the fastest way to bloat a brief past the point anyone reads it.

When a sentence feels insightful but you're unsure, ask which side of that line it's on. Insightful
*why-it's-hard* detail is the most tempting thing to include and the most important to cut.

**Tie-breaker for mechanism detail.** The hardest case is a mechanism — a field, a behavior, a step
in the flow — that sits right on the line. Keep it only if the fix *pivots* on it: it names the
exact thing being added or changed (e.g. the missing field the whole fix hinges on). Mechanism that
merely *explains how something works*, without being the fulcrum of the fix, is digging-depth — cut
it.

One exception: a mechanism that could *enable or invalidate a competing approach* — e.g. an existing
capability that might make the proposed fix unnecessary — is load-bearing even though it isn't the
current fix's fulcrum. Don't inline it as mechanism; surface it as an **open question**, so the user
weighs the alternative instead of assuming the proposed path.

## Procedure

1. **Read the action file.** Get the one-line description, `project:` (owning entity), `source:`,
   status, and any existing `## Log` entries. The log often already states the current situation —
   don't re-derive it.

2. **Read the owning entity.** Follow `project:` to `projects/<e>/README.md` or
   `services/<e>/README.md`. Skim its `## Built on` / `## Consumers` lines. The entity's `log.md` is
   usually the single best current-state source — skim its most recent entries touching this action.
   In `knowledge/`, **skim filenames and read only the notes that touch this action** — don't read
   the whole directory. Note related services the work spans.

3. **Gather just enough — and stop early.** Pull only what's needed to orient:
   - **Architecture / mental model** — if the action spans systems the user may not hold in head,
     use the `brainly-services` skill to understand how the pieces connect (e.g. event flow between
     services). You need the shape, not the internals. Skip it if the entity's README/log already
     gave you the flow.
   - **Current state** — the entity's `log.md` and the action's own `## Log` (from steps 1–2) are
     usually the best current-state source. If a `source:` Slack permalink is present and Slack read
     tools are available, use the thread as a *freshness check* — skim for decisions/ETAs newer than
     the log, not to re-derive what the log already synthesized.
   - **People** — check `resources/people/<name>.md` for anyone owning a decision or answer. Map
     roles precisely (PM vs owner vs engineer); whoever requests or confirms a requirement is often
     not who implements or owns it.
   - **Related actions** — a quick scan of `actions/` for sibling items on the same entity.

   This is timeboxed research. When you can write the five sections below, stop looking. Resist
   the urge to read one more file.

4. **Synthesize the brief** using the template below. Every line must earn its place. If a section
   has nothing real to say, drop the section rather than pad it.

5. **Write it inline** into the action file as a `## Context` section placed **between the one-line
   description and `## Log`**. If a `## Context` section already exists, replace it (briefs are
   regenerated, not appended). Leave the frontmatter, description, and `## Log` untouched. The
   `built` date is **today** (the build date), not the action's `created` date.

## Output template

Use this shape. Keep the whole thing tight — aim for something that fits on one screen. Omit any
section that would just be filler.

```markdown
## Context
*Orientation brief — built <today's date>. Skim to start; dig deeper as you work.*

**The crux** — 1–2 sentences naming the real problem and why it matters/blocks. Not a restatement
of the description; the sharpened version. Use the source's own framing for status — don't promote
an open question or design point into a blocker.

**How it fits** — the minimal mental model: which systems are involved and how they connect
(e.g. the event/data flow), only to the depth needed to know *where the problem lives*. Stop there —
do not explain why it's hard to fix (that's the altitude test).

**Where to dig**
- [[<entity>/README|<entity>]] — what to look at there
- Slack: <thread ref> — what's in it
- [[person-name]] — owns / decides X
- `repo or path` — the code/config that matters (if known)

**State & next move** — where it stands right now (e.g. "fix proposed, not yet agreed by X team")
and the immediate next action the user should take. This is the part that saves re-deriving status.

**Open questions**
- The handful of genuine unknowns worth resolving early. Skip if none.
```

## Keeping it lean

- **When in doubt, cut.** The failure mode is a bloated brief, not a sparse one. Missing detail gets
  filled in by digging; excess detail just doesn't get read. Apply the altitude test above.
- **Cap the pointers.** "Where to dig" is the few sources that actually matter (~3–5), not an
  inventory of everything you touched. More links = less signal.
- **Link, don't inline.** Point to READMEs, knowledge notes, Slack threads, and people with
  wikilinks rather than reproducing their content. Wikilinks follow vault convention:
  `[[<entity>/README|<entity>]]` for projects/services, `[[first-last]]` for people, `[[filename]]`
  otherwise.
- **Don't invent certainty.** If the current state is genuinely unclear, say so in "State & next
  move" — an honest "unknown, confirm with X" is more useful than a confident guess.
- **Graduate durable facts.** If research surfaces an atomic domain fact that will outlive this
  action, offer to write it into the entity's `knowledge/` and link it from the brief — don't bury
  it inline where it dies when the action closes.
