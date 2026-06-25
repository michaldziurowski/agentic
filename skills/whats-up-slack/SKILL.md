---
name: whats-up-slack
description: |
  Catch up on Slack activity since the last run and route the content directly into the vault —
  no intermediate digest file. Reads channels, threads, and DMs since the last run; classifies
  each item by content (decision, action item, blocker, etc.) to the right project's log.md, or
  to a per-action file in actions/. Routing is content-based, with a soft prior from the
  channel's owning project. Surfaces low-confidence
  items in terminal output without writing them. Must be invoked from the vault root. Tracks last
  run time in .whats-up-slack.idx; if no prior run exists, asks the user for a start date.
  Use this skill whenever the user asks for a Slack summary, daily digest, catch-up on Slack,
  "what did I miss", "what's going on", "whats up", or wants to review recent activity.
  Also trigger when the user mentions summarizing channels, catching up on messages, or
  checking what happened while they were away.
allowed-tools:
  - AskUserQuestion
  - Bash
  - Read
  - Write
  - Edit
  - Agent
  - mcp__plugin_slack_slack__slack_read_channel
  - mcp__plugin_slack_slack__slack_read_thread
  - mcp__plugin_slack_slack__slack_read_user_profile
  - mcp__plugin_slack_slack__slack_search_channels
  - mcp__plugin_slack_slack__slack_search_public_and_private
---

# What's Up Slack — Route Slack Into Your Vault

Catch up on Slack activity since the last run and route the content directly into the vault. Action items become individual files in `actions/` (one per action, status in frontmatter). Decisions, blockers, announcements, FYIs, active discussions, and open questions land in `projects/<project>/log.md` for the project they belong to — decided primarily by content, with a soft prior from the channel's owning project. Items the skill cannot confidently route surface in terminal output for manual handling. No intermediate digest file is produced.

## Prerequisites

- **Invoke from vault root.** The skill writes to `actions/` and `projects/<project>/log.md` paths relative to CWD. It refuses to run if `CWD/projects/` is missing; `actions/` is created on demand.
- **Channels come from `.slack` files** (one channel name per line, no `#` prefix): `projects/<p>/.slack` per project, plus a root `.slack` for general/cross-cutting channels. The monitored set is the union of all active-project files plus root, deduped (`archive/` is never read). Channels say *where to look*; a channel listed in exactly one project's `.slack` is a soft routing prior toward that project — content still decides *where to file*.
- `.whats-up-slack.idx` in CWD — ISO-8601 datetime of last run. Created on first successful run.

## Workflow

### Step 1: Setup

1. **Validate vault root.** Confirm `projects/` (directory) exists in CWD. If missing, error and exit with: *"This skill must be run from your vault root (expected projects/ in CWD)."* Create `actions/` if it does not exist yet.

2. **Get user profile.** Call `slack_read_user_profile` (no args). Record `user_id` and `display_name` — needed for mention detection and own-message attribution.

3. **Resolve time range.**
   - Read `.whats-up-slack.idx`. If present, parse as ISO-8601 → use as `oldest`. Convert to Unix timestamp.
   - If absent, ask via `AskUserQuestion`: *"No previous run recorded. Since when should I summarize? (e.g., 2026-04-11, yesterday, last Monday)"*. Parse the answer to ISO-8601.
   - `latest` = now. Get Unix via `date +%s` and ISO via `date -u +"%Y-%m-%dT%H:%M:%SZ"`.

4. **Assemble channels.** Glob `projects/*/.slack` (active projects only — never `archive/`) and the root `.slack`. Union all listed channel names and dedup. For each channel, compute its `owning_project`: the project whose `.slack` lists it, **iff exactly one** project does; if zero list it (root/general) or two-plus do (shared), it has no owner. Carry the `{channel → owning_project}` map into Step 5. If no `.slack` files exist anywhere, ask which channels to monitor and create a root `.slack`.

5. **Resolve channel IDs.** Use `slack_search_channels` for each channel name. Tolerate optional `#` prefix.

