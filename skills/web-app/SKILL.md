---
name: web-app
description: "Use when building Go web apps. Enforces templ templates, Alpine AJAX, semantic HTML, minimal JavaScript. Triggers: go web, server-side rendering, SSR, fullstack go, templ, alpine."
---

# Web App

Build server-side rendered web applications with Go, templ, and Alpine AJAX.

## Philosophy

These principles shape every decision:

1. **Semantic HTML first** - Use meaningful elements (`<article>`, `<nav>`, `<section>`, `<button>`, `<form>`), not `<div>` soup. HTML communicates structure and meaning.

2. **CSS only** - Custom CSS with CSS variables for theming. No utility frameworks (Tailwind, Bootstrap). Write purposeful styles that describe what elements *are*, not how they look.

3. **No JS frameworks** - Only Alpine.js + Alpine AJAX when absolutely necessary. The server renders HTML; the browser displays it.

4. **Alpine.js sparingly** - Only when HTML/CSS cannot achieve the goal. Don't recreate in JavaScript what the platform already provides.

5. **Don't fight the browser** - Use native form submission, links, and browser navigation. Enhance progressively, don't replace.

## Technology Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Language | Go | Standard library `net/http` for routing |
| Templates | templ | Never use `html/template` or `text/template` |
| Database | sqlc + SQLite | See @go-database skill |
| Interactivity | Alpine.js | Minimal client-side state |
| Dynamic content | Alpine AJAX | Server-driven partial updates |
| Logging | log/slog | Structured logging only |
| Styling | Plain CSS | No frameworks unless requested |

State before coding: "Using Go stdlib, templ, Alpine AJAX, sqlc/SQLite, slog"

## Request Flow

```
Request → Handler → Query → Template → Response
```

- **Handlers handle the request flow** - parse input, validate, call queries/services, render template
- For simple CRUD: logic lives directly in handlers
- For complex business logic: extract to a service layer in `internal/services/`
- Keep handlers flat and readable; avoid premature abstraction

## Templ Code Generation

Declare templ as a Go tool dependency in go.mod:

```
tool github.com/a-h/templ/cmd/templ
```

Add generate directive in templates package:

```go
//go:generate go tool templ generate
package templates
```

Run `go generate ./...` before building.

## Server Setup

main.go must implement graceful shutdown:

```go
func main() {
    logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
    slog.SetDefault(logger)

    mux := http.NewServeMux()
    // register handlers...

    srv := &http.Server{Addr: ":8080", Handler: mux}

    go func() {
        slog.Info("server starting", "addr", srv.Addr)
        if err := srv.ListenAndServe(); err != http.ErrServerClosed {
            slog.Error("server error", "err", err)
        }
    }()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    slog.Info("shutting down")
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    srv.Shutdown(ctx)
}
```

## Alpine AJAX Integration

Alpine AJAX enables server-driven partial updates without full page reloads.

Include via CDN (Alpine AJAX must load before Alpine.js):

```html
<script defer src="https://cdn.jsdelivr.net/npm/@imacrayon/alpine-ajax@0.12.6/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"></script>
```

### Basic Pattern

```html
<form x-target="results" action="/search" method="get">
    <input type="search" name="q" />
    <button type="submit">Search</button>
</form>
<div id="results">
    <!-- Server response replaces this content -->
</div>
```

### Critical: Server Response Must Include Matching ID

The server response MUST contain an element with the same `id` that `x-target` points to. Without this, Alpine AJAX cannot perform the replacement.

```go
// Response MUST include element with id="results"
templ SearchResults(results []Result) {
    <div id="results">
        // ... content ...
    </div>
}
```

### Key Attributes

| Attribute | Purpose |
|-----------|---------|
| `x-target="id"` | Element ID to replace with response |
| `x-target.replace` | Replace entire element, not just content |
| `x-target.append` | Append response to target |
| `x-target.prepend` | Prepend response to target |

## Quality Checklist

Before completing any web app task, verify:

- [ ] Using templ, not Go templates
- [ ] Using slog, not log package
- [ ] main.go has graceful shutdown
- [ ] All pages have proper document structure (header, main, footer)
- [ ] No div soup - semantic elements used appropriately
- [ ] No JavaScript for what HTML/CSS can do
- [ ] Forms use native validation where possible
- [ ] Interactive elements are correct (button vs a vs input)
- [ ] AJAX responses return HTML fragments, not JSON
- [ ] AJAX responses include element with matching `id` for `x-target`

## Reference Files

- @project-structure.md - Directory layout and file organization
- @handlers.md - HTTP handler patterns, routing, middleware, services
- @templ-patterns.md - Component composition and typed props
- @alpine-ajax-patterns.md - Dynamic content patterns
- @semantic-html.md - Element selection guide
- @anti-patterns.md - What to avoid
- @examples.md - Common UI patterns
