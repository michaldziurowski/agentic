---
name: dz-brainstorm
description: "Use before there is a clear picture — when you have an itch rather than an idea — to open up the option space and end with a shortlist of candidate directions, not a spec. Triggers: brainstorm, explore options, I have a vague idea, not sure what to build, kick ideas around, what could we do here, think out loud with me."
---

# Brainstorm

Open the space before committing to a direction. This is the divergent step: it generates framings and options, and deliberately does **not** produce requirements.

Runs before `dex-product-review`, which is where converging happens. If you already know the direction and only need it sharpened, you are past this skill.

## When to Run

Run when you cannot yet state what you're building in a sentence — a vague itch, a complaint, a "we should probably do something about X".
Skip when the direction is already chosen, and skip trivial work outright.
Timebox it. This is cheap thinking and it should stay cheap.

## Reframe Before Generating

The first framing is almost always the feature someone already imagined, not the problem underneath it. Restate the itch several ways before accepting one:

- Whose problem is this, and what do they do about it today?
- What is the pain *underneath* the request as stated?
- Invert it — what would make this deliberately worse? Now what's the opposite?
- If this problem vanished overnight, what would actually change?

## Generate Past Comfort

Quantity before judgment. Capture options, do not critique them while generating — evaluation kills the half-formed one that was going somewhere.
Push past the first three. The obvious options come out first and are rarely the good ones.

Force these into the list every time:

- **Do nothing / do it manually** — the baseline everything else has to beat.
- **The smallest thing that delivers any value at all.**
- **The 10× budget version** — then ask which part of it you could have now.
- **One option you expect to reject** — it marks the edge of the space and makes the others easier to judge.

Look outward too: how do adjacent products solve this, and does some other part of this codebase already solve a version of it?

## Probe, Don't Argue

When two options differ on a matter of fact, go get the fact — it is cheaper than the debate.

- A rough HTML mockup settles a UX argument that three paragraphs would only prolong.
- A timeboxed spike settles feasibility.
- Reading the codebase reveals which option it makes ten times harder.

If a technical unknown is blocking the product question, stop discussing and go find out.

## Converge Just Enough

Cluster near-duplicates, drop whatever fails a hard constraint, and keep **2–3 live candidates**.
For each survivor, state the bet it makes and what would kill it.
Then name the **deciding question** — the one thing you'd need to know to choose. It can often be answered in an hour.

## Output

- **The itch** — raw and unpolished, in the words it arrived in.
- **Framings** — the different ways to see the problem.
- **Options** — the full list, including the rejected ones; they document the edges.
- **Shortlist** — 2–3 candidates, each with its bet and its kill condition.
- **Recommendation** — plus the deciding question and how to answer it.
- **Discarded** — one line each on why, so nobody re-proposes them next week.

Hand the shortlist to `dex-product-review` to turn the chosen direction into a product spec. For small work that will be oneshot anyway, the shortlist and its recommendation are enough on their own.

## Constraints

Do not converge early. Killing options before the list is full is the main failure mode of this skill.
Do not write requirements, acceptance criteria, or non-goals — if you are, you have left this skill.
Do not design the implementation.
Do not present a shortlist of one. That is a decision already made wearing a brainstorm's clothes.