6. **Load project context.** Enumerate `projects/*/` in CWD. For each project directory:
   - Read `README.md` in full.
   - Read the first ~20 lines of `log.md` (reverse-chronological — this is recent activity). Skip if `log.md` does not exist yet.
   - Build an in-memory map `{project_slug → {readme, recent_log}}`. This is the corpus Step 5 scores items against.

7. **Load the people roster.** List `resources/people/*.md` (if the directory exists) to get the canonical set of person slugs — Step 6 resolves Slack authors against this set so wikilinks match real notes and first-name collisions are detected.

### Step 2: Read channels

For each monitored channel, call `slack_read_channel` with:
- `channel_id`: resolved ID
- `oldest`: range start (Unix)
- `latest`: range end (Unix)
- `limit`: 100
- `response_format`: `"concise"`

Paginate via `cursor` if a channel has more than 100 messages in range.

For any message with `reply_count > 0` or a `thread_ts`, read the full thread with `slack_read_thread` using the message's `ts` as `message_ts`, same `oldest`/`latest`, `response_format: "concise"`.

**Reconcile each channel with a search pass.** `slack_read_channel` only returns top-level messages whose `ts` falls inside the range. A thread reply to an *older* parent (parent `ts` before `oldest`) is invisible to the channel read. Common in long-running project channels.

For each monitored channel:
```
slack_search_public_and_private(
  query="in:<#CHANNEL_ID> after:AFTER_DATE before:BEFORE_DATE",
  sort="timestamp",
  include_context=false
)
```
where `AFTER_DATE` = day before `oldest` and `BEFORE_DATE` = day after `latest`. Paginate as needed; discard results outside the exact `oldest`/`latest` range.

Deduplicate hits against the channel read by `message_ts`. For each remainder:
- If `thread_ts` ≠ `ts`, it's a reply on an older parent — read the thread with `slack_read_thread` using `thread_ts` as `message_ts` (no `oldest`/`latest` so you get the parent for context). Fold the new replies into the data set.
- Otherwise treat as a missed top-level message and fold in.

Note: Slack search indexing lags `conversations.history` by a few seconds. A message posted seconds before the run may not appear in search yet — acceptable; the next run picks it up.

### Step 3: Search for direct mentions and your own posts

`AFTER_DATE` / `BEFORE_DATE` as in Step 2.

```
slack_search_public_and_private(query="to:me after:AFTER_DATE before:BEFORE_DATE", sort="timestamp", include_context=false)
slack_search_public_and_private(query="<@USER_ID> after:AFTER_DATE before:BEFORE_DATE", sort="timestamp", include_context=false)
```

Deduplicate by `message_ts`. Discard results outside the exact `oldest`/`latest` range.

```
slack_search_public_and_private(query="from:me after:AFTER_DATE before:BEFORE_DATE", sort="timestamp", include_context=true)
```

Paginate all pages. The user's own posts in **unmonitored** channels are signal — substantive activity (proposals, decisions, position-taking, action-item completions) that the monitored-channel pass would miss. Skip chatter and reactions. Activity in unmonitored channels still flows through Step 5 classification; the channel being off the monitored list does not change routing.

Proposal shares and position-taking posts by the user are **decisions** for classification (they move work). Action-item completions are **Your commitments [DONE]** items.

### Step 4: Read DMs

DMs need the same full read as channels — a search alone is not enough. Slack search ranks by timestamp and paginates, so a single high-traffic DM (e.g. a chatty group DM) saturates the results and buries substantive ones; and the `from:me` pass only shows *your* side, missing the links, forwarded notes, and asks that colleagues send you — exactly the high-value DM content.

1. **Discover active DM/group-DM channels.** Run the search below to find which DMs had activity in range, and also collect every `im`/`mpim` channel ID that surfaced in any Step 3 search pass (`to:me`, `<@USER_ID>`, `from:me`):
   ```
   slack_search_public_and_private(
     query="after:AFTER_DATE before:BEFORE_DATE",
     channel_types="im,mpim",
     sort="timestamp"
   )
   ```
   Paginate as needed. Union all the channel IDs into one set — don't classify off the search snippets themselves.
