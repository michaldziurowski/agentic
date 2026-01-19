// internal/db/time.go
package db

import (
	"database/sql/driver"
	"fmt"
	"time"
)

// Time wraps time.Time for SQLite RFC3339 text storage.
type Time struct {
	time.Time
}

func (t *Time) Scan(value interface{}) error {
	if value == nil {
		t.Time = time.Time{}
		return nil
	}
	s, ok := value.(string)
	if !ok {
		return fmt.Errorf("expected string, got %T", value)
	}
	parsed, err := time.Parse(time.RFC3339, s)
	if err != nil {
		return err
	}
	t.Time = parsed
	return nil
}

func (t Time) Value() (driver.Value, error) {
	if t.IsZero() {
		return nil, nil
	}
	return t.UTC().Format(time.RFC3339), nil
}

func Now() Time {
	return Time{time.Now().UTC()}
}
