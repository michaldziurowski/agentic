#!/usr/bin/env bash
# Builds three template git repos used as eval fixtures for the dz-commit skill.
# Usage: make_fixtures.sh <template-dir>
set -euo pipefail

TPL="$1"
rm -rf "$TPL"
mkdir -p "$TPL"

git_init() {
    git init -q -b main "$1"
    git -C "$1" config user.name "Dev"
    git -C "$1" config user.email "dev@example.com"
}

commit() { git -C "$1" add -A && git -C "$1" commit -q -m "$2"; }

################################################################################
# Fixture A: mixed-concern working tree (plain lowercase house style)
#   Ideal: 3 commits — feature (2 files), bugfix (1 file), typo (1 file)
################################################################################
A="$TPL/mixed-concerns"
git_init "$A"
mkdir -p "$A/cmd" "$A/internal/store"

cat > "$A/go.mod" <<'EOF'
module github.com/example/tracker

go 1.22
EOF

cat > "$A/README.md" <<'EOF'
# tracker

A small command line tool for tracking time entries.

## Usage

    tracker add "writing docs" 45m
    tracker list

Entries are stored in a local SQLite databse under ~/.tracker.
EOF

cat > "$A/internal/store/store.go" <<'EOF'
package store

import "database/sql"

type Entry struct {
	ID    int64
	Note  string
	Mins  int
}

type Store struct {
	db *sql.DB
}

func New(db *sql.DB) *Store {
	return &Store{db: db}
}

func (s *Store) List() ([]Entry, error) {
	rows, err := s.db.Query("SELECT id, note, mins FROM entries ORDER BY id")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []Entry
	for rows.Next() {
		var e Entry
		if err := rows.Scan(&e.ID, &e.Note, &e.Mins); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, nil
}
EOF

cat > "$A/cmd/root.go" <<'EOF'
package cmd

import (
	"fmt"
	"os"
)

func Run(args []string) int {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: tracker <add|list>")
		return 1
	}

	switch args[1] {
	case "add":
		return runAdd(args[2:])
	case "list":
		return runList()
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n", args[1])
		return 1
	}
}
EOF

README_A="$(cat "$A/README.md")"
rm "$A/README.md" "$A/internal/store/store.go"
commit "$A" "skeleton cli with add and list subcommands"

mkdir -p "$A/internal/store"
cat > "$A/internal/store/store.go" <<'EOF'
package store

import "database/sql"

type Entry struct {
	ID    int64
	Note  string
	Mins  int
}

type Store struct {
	db *sql.DB
}

func New(db *sql.DB) *Store {
	return &Store{db: db}
}

