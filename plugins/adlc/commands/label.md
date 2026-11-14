---
name: adlc-label
description: Set or confirm a ticket's Type in Notion (bug/chore/feature)
---

# Label - Classify Tickets

Set or confirm a ticket's Type (`bug` / `chore` / `feature`). The Type picks the execution pathway.

## Usage

```bash
/adlc:label 42 bug       # Set Type to bug
/adlc:label 42 chore     # Set Type to chore
/adlc:label 42 feature   # Set Type to feature
/adlc:label 42           # Interactive: suggest a Type and confirm
```

The ticket can be its number, `#42`, or its Notion URL.

## Process

All ticket steps use `Skill(adlc:tracking-tickets)`.

1. **find ticket** / **get ticket**. Not found → say so and stop.
2. **With a Type argument:** it must be `bug`, `chore` or `feature` (anything else: list the valid ones and
   stop). **set type**, then confirm: "Ticket 42 (Name) is now a feature."
3. **Without one:** suggest a Type from the title and body (broken behaviour → `bug`; new or changed behaviour →
   `feature`; no user-facing change → `chore`; see `creating-tickets`). Ask with AskUserQuestion, the suggestion
   first, then **set type** to the answer.

## Model Recommendation (cost)

After the Type is set or confirmed, **surface a one-line model tip keyed to it** (advisory only; continue without
waiting):

- **chore** → 💡 routine work: Sonnet handles it well at ~1/5 the Opus cost; consider `/model sonnet` when you
  execute it.
- **feature / bug** → 💡 likely needs stronger reasoning: Opus is a reasonable default; if you'd switched to
  Sonnet, consider `/model opus` for the hard parts.

See `skills/execution-orchestration/references/model-routing.md`.

## What happens next

- **bug** (standalone) → `/adlc:bug-fix 42`
- **chore** (standalone) → `/adlc:chore 42`
- **feature** → `/adlc:refine 42`, then plan, breakdown, execute
