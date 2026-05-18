---
name: whats-up-slack
description: |
  Generate a "What's Up?" summary of Slack activity since the last time this skill was run.
  Reads channels, threads, and DMs for the period since last run, then writes a structured
  markdown digest grouped by channel — highlighting decisions, action items, blockers, and
  announcements. Tracks last run time in .whats-up-slack.idx; if no prior run exists, asks
  the user for a start date.
  Use this skill whenever the user asks for a Slack summary, daily digest, catch-up on Slack,
  "what did I miss", "what's going on", "whats up", or wants to review recent activity.
  Also trigger when the user mentions summarizing channels, catching up on messages, or
  checking what happened while they were away.
allowed-tools:
  - AskUserQuestion
  - Bash
  - Read
  - Write
  - Agent
  - mcp__plugin_slack_slack__slack_read_channel
  - mcp__plugin_slack_slack__slack_read_thread
  - mcp__plugin_slack_slack__slack_read_user_profile
  - mcp__plugin_slack_slack__slack_search_channels
  - mcp__plugin_slack_slack__slack_search_public_and_private
---

# What's Up Slack — Digest Since Last Run

Generate a focused summary of what happened in the user's Slack channels and DMs since the last time this skill was run. The goal is to surface signal from noise so the user can catch up quickly without scrolling through hundreds of messages.

## Inputs

Channels are loaded from `.whats-up-slack.channels` in the current working directory — one channel name per line (without `#` prefix). If the file does not exist, ask the user which channels to monitor and create the file.

The time range is determined automatically — see Step 1.

## Workflow

### Step 1: Setup

1. Get the user's own Slack profile via `slack_read_user_profile` (no arguments — returns the current user). Note their `user_id` and `display_name` — you need these to detect mentions and to attribute the user's own messages correctly.

2. Determine the time range:
   - **Read `.whats-up-slack.idx`** from the current working directory. The file contains a single line: an ISO-8601 datetime of the last run (e.g., `2026-04-13T14:30:00Z`).
   - If the file **exists**: use its value as the start of the range (`oldest`). Convert to Unix timestamp with bash.
   - If the file **does not exist**: ask the user with `AskUserQuestion`: *"No previous run recorded. Since when should I summarize? (e.g., 2026-04-11, yesterday, last Monday)"*. Parse the user's answer into an ISO-8601 datetime and use it as `oldest`.
   - `latest` is **now** — compute the current Unix timestamp with `date +%s`.
   - Record these values; you'll need `oldest` and `latest` as Unix timestamps throughout the workflow, and the ISO-8601 forms for display and for the `.idx` file update.

3. **Read `.whats-up-slack.channels`** from the current working directory. Each line is a channel name (without `#`). If the file does not exist, ask the user which channels to monitor with `AskUserQuestion`, then create the file with their answer (one channel per line).

4. Resolve each channel name to a channel ID using `slack_search_channels`. Channel names may or may not include the `#` prefix — handle both.

### Step 2: Read channels

For each channel, call `slack_read_channel` with:
- `channel_id`: the resolved ID
- `oldest`: the start timestamp (from `.idx` or user input)
- `latest`: the current timestamp
- `limit`: 100
- `response_format`: "concise"

If a channel has more than 100 messages, paginate using the `cursor` from the response until you've fetched all messages for the range.

For any message that has thread replies (indicated by `reply_count` > 0 or a `thread_ts` field), read the full thread with `slack_read_thread` using `channel_id` and the message's `ts` as `message_ts`, with the same `oldest`/`latest` range and `response_format: "concise"`.

**Reconcile each channel with a search pass.** `slack_read_channel` wraps Slack's `conversations.history`, which only returns top-level messages whose `ts` falls inside the time range. If the only activity in a channel during the range is a reply to an *older* thread (parent `ts` before `oldest`), the channel read returns empty or incomplete — the thread reply is invisible. This happens more often than you'd expect in long-running project channels.

For each monitored channel, run:
```
slack_search_public_and_private(
  query="in:<#CHANNEL_ID> after:AFTER_DATE before:BEFORE_DATE",
  sort="timestamp",
  include_context=false
)
```
(where `AFTER_DATE` is the day before `oldest` and `BEFORE_DATE` is the day after `latest`; paginate if needed, and discard results outside the exact `oldest`/`latest` range).