func (s *Store) List() ([]Entry, error) {
	rows, err := s.db.Query("SELECT id, note, mins FROM entries ORDER BY id")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []Entry
	for rows.Next() {
		var e Entry
		if err := rows.Scan(&e.ID, &e.Note, &e.Mins); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, nil
}
EOF
commit "$A" "store: back list with a sqlite query"

printf '%s\n' "$README_A" > "$A/README.md"
commit "$A" "readme: document usage and storage location"

# --- uncommitted work: three unrelated concerns ---

# (1) feature: csv export — new package + wiring in root.go
mkdir -p "$A/internal/export"
cat > "$A/internal/export/csv.go" <<'EOF'
package export

import (
	"encoding/csv"
	"io"
	"strconv"

	"github.com/example/tracker/internal/store"
)

// CSV writes entries as comma separated values with a header row.
func CSV(w io.Writer, entries []store.Entry) error {
	cw := csv.NewWriter(w)
	if err := cw.Write([]string{"id", "note", "minutes"}); err != nil {
		return err
	}
	for _, e := range entries {
		row := []string{strconv.FormatInt(e.ID, 10), e.Note, strconv.Itoa(e.Mins)}
		if err := cw.Write(row); err != nil {
			return err
		}
	}
	cw.Flush()
	return cw.Error()
}
EOF

cat > "$A/cmd/root.go" <<'EOF'
package cmd

import (
	"fmt"
	"os"
)

func Run(args []string) int {
	if len(args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: tracker <add|list|export>")
		return 1
	}

	switch args[1] {
	case "add":
		return runAdd(args[2:])
	case "list":
		return runList()
	case "export":
		return runExport()
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n", args[1])
		return 1
	}
}
EOF

# (2) bugfix: rows.Err() was never checked, so a truncated result set looked empty
cat > "$A/internal/store/store.go" <<'EOF'
package store

import "database/sql"

type Entry struct {
	ID    int64
	Note  string
	Mins  int
}

type Store struct {
	db *sql.DB
}

func New(db *sql.DB) *Store {
	return &Store{db: db}
}

func (s *Store) List() ([]Entry, error) {
	rows, err := s.db.Query("SELECT id, note, mins FROM entries ORDER BY id")
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []Entry
	for rows.Next() {
		var e Entry
		if err := rows.Scan(&e.ID, &e.Note, &e.Mins); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}
EOF

# (3) docs: typo fix
sed -i 's/databse/database/' "$A/README.md"

################################################################################
# Fixture B: one file, two unrelated changes (needs hunk-level splitting)
################################################################################
B="$TPL/two-in-one-file"
git_init "$B"

cat > "$B/config.py" <<'EOF'
"""Configuration loading for the report generator."""

import json
import os

DEFAULT_TIMEOUT = 30


class Config:
    def __init__(self, path):
        self.path = path
        self._data = None

    def load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError("config file not found: %s" % self.path)
        with open(self.path) as fh:
            self._data = json.load(fh)
        return self._data

    def get(self, key, default=None):
        if self._data is None:
            self.load()
        return self._data.get(key, default)

    def timeout(self):
        return self.get("timeout", DEFAULT_TIMEOUT)

    def output_dir(self):
        return self.get("output_dir", "./out")

    def describe(self):
        return "Config(path=%s, keys=%d)" % (self.path, len(self._data or {}))
EOF

cat > "$B/README.md" <<'EOF'
# report-gen

Generates weekly reports from a JSON config.
EOF

commit "$B" "initial commit"

# --- uncommitted work: two unrelated changes in the same file ---
#   (1) raise the default timeout, which was too low for the slow upstream API
#   (2) expand ~ in output_dir, which was creating a literal "~" directory
cat > "$B/config.py" <<'EOF'
"""Configuration loading for the report generator."""

import json
import os

DEFAULT_TIMEOUT = 120


class Config:
    def __init__(self, path):
        self.path = path
        self._data = None

    def load(self):
        if not os.path.exists(self.path):
            raise FileNotFoundError("config file not found: %s" % self.path)
        with open(self.path) as fh:
            self._data = json.load(fh)
        return self._data

    def get(self, key, default=None):
        if self._data is None:
            self.load()
        return self._data.get(key, default)

    def timeout(self):
        return self.get("timeout", DEFAULT_TIMEOUT)

    def output_dir(self):
        return os.path.expanduser(self.get("output_dir", "./out"))

    def describe(self):
        return "Config(path=%s, keys=%d)" % (self.path, len(self._data or {}))
EOF

################################################################################
# Fixture C: one coherent change, Conventional Commits house style
#   Ideal: 1 commit, subject matching feat(scope): style
################################################################################
C="$TPL/single-change-conventional"
git_init "$C"
mkdir -p "$C/api"

cat > "$C/api/rates.js" <<'EOF'
const RATES = new Map();

function setRate(currency, value) {
  RATES.set(currency.toUpperCase(), value);
}

function convert(amount, from, to) {
  const fromRate = RATES.get(from.toUpperCase());
  const toRate = RATES.get(to.toUpperCase());
  return (amount / fromRate) * toRate;
}

module.exports = { setRate, convert };
EOF

cat > "$C/api/rates.test.js" <<'EOF'
const { setRate, convert } = require('./rates');

test('converts between two known currencies', () => {
  setRate('USD', 1);
  setRate('EUR', 0.5);
  expect(convert(10, 'USD', 'EUR')).toBe(5);
});
EOF

git -C "$C" add -A
git -C "$C" commit -q -m "feat(api): add currency conversion helper"

cat > "$C/api/rates.js" <<'EOF'
const RATES = new Map();

function setRate(currency, value) {
  RATES.set(currency.toUpperCase(), value);
}

function convert(amount, from, to) {
  const fromRate = RATES.get(from.toUpperCase());
  const toRate = RATES.get(to.toUpperCase());
  if (fromRate === undefined || toRate === undefined) {
    throw new Error(`unknown currency: ${fromRate === undefined ? from : to}`);
  }
  return (amount / fromRate) * toRate;
}

module.exports = { setRate, convert };
EOF
git -C "$C" add -A
git -C "$C" commit -q -m "fix(api): reject unknown currency codes"

cat > "$C/README.md" <<'EOF'
# rates

Currency conversion helpers.
EOF
git -C "$C" add -A
git -C "$C" commit -q -m "docs(readme): describe the rates module"

# --- uncommitted work: one coherent change (feature + its test) ---
cat > "$C/api/rates.js" <<'EOF'
const RATES = new Map();

function setRate(currency, value) {
  RATES.set(currency.toUpperCase(), value);
}

function convert(amount, from, to) {
  const fromRate = RATES.get(from.toUpperCase());
  const toRate = RATES.get(to.toUpperCase());
  if (fromRate === undefined || toRate === undefined) {
    throw new Error(`unknown currency: ${fromRate === undefined ? from : to}`);
  }
  return (amount / fromRate) * toRate;
}

function convertAll(amounts, from, to) {
  return amounts.map((amount) => convert(amount, from, to));
}

module.exports = { setRate, convert, convertAll };
EOF

cat >> "$C/api/rates.test.js" <<'EOF'

test('converts a batch of amounts', () => {
  setRate('USD', 1);
  setRate('EUR', 0.5);
  expect(convertAll([10, 20], 'USD', 'EUR')).toEqual([5, 10]);
});
EOF

echo "templates built in $TPL"
for d in "$A" "$B" "$C"; do
    echo "--- $(basename "$d")"
    git -C "$d" status --porcelain
done
