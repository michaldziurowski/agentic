---
name: create-prd
description: "Use when creating a Product Requirements Document. Guides PRD creation with clarifying questions and structured output. Triggers: PRD, product requirements, feature spec, requirements document."
---

# Create PRD

Generate a Product Requirements Document from a user's feature request.

## Process

1. Receive initial feature description from user
2. Ask 3-8 clarifying questions to resolve all ambiguity
3. Generate PRD based on answers
4. Save to `/docs/[NNN]_prd_[feature-name].md`

You must ask clarifying questions before writing.
You must not implement the feature.

## Clarifying Questions

Ask only when the answer is not inferable from the prompt.
Limit to 3-8 questions covering critical gaps.
**Goal: Resolve all ambiguity before writing the PRD. No open questions should remain unless the user explicitly states they want to leave something open.**

Focus areas:
- Problem/Goal: What problem does this solve?
- Core Functionality: What key actions should users perform?
- Scope: What should this feature not do?
- Success Criteria: How do we know it's done?

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

## Target Audience

Write for a junior developer.
Be explicit and unambiguous.
Avoid jargon.
Provide enough detail to understand purpose and core logic.

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
2. Identify 3-8 critical information gaps
3. Present numbered questions with lettered options (indented)
4. Wait for user responses
5. Generate complete PRD with all required sections
6. Check `/docs/` for existing PRD files to determine next number
7. Save to `/docs/[NNN]_prd_[feature-name].md`
8. Stop - do not implement