2. **Full-read each DM channel.** For every DM/group-DM channel ID in that set, call `slack_read_channel` with the channel ID, `oldest`/`latest` (Unix), `limit: 100`, `response_format: "concise"` — this returns **both sides** of the conversation, not just yours. Paginate via `cursor` if needed. For any message with `reply_count > 0` or a `thread_ts`, read the full thread with `slack_read_thread`.

DM content flows through the same Step 5 classifier as channel content. A DM about credits routes to `credits`; a generic check-in with no project signal routes to no-match. Watch specifically for **links/documents shared, notes forwarded from a third person** (e.g. "from Mari: …"), **and soft asks** ("let me know if that looks good") — these are Needs-response or FYI items that the one-sided `from:me` pass cannot see.

### Step 5: Classify

Two passes per item — **type** and **project**.

#### Type classification

Assign one of:

1. **Action item — Needs response** — questions directed at the user, review requests, explicit asks from someone else.
   **Before flagging, verify the ask is still open and actually for the user:**
   - **Read the rest of the thread.** If someone else already answered or handled the ask (often within minutes), it's resolved — drop it, or reclassify as FYI if the resolution itself is worth knowing.
   - **Parse the addressee.** A message opening with "Hi <name>," or @-mentioning a specific person is for *that* person, even if it landed in a monitored channel. Only flag when the addressee is the user, or the message has no specific addressee and asks the channel at large.

2. **Action item — Your commitments [OPEN]** — things the user said they would do in their own messages ("I'll fix it", "let me look into Z", "I'll send the doc by Friday"), not completed within the digest range. Surface even when the user wasn't @mentioned.

3. **Action item — Your commitments [DONE]** — commitments where there's a follow-up from the user reporting completion, or an artifact (merged PR, shared doc) tying off the commitment within the range. These go to `log.md` — no action file is created (the action is already complete).

4. **Action item — Waiting on** — items where the user has done their part and is waiting for someone else's reply or review.

5. **Decisions & outcomes** — "we decided to...", "going with...", "approved", "merged", conclusions of discussions, agreed-upon plans. Highest-signal category. Include the user's own decisions.
   **Pair user proposals with stakeholder approvals.** When the user posted a proposal/question, scan the same thread for replies from decision-makers. Even one-line approvals ("yes ok with me", "approved", "go ahead") belong in the same entry — they're what unblocks the work.

6. **Blockers & incidents** — outages, broken builds, blocked PRs, dependency issues, production alerts. Mark `[OPEN]` or `[RESOLVED]` by end of range.

7. **Announcements** — deployments, releases, policy changes, deadline shifts, team changes, new tooling.

8. **Active discussions** — threads with 5+ replies the user did not participate in. Might warrant attention.

9. **Open questions** — questions in channels with no answer by end of range, where the user might have relevant context.
   **Check the user's own replies before declaring a question open.** Read the full thread, including any `from:me` reply. If the user answered or redirected part of the question, note the addressed part briefly and only flag the still-open part.

10. **FYI** — informational mentions, CC tags, notifications.

For **Needs response** and **FYI**, skip the user's own messages — only items from other people belong there. **Your commitments** is the place for the user's own action items. **Decisions & outcomes** includes the user's own decisions.

#### Project classification

For each item, score against the project context map from Step 1.6. Signals to weigh:

- **Domain keywords** — system names, feature names, file paths, ticket IDs that appear in a project's README or recent `log.md`.
- **People mentioned** — some people are tightly bound to specific projects (visible in `log.md` history).
- **Recent thread continuity** — if a project's recent `log.md` covers topic X and a new message extends X, that's a strong signal even without keyword overlap.
- **Explicit references** — `[[project/README|project]]` wikilinks, PR numbers, project slug mentions.
- **Channel ownership (soft prior)** — if the item's source channel has an `owning_project` (from Step 1.4), treat it as a strong prior toward that project. Absent a contradicting content signal, an item from an owned channel is `clear:<owning_project>`. Strong content pointing elsewhere overrides the prior; weak or conflicting signal makes it `ambiguous:<owning_project>,<content_project>`. Channels with no owner (root/general, or shared across projects) contribute no prior. Items from unmonitored channels — your own posts/DMs in Steps 3–4 — also have no owner.

Output one of:

- **`clear:<project>`** — strong single-project match. Will be written directly.
- **`ambiguous:<a>,<b>[,<c>]`** — two or three plausible matches with similar score. Queues for user confirmation in Step 6.
- **`none`** — no project scores meaningfully. Queues for unrouted terminal output.

Lean cautious — when in doubt between "clear" and "ambiguous", choose ambiguous. When in doubt between "ambiguous" and "none", choose none. Mis-routes are worse than unrouted items because there's no inbox to catch them.

For cross-project items (truly multi-project decisions), file under the highest-scoring project and mention the secondary inline via `[[other-project/README|other-project]]`.

#### Exclusions

- Social chatter, greetings, "thanks!", emoji-only messages.
- Routine bot messages (CI notifications, scheduled reminders) unless they indicate a failure or incident.
- The same topic appearing in multiple channels — consolidate into one item; routing is per item, not per source.

### Step 6: Route, prompt, write

Process in this order:

1. **Write clear matches.**

   For each `clear:<project>` item, route by type:
   - **Needs response** and **[OPEN] commitments** → new action file, `status: now`.
   - **Waiting on** → new action file, `status: waiting`.
   - **[DONE] commitments** → `log.md` (no action file; the action is complete).
   - **Everything else** (decisions, blockers, announcements, active discussions, open questions, FYI) → `log.md`.

   **Writing an action file (`actions/`):**
   - **Dedup first**: scan the `source:` frontmatter of every `actions/*.md` for this Slack permalink. If any file already carries it, skip — the action exists.
   - Filename: `YYYY-MM-DD-<kebab-slug>.md`, date = source message date, slug = a distinctive 3–6 word kebab summary. If that filename already exists, suffix `-2`, `-3`, etc.
   - Frontmatter: `status` (`now` or `waiting` — never `next`/`done`/`dropped`), `project: "[[<project>/README|<project>]]"`, `created: <source date>`, `source: <slack permalink>`. Add `waiting_on: "[[person]]"` when status is `waiting` and the blocker is a known person.
   - Body: a one-line description of the action with `[[people]]` wikilinks, then a `## Log` section seeded with one entry — `- <source date> — <where it came from, e.g. #channel or DM>`.

   **Writing to `projects/<project>/log.md`:**
   - If `log.md` does not exist for the project, create it with the new dated block as its only content.
   - Otherwise prepend a `## YYYY-MM-DD` block at the top of the file (after a title line if one exists, otherwise as the first content), containing all entries for that project from this run.
   - **Same-day merge**: if the topmost header is already today's `## YYYY-MM-DD`, append the new entries within that block instead of creating a duplicate.
   - Entries within a block are reverse-chronological.
   - Use grep-friendly inline markers: `**Decided:**`, `**Agreed:**`, `**Tentative:**`, `[OPEN]`, `[RESOLVED]`.
   - People as `[[first-name-last-name]]` wikilinks.
   - End each entry with `(source: <slack-permalink>)`.

2. **Prompt for ambiguous items.**

   Batch ambiguous items into `AskUserQuestion` calls (max 4 questions per call). For each item:
   - The question is a one-line summary of the content.
   - Options: top 2–3 candidate projects + "Skip — leave unrouted".
   - `header`: short tag like "Routing".

   If more than 4 ambiguous items, issue multiple sequential `AskUserQuestion` calls. After all items are resolved:
   - For each picked project, write using the same logic as step 6.1.
   - For "Skip" picks, treat as unrouted (terminal output, no write).

3. **Print unrouted items to terminal output.**

   For each `none` item and each "Skip" pick from ambiguous prompting, print one line:

   `Unrouted: <one-line gist> — <reason or top-candidate-and-why-rejected>`

   These are **not** written to any file.

4. **Update `.whats-up-slack.idx`.**

   Write the ISO-8601 `latest` value, overwriting any previous content. **Do this last**, after every action-file and `log.md` write succeeds. If any write fails, leave `.idx` untouched so the next run reprocesses the window.

   Write it via a shell redirect, **not** the Write tool — the bare-timestamp file is often sniffed as binary, so Read/Write refuse it (Write demands a prior Read, and Read errors on "binary"):
   ```
   printf '%s\n' "$LATEST_ISO" > .whats-up-slack.idx
   ```

