---
name: generate-tasks
description: "Use when creating implementation task lists from requirements. Generates phased task breakdown with user confirmation. Triggers: feature request, task planning, implementation roadmap, break down tasks."
---

# Generate Tasks from Requirements

Creates step-by-step task lists for developers implementing features.

## Workflow

Phase 1: Parent Tasks
1. Analyze requirements from user input or documentation
2. Generate 4-6 high-level parent tasks
3. Save to `/docs/` with appropriate filename (see naming below)
4. Present tasks and ask: "Ready to generate sub-tasks? Respond with 'Go' to proceed."
5. Stop and wait for user confirmation

Phase 2: Sub-Tasks (after user confirms)
1. Break each parent into actionable sub-tasks
2. Identify files to create or modify
3. Update the task file with complete structure

## File Naming

Default: `tasks-[feature-name].md`

If source is a PRD with number prefix (e.g., `001_prd_user_auth.md`):
Use same prefix: `001_tasks_user_auth.md`

## Output Format

Save to `/docs/`:

```markdown
## Relevant Files

- `path/to/file.go` - Brief description of relevance

## Instructions for Completing Tasks

**IMPORTANT:** Check off tasks by changing `- [ ]` to `- [x]` after completing each sub-task.

## Tasks

- [ ] 1.0 Parent Task Title
  - [ ] 1.1 Sub-task description
  - [ ] 1.2 Sub-task description
- [ ] 2.0 Parent Task Title
  - [ ] 2.1 Sub-task description
```

## Guidelines

- Target audience: junior developers
- Sub-tasks must be concrete and actionable
- Include test files in Relevant Files section
- Number format: `1.0` for parents, `1.1` for sub-tasks
