# Alpine AJAX Patterns

Alpine AJAX enables server-driven partial page updates. The server returns HTML fragments that replace targeted elements.

## Setup

Include Alpine AJAX via CDN (preferred). Alpine AJAX must load before Alpine.js:

```html
<script defer src="https://cdn.jsdelivr.net/npm/@imacrayon/alpine-ajax@0.12.6/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.14.1/dist/cdn.min.js"></script>
```

The `defer` attribute ensures scripts load in order after DOM is ready.

## Core Concepts

### x-target Attribute

`x-target` specifies which element receives the server response:

```html
<form x-target="results" action="/search">
    <input type="search" name="q"/>
    <button>Search</button>
</form>

<div id="results">
    <!-- Server response replaces this content -->
</div>
```

### Critical: Server Response Must Include Matching ID

**The server response MUST contain an element with the same `id` that `x-target` points to.** Alpine AJAX finds the matching element in the response and uses it to replace the target. Without a matching ID, the replacement fails silently.

```html
<!-- Page has: -->
<ul id="comments">
    <li>Comment #1</li>
</ul>
<form x-target="comments" method="post" action="/comment">
    <input name="text" required/>
    <button>Submit</button>
</form>
```

```html
<!-- Server MUST respond with element that has id="comments": -->
<ul id="comments">
    <li>Comment #1</li>
    <li>New comment</li>
</ul>
```

```html
<!-- WRONG - response without matching ID (will not work): -->
<li>New comment</li>
```

### Target Modifiers

| Modifier | Behavior |
|----------|----------|
| `x-target="id"` | Replace inner content of target |
| `x-target.replace="id"` | Replace entire element |
| `x-target.append="id"` | Append response to target |
| `x-target.prepend="id"` | Prepend response to target |

## Form Patterns

### Basic Form Submission

Forms with `x-target` submit via AJAX automatically:

```html
<form x-target="messages" action="/messages" method="post">
    <input name="content" required/>
    <button>Send</button>
</form>

<ul id="messages">
    <!-- New messages appear here -->
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

### AJAX Link

```html
<a x-target="content" href="/page/2">Next Page</a>

<div id="content">
    <!-- Page content loaded here -->
</div>
```

### Navigation with Active State

Handle via server - return updated nav with active class:

```go
templ NavLink(href string, label string, current string) {
    <a
        x-target="main-content"
        href={ templ.SafeURL(href) }
        class={ templ.KV("active", href == current) }
    >
        { label }
    </a>
}
```

## Loading States

### Disable During Request

```html
<form x-target="results" action="/search">
    <button x-bind:disabled="$ajax.submitting">
        <span x-show="!$ajax.submitting">Search</span>
        <span x-show="$ajax.submitting">Loading...</span>
    </button>
</form>
```

### Loading Indicator

```html
<div x-data>
    <form x-target="results" action="/data">
        <button>Load Data</button>
    </form>

    <div id="results">
        <template x-if="$ajax.loading">
            <div class="loading">Loading...</div>
        </template>
    </div>
</div>
```

## Event Handling

### Available Events

| Event | When |
|-------|------|
| `ajax:before` | Before request is sent |
| `ajax:success` | Request completed successfully |
| `ajax:error` | Request failed |
| `ajax:after` | After request completes (success or error) |

### Example Usage

```html
<form
    x-target="results"
    action="/submit"
    method="post"
    @ajax:success="showNotification('Saved!')"
    @ajax:error="showNotification('Error occurred')"
>
    ...
</form>
```

## Server Response Patterns

### Return Partial HTML with Matching ID

The response must include an element with the same `id` as the `x-target`. Wrap the content in the target element:

```go
func handleSearch(w http.ResponseWriter, r *http.Request) {
    query := r.URL.Query().Get("q")
    results := search(query)
    templates.SearchResults(results).Render(r.Context(), w)
}
```

```go
// Response MUST include the target element with matching id
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

The page has `<div id="results">` and `x-target="results"`. The response contains `<div id="results">...</div>` which replaces the target.

### Multiple Targets

Server can return multiple elements; Alpine AJAX matches by ID:

```go
templ UpdateResponse(user User, stats Stats) {
    <div id="user-info">
        @UserCard(user)
    </div>
    <div id="stats">
        @StatsPanel(stats)
    </div>
}
```

```html
<button x-target="user-info stats" hx-get="/refresh">
    Refresh
</button>
```

## Server State vs Client State

Prefer server state. Use Alpine.js client state only for:

- UI-only concerns (dropdowns, modals open/close)
- Optimistic updates
- Form validation feedback

Everything else should come from the server.

### Client State Example

```html
<div x-data="{ open: false }">
    <button @click="open = !open">Menu</button>
    <nav x-show="open" @click.outside="open = false">
        <a href="/settings">Settings</a>
        <a href="/logout">Logout</a>
    </nav>
</div>
```

### Server State Example

User data, lists, counts - fetch from server:

```html
<div id="notifications">
    @NotificationList(notifications)
</div>

<button x-target="notifications" hx-get="/notifications">
    Refresh
</button>
```
