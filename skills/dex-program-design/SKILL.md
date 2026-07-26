---
name: dex-program-design
description: "Use as phase 3 of Dex Horthy's front-loaded SDLC, after system architecture and before implementation, to decide the shape of the code — call stacks, file layout, types, and method signatures — as light pseudocode. Triggers: program design, shape of the code, call stack, call graph, file tree diff, method signatures, what files does this touch, how should this be structured internally."
---

# Program Design

Phase 3 of four, and the one most people skip. After architecture, before anyone (human or agent) writes the implementation, go a level down into the **shape of code**: the types, the method signatures, the program layout, and the call stacks.

Most people assume that once the architecture is right the model can just cook. You can do that — you might not like what you get back.

Comes after `dex-system-architecture`. Hands off to `dex-vertical-slices`.

## Scope

The target is everything too internal for an architecture doc that an agent might still get wrong.
Architecture says the endpoint exists and what it returns. Program design says which file wraps it, what the function is called, what it takes, and who calls it.

## Light Visualizations in Pseudocode

Mermaid has its place, but it is the wrong tool here — it reads as exhausting and it hides the detail that matters. Pseudocode with diff syntax works far better.

**Call-stack trees**, for any orchestration or control-flow change. Use diff syntax when the interesting part is what's changing:

```diff
 entrypoint
   runCommand
+    handleCreateResource
+      ResourceClient.create(input)
+        POST /resources
+      renderResult
-    legacyCreateFlow
```

**File-tree diffs**, so you stay in touch with the layout of the codebase and where things live:

```diff
 src
 └── resource
+    ├── resource-client.ts      # NEW - wraps API contract calls
+    ├── resource-client.test.ts # NEW - covers request/response mapping
~    └── resource-route.ts       # MODIFIED - wires create action into UI
```

**Types and method signatures** for the key new functions:

```ts
interface Cursor {
  position: ItemId
  direction: 'up' | 'down'
}

resolveTarget(items: Item[], cursor: Cursor) -> ItemId | null
```

## How to Work It

Have the model draft all three, then argue with it. None of them take long to produce.
Read the codebase first — mirror the layout, naming, and patterns that are already there rather than inventing a parallel structure.
Be concrete enough to be wrong. A vague box-and-arrow sketch cannot be disagreed with; a named file and a typed signature can.

Every one of these is a decision you would otherwise make implicitly during code review — at the most expensive possible time to change your mind.

## Output

- **Call-stack tree** — the control flow, in diff syntax where it changes.
- **File-tree diff** — new and modified files, annotated with what each is for.
- **Signatures** — key new types and functions.
- **Deletions** — what this replaces or removes.

## Constraints

Do not write the implementation. This is the shape, not the code.
Do not redesign the architecture here; if the design forces a contract change, go back to `dex-system-architecture`.
Do not spec every function — cover the ones an agent would plausibly get wrong.
