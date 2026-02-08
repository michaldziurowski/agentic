---
name: create-prd
description: "Use when creating a Product Requirements Document. Guides PRD creation with clarifying questions and structured output. Triggers: PRD, product requirements, feature spec, requirements document."
---

# Create PRD

Generate a Product Requirements Document from a user's feature request.

## Process

1. Receive initial feature description from user
2. Determine output location (see Output section)
3. Ask clarifying questions until all ambiguity is resolved (or user says stop)
4. Generate PRD based on answers
5. Save to determined location

You must ask clarifying questions before writing.
You must not implement the feature.

## Clarifying Questions

**Leave no stone unturned.** Ask as many questions as necessary to fully understand the feature. Start with the most important questions first. Continue asking until:
- All ambiguity is resolved, OR
- The user explicitly says to stop or move on

Do not limit questions artificially. A complex feature may require many rounds of clarification. A simple feature may need only a few.

Focus areas (in rough priority order):
- Problem/Goal: What problem does this solve? Why now?
- Users: Who experiences this problem? How severely?
- Core Functionality: What key actions should users perform?
- Scope: What should this feature not do?
- Success Criteria: How do we measure success?
- Constraints: Any technical, timeline, or resource limitations?
- Dependencies: What else must exist or be true?

### Question Format

Number all questions.
Provide options as A, B, C, D for each.
Indent options under each question.
Enable responses like "1A, 2C, 3B".

Example:
```
1. What is the primary goal?
      A. Improve onboarding
      B. Increase retention
      C. Reduce support burden
      D. Generate revenue

2. Who is the target user?
      A. New users only
      B. Existing users only
      C. All users
      D. Admin users only
```

## PRD Structure

Include all sections in this order:

1. **Introduction/Overview** - Feature description and problem it solves
2. **Goals** - Specific, measurable objectives
3. **User Stories** - Narratives describing usage and benefits
4. **Functional Requirements** - Numbered list of required functionalities
5. **Non-Goals (Out of Scope)** - What this feature will not include
6. **Design Considerations** (Optional) - UI/UX requirements, mockups
7. **Technical Considerations** (Optional) - Constraints, dependencies
8. **Open Questions** - Only include items the user explicitly chose to leave open; otherwise this section should be empty or omitted

## Boundaries

A PRD describes WHAT to build, not HOW to build it.

Do not include:
- Specific file names or paths to modify
- Function, class, or module names
- Code snippets or pseudocode
- Database schema or API endpoint details
- Architecture decisions

Leave implementation decisions to engineers. If technical context is needed, keep it at the level of constraints ("must work offline", "needs to support 10k concurrent users") not solutions ("use Redis", "modify auth.go").

## Output

Format: Markdown

### Location

Check for existing PRD files matching any of these patterns:

| Pattern | Path | Example |
|---------|------|---------|
| A | `/docs/[NNN]_prd_[feature-name].md` | `docs/003_prd_login.md` |
| B | `/docs/prd/[NNN]_[feature-name].md` | `docs/prd/003_login.md` |
| C | `/docs/adr/[NNNN]_[feature-name].md` | `docs/adr/0003_login.md` |

If existing PRD/ADR files are found, follow the established pattern. If no existing files are found, ask the user which pattern to use.

### Filename Numbering

1. Find the highest number among existing files in the chosen location
2. Use that number + 1, zero-padded to match the pattern (3 digits for A/B, 4 digits for C)
3. If no existing files, start with `001` (or `0001` for pattern C)
