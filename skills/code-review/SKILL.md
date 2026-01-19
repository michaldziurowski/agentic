---
name: code-review
description: "Use when reviewing code changes. Analyzes diffs or pull requests for code quality issues. Triggers: review code, code review, review PR, review pull request, check my changes."
---

# Code Review

Run a code review on code changes.

## Retrieving Code to Review

If a GitHub pull request URL is provided:
Use `gh pr diff <url>` to retrieve the diff.

If no URL is provided:
Use `git diff` to review the current unstaged changes,
or `git diff --staged` for staged changes.
Ask the user which diff they want reviewed if unclear.

## Review Scope

Only review new additions and modifications in the diff.
Do not review unchanged code outside the diff context.

## Review Checklist

Check for the following issues:

1. Unnecessary or duplicate code
2. Type errors, language-specific gotchas, footguns, or rookie mistakes
3. Unnecessary comments or bloat
4. Overly complicated logic that could be simplified
5. Unintuitive or inconsistent naming
6. Inconsistent coding patterns within the codebase

## Language Idioms

Follow idiomatic conventions for the language under review.
What constitutes clean code varies by language.
Apply language-specific best practices and community standards.

Examples:
- Go: prefer explicit error handling, avoid naked returns, use short variable names in limited scope
- TypeScript: leverage type system, avoid `any`, use discriminated unions
- Python: follow PEP 8, use list comprehensions appropriately, prefer explicit over implicit
- Rust: leverage ownership system, prefer iterators, avoid unnecessary clones

## Output Format

For each issue found:

1. State the issue clearly
2. Reference the specific location (file and line)
3. Explain why it is problematic
4. Suggest how to improve it

## Constraints

Do not edit any files.
Present findings and suggestions only.

For difficult or ambiguous cases, consult the user before making a judgment.