Deduplicate hits by `message_ts` against what `slack_read_channel` already returned. For each remainder:
- If it has a `thread_ts` different from its own `ts`, it's a thread reply on an older parent — read the thread with `slack_read_thread` using `thread_ts` as `message_ts` (no `oldest`/`latest` so you get the parent for context), and fold the new replies into the digest.
- Otherwise treat it as a regular missed top-level message and fold it in.

Note: Slack search indexing can lag a few seconds behind `conversations.history`, so a message posted seconds before the run may not appear in search yet. Acceptable — the next run picks it up.

### Step 3: Search for direct mentions

Search for messages mentioning the user in the time range. Slack search supports `after:` and `before:` date filters (YYYY-MM-DD format). Compute `AFTER_DATE` as the day before `oldest` and `BEFORE_DATE` as the day after `latest` to ensure full coverage:
```
slack_search_public_and_private(
  query="to:me after:AFTER_DATE before:BEFORE_DATE",
  sort="timestamp",
  include_context=false
)
```

Also search with:
```
slack_search_public_and_private(
  query="<@USER_ID> after:AFTER_DATE before:BEFORE_DATE",
  sort="timestamp",
  include_context=false
)
```

This catches mentions that `to:me` might miss. Deduplicate results by message timestamp. Discard any results whose timestamp falls outside the exact `oldest`/`latest` range (the date filters are day-granularity, so edge messages may leak in).

**Also search for the user's own posts** — this surfaces substantive activity the user initiated in channels that aren't on the monitored list (proposals, decisions, position-taking posts in ad-hoc channels). The per-channel reconciliation pass in Step 2 already handles misses within monitored channels; `from:me` covers the off-list case:
```
slack_search_public_and_private(
  query="from:me after:AFTER_DATE before:BEFORE_DATE",
  sort="timestamp",
  include_context=true
)
```
Paginate through all pages. For each hit in a channel NOT on `.whats-up-slack.channels`: if the user posted something substantive (proposals, decisions, action-item completions, architectural arguments — not just reactions/acks), include it in the digest under the most fitting section. Flag the channel name so the user sees it came from outside the monitored list. Skip hits in monitored channels (already reconciled in Step 2) and skip chatter/acks.

Proposal shares and position-taking posts by the user belong in **Decisions & outcomes** even though they're the user's own messages. Action-item completions by the user belong in **Action items & mentions → Your commitments** with a `[DONE]` tag. The rule about skipping the user's own messages applies only to the **Needs response** and **FYI** subsections.

### Step 4: Read DMs

Search for DM activity in the time range:
```
slack_search_public_and_private(
  query="after:AFTER_DATE before:BEFORE_DATE",
  channel_types="im,mpim",
  sort="timestamp"
)
```

Paginate if needed. Discard results outside the exact `oldest`/`latest` range.

### Step 5: Build the summary

Process all collected messages and produce the digest. Use parallel Agent subagents per channel if there's a lot of content — each agent summarizes one channel, then you merge results.

#### Classification rules

For each message or thread, classify it into one of these categories:

1. **Decisions & outcomes** — statements like "we decided to...", "going with...", "approved", "merged", conclusions of discussions, agreed-upon plans. This is the highest-signal category — a missed decision can cause wasted work. Include the user's own decisions too — they belong in the record.
   - **Pair user proposals with stakeholder approvals.** When the user posted a proposal/question, scan the same thread for replies from decision-makers. Even one-line approvals ("yes ok with me", "approved", "go ahead") belong in the same bullet as the proposal — they're what unblocks the work. Summarising the proposal alone, while a sign-off sits in the thread, misrepresents the state of play.

2. **Action items & mentions** — work owed by or to the user. Split into three subsections:
   - **Needs response** — questions directed at the user, review requests, explicit asks from someone else
   - **Your commitments** — things the user said they would do in their own messages ("I'll fix it", "let me look into Z", "I'll send the doc by Friday", "I'll dig in tomorrow"). Tag each as `[OPEN]` if not completed within the digest range, or `[DONE]` if completed within the range (look for a follow-up message from the user reporting completion, or for an artifact like a merged PR / shared doc tied to the commitment). Surface these even when the user wasn't @mentioned — they're action items regardless.
   - **FYI** — informational mentions, CC-style tags, notifications
   - For **Needs response** and **FYI**, skip the user's own messages — only items from other people belong there. **Your commitments** is the place for the user's own action items.

   **Before flagging as Needs response, verify the ask is still open and actually for the user:**
   - **Read the rest of the thread.** If someone else already answered or handled the ask (often within minutes), it is resolved — drop it, or move to FYI if the resolution is itself worth knowing.
   - **Parse the addressee.** A message that opens with "Hi <name>," or directly @mentions a specific person is addressed to *that* person, even if it lands in a channel the user monitors. Only flag as Needs response when the addressee is the user, or the message has no specific addressee and asks the channel at large for input. A substantive doc shared in the channel is not automatically a Needs-response item for the user.

