# Handler Patterns

## Handler Dependencies

```go
type Handlers struct {
    queries *db.Queries
    logger  *slog.Logger
}

func NewHandlers(queries *db.Queries, logger *slog.Logger) *Handlers {
    return &Handlers{queries: queries, logger: logger}
}
```

## Basic Handler Structure

```go
func (h *Handlers) ShowUser(w http.ResponseWriter, r *http.Request) {
    id, err := strconv.Atoi(r.PathValue("id"))
    if err != nil {
        http.Error(w, "invalid id", http.StatusBadRequest)
        return
    }

    user, err := h.queries.GetUser(r.Context(), int64(id))
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            http.NotFound(w, r)
            return
        }
        h.serverError(w, err)
        return
    }

    templates.UserPage(user).Render(r.Context(), w)
}
```

## Routing (Go 1.22+)

```go
mux := http.NewServeMux()

// Static files
mux.Handle("GET /static/", http.StripPrefix("/static/", http.FileServer(http.Dir("static"))))

// Pages
mux.HandleFunc("GET /", h.Home)
mux.HandleFunc("GET /users", h.ListUsers)
mux.HandleFunc("GET /users/{id}", h.ShowUser)

// Forms
mux.HandleFunc("GET /users/new", h.NewUserForm)
mux.HandleFunc("POST /users", h.CreateUser)
mux.HandleFunc("GET /users/{id}/edit", h.EditUserForm)
mux.HandleFunc("POST /users/{id}", h.UpdateUser)
mux.HandleFunc("POST /users/{id}/delete", h.DeleteUser)
```

## Form Handling

```go
func (h *Handlers) CreateUser(w http.ResponseWriter, r *http.Request) {
    if err := r.ParseForm(); err != nil {
        http.Error(w, "bad request", http.StatusBadRequest)
        return
    }

    name := strings.TrimSpace(r.FormValue("name"))
    email := strings.TrimSpace(r.FormValue("email"))

    // Validate
    var errors []string
    if name == "" {
        errors = append(errors, "name is required")
    }
    if email == "" {
        errors = append(errors, "email is required")
    }

    if len(errors) > 0 {
        templates.NewUserForm(name, email, errors).Render(r.Context(), w)
        return
    }

    // Create
    user, err := h.queries.CreateUser(r.Context(), db.CreateUserParams{
        Name:  name,
        Email: email,
    })
    if err != nil {
        h.serverError(w, err)
        return
    }

    http.Redirect(w, r, fmt.Sprintf("/users/%d", user.ID), http.StatusSeeOther)
}
```

## Error Helpers

```go
func (h *Handlers) serverError(w http.ResponseWriter, err error) {
    h.logger.Error("server error", "error", err)
    http.Error(w, "internal server error", http.StatusInternalServerError)
}
```

## Middleware

```go
func LogRequests(logger *slog.Logger) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            logger.Info("request", "method", r.Method, "path", r.URL.Path)
            next.ServeHTTP(w, r)
        })
    }
}

// Usage
handler := LogRequests(logger)(mux)
```

## Alpine AJAX Partial Responses

When a request comes from Alpine AJAX, return just the fragment:

```go
func (h *Handlers) ListComments(w http.ResponseWriter, r *http.Request) {
    comments, err := h.queries.ListComments(r.Context())
    if err != nil {
        h.serverError(w, err)
        return
    }

    // Check if this is an AJAX request
    if r.Header.Get("X-Alpine-Request") == "true" {
        templates.CommentsList(comments).Render(r.Context(), w)
        return
    }

    // Full page render
    templates.CommentsPage(comments).Render(r.Context(), w)
}
```

## When to Extract Services

**Keep in handlers:**
- Simple flows (get data, render)
- Basic validation
- Single query operations

**Extract to services:**
- Multi-step transactions
- Logic reused across handlers
- Complex domain rules
- Logic that benefits from isolated testing

### Service Pattern

```
Handler → Service → Queries
```

```go
// internal/services/orders.go
type OrderService struct {
    queries *db.Queries
}

func NewOrderService(queries *db.Queries) *OrderService {
    return &OrderService{queries: queries}
}

func (s *OrderService) PlaceOrder(ctx context.Context, userID int64, items []OrderItem) (*db.Order, error) {
    // Complex logic: validate inventory, calculate totals, create order + line items
}
```

```go
// internal/handlers/orders.go
func (h *Handlers) CreateOrder(w http.ResponseWriter, r *http.Request) {
    // Parse and validate input
    items := parseOrderItems(r)

    order, err := h.orderService.PlaceOrder(r.Context(), userID, items)
    if err != nil {
        // Handle error
    }

    http.Redirect(w, r, fmt.Sprintf("/orders/%d", order.ID), http.StatusSeeOther)
}
```
