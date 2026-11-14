---
name: updating-pm-status
description: Update the Notion ticket with task status changes and lifecycle comments
when_to_use: when task status changes during execution (start, PR created, CI status, merged)
version: 2.0.0
---

# Updating PM Status

Keep the Notion ticket in step with the task's lifecycle so anyone looking at the board sees where work stands.

**Core principle:** the ticket is the source of truth for task status.

**Called by:** execution-orchestration and executing-tasks skills.

Every action below is a ticket operation from `Skill(adlc:tracking-tickets)` (**set status**, **comment**,
**set field**). Statuses are ADLC statuses; tracking-tickets maps them to the database's values.

## Events

| Event | Set status | Set fields | Comment (one line per fact) |
|---|---|---|---|
| Task started | `in_progress` | branch | 🚀 Started on `<branch>` (worktree `<path>`) |
| PR created | `in_review` | PR URL | 📝 PR #N opened: `<task branch>` → `<target branch>`. Waiting on CI and review. |
| CI failed | `blocked` | | ❌ CI failed on PR #N: `<check>` (`<details url>`), one line per failed check |
| CI passed | (stays `in_review`) | | ✅ CI passed on PR #N (N checks) |
| Changes requested | `in_progress` | | 🔄 Changes requested on PR #N by `<reviewer>` |
| Review approved | (stays `in_review`) | | ✅ PR #N approved by `<reviewer>`. Ready to merge. |
| PR merged | `done` | | ✅ Merged PR #N (`<sha8>`, `<strategy>`). `<one-line summary>`. Tests: `<summary>`. |

If the database has a `CI Status` select, also set it (`Pending` / `Passing` / `Failing`) on the CI events. If it
has a `Blocked Reason` text, set it when you set `blocked`, and clear it when the ticket leaves `blocked`.

## Where to call it

1. Task branch created → **Task started**
2. PR created → **PR created**
3. While monitoring the PR → **CI failed / CI passed / Changes requested / Review approved**
4. PR merged → **PR merged**

## Rules

- Update immediately on each transition; don't batch.
- Comment only on transitions, not on every poll. CI passed is worth one comment per PR, not per push.
- Always include the PR link once there is one.
- CI failure comments name the failing check and link to its log, so a human can act without opening GitHub.
- A Notion error is retried once (see tracking-tickets). After that, carry on with the code work and tell the
  user which update didn't sync. A failed status update never fails the task.
