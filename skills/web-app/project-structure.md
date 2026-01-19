# Project Structure

## Directory Layout

```
project/
├── cmd/
│   └── server/
│       └── main.go           # Entry point, server setup
├── internal/
│   ├── handlers/             # HTTP handlers by feature
│   │   ├── home.go
│   │   ├── users.go
│   │   └── middleware.go
│   ├── services/             # Business logic (if needed)
│   │   └── user.go
│   ├── db/                   # Database layer
│   │   ├── queries.sql       # sqlc queries
│   │   ├── schema.sql        # Table definitions
│   │   ├── db.go             # Generated sqlc code
│   │   ├── models.go         # Generated models
│   │   └── queries.sql.go    # Generated query methods
│   └── templates/            # templ components
│       ├── layouts/          # Base layouts
│       │   └── base.templ
│       ├── pages/            # Full page templates
│       │   ├── home.templ
│       │   └── users.templ
│       └── components/       # Reusable partials
│           ├── header.templ
│           ├── footer.templ
│           └── user_card.templ
├── static/                   # Static assets
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── alpine.min.js     # Alpine.js
│       └── ajax.min.js       # Alpine AJAX plugin
├── migrations/               # SQL migrations
│   ├── 001_initial.up.sql
│   └── 001_initial.down.sql
├── go.mod
├── go.sum
├── sqlc.yaml                 # sqlc configuration
└── Makefile                  # Build commands
```

## Why This Structure

Go handlers are controllers. Creating a separate "controllers" directory adds an unnecessary layer. Handlers call services for business logic, services call the database layer.

```
Request → Handler → Service → DB
                ↓
            Response ← templ component
```

## File Naming

| Type | Convention | Example |
|------|------------|---------|
| Handlers | Feature name | `users.go`, `auth.go` |
| Services | Domain name | `user.go`, `order.go` |
| Templates | Component name | `user_card.templ`, `nav.templ` |
| Pages | Page name | `home.templ`, `settings.templ` |
| CSS | Purpose | `style.css`, `forms.css` |

## main.go Pattern

```go
package main

import (
    "context"
    "log/slog"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "project/internal/db"
    "project/internal/handlers"
)

func main() {
    // Structured logging
    logger := slog.New(slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{
        Level: slog.LevelInfo,
    }))
    slog.SetDefault(logger)

    // Database connection
    database, err := db.Connect("data.db")
    if err != nil {
        slog.Error("database connection failed", "err", err)
        os.Exit(1)
    }
    defer database.Close()

    // Router setup
    mux := http.NewServeMux()

    // Static files
    mux.Handle("GET /static/", http.StripPrefix("/static/",
        http.FileServer(http.Dir("static"))))

    // Handlers
    h := handlers.New(database, logger)
    mux.HandleFunc("GET /", h.Home)
    mux.HandleFunc("GET /users", h.ListUsers)
    mux.HandleFunc("POST /users", h.CreateUser)

    // Server with timeouts
    srv := &http.Server{
        Addr:         ":8080",
        Handler:      mux,
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  120 * time.Second,
    }

    // Start server
    go func() {
        slog.Info("server starting", "addr", srv.Addr)
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            slog.Error("server error", "err", err)
            os.Exit(1)
        }
    }()

    // Graceful shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    slog.Info("shutting down server")
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        slog.Error("shutdown error", "err", err)
    }
    slog.Info("server stopped")
}
```

## slog Usage

Use structured logging throughout:

```go
// Info with context
slog.Info("user created", "user_id", user.ID, "email", user.Email)

// Errors with context
slog.Error("failed to fetch user", "err", err, "user_id", id)

// Debug (requires level configuration)
slog.Debug("cache hit", "key", cacheKey)

// With request context
slog.InfoContext(r.Context(), "request processed",
    "method", r.Method,
    "path", r.URL.Path,
    "duration", time.Since(start))
```

## Database Configuration

See @go-database skill for sqlc configuration, date handling, and database layer patterns.
