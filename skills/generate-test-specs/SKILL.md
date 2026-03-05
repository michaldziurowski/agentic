---
name: generate-test-specs
description: "Generate plain-text e2e/integration test specifications as markdown files from API contracts and requirements — before implementation. Produces Given/When/Then test cases grouped by logical feature. Use this skill whenever the user wants to create test specs, write test scenarios, generate e2e test cases, plan integration tests, or uses /generate-test-specs. Also trigger when the user says things like 'write tests for this feature', 'create test cases for the API', 'what should we test', or 'generate test scenarios'. Can focus on a specific feature area, a requirements document, an OpenAPI schema, or cover the entire application."
---

# Generate Test Specs

Produces markdown files containing e2e/integration test cases written in freeform Given/When/Then English. One file per logical feature.

This is a **test-first** tool. Test specs describe how functionality **should** behave based on contracts and requirements — not how it currently works. The generated specs serve as an acceptance criteria that the implementation must satisfy.

## What to read, what to ignore

**DO read** (contracts and requirements):
- OpenAPI/Swagger schemas — endpoints, request/response shapes, status codes, validation rules
- Requirements documents, PRDs, ADRs, feature specs
- API contracts, proto files, GraphQL schemas
- `compose.yaml` / `docker-compose.yaml` — to understand external dependencies and infrastructure

**DO NOT read** (implementation):
- Source code (handlers, services, repositories, models)
- Database migrations or schema files
- Existing test files
- Internal package structure

The point is to derive tests purely from what the feature **should** do, not from what the code currently does. This way the tests remain valid whether the feature is implemented yet or not.

## Workflow

### Step 1: Determine Scope

The user may provide:
- **A specific feature or area** (e.g. "user management", "authentication") — scope to that area
- **A requirements document or schema** (e.g. "the lots endpoints in openapi.yaml") — scope to that contract
- **Nothing** — cover the entire application's contracts

If the scope is ambiguous, ask the user to clarify before proceeding.

### Step 2: Gather Contracts and Requirements

Scan the project for contracts:

1. **API Schema** — look for OpenAPI/Swagger files (`openapi.yaml`, `openapi.json`, `swagger.yaml`, `swagger.json`, `api.yaml`, `docs/` directory). Read the schema to understand available endpoints, request/response shapes, and validation rules.

2. **Requirements docs** — look for PRDs, ADRs, feature specs in `docs/` or similar directories.

3. **Dependencies** — read `compose.yaml` or `docker-compose.yaml` to understand external dependencies (databases, queues, caches, external services). This is relevant for understanding what infrastructure is available, not for deriving test cases from implementation.

If no contracts or requirements are found, ask the user to point you to them or describe the feature's intended behavior.

### Step 3: Group Into Features

Organize endpoints and functionality into logical features. A feature groups related operations — for example, "User Management" might cover create, read, update, delete users plus listing and search.

If the grouping is not obvious (e.g. endpoints that could belong to multiple features), ask the user how they'd like to group them.

### Step 4: Generate Test Specs

For each feature, create a markdown file in a `tests/` directory close to the relevant code (e.g. `tests/user_management.md`).

Each file contains multiple test cases. Each test case has:
- A `#` header with a descriptive test case name
- Steps written in freeform English using Given/When/Then/And keywords
- Coverage of happy path and obvious error cases (invalid input, duplicates, not found, unauthorized)

The steps should be specific enough that someone reading the API schema can unambiguously translate them into API calls, but written in natural language — not code or pseudocode.

### Step 5: Present to User

Show the user what files were created and give a brief summary of test coverage per feature. The user will review and edit before generating test code.

## Output Format

Each markdown file follows this structure:

```markdown
# Create user successfully

Given no users exist
When I create a user with name "John" and email "john@example.com"
Then the response status is 201
And the response contains the user with name "John"
And the user list contains exactly 1 user

# Create user with missing required fields

When I create a user without a name
Then the response status is 400
And the response contains a validation error for the name field

# Create user with duplicate email

Given a user with email "john@example.com" exists
When I create a user with name "Jane" and email "john@example.com"
Then the response status is 409
And the response contains an error indicating the email is already taken

# Get user by ID

Given a user with name "John" exists
When I get the user by their ID
Then the response status is 200
And the response contains the user with name "John"

# Get non-existent user

When I get a user with a non-existent ID
Then the response status is 404
```

## Guidelines

- Write steps that reference concrete values ("John", "john@example.com") rather than abstract placeholders — this makes test cases readable and unambiguous
- Each test case should be independent — do not assume state from a previous test case. Use Given steps to establish preconditions
- "Given" establishes preconditions (data setup). "When" is the action being tested. "Then"/"And" are assertions
- Cover: happy path, missing/invalid input, duplicate/conflict, not found, and any authorization rules visible in the schema
- Do not over-test — focus on behavior that matters to users, not internal implementation details
- If an endpoint has complex validation rules (visible in the schema), add a test case for each distinct validation failure
- Keep test case names descriptive — they become Go subtest names later
- Derive all test expectations from the contract/requirements, never from reading the implementation
