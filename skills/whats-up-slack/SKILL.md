---
name: whats-up-slack
description: |
  Generate a daily "What's Up?" summary of Slack activity across specified channels and DMs.
  Reads channels, threads, and DMs for a given date, then writes a structured markdown digest
  grouped by channel — highlighting decisions, action items, blockers, and announcements.
  Use this skill whenever the user asks for a Slack summary, daily digest, catch-up on Slack,
  "what did I miss", "what's going on", "whats up", or wants to review yesterday's activity.
  Also trigger when the user mentions summarizing channels, catching up on messages, or
  checking what happened while they were away.
allowed-tools:
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

# What's Up Slack — Daily Digest

Generate a focused summary of what happened in the user's Slack channels and DMs on a specific day. The goal is to surface signal from noise so the user can catch up quickly without scrolling through hundreds of messages.

## Inputs

The user provides:
- **Channels**: a list of channel names (e.g., `#backend`, `#incident-response`, `#team-platform`)
- **Date** (optional): the day to summarize, in YYYY-MM-DD format. If not provided, default to **yesterday** (the calendar day before today's date from context).

## Workflow

### Step 1: Setup

1. Get the user's own Slack profile via `slack_read_user_profile` (no arguments — returns the current user). Note their `user_id` and `display_name` — you need these to detect mentions and to attribute the user's own messages correctly.

2. Calculate the time range for the target date:
   - `oldest`: Unix timestamp for the start of the target date at 00:00:00 UTC
   - `latest`: Unix timestamp for the end of the target date at 23:59:59 UTC
   - Use bash to compute these: `date -d "YYYY-MM-DD 00:00:00 UTC" +%s` and `date -d "YYYY-MM-DD 23:59:59 UTC" +%s`

3. Resolve each channel name to a channel ID using `slack_search_channels`. Channel names may or may not include the `#` prefix — handle both.

### Step 2: Read channels

For each channel, call `slack_read_channel` with:
- `channel_id`: the resolved ID
- `oldest`: start-of-day timestamp
- `latest`: end-of-day timestamp
- `limit`: 100
- `response_format`: "concise"

If a channel has more than 100 messages, paginate using the `cursor` from the response until you've fetched all messages for the day.

For any message that has thread replies (indicated by `reply_count` > 0 or a `thread_ts` field), read the full thread with `slack_read_thread` using `channel_id` and the message's `ts` as `message_ts`, with the same `oldest`/`latest` range and `response_format: "concise"`.

### Step 3: Search for direct mentions

Search for messages mentioning the user on the target date:
```
slack_search_public_and_private(
  query="to:me on:YYYY-MM-DD",  
  sort="timestamp",
  include_context=false
)
```

Also search with:
```
slack_search_public_and_private(
  query="<@USER_ID> on:YYYY-MM-DD",
  sort="timestamp",
  include_context=false
)
```

This catches mentions that `to:me` might miss. Deduplicate results by message timestamp.

### Step 4: Read DMs

Search for DM activity on the target date:
```
slack_search_public_and_private(
  query="on:YYYY-MM-DD",
  channel_types="im,mpim",
  sort="timestamp"
)
```

Paginate if needed to capture all DM activity for the day.

### Step 5: Build the summary

Process all collected messages and produce the digest. Use parallel Agent subagents per channel if there's a lot of content — each agent summarizes one channel, then you merge results.

#### Classification rules

For each message or thread, classify it into one of these categories:

1. **Decisions & outcomes** — statements like "we decided to...", "going with...", "approved", "merged", conclusions of discussions, agreed-upon plans. This is the highest-signal category — a missed decision can cause wasted work. Include the user's own decisions too — they belong in the record.

2. **Action items & mentions** — messages where the user was @mentioned or asked to do something by someone else. Split into:
   - **Needs response** — questions directed at the user, review requests, explicit asks
   - **FYI** — informational mentions, CC-style tags, notifications
   - Skip the user's own messages in this section only — the user doesn't need to action themselves.

3. **Blockers & incidents** — messages about outages, broken builds, blocked PRs, dependency issues, production alerts. Note whether the status is **open** or **resolved** by end of day. Include blockers the user raised too.

4. **Announcements** — deployments, releases, policy changes, deadline shifts, team changes, new tooling. Include announcements the user made.

5. **Active discussions** — threads with 5+ replies that the user did NOT participate in. These might need the user's attention or awareness.

6. **Open questions** — questions posted in channels that received no answer by end of day, where the user might have relevant context.

#### What to exclude

- Social chatter, greetings, "thanks!", emoji-only messages
- Bot messages that are routine (CI notifications, scheduled reminders) — unless they indicate a failure or incident
- If the same topic appears in multiple channels, consolidate into one entry and note which channels discussed it

### Step 6: Write the output file

Write the summary to `whats-up-slack-YYYY-MM-DD.md` in the current working directory.

## Output format

Use this structure exactly. Only include sections that have content — skip empty sections entirely.

```markdown
# What's Up — YYYY-MM-DD

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
