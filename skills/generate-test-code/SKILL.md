---
name: generate-test-code
description: "Generate Go test code from plain-text e2e/integration test specification markdown files. Reads Given/When/Then test specs, scans project context (OpenAPI schema, compose.yaml, source code), and produces Go test files with HTTP client code or agent-browser CLI calls. Use this skill whenever the user wants to generate test code from specs, implement e2e tests, create integration tests from markdown, convert test specs to code, or uses /generate-test-code. Also trigger when the user has .md test spec files and says things like 'implement these tests', 'generate the Go code', 'make these tests runnable', or 'turn specs into tests'."
---

# Generate Test Code

Reads plain-text test specification markdown files (Given/When/Then format) and generates Go test code that executes those scenarios against a running application.

## Workflow

### Step 1: Find Test Spec Files

Locate `.md` files containing test specs. Look for files with Given/When/Then patterns in directories like `tests/`, `e2e/`, `integration/`, or ask the user which files to process.

### Step 2: Gather Project Context

Scan the project to understand how to interact with the application:

1. **API Schema** — find and read OpenAPI/Swagger files to understand endpoints, request/response shapes, authentication requirements.

2. **App type** — determine whether this is a backend service or an SSR web app:
   - Backend indicators: OpenAPI schema, REST/gRPC handlers, API-only routes, JSON responses
   - SSR indicators: HTML template files (`.templ`, `.html`, `.gohtml`), template rendering in handlers, form-based endpoints, static assets
   - If unclear, ask the user

3. **Database** — read `compose.yaml`/`docker-compose.yaml` to find database services:
   - Extract the database type (postgres, mysql, sqlite)
   - Derive connection string from environment variables in the compose file
   - Identify tables from migration files, schema files, or model definitions
   - If connection info is unclear, ask the user

4. **Base URL** — determine the application's base URL from compose.yaml port mappings, or ask the user.

### Step 3: Generate Go Test Files

For each `.md` spec file, generate a corresponding `_test.go` file in the same directory.

#### Mapping Markdown to Go

- The `#` header (feature name) becomes the top-level test function: `# User Management` → `func TestUserManagement(t *testing.T)`
- Each `##` header (test case) becomes a subtest: `## Create user successfully` → `t.Run("Create user successfully", ...)`

#### File Structure

```go
package e2e_test

import (
    "testing"
    // ... other imports based on what's needed
)

// truncateTables resets database state between test cases.
func truncateTables(t *testing.T) {
    t.Helper()
    // Connect to DB using connection string from compose.yaml
    // TRUNCATE relevant tables
    // Close connection
}

func TestUserManagement(t *testing.T) {
    t.Run("Create user successfully", func(t *testing.T) {
        truncateTables(t)
        // Given/When/Then steps translated to Go code
    })

    t.Run("Create user with duplicate email", func(t *testing.T) {
        truncateTables(t)
        // Given/When/Then steps translated to Go code
    })
}
```

#### Translating Steps — Backend Services

Each Given/When/Then step becomes Go code that makes HTTP requests and checks responses:

- **Given** steps translate to setup: HTTP calls to create prerequisite data, or SQL inserts for data that can't be created via API
- **When** steps translate to the HTTP request being tested
- **Then/And** steps translate to assertions on the HTTP response (status code, body content, headers)

Use `net/http` and `encoding/json` from the standard library. Use `testing` assertions (`t.Errorf`, `t.Fatalf`). Do not introduce external test libraries unless the project already uses them.

Read response bodies into structs or `map[string]interface{}` as appropriate based on the API schema.

Example translation:

```
Given a user with name "John" exists
```
becomes:
```go
// Create prerequisite user
body := `{"name": "John", "email": "john@example.com"}`
resp, err := http.Post(baseURL+"/api/users", "application/json", strings.NewReader(body))
if err != nil {
    t.Fatalf("setup: creating user: %v", err)
}
resp.Body.Close()
if resp.StatusCode != http.StatusCreated {
    t.Fatalf("setup: expected 201, got %d", resp.StatusCode)
}
```

```
Then the response status is 200
And the response contains the user with name "John"
```
becomes:
```go
if resp.StatusCode != http.StatusOK {
    t.Errorf("expected status 200, got %d", resp.StatusCode)
}
var result map[string]interface{}
json.NewDecoder(resp.Body).Decode(&result)
if result["name"] != "John" {
    t.Errorf("expected name John, got %v", result["name"])
}
```

#### Translating Steps — SSR Web Apps

For SSR web apps, use the `agent-browser` CLI to interact with the application through a browser. Each test case becomes an `exec.Command` call that passes instructions to agent-browser.

Construct the agent-browser instruction from the Given/When/Then steps, providing the full scenario as a natural language instruction. Parse the structured JSON output from agent-browser for assertions.

```go
t.Run("Create user via form", func(t *testing.T) {
    truncateTables(t)

    instruction := `Go to http://localhost:8080/users/new. ` +
        `Fill in the name field with "John" and the email field with "john@example.com". ` +
        `Click the submit button. ` +
        `Verify that the page shows a success message containing "User created". ` +
        `Then go to http://localhost:8080/users and verify that "John" appears in the user list.`

    cmd := exec.Command("npx", "@anthropic-ai/agent-browser", "--instruction", instruction)
    output, err := cmd.Output()
    if err != nil {
        t.Fatalf("agent-browser failed: %v", err)
    }

    var result AgentBrowserResult
    if err := json.Unmarshal(output, &result); err != nil {
        t.Fatalf("parsing agent-browser output: %v", err)
    }

    if !result.Success {
        t.Errorf("agent-browser reported failure: %s", result.Message)
    }
})
```

Check agent-browser's actual CLI interface and output format before generating code — read its documentation or `--help` output if available. The example above is illustrative; adapt to the real CLI.

#### Database Truncation

Derive the truncation logic from compose.yaml:

- **PostgreSQL**: connect via `pgx` or `database/sql` with `lib/pq`, run `TRUNCATE table1, table2, ... CASCADE`
- **MySQL**: `SET FOREIGN_KEY_CHECKS=0; TRUNCATE table1; ... SET FOREIGN_KEY_CHECKS=1;`
- **SQLite**: `DELETE FROM table1; DELETE FROM table2; ...`

Identify tables from migration files or model definitions. Exclude migration-tracking tables (e.g. `schema_migrations`, `goose_db_version`). If table list is unclear, ask the user.

The `truncateTables` function should call `t.Fatalf` on any error — a failed cleanup means subsequent assertions are unreliable.

### Step 4: Present Results

Show the user what files were generated and a brief summary. The generated files are complete and runnable — the user should be able to run `go test ./tests/...` with the application stack already running.

## Guidelines

- Generate the entire test file fresh each time — do not attempt incremental updates
- Use the base URL consistently — define it as a constant or read from an environment variable (`TEST_BASE_URL`) with a sensible default
- Each `t.Run` subtest must be fully independent — truncate tables at the start of each subtest
- Prefer standard library over external dependencies. If the project already uses `testify` or similar, follow existing conventions
- For "Given" steps that create data via API calls, check the response to fail fast if setup fails (use `t.Fatalf`)
- For "Then" assertion steps, use `t.Errorf` (not `t.Fatalf`) so multiple assertions can report failures
- Derive request/response shapes from the OpenAPI schema — use correct field names, types, and paths
- If the spec mentions checking something that cannot be verified via HTTP response (e.g. "an email was sent"), fall back to a database query or note it as a TODO comment
