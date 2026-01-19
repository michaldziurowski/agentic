---
name: go-database
description: "Use when setting up database layer in Go projects. Enforces modernc.org/sqlite (pure Go), sqlc, go:generate, RFC3339 dates in UTC, embedded migrations. Triggers: database setup, sqlc, sqlite, go database, data layer, modernc, migrations, embed."
---

# Go Database Layer

Database layer conventions for Go applications using SQLite and sqlc.

**Applies only when the project does not already have a database setup.** If the project has an existing database layer, follow existing conventions instead.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Database | SQLite via `modernc.org/sqlite` |
| Query Generator | sqlc |
| Date Format | RFC3339 (TEXT), always UTC |
| DB Path | `DB_PATH` env var, fallback to `data/app.db` |

## Why These Choices

- **modernc.org/sqlite**: Pure Go, no CGO. Simplifies cross-compilation and CI.
- **RFC3339 TEXT**: Human-readable, timezone-explicit, sorts lexicographically. SQLite DATETIME lacks timezone handling.
- **Embedded migrations**: No external tools, single binary deployment.

## SQLite Driver

```go
import _ "modernc.org/sqlite"
```

Driver name for `sql.Open` is `"sqlite"`.

## sqlc as Go Tool

Add sqlc as a tool dependency in `go.mod` (Go 1.24+):

```bash
go get -tool github.com/sqlc-dev/sqlc/cmd/sqlc
```

This adds a `tool` directive to `go.mod`:

```
tool github.com/sqlc-dev/sqlc/cmd/sqlc
```

## Code Generation

Place `//go:generate` directive in the db package:

```go
// internal/db/generate.go
package db

//go:generate go tool sqlc generate
```

Run `go generate ./...` to generate sqlc files.

## sqlc Configuration

```yaml
# sqlc.yaml
version: "2"
sql:
  - engine: "sqlite"
    queries: "internal/db/queries.sql"
    schema: "internal/db/schema.sql"
    gen:
      go:
        package: "db"
        out: "internal/db"
        overrides:
          - column: "*.created_at"
            go_type: "Time"
          - column: "*.updated_at"
            go_type: "Time"
```

## Date Handling

Store dates as RFC3339 TEXT in SQLite, always in UTC.

### Schema

```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,  -- RFC3339 format
    updated_at TEXT NOT NULL   -- RFC3339 format
);
```

### Custom Time Type

sqlc needs a custom type to properly scan RFC3339 strings into `time.Time`. See @time.go for implementation.

### Usage

```go
// Insert with UTC time
now := db.Now()
queries.CreateEvent(ctx, db.CreateEventParams{
    Name:      "Meeting",
    CreatedAt: now,
    UpdatedAt: now,
})

// Display in local timezone
event, _ := queries.GetEvent(ctx, id)
fmt.Println(event.CreatedAt.Local().Format("2006-01-02 15:04"))
```

## Directory Structure

```
internal/db/
├── generate.go      # //go:generate directive
├── migrate.go       # Migration runner
├── schema.sql       # Table definitions (full schema for sqlc)
├── queries.sql      # sqlc queries
├── time.go          # Custom Time type
├── migrations/      # SQL migration files
│   ├── 001_initial.sql
│   ├── 002_add_feature.sql
│   └── ...
├── db.go            # Generated
├── models.go        # Generated
└── queries.sql.go   # Generated
```

## Migrations

Embedded SQL migrations with a custom runner. No external tools required.

### Migration Files

Place SQL files in `internal/db/migrations/` with numeric prefixes:

```
migrations/
├── 001_initial.sql
├── 002_add_users.sql
└── 003_add_indexes.sql
```

### Migration Runner

See @migrate.go for full implementation. Key features:
- Embeds SQL files via `//go:embed migrations/*.sql`
- Tracks applied migrations in `schema_migrations` table
- Runs pending migrations in transaction

### Call on Startup

```go
// cmd/server/main.go
package main

import (
	"context"
	"database/sql"
	"log/slog"
	"os"

	"yourmodule/internal/db"

	_ "modernc.org/sqlite"
)

func main() {
	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "data/app.db"
	}
	conn, err := sql.Open("sqlite", dbPath)
	if err != nil {
		slog.Error("db open failed", "err", err)
		os.Exit(1)
	}
	if err := db.Migrate(context.Background(), conn); err != nil {
		slog.Error("migration failed", "err", err)
		os.Exit(1)
	}
	// ... rest of startup
}
```

### schema.sql for sqlc

Keep `schema.sql` as the full schema (all tables with `IF NOT EXISTS`). sqlc uses this for code generation while migrations handle actual DB changes.

## Quality Checklist

- [ ] Using `modernc.org/sqlite` driver (no CGO)
- [ ] DB path from `DB_PATH` env var with fallback
- [ ] sqlc declared as Go tool in `go.mod`
- [ ] `//go:generate` directive in db package
- [ ] Dates stored as RFC3339 TEXT
- [ ] All timestamps in UTC
- [ ] Custom Time type for scanning
- [ ] Type overrides in sqlc.yaml for date columns
- [ ] Migrations in `internal/db/migrations/` with numeric prefixes
- [ ] Migration runner with `//go:embed migrations/*.sql`
- [ ] Migrations called on startup (fail-fast)