5. **Print run summary to terminal.**

   ```
   Created N action files in actions/ (now: A, waiting: B).
   Updated log.md for projects: X, Y, Z (M entries total).
   Unrouted: K items (listed above).
   Unverified person links: [[slug]], [[slug]] (couldn't disambiguate — verify).
   ```
   Omit the last line when every person link resolved cleanly.

## Voice rules

When distilling threads / meetings into log entries:

- **Paraphrase** discussion flow, exploratory back-and-forth, meeting context.
- **Quote near-verbatim** for decisions, commitments, dates, names of systems/fields/flags — anything load-bearing for a future reader.
- Use `(source: <slack-permalink>)` for traceability.

### People slug resolution

People wikilinks use the real-name slug matching a note in `resources/people/`, never the Slack handle or a partial name. Resolve each Slack author to a slug in this order:

1. **Get the full real name.** Prefer the profile `real_name` (look it up by `user_id` via `slack_read_user_profile` if the message data carries only a display name or handle; cache per `user_id` to avoid repeat calls). Fall back to the display name only when no real name is available.
2. **Fold to a slug:**
   - Lowercase.
   - Unicode NFD normalize and drop combining marks. This strips most Polish diacritics — `ą ć ę ń ó ś ź ż` all decompose to their base letter.
   - **Then apply an explicit map for letters NFD does not decompose** — notably `ł`/`Ł` → `l` (it is an atomic codepoint; NFD leaves it intact), plus `đ`→`d`, `ø`→`o`, `ħ`→`h`. Without this, "Łukasz" folds to `łukasz` and the wikilink breaks against `lukasz-*`.
   - Replace any run of non-alphanumeric characters with a single hyphen; trim leading/trailing hyphens.
3. **Match against the roster and disambiguate.** Compare the folded slug to the `resources/people/` set loaded in Step 1.7. Exact match → use it. If the slug is a first name only (e.g. `lukasz`) and several notes share it (`lukasz-duraj`, `lukasz-garncarek`), a first name is not enough — use the full real name from step 1.

   **If the folded real-name slug has no exact roster match, try a surname match before giving up.** Rosters often file a person under a nickname that does not fold from the real name — e.g. `Bartosz`/`Bartłomiej` → `bartek-*`, `Irena` → `irka-*`. Match the folded surname against the roster (`*-<surname>`); on a unique hit, adopt that note's slug — it's the canonical one (and is what project READMEs/logs already link to). If the surname hits several notes, use the real first name to pick among them. Only when there's no exact match **and** no unique surname match do you emit the best full-name slug and flag it in the run summary as `unverified person link: [[slug]]` so the user can fix it.

Create the wikilink even if no person note exists yet — Obsidian surfaces unresolved links and the note can be created later. A folded slug with no matching note is fine; a *wrong* slug that silently resolves to a different person is not — that's why real-name-first resolution and roster matching matter.

## Format reference

### `actions/` file

```markdown
---
status: now
project: "[[entitlements/README|entitlements]]"
created: 2026-05-26
source: https://workspace.slack.com/archives/C123/p1716000000000000
---
Reply to [[radek-warisch]] re: retry-period BPS emit.

## Log
- 2026-05-26 — raised in #entitlements-dev
```

### `projects/<project>/log.md` block

```markdown
## 2026-05-26
**Decided:** route credit allocation via the daily job, not the upgrade hook ([[bill-salak]]).
Context: avoids double-credit during mid-month upgrades.
(source: https://workspace.slack.com/archives/C123/p1716000000000000)

[OPEN] [[radek-warisch]] still waiting on [[egor-...]]'s confirmation for the retry-period emit fix.
(source: ...)

[[sebastian-nowicki]] shared the AI Tutor Support sequence diagram in #design-syncs; flagged orchestration boundaries.
(source: ...)
```

Slack permalink format: `https://WORKSPACE.slack.com/archives/CHANNEL_ID/pTIMESTAMP` (the `p` prefix; `TIMESTAMP` is the message `ts` with the dot removed — e.g., `ts=1716000000.123456` → `p1716000000123456`).
