---
name: web-app
description: "Use when building Go web apps. Enforces templ templates, Alpine AJAX, semantic HTML, minimal JavaScript. Triggers: go web, server-side rendering, SSR, fullstack go, templ, alpine."
---

# Web App

Build server-side rendered web applications with Go, templ, and Alpine AJAX.

## Technology Stack

You must use this exact stack:

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

## Core Principles

### HTML-First Development

HTML and CSS can do more than you think. Before adding JavaScript, verify the behavior cannot be achieved with:

- Native form submission and validation
- CSS transitions and animations
- Details/summary for disclosure
- Dialog element for modals
- Anchor links for navigation

JavaScript augments HTML. It never replaces it.

### Server-Driven UI

The server owns the UI. Client requests HTML fragments, not JSON.

Pattern:
1. User action triggers Alpine AJAX request
2. Server renders templ component
3. Response HTML replaces target element

No client-side templating. No JSON APIs for UI data.

### Semantic Markup

Every element must have semantic meaning. See @semantic-html.md for element selection guide.

Required document structure:
```html
<!DOCTYPE html>
<html lang="en">
<head>...</head>
<body>
  <header><!-- site header, nav --></header>
  <main><!-- primary content --></main>
  <footer><!-- site footer --></footer>
</body>
</html>
```

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

See @project-structure.md for full directory layout.

## Handler Patterns

Handlers return templ components. Keep handlers thin.

### Full Page Response

```go
func handleHome(w http.ResponseWriter, r *http.Request) {
    data := HomeData{Title: "Welcome"}
    templates.HomePage(data).Render(r.Context(), w)
}
```

### Partial Response for Alpine AJAX

Check for AJAX header to return partial or full page:

```go
func handleUsers(w http.ResponseWriter, r *http.Request) {
    users := fetchUsers()

    if r.Header.Get("X-Alpine-Request") == "true" {
        templates.UserList(users).Render(r.Context(), w)
        return
    }
    templates.UsersPage(users).Render(r.Context(), w)
}
```

See @templ-patterns.md for component composition.

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

### Form Submission

Forms with `x-target` submit via AJAX automatically:

```html
<form x-target="messages" action="/messages" method="post">
    <input name="content" required />
    <button>Send</button>
</form>
```

### Triggered Updates

Use Alpine events to trigger updates:

```html
<form x-target="results" action="/search">
    <input
        type="search"
        name="q"
        @input.debounce.300ms="$el.form.requestSubmit()"
    />
</form>
```

See @alpine-ajax-patterns.md for advanced patterns.

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
- @templ-patterns.md - Component composition and typed props
- @alpine-ajax-patterns.md - Dynamic content patterns
- @semantic-html.md - Element selection guide
- @anti-patterns.md - What to avoid
- @examples.md - Common UI patterns
