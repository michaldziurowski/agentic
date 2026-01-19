# Examples

Complete patterns for common UI components.

## Login Form

### Template

```go
// templates/pages/login.templ
package pages

import "project/internal/templates/layouts"

templ Login(errorMsg string) {
    @layouts.Base("Login") {
        <article class="login-form">
            <h1>Sign In</h1>

            if errorMsg != "" {
                <div role="alert" class="error">
                    { errorMsg }
                </div>
            }

            <form method="post" action="/login">
                <label>
                    Email
                    <input
                        type="email"
                        name="email"
                        required
                        autocomplete="email"
                    />
                </label>

                <label>
                    Password
                    <input
                        type="password"
                        name="password"
                        required
                        autocomplete="current-password"
                    />
                </label>

                <button type="submit">Sign In</button>
            </form>

            <p>
                Don't have an account? <a href="/register">Sign up</a>
            </p>
        </article>
    }
}
```

### Handler

```go
func (h *Handler) Login(w http.ResponseWriter, r *http.Request) {
    if r.Method == http.MethodGet {
        pages.Login("").Render(r.Context(), w)
        return
    }

    email := r.FormValue("email")
    password := r.FormValue("password")

    user, err := h.db.AuthenticateUser(r.Context(), email, password)
    if err != nil {
        pages.Login("Invalid email or password").Render(r.Context(), w)
        return
    }

    // Set session, redirect
    h.sessions.Put(r.Context(), "user_id", user.ID)
    http.Redirect(w, r, "/", http.StatusSeeOther)
}
```

## Search with Live Results

### Template

```go
// templates/pages/users.templ
package pages

import "project/internal/templates/layouts"
import "project/internal/templates/components"
import "project/internal/db"

templ Users(users []db.User, query string) {
    @layouts.Base("Users") {
        <h1>Users</h1>

        <form x-init x-target="user-list" action="/users" method="get">
            <label>
                <span class="visually-hidden">Search users</span>
                <input
                    type="search"
                    name="q"
                    value={ query }
                    placeholder="Search by name..."
                    @input.debounce.300ms="$el.form.requestSubmit()"
                />
            </label>
        </form>

        <section aria-label="User list">
            @components.UserList(users)
        </section>
    }
}
```

```go
// templates/components/user_list.templ
package components

import "project/internal/db"

templ UserList(users []db.User) {
    <ul id="user-list" class="user-list">
        if len(users) == 0 {
            <li>No users found.</li>
        }
        for _, user := range users {
            <li>
                @UserCard(user)
            </li>
        }
    </ul>
}

templ UserCard(user db.User) {
    <article class="user-card">
        <h3>{ user.Name }</h3>
        <p>{ user.Email }</p>
    </article>
}
```

### Handler

```go
func (h *Handler) Users(w http.ResponseWriter, r *http.Request) {
    query := r.URL.Query().Get("q")

    var users []db.User
    if query != "" {
        users, _ = h.db.SearchUsers(r.Context(), "%"+query+"%")
    } else {
        users, _ = h.db.ListUsers(r.Context())
    }

    // Return partial for AJAX, full page otherwise
    if r.Header.Get("X-Alpine-Request") == "true" {
        components.UserList(users).Render(r.Context(), w)
        return
    }
    pages.Users(users, query).Render(r.Context(), w)
}
```

## Modal Dialog

Using native `<dialog>` with Alpine for control:

### Template

```go
templ DeleteButton(itemID int) {
    <div x-data="{ open: false }">
        <button type="button" @click="open = true">
            Delete
        </button>

        <dialog
            x-ref="dialog"
            x-effect="open ? $refs.dialog.showModal() : $refs.dialog.close()"
            @close="open = false"
        >
            <form method="dialog">
                <h2>Confirm Delete</h2>
                <p>Are you sure you want to delete this item?</p>

                <div class="dialog-actions">
                    <button type="submit" value="cancel">Cancel</button>
                    <button
                        type="submit"
                        value="confirm"
                        class="danger"
                        @click="deleteItem({ strconv.Itoa(itemID) })"
                    >
                        Delete
                    </button>
                </div>
            </form>
        </dialog>
    </div>
}
```

### CSS

```css
dialog {
    border: 1px solid #ccc;
    border-radius: 8px;
    padding: 1.5rem;
    max-width: 400px;
}

dialog::backdrop {
    background: rgba(0, 0, 0, 0.5);
}

.dialog-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 1rem;
}
```

## Navigation with Active State

### Template

```go
// templates/components/nav.templ
package components

type NavItem struct {
    Href  string
    Label string
}

var navItems = []NavItem{
    {Href: "/", Label: "Home"},
    {Href: "/users", Label: "Users"},
    {Href: "/settings", Label: "Settings"},
}

templ Nav(currentPath string) {
    <nav aria-label="Main navigation">
        <ul>
            for _, item := range navItems {
                <li>
                    <a
                        href={ templ.SafeURL(item.Href) }
                        class={ templ.KV("active", item.Href == currentPath) }
                        if item.Href == currentPath {
                            aria-current="page"
                        }
                    >
                        { item.Label }
                    </a>
                </li>
            }
        </ul>
    </nav>
}
```

### Layout Using Nav

```go
templ Base(title string, currentPath string) {
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8"/>
            <title>{ title }</title>
            <link rel="stylesheet" href="/static/css/style.css"/>
        </head>
        <body>
            <header>
                @Nav(currentPath)
            </header>
            <main>
                { children... }
            </main>
            <footer>
                <p>&copy; 2024</p>
            </footer>
            <script src="/static/js/alpine.min.js" defer></script>
            <script src="/static/js/ajax.min.js" defer></script>
        </body>
    </html>
}
```

## Infinite Scroll / Load More

### Template

```go
templ ItemList(items []Item, nextCursor string) {
    <ul id="items">
        for _, item := range items {
            <li>{ item.Name }</li>
        }

        if nextCursor != "" {
            <li>
                <button
                    x-init
                    x-target.append="items"
                    hx-get={ "/items?cursor=" + nextCursor }
                    @ajax:success="$el.remove()"
                >
                    Load More
                </button>
            </li>
        }
    </ul>
}
```

### Handler

```go
func (h *Handler) ListItems(w http.ResponseWriter, r *http.Request) {
    cursor := r.URL.Query().Get("cursor")
    items, nextCursor := h.db.GetItems(r.Context(), cursor, 20)

    components.ItemList(items, nextCursor).Render(r.Context(), w)
}
```

## Flash Messages

### Middleware

```go
func (h *Handler) Flash(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        msg := h.sessions.PopString(r.Context(), "flash")
        if msg != "" {
            ctx := context.WithValue(r.Context(), flashKey, msg)
            r = r.WithContext(ctx)
        }
        next.ServeHTTP(w, r)
    })
}
```

### Template

```go
templ FlashMessage(ctx context.Context) {
    if msg := ctx.Value(flashKey); msg != nil {
        <div role="alert" class="flash" x-data x-init="setTimeout(() => $el.remove(), 5000)">
            { msg.(string) }
        </div>
    }
}

templ Base(title string) {
    <!DOCTYPE html>
    <html lang="en">
        <head>...</head>
        <body>
            @FlashMessage(ctx)
            <header>...</header>
            <main>{ children... }</main>
        </body>
    </html>
}
```

### Setting Flash

```go
func (h *Handler) CreateItem(w http.ResponseWriter, r *http.Request) {
    // ... create item ...

    h.sessions.Put(r.Context(), "flash", "Item created successfully")
    http.Redirect(w, r, "/items", http.StatusSeeOther)
}
```
