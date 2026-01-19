# Anti-Patterns

These patterns are forbidden. Do not use them.

## Template Anti-Patterns

### Never: Go Templates

```go
// WRONG - using html/template
import "html/template"

func render(w http.ResponseWriter, data any) {
    tmpl := template.Must(template.ParseFiles("template.html"))
    tmpl.Execute(w, data)
}
```

```go
// CORRECT - using templ
import "project/internal/templates"

func render(w http.ResponseWriter, r *http.Request, data PageData) {
    templates.Page(data).Render(r.Context(), w)
}
```

Rationale: templ provides compile-time type safety. Go templates fail at runtime.

### Never: text/template for HTML

```go
// WRONG - text/template has no escaping
import "text/template"
```

This creates XSS vulnerabilities. Always use templ.

## Logging Anti-Patterns

### Never: log Package

```go
// WRONG
import "log"

log.Printf("user created: %s", user.ID)
log.Fatal("database error")
```

```go
// CORRECT
import "log/slog"

slog.Info("user created", "user_id", user.ID)
slog.Error("database error", "err", err)
```

Rationale: slog provides structured logging for observability.

## Server Anti-Patterns

### Never: Missing Graceful Shutdown

```go
// WRONG - no signal handling
func main() {
    http.ListenAndServe(":8080", mux)
}
```

```go
// CORRECT - graceful shutdown
func main() {
    srv := &http.Server{Addr: ":8080", Handler: mux}

    go srv.ListenAndServe()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()
    srv.Shutdown(ctx)
}
```

Rationale: Graceful shutdown allows in-flight requests to complete.

## Alpine AJAX Anti-Patterns

### Never: Response Without Matching ID

The server response MUST contain an element with the same `id` that `x-target` points to. Without this, Alpine AJAX cannot replace the target.

```go
// WRONG - response without matching id
templ SearchResults(results []Result) {
    <ul>
        for _, r := range results {
            <li>{ r.Title }</li>
        }
    </ul>
}
```

```go
// CORRECT - response includes element with id="results"
templ SearchResults(results []Result) {
    <div id="results">
        <ul>
            for _, r := range results {
                <li>{ r.Title }</li>
            }
        </ul>
    </div>
}
```

The page has `x-target="results"` pointing to `<div id="results">`. The response must include `<div id="results">...</div>` for the replacement to work.

## JavaScript Anti-Patterns

### Never: JavaScript for What HTML Does

```html
<!-- WRONG - JS for navigation -->
<span class="link" onclick="window.location='/about'">About</span>

<!-- CORRECT - native link -->
<a href="/about">About</a>
```

```html
<!-- WRONG - JS for form submission -->
<div onclick="submitForm()">Submit</div>

<!-- CORRECT - native form -->
<button type="submit">Submit</button>
```

### Never: JavaScript for What CSS Does

```html
<!-- WRONG - JS for hover effects -->
<div onmouseover="this.style.color='red'" onmouseout="this.style.color='black'">
    Hover me
</div>
```

```css
/* CORRECT - CSS handles hover */
.link:hover {
    color: red;
}
```

```html
<!-- WRONG - JS for show/hide -->
<button onclick="document.getElementById('menu').style.display='block'">
    Open Menu
</button>

<!-- CORRECT - CSS with details/summary or Alpine -->
<details>
    <summary>Menu</summary>
    <nav>...</nav>
</details>
```

### Never: Client-Side Templating

```html
<!-- WRONG - building HTML in JavaScript -->
<script>
function renderUsers(users) {
    return users.map(u => `<div class="user">${u.name}</div>`).join('');
}
</script>

<!-- CORRECT - server returns HTML via Alpine AJAX -->
<div x-init x-target="users" hx-get="/users">
    @UserList(users)
</div>
```

### Never: JSON APIs for UI Data

```go
// WRONG - returning JSON for UI consumption
func handleUsers(w http.ResponseWriter, r *http.Request) {
    users := getUsers()
    json.NewEncoder(w).Encode(users)
}
```

```go
// CORRECT - returning HTML
func handleUsers(w http.ResponseWriter, r *http.Request) {
    users := getUsers()
    templates.UserList(users).Render(r.Context(), w)
}
```

Exception: APIs consumed by other services can return JSON.

## Semantic HTML Anti-Patterns

### Never: Div Soup

```html
<!-- WRONG -->
<div class="header">
    <div class="nav">
        <div class="nav-item">Home</div>
    </div>
</div>
<div class="content">
    <div class="article">
        <div class="title">Hello</div>
    </div>
</div>

<!-- CORRECT -->
<header>
    <nav>
        <a href="/">Home</a>
    </nav>
</header>
<main>
    <article>
        <h1>Hello</h1>
    </article>
</main>
```

### Never: Clickable Divs

```html
<!-- WRONG -->
<div class="button" onclick="doSomething()">Click Me</div>
<div class="link" onclick="navigate('/page')">Go to Page</div>

<!-- CORRECT -->
<button type="button" onclick="doSomething()">Click Me</button>
<a href="/page">Go to Page</a>
```

### Never: Links for Actions

```html
<!-- WRONG - link that doesn't navigate -->
<a href="#" onclick="deleteItem(1); return false;">Delete</a>

<!-- CORRECT - button for action -->
<button type="button" onclick="deleteItem(1)">Delete</button>
```

### Never: Skipping Heading Levels

```html
<!-- WRONG -->
<h1>Page Title</h1>
<h4>Section</h4>  <!-- Skipped h2, h3 -->

<!-- CORRECT -->
<h1>Page Title</h1>
<h2>Section</h2>
```

## Architecture Anti-Patterns

### Never: Adding React/Vue/Svelte

This stack uses templ + Alpine. Adding a frontend framework contradicts the architecture. If you need client-side rendering, you're solving the wrong problem.

### Never: Build Tools for CSS/JS

No webpack, vite, or bundlers. Serve static files directly:

```go
mux.Handle("GET /static/", http.StripPrefix("/static/",
    http.FileServer(http.Dir("static"))))
```

### Never: Separate API + SPA

This is not a SPA architecture. The server renders HTML. Do not create separate `/api/*` routes returning JSON for UI consumption.

### Never: Over-Abstraction

```go
// WRONG - unnecessary abstraction
type UserRepository interface {
    GetAll() []User
    GetByID(id int) User
}

type userRepository struct {
    db *sql.DB
}

// CORRECT - sqlc generates what you need
// Just use db.GetUsers(), db.GetUser() directly
```

Keep it simple. sqlc generates the repository layer.
