# Alpine AJAX Patterns

Alpine AJAX turns server-rendered pages into an SPA-like experience. Forms submit, content updates, and navigation happen through partial HTML replacement — no full page reloads, no JSON APIs, no client-side rendering.

The goal is that every user interaction feels instant. Full page reloads should be the rare exception, not the default. Use `x-target` on forms and links so the server swaps just the relevant fragment.

## Setup

Include Alpine AJAX via CDN. Alpine AJAX must load before Alpine.js:

```html
<script defer src="https://cdn.jsdelivr.net/npm/@imacrayon/alpine-ajax@0.12.7/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"></script>
```

The `defer` attribute ensures scripts load in order after DOM is ready.

## Core Concepts

### x-target

`x-target` specifies which element receives the server response. Add it to a form or link:

```html
<form x-target="results" action="/search">
    <input type="search" name="q"/>
    <button>Search</button>
</form>

<div id="results">
    <!-- Server response replaces this element -->
</div>
```

The server response must contain an element with the same `id` that `x-target` points to. Alpine AJAX finds the matching element in the response and uses it to replace the target on the page. Without a matching ID, the replacement fails silently.

```go
// Server MUST respond with element that has id="results"
templ SearchResults(results []Result) {
    <div id="results">
        if len(results) == 0 {
            <p>No results found.</p>
        } else {
            <ul>
                for _, r := range results {
                    <li>{ r.Title }</li>
                }
            </ul>
        }
    </div>
}
```

### Self-Targeting

When a form or link targets itself, leave `x-target` empty (the element must have an `id`):

```html
<form x-target id="star_repo" method="post" action="/repos/1/star">
    <button>Star Repository</button>
</form>
```

### Target Aliases

When the target `id` on the page differs from the `id` in the server response, use a colon to map them:

```html
<!-- Replace #modal_body with #page_body from the response -->
<a x-target="modal_body:page_body" href="/load">Load into modal</a>
<div id="modal_body"></div>
```

### x-target Modifiers

**History:**

| Modifier | Purpose |
|----------|---------|
| `.push` | Push URL to browser history (enables back/forward navigation) |
| `.replace` | Replace URL in browser history (replaceState, no new history entry) |

**Focus:**

| Modifier | Purpose |
|----------|---------|
| `.nofocus` | Disable autofocus behavior after content update |

**Status code targeting** — define different targets based on response status:

| Modifier | When |
|----------|------|
| `.422` | Response has 422 status code |
| `.4xx` | Response has any 400-class status code |
| `.error` | Response has any 400 or 500-class status code |
| `.back` | Response is redirected back to the same page |
| `.away` | Response is redirected to a different page |

```html
<!-- SPA-style navigation: update content and URL -->
<a x-target.push="main-content" href="/dashboard">Dashboard</a>

<!-- Form: show validation errors in-place, full page redirect on success -->
<form x-target="login" x-target.away="_top" id="login" method="post" action="/login">
    <input type="email" name="email"/>
    <button>Log in</button>
</form>
```

### x-merge: Controlling How Content Updates

By default, `x-target` replaces the entire target element. Use `x-merge` on the **target element** (the one receiving content) to change this:

| `x-merge` value | Behavior |
|-----------------|----------|
| `"replace"` (default) | Replace entire target element |
| `"update"` | Replace inner HTML only |
| `"prepend"` | Prepend response content inside target |
| `"append"` | Append response content inside target |
| `"before"` | Insert content of response before target |
| `"after"` | Insert content of response after target |
| `"morph"` | Morph target into response, preserving Alpine state (requires Alpine Morph Plugin) |

**Morph** requires the [Alpine Morph Plugin](https://alpinejs.dev/plugins/morph) loaded **before** Alpine AJAX:

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/morph@3.14.1/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/@imacrayon/alpine-ajax@0.12.7/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"></script>
```

Use `x-merge.transition` to animate merges via the View Transitions API (progressive — falls back to no animation in unsupported browsers).

```html
<!-- New messages get appended to the list -->
<ul id="messages" x-merge="append">
    <li>Message #1</li>
</ul>
<form x-target="messages" method="post" action="/messages">
    <input name="content" required/>
    <button>Send</button>
</form>
```

## Form Patterns

### Basic Form Submission

Forms with `x-target` submit via AJAX automatically:

```html
<form x-target="messages" action="/messages" method="post">
    <input name="content" required/>
    <button>Send</button>
</form>

<ul id="messages">
    <!-- Updated messages appear here -->
</ul>
```

### Form with Reset on Success

```html
<form
    x-target="items"
    action="/items"
    method="post"
    @ajax:success="$el.reset()"
>
    <input name="title" required/>
    <button>Add Item</button>
</form>
```

### Search with Debounce

```html
<form x-target="results" action="/search">
    <input
        type="search"
        name="q"
        @input.debounce.300ms="$el.form.requestSubmit()"
    />
</form>

<div id="results"></div>
```

## Link Patterns

### AJAX Navigation

Links with `x-target` fetch content without a full page reload. Use `.push` to update the URL so back/forward buttons work — this is what makes the app feel like an SPA:

```html
<nav>
    <a x-target.push="main-content" href="/dashboard">Dashboard</a>
    <a x-target.push="main-content" href="/settings">Settings</a>
</nav>
<main id="main-content">
    <!-- Content swapped here, URL updates in address bar -->
</main>
```

### Navigation with Active State

Handle via server — return updated nav with active class:

```go
templ NavLink(href string, label string, current string) {
    <a
        x-target.push="main-content"
        href={ templ.SafeURL(href) }
        class={ templ.KV("active", href == current) }
    >
        { label }
    </a>
}
```

## Loading States

Alpine AJAX automatically manages loading states:

- **Target elements** get `aria-busy="true"` during requests
- **Submit buttons** are automatically `disabled` during submission (prevents double-clicks)

Style these with CSS:

```css
[aria-busy="true"] {
    opacity: 0.6;
}

button:disabled {
    opacity: 0.6;
    pointer-events: none;
}
```

### Loading Spinner via CSS

```css
[aria-busy="true"] {
    position: relative;
}

[aria-busy="true"]::after {
    content: "";
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.7);
}
```

## Events

| Event | When | Cancelable |
|-------|------|------------|
| `ajax:before` | Before request is sent | Yes |
| `ajax:send` | Request issued (`detail` has fetch options) | No |
| `ajax:redirect` | 300-class redirect response (`detail` has response) | No |
| `ajax:success` | 200 or 300-class response (`detail` has response) | No |
| `ajax:error` | 400/500-class response (`detail` has response) | No |
| `ajax:sent` | After request receives any response | No |
| `ajax:missing` | Target not found in response | Yes |
| `ajax:merge` | Before content merge (`detail` has `content`, `merge()`) | Yes |
| `ajax:merged` | After merge complete (fires on merged element) | No |
| `ajax:after` | All merging settled (`detail` has `render` array of targets) | No |

### Example Usage

```html
<form
    x-target="results"
    action="/submit"
    method="post"
    @ajax:success="$el.reset()"
    @ajax:error="alert('Something went wrong')"
