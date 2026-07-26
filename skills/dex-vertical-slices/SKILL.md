---
name: dex-vertical-slices
description: "Use as phase 4 of Dex Horthy's front-loaded SDLC, after program design, to break work into thin end-to-end slices you can actually touch as you build — middle-out, not stack-order. Triggers: vertical slices, tracer bullets, slice the work, break this into steps, build order, horizontal plan, stack order plan."
---

# Vertical Slices

Phase 4 of four. Break the work into thin end-to-end cuts — "tracer bullets" — that you can actually *touch* while building, instead of layers built in stack order.

Comes after `dex-program-design`. This is the last gate before implementation.

## The Failure Mode

Models love **horizontal plans** — doing things in stack order:

1. Database migrations
2. Service layer
3. API
4. Frontend

Nothing is touchable until the end. You can test with code, but for almost any real feature, pulling it up in a browser or hitting it with curl while you work is part of the loop. Before AI, nobody wrote 500 lines — let alone 2000 — without checking *something* along the way.

Most frontier models will not produce a vertical plan without steering, and the right slicing is hard to generalize per codebase or per task. Stay in the loop here.

## Slice Middle-Out

Start in the middle and work outwards. Roughly:

1. Create the API contract, serve mock data — test with curl
2. Build the frontend against the mock — iterate and polish in the browser
3. Wire the API to the services layer (services still serving mock behavior)
4. Add migrations, wire services to the database
5. Add the business logic
6. Add the error handling

Test, iterate, and polish at each step. Each slice should be something you can exercise for real, not just a layer that compiles.

Adapt the order to the change — the principle is "touchable at every step", not this exact list.

## Working the Slices

Send the model 1–3 slices at a time, not the whole plan.
Review the code as you go. Checking 100–200 lines and resteering is far cheaper than landing on the other side of 2k+ lines with no idea what broke.
Review at each step when you care about the code, or when you're skeptical of the model in that part of the codebase.

## Output

An ordered list of slices. For each:

- **What it delivers** — the end-to-end behavior that exists once it lands.
- **How you touch it** — the curl command, the screen, the CLI invocation that proves it.
- **What's still mocked** — what this slice deliberately fakes.
- **Dependencies** — what must land first.

## Constraints

No slice that isn't exercisable on its own — if you can't touch it, it's a horizontal layer wearing a disguise.
Do not hand the model the full plan and walk away.
Do not batch review to the end. The whole point is cheap resteering.
