---
name: dex-product-review
description: "Use as phase 1 of Dex Horthy's front-loaded SDLC, before any technical design, to pin down what we're building and why in product terms — with rough HTML mockups instead of prose. Triggers: product review, product spec, product requirements, what are we building, mock up the screens, turn this voice note into a spec."
---

# Product Review

Phase 1 of four. A short doc that pins down **what** we're building and **why**, before anyone touches architecture.
The job is to take two sentences or a long voice-note ramble and turn it into something semi-structured.

Stay in product space, not technical space. Hand off to `dex-system-architecture` when this is settled.

## When to Run

Run when an agent misunderstanding the intent would be expensive.
Skip it for a copy tweak, a one-off script, or a bug with an obvious repro — oneshot those straight to the agent.
Skip it for large refactors too, where there is no user-visible product question; go straight to architecture.
For medium tasks, fold this into a single plan document with the system architecture rather than writing two.

## What to Pin Down

**The problem to solve** — the actual user pain, in the user's terms. Not the feature, the pain.

**What success looks like** — what you can read after shipping to decide the thing was worth building.
Ideally a user outcome: "can do XYZ workflow in less time", "reaches onboarding milestone ABC earlier".
Sometimes lower level — an error rate, a latency number. Sometimes just "the support tickets about X stop."

**The feature itself**, semi-structured. A JSON or outline form of the steps, states, and exits works well.

## Mock It Up, Don't Describe It

Most of this is about what the user sees, so build it rather than writing about it.
A rough HTML mockup of the actual screen settles an argument that three paragraphs would only prolong.
Rough is the point — this is a decision-forcing artifact, not a design deliverable.

## Staying in Product Space

You will drift into technical detail. When you catch it, jot the thought down for a later phase and get back to what the user experiences.
If a technical decision is genuinely blocking a product decision: commit what you have, and either move into architecture or spike the feasibility question directly.

## Output

- **Problem** — the user pain, in the user's terms.
- **Success** — what you'll read after shipping to know it worked.
- **Feature outline** — the steps, states, and exits, semi-structured.
- **Mockups** — rough HTML of the real screens.
- **Parked** — technical notes deferred to later phases.

Then run an **author-opt-in review**: pick the person who would review the PR and walk them through this doc — async via doc comments is fine — before any code exists.

## Constraints

Do not design the system here. Services, endpoints, and schemas belong in `dex-system-architecture`.
Do not describe a screen you could mock up in ten minutes of HTML.
Do not let this become a spec document. It is short by design.
