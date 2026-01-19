# Semantic HTML

Every element must convey meaning. Using `<div>` when a semantic element exists is incorrect.

## Document Landmarks

Every page requires these landmarks:

```html
<body>
    <header>
        <!-- Site header, logo, primary navigation -->
    </header>

    <main>
        <!-- Primary content, one per page -->
    </main>

    <footer>
        <!-- Site footer, secondary links, copyright -->
    </footer>
</body>
```

### Heading Hierarchy

Start with `<h1>`, increment sequentially. Never skip levels.

```html
<h1>Page Title</h1>
    <h2>Section</h2>
        <h3>Subsection</h3>
    <h2>Another Section</h2>
```

Wrong:
```html
<h1>Title</h1>
<h3>Section</h3>  <!-- Skipped h2 -->
```

## Sectioning Elements

| Element | Use When |
|---------|----------|
| `<article>` | Self-contained content that could stand alone (blog post, product card, comment) |
| `<section>` | Thematic grouping with a heading |
| `<nav>` | Navigation links |
| `<aside>` | Tangentially related content (sidebar, pull quote) |
| `<header>` | Introductory content for its parent |
| `<footer>` | Footer content for its parent |

### When to Use section vs div

`<section>` requires a heading. Use `<div>` only for styling hooks with no semantic meaning.

```html
<!-- Correct: section has heading -->
<section>
    <h2>Features</h2>
    <ul>...</ul>
</section>

<!-- Correct: div for styling only -->
<div class="grid">
    <article>...</article>
    <article>...</article>
</div>

<!-- Wrong: section without heading -->
<section class="grid">
    <article>...</article>
</section>
```

## Interactive Elements

### Buttons vs Links

| Element | Use When |
|---------|----------|
| `<button>` | Triggers an action (submit, toggle, open modal) |
| `<a>` | Navigates to a URL |

```html
<!-- Correct -->
<button type="button" @click="openModal()">Open Settings</button>
<a href="/settings">Go to Settings</a>

<!-- Wrong -->
<a href="#" @click="openModal()">Open Settings</a>
<div class="button" @click="submit()">Submit</div>
```

### Button Types

Always specify type:

| Type | Use When |
|------|----------|
| `type="submit"` | Submits a form (default) |
| `type="button"` | Action that doesn't submit |
| `type="reset"` | Resets form fields |

### Input Types

Use specific types for validation and mobile keyboards:

| Type | Use When |
|------|----------|
| `email` | Email addresses |
| `tel` | Phone numbers |
| `url` | URLs |
| `number` | Numeric input |
| `date` | Date selection |
| `search` | Search queries |
| `password` | Passwords |

## List Elements

| Element | Use When |
|---------|----------|
| `<ul>` | Unordered list (order doesn't matter) |
| `<ol>` | Ordered list (sequence matters) |
| `<dl>` | Description list (term-definition pairs) |
| `<menu>` | List of commands/actions |

```html
<!-- Navigation menu -->
<nav>
    <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/about">About</a></li>
    </ul>
</nav>

<!-- Steps (order matters) -->
<ol>
    <li>Sign up</li>
    <li>Verify email</li>
    <li>Complete profile</li>
</ol>

<!-- Key-value pairs -->
<dl>
    <dt>Name</dt>
    <dd>John Doe</dd>
    <dt>Email</dt>
    <dd>john@example.com</dd>
</dl>
```

## Form Patterns

### Labels

Every input needs a label. Use `for` attribute or wrap:

```html
<!-- Explicit association -->
<label for="email">Email</label>
<input id="email" type="email" name="email"/>

<!-- Implicit association -->
<label>
    Email
    <input type="email" name="email"/>
</label>
```

### Fieldsets

Group related inputs:

```html
<fieldset>
    <legend>Shipping Address</legend>
    <label>Street <input name="street"/></label>
    <label>City <input name="city"/></label>
</fieldset>
```

### Required and Validation

Use native attributes:

```html
<input
    type="email"
    name="email"
    required
    pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"
    title="Enter a valid email"
/>
```

## Text Elements

| Element | Use When |
|---------|----------|
| `<p>` | Paragraph of text |
| `<strong>` | Important text |
| `<em>` | Emphasized text |
| `<mark>` | Highlighted/relevant text |
| `<code>` | Inline code |
| `<pre>` | Preformatted text |
| `<blockquote>` | Extended quotation |
| `<cite>` | Title of a work |
| `<time>` | Date/time |
| `<address>` | Contact information |

```html
<article>
    <h2>Meeting Notes</h2>
    <p>Published <time datetime="2024-01-15">January 15, 2024</time></p>
    <p>The team discussed <strong>critical</strong> updates.</p>
    <blockquote>
        <p>We need to ship by Friday.</p>
        <cite>Project Manager</cite>
    </blockquote>
</article>
```

## Tables

Use tables for tabular data only, never for layout:

```html
<table>
    <caption>User Statistics</caption>
    <thead>
        <tr>
            <th scope="col">Name</th>
            <th scope="col">Role</th>
            <th scope="col">Status</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>John</td>
            <td>Admin</td>
            <td>Active</td>
        </tr>
    </tbody>
</table>
```

## ARIA (Use Sparingly)

Semantic HTML is preferred. Use ARIA only when HTML lacks the semantics:

```html
<!-- Native is better -->
<button>Submit</button>

<!-- ARIA only when needed -->
<div role="alert">Error: Invalid input</div>
<div aria-live="polite" id="status">Loading...</div>
```

Common ARIA attributes:
- `aria-label`: Label when visible text is insufficient
- `aria-describedby`: Reference to descriptive text
- `aria-live`: Announce dynamic content changes
- `role`: Define element's purpose when HTML element doesn't convey it
