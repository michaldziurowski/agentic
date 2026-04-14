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

The user provides:
- **Channels**: a list of channel names (e.g., `#backend`, `#incident-response`, `#team-platform`)

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

3. Resolve each channel name to a channel ID using `slack_search_channels`. Channel names may or may not include the `#` prefix — handle both.

### Step 2: Read channels

For each channel, call `slack_read_channel` with:
- `channel_id`: the resolved ID
- `oldest`: the start timestamp (from `.idx` or user input)
- `latest`: the current timestamp
- `limit`: 100
- `response_format`: "concise"

If a channel has more than 100 messages, paginate using the `cursor` from the response until you've fetched all messages for the range.

For any message that has thread replies (indicated by `reply_count` > 0 or a `thread_ts` field), read the full thread with `slack_read_thread` using `channel_id` and the message's `ts` as `message_ts`, with the same `oldest`/`latest` range and `response_format: "concise"`.

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

2. **Action items & mentions** — messages where the user was @mentioned or asked to do something by someone else. Split into:
   - **Needs response** — questions directed at the user, review requests, explicit asks
   - **FYI** — informational mentions, CC-style tags, notifications
   - Skip the user's own messages in this section only — the user doesn't need to action themselves.

3. **Blockers & incidents** — messages about outages, broken builds, blocked PRs, dependency issues, production alerts. Note whether the status is **open** or **resolved** by the end of the range. Include blockers the user raised too.

4. **Announcements** — deployments, releases, policy changes, deadline shifts, team changes, new tooling. Include announcements the user made.

5. **Active discussions** — threads with 5+ replies that the user did NOT participate in. These might need the user's attention or awareness.

6. **Open questions** — questions posted in channels that received no answer by the end of the range, where the user might have relevant context.

#### What to exclude

- Social chatter, greetings, "thanks!", emoji-only messages
- Bot messages that are routine (CI notifications, scheduled reminders) — unless they indicate a failure or incident
- If the same topic appears in multiple channels, consolidate into one entry and note which channels discussed it

### Step 6: Write the output file and update the index

1. Write the summary to `whats-up-slack-YYYYMMDDhhmmss.md` in the current working directory, using the compact timestamp of the current run. For example: `whats-up-slack-20260414143022.md`.

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
- Use `[OPEN]` and `[RESOLVED]` tags on blockers/incidents
- When mentioning people, use their display names, not Slack user IDs
