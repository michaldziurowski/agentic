---
name: create-prd
description: "Use when creating a Product Requirements Document. Guides PRD creation with clarifying questions and structured output. Triggers: PRD, product requirements, feature spec, requirements document."
---

# Create PRD

Generate a Product Requirements Document from a user's feature request.

## Process

1. Receive initial feature description from user
2. Ask clarifying questions until all ambiguity is resolved (or user says stop)
3. Generate PRD based on answers
4. Save to `/docs/[NNN]_prd_[feature-name].md`

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

- Format: Markdown
- Location: `/docs/`
- Filename: `[NNN]_prd_[feature-name].md`

### Filename Numbering

1. Check `/docs/` for existing files matching pattern `[0-9][0-9][0-9]_prd_*`
2. Find the highest number among existing PRD files
3. Use that number + 1, zero-padded to 3 digits
4. If no existing PRD files, start with `001`

Examples:
- No existing PRDs → `001_prd_user-auth.md`
- Existing `003_prd_login.md` and `001_prd_signup.md` → `004_prd_dashboard.md`

## Workflow

1. Read user's feature request
2. Identify information gaps, starting with most critical
3. Present numbered questions with lettered options (indented)
4. Wait for user responses
5. If ambiguity remains, ask follow-up questions (repeat until resolved or user stops)
6. Generate complete PRD with all required sections
7. Check `/docs/` for existing PRD files to determine next number
8. Save to `/docs/[NNN]_prd_[feature-name].md`
9. Stop - do not implement
