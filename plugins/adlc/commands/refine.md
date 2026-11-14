---
name: adlc-refine
description: Refine feature ideas into specifications focusing on WHAT to build not HOW
---

# Refine - Issue Refinement Command

Transform rough ideas into validated specifications (WHAT to build), ready for technical planning.

## Usage

```bash
/refine <ticket>            # Refine an existing Notion ticket (number or URL)
/refine <free text>         # Create new issue and refine it
```

## Overview

This command uses the `refining-issues` skill to:

1. Load or create the ticket in Notion
2. Ask questions about user needs (WHAT, not HOW)
3. Explore expected behaviors and edge cases
4. Present specification for validation
5. Write specification to issue
6. Offer to chain to `/plan`

**Focus:** Requirements, behaviors, success criteria (NOT technology or architecture)

## How It Works

### Step 1: Load or Create Issue

**Existing issue:**

**find ticket** / **get ticket** (`Skill(adlc:tracking-tickets)`).

**New issue from text:**

**create ticket** in the repo's ticket database (from `## ADLC tickets`), status `refining`.

### Step 2: Run Refining-Issues Skill

```bash
Skill(adlc:refining-issues)
```

The skill handles:

- Understanding user needs
- Exploring behaviors and edge cases
- Presenting specification
- Writing to issue with "Specification" section

### Step 3: Offer Next Step

```markdown
✓ Specification written to issue <ISSUE-ID>

Ready to create technical plan? Run `/adlc:plan <ISSUE-ID>`
```

**If user agrees, chain to `/adlc:plan`**

## Error Handling

### No PM System

```markdown
ERROR: No ticket database configured

Add an `## ADLC tickets` section to CLAUDE.md or AGENTS.md naming the Notion data source
(see `Skill(adlc:tracking-tickets)`), and make sure the Notion connector is connected.
```

### Issue Not Found

```markdown
ERROR: Issue <ISSUE-ID> not found

Use the ticket's number (its `Ticket ID`, e.g. 42) or its Notion URL.

Or create new: `/refine "your feature description"`
```

## Integration

**Requires:**

- Notion connected and an `## ADLC tickets` section in CLAUDE.md/AGENTS.md
- `refining-issues` skill

**Chains to:**

- `/adlc:plan` (optional)

## Remember

- Use `refining-issues` skill for all refinement work
- Focus on WHAT not HOW
- Specification drives tests later
- Chain to `/adlc:plan` (not `/adlc:breakdown`)
- All in PM system (no separate files)