3. **Blockers & incidents** — messages about outages, broken builds, blocked PRs, dependency issues, production alerts. Note whether the status is **open** or **resolved** by the end of the range. Include blockers the user raised too.

4. **Announcements** — deployments, releases, policy changes, deadline shifts, team changes, new tooling. Include announcements the user made.

5. **Active discussions** — threads with 5+ replies that the user did NOT participate in. These might need the user's attention or awareness.

6. **Open questions** — questions posted in channels that received no answer by the end of the range, where the user might have relevant context.
   - **Check the user's own replies before declaring a question open.** Read the full thread, including any reply from the user (also surfaced via `from:me`). If the user's reply addressed or redirected part of the question — e.g., pointing to another decision thread — note that explicitly: mark addressed parts as resolved with a one-line "you replied: …" and only list the parts that are still actually open. A multi-part question is rarely all-open or all-closed.

#### What to exclude

- Social chatter, greetings, "thanks!", emoji-only messages
- Bot messages that are routine (CI notifications, scheduled reminders) — unless they indicate a failure or incident
- If the same topic appears in multiple channels, consolidate into one entry and note which channels discussed it

### Step 6: Write the output file and update the index

1. Write the summary to `whats-up-slack-YYYYMMDDhhmmss.md` using the compact timestamp of the current run. If an `inbox/` directory exists in the current working directory, write the file there (e.g., `inbox/whats-up-slack-20260414143022.md`). Otherwise, write to the current working directory.

2. **Update `.whats-up-slack.idx`**: write the current ISO-8601 datetime (the `latest` value used for this run) to `.whats-up-slack.idx` in the current working directory, overwriting any previous content. This records the run time so the next invocation picks up where this one left off.

## Output format

Use this structure exactly. Only include sections that have content — skip empty sections entirely.

```markdown
# What's Up — YYYY-MM-DDThh:mm:ssZ to YYYY-MM-DDThh:mm:ssZ

## Action items & mentions

Items that need the user's response come first, marked with a warning indicator.

### [!] Needs response

- **#channel-name** — [Brief description of what's needed]. [Thread link]
- **DM from @person** — [Brief description]. [Thread link]

### Your commitments

- **#channel-name** — [OPEN] [What the user said they'd do]. [Thread link]
- **#channel-name** — [DONE] [What the user committed to and shipped within the range]. [Thread link]

### FYI

- **#channel-name** — [What the user was mentioned for]. [Thread link]

## Decisions & outcomes

- **#channel-name** — [What was decided and by whom]. [Thread link]
- **#channel-name** — [Another decision]. [Thread link]

## Blockers & incidents

- **#channel-name** — [OPEN] [Description of the blocker/incident]. [Thread link]
- **#channel-name** — [RESOLVED] [What happened and how it was resolved]. [Thread link]

## Announcements

- **#channel-name** — [What was announced]. [Thread link]

## Active discussions

- **#channel-name** — [Topic summary, N replies]. [Thread link]

## Open questions

- **#channel-name** — @person asked: "[Brief question]" — no replies yet. [Thread link]
```

### Formatting rules

- Each item is a single bullet point — concise, one to two sentences max
- Bold the channel name or DM source at the start of each bullet
- Include a Slack deep link to the original message or thread when available (format: `https://WORKSPACE.slack.com/archives/CHANNEL_ID/pTIMESTAMP`)
- The `[!]` marker on "Needs response" items helps the user scan for urgent items
- Use `[OPEN]` / `[RESOLVED]` tags on **Blockers & incidents** items, and `[OPEN]` / `[DONE]` tags on **Your commitments** items
- When mentioning people, use their **full display name on every reference within a bullet** — never drop to first-name-only later in the same paragraph. The team has multiple Łukaszes, Bartoszes, Michałs, etc., and downstream consumers (e.g., wikilink resolution against `resources/people/`) need unambiguous identifiers
- **Per-bullet event date.** When the digest range spans 2+ calendar days, prefix each bullet's content (after the bolded channel and any `[OPEN]`/`[DONE]`/`[!]` tag) with `(YYYY-MM-DD)` indicating when the event happened. For thread items, use the date of the most recent activity within the range. For single-day digests (range start and end fall on the same calendar day), omit the prefix
