# templ Patterns

## Why templ

templ provides compile-time type safety that Go's `html/template` lacks:

- Type-checked parameters catch errors at build time
- IDE autocompletion for component props
- No runtime template parsing errors
- Automatic HTML escaping

## Layout Composition

Use `children...` to create composable layouts:

```go
// layouts/base.templ
package layouts

templ Base(title string) {
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
            <title>{ title }</title>
            <link rel="stylesheet" href="/static/css/style.css"/>
        </head>
        <body>
            @Header()
            <main>
                { children... }
            </main>
            @Footer()
            <script src="/static/js/alpine.min.js" defer></script>
            <script src="/static/js/ajax.min.js" defer></script>
        </body>
    </html>
}

templ Header() {
    <header>
        <nav>
            <a href="/">Home</a>
            <a href="/users">Users</a>
        </nav>
    </header>
}

templ Footer() {
    <footer>
        <p>&copy; 2024</p>
    </footer>
}
```

## Page Templates

Pages use layouts and compose components:

```go
// pages/home.templ
package pages

import "project/internal/templates/layouts"
import "project/internal/templates/components"

type HomeData struct {
    Title    string
    Users    []User
    Message  string
}

templ Home(data HomeData) {
    @layouts.Base(data.Title) {
        <h1>Welcome</h1>
        if data.Message != "" {
            <p class="message">{ data.Message }</p>
        }
        <section>
            <h2>Recent Users</h2>
            @components.UserList(data.Users)
        </section>
    }
}
```

## Component Patterns

### Simple Components (Explicit Parameters)

For components with few props, use explicit parameters:

```go
templ Button(label string, variant string) {
    <button class={ "btn", "btn-" + variant }>
        { label }
    </button>
}

// Usage
@Button("Submit", "primary")
```

### Complex Components (Struct Props)

For components with many props, use a struct:

```go
type CardProps struct {
    Title       string
    Description string
    ImageURL    string
    Link        string
}

templ Card(props CardProps) {
    <article class="card">
        if props.ImageURL != "" {
            <img src={ props.ImageURL } alt=""/>
        }
        <h3>{ props.Title }</h3>
        <p>{ props.Description }</p>
        if props.Link != "" {
            <a href={ templ.SafeURL(props.Link) }>Read more</a>
        }
    </article>
}
```

### List Components

Iterate over slices directly:

```go
templ UserList(users []User) {
    if len(users) == 0 {
        <p>No users found.</p>
    } else {
        <ul class="user-list">
            for _, user := range users {
                <li>@UserCard(user)</li>
            }
        </ul>
    }
}

templ UserCard(user User) {
    <article class="user-card">
        <h3>{ user.Name }</h3>
        <p>{ user.Email }</p>
    </article>
}
```

## Partial Templates for AJAX

Create standalone partials that handlers can render for AJAX requests:

```go
// components/user_list.templ

// Full section with heading (for full page loads)
templ UserSection(users []User) {
    <section id="users">
        <h2>Users</h2>
        @UserList(users)
    </section>
}

// Just the list (for AJAX updates)
templ UserList(users []User) {
    <div id="user-list">
        for _, user := range users {
            @UserCard(user)
        }
    </div>
}
```

Handler returns partial or full based on request:

```go
func (h *Handler) ListUsers(w http.ResponseWriter, r *http.Request) {
    users := h.db.GetUsers(r.Context())

    if isAJAX(r) {
        components.UserList(users).Render(r.Context(), w)
        return
    }
    pages.UsersPage(users).Render(r.Context(), w)
}

func isAJAX(r *http.Request) bool {
    return r.Header.Get("X-Alpine-Request") == "true"
}
```

## Conditional Classes

Use templ's class helper for conditional classes:

```go
templ NavLink(href string, label string, active bool) {
    <a
        href={ templ.SafeURL(href) }
        class={ "nav-link", templ.KV("active", active) }
    >
        { label }
    </a>
}
```

## Attributes from Maps

Pass dynamic attributes:

```go
templ Input(attrs templ.Attributes) {
    <input { attrs... }/>
}

// Usage
@Input(templ.Attributes{
    "type":        "email",
    "name":        "email",
    "required":    true,
    "placeholder": "Enter email",
})
```

## Common Gotchas

### Raw HTML

Use `@templ.Raw()` sparingly and only for trusted content:

```go
// Only for content you control
templ RichContent(html string) {
    <div class="content">
        @templ.Raw(html)
    </div>
}
```

### URLs

Always use `templ.SafeURL()` for dynamic URLs:

```go
<a href={ templ.SafeURL(user.ProfileURL) }>Profile</a>
```

### Script Content

Use `templ.JSExpression()` for inline JavaScript:

```go
<button onclick={ templ.JSExpression("handleClick(" + strconv.Itoa(id) + ")") }>
    Click
</button>
```

### Whitespace

templ strips whitespace. Use explicit spaces:

```go
// Won't have space between spans
<span>Hello</span><span>World</span>

// Add explicit space
<span>Hello</span>{ " " }<span>World</span>
```