>
    ...
</form>
```

## Additional Directives

### x-sync: Update Elements Outside the Target

`x-sync` marks an element that should be updated whenever the server response includes a matching element, even if it isn't targeted with `x-target`. The `x-sync` element must have a unique `id` — the element itself gets replaced when the server sends a matching `id`.

Useful for notification counts, flash messages, or other global UI that changes as a side effect of other actions:

```html
<ul x-sync id="notifications">
    <!-- Replaced on any AJAX response that includes id="notifications" -->
</ul>

<div id="content">
    <!-- Main content targeted by x-target -->
</div>
```

Any server response that includes an element with `id="notifications"` will replace this list, regardless of what `x-target` was set to.

### x-headers: Custom Request Headers

Add custom headers to AJAX requests (useful for CSRF tokens):

```html
<meta name="csrf-token" content="abc123"/>
<body x-headers='{ "X-CSRF-Token": document.querySelector("meta[name=csrf-token]").content }'>
    ...
</body>
```

### x-autofocus: Restore Focus After Content Updates

`x-autofocus` restores keyboard focus when AJAX replaces the element the user was focused on. Important for accessibility in inline editing and toggle patterns:

```html
<input type="email" name="email" x-autofocus/>
```

The standard `autofocus` attribute also works, but `x-autofocus` takes precedence when both are present. Alternatively, `x-merge="morph"` preserves focus too, but `x-autofocus` is more predictable when the DOM changes significantly.

Disable autofocus on a specific request with `x-target.nofocus` (useful when handing focus to a dialog or third-party script).

### Disabling AJAX on Specific Elements

Use special targets or `formnoajax` to opt out of AJAX:

```html
<!-- Full page reload via special target _top -->
<a x-target="_top" href="/logout">Logout</a>

<!-- Do nothing (suppress AJAX without navigating) -->
<a x-target="_none" href="/preview">Preview</a>

<!-- Normal form submission for a specific button -->
<button type="submit" formnoajax>Download PDF</button>
```

Special target values:
- `_top` — triggers a full page reload
- `_none` — does nothing (suppresses the request)

## Multiple Targets

Target multiple elements by space-separating IDs. The server response must include all matching elements:

```html
<a x-target="user-info stats" href="/refresh">Refresh</a>
```

```go
templ RefreshResponse(user User, stats Stats) {
    <div id="user-info">
        @UserCard(user)
    </div>
    <div id="stats">
        @StatsPanel(stats)
    </div>
}
```

## Detecting AJAX Requests on the Server

Alpine AJAX sends two headers on every request:
- `X-Alpine-Request: true` — the request came from Alpine AJAX
- `X-Alpine-Target: <ids>` — space-separated target IDs

Use these to return partial HTML for AJAX and full pages for direct navigation:

```go
func isAJAX(r *http.Request) bool {
    return r.Header.Get("X-Alpine-Request") == "true"
}

func (h *Handlers) ListUsers(w http.ResponseWriter, r *http.Request) {
    users, _ := h.queries.ListUsers(r.Context())

    if isAJAX(r) {
        components.UserList(users).Render(r.Context(), w)
        return
    }
    pages.UsersPage(users).Render(r.Context(), w)
}
```

## Server State vs Client State

Prefer server state. Use Alpine.js client state only for:

- UI-only concerns (dropdowns, modals open/close)
- Optimistic updates
- Form validation feedback

Everything else should come from the server via Alpine AJAX.

### Client State Example

```html
<div x-data="{ open: false }">
    <button @click="open = !open">Menu</button>
    <nav x-show="open" @click.outside="open = false">
        <a href="/settings">Settings</a>
        <a x-target="_top" href="/logout">Logout</a>
    </nav>
</div>
```

### Server State Example

```html
<div id="notifications">
    @NotificationList(notifications)
</div>

<a x-target="notifications" href="/notifications">Refresh</a>
```
