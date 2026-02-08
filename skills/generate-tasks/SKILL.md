---
name: generate-tasks
description: "Use when creating implementation task lists from requirements. Generates phased task breakdown with user confirmation. Triggers: feature request, task planning, implementation roadmap, break down tasks."
---

# Generate Tasks from Requirements

Creates step-by-step task lists for developers implementing features.

## Workflow

Phase 1: Present Parent Tasks for Approval
1. Analyze requirements from user input or documentation
2. Generate high-level parent tasks
3. Present tasks and ask: "Ready to generate sub-tasks? Respond with 'Go' to proceed."
4. Stop and wait for user confirmation

Phase 2: Generate Sub-Tasks and Save (after user confirms)
1. Break each parent into actionable sub-tasks
2. Identify files to create or modify
3. Save the complete task file (see File Location below)

## File Location

Save the tasks file next to the source PRD/ADR, matching its naming convention:

- Source `docs/003_prd_login.md` → `docs/003_tasks_login.md`
- Source `docs/prd/003_login.md` → `docs/prd/003_tasks_login.md`
- Source `docs/adr/0003_login.md` → `docs/adr/0003_tasks_login.md`

If there is no source document, save as `[NNN]_tasks_[feature-name].md` in `/docs/`.

## Output Format

```markdown
## Relevant Files

- `path/to/file.go` - Brief description of relevance

## Instructions for Completing Tasks

- Mark each sub-task as done (`- [x]`) immediately after completing it
- Mark the parent task as done after all its sub-tasks are complete
- Update this file incrementally, not all at once at the end

## Tasks

- [ ] 1.0 Parent Task Title
  - [ ] 1.1 Sub-task description
  - [ ] 1.2 Sub-task description
- [ ] 2.0 Parent Task Title
  - [ ] 2.1 Sub-task description
```

## Guidelines

- Sub-task granularity should match task complexity
- Sub-tasks must be concrete and actionable
- Include test files in Relevant Files section
- Number format: `1.0` for parents, `1.1` for sub-tasks

