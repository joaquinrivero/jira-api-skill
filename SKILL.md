---
name: jira-api-skill
description: Search, read, create, comment on, and update Adobe Jira issues using Jira Personal Access Tokens. Triggers on requests like "search Jira", "fetch a Jira issue", "create a Jira ticket", "add a comment to a Jira issue", "transition an issue", or any task that reads from or writes to Adobe Jira. Requires ADOBE_JIRA_URL and ADOBE_JIRA_PAT environment variables.
---

# Adobe Jira API

Read and write Adobe Jira issues via Personal Access Token auth.

One rule: **fetch current state before every write.**

## Why this matters

Jira writes that reference stale field values or wrong keys produce 400/404 errors or corrupt data. Fetching before every write gives you the current field values and confirms the key is valid.

---

## Dispatch

| Task | Operation |
|------|-----------|
| Find issues by keyword or filter | `search` |
| Read a specific issue | `get-issue` |
| Create a new issue | `create-issue` |
| Add a comment | `add-comment` |
| Change issue fields | `update-issue` |
| Move an issue to a new status | `transition-issue` |
| See available transitions | `list-transitions` |
| Inspect editable fields | `get-editmeta` |
| Inspect creatable fields | `get-createmeta` |

Always confirm the issue key before any write. Keys are stable; summaries change.

---

## Tool

All operations run through `jira_api.py` (located alongside this skill). Requires `uv` on PATH; the script declares its own dependencies inline via PEP 723:

```bash
~/.claude/skills/jira-api-skill/jira_api.py <subcommand> [options]
```

### Environment

```bash
export ADOBE_JIRA_URL="https://jira.corp.adobe.com"
export ADOBE_JIRA_PAT="your-personal-access-token"
```

Optional:
```bash
export ADOBE_JIRA_VERIFY_SSL="true"   # default: true
```

Never print the raw PAT in chat or logs. Treat it like a password.

---

## Operations

### Get issue

```bash
jira_api.py get-issue --issue-key SKYOPS-12345
jira_api.py get-issue --issue-key SKYOPS-12345 --expand changelog,renderedFields
```

Returns: `key`, `id`, `summary`, `status`, `issueType`, `assignee`, `reporter`, `project`, `description`, `url`.

### Search

```bash
jira_api.py search --jql "project = SKYOPS AND statusCategory != Done ORDER BY updated DESC"
jira_api.py search --jql "assignee = currentUser()" --limit 5 --start-at 0
```

Returns: paginated list (`startAt`, `maxResults`, `total`, `issues`) with `key`, `summary`, `status`, `issueType`, `assignee`, `reporter`, `project`, `updated`, `url` per result. Defaults: `--limit 10`, `--start-at 0`.

### Create issue

```bash
jira_api.py create-issue \
  --project SKYOPS \
  --issue-type Task \
  --summary "Issue summary" \
  --description-file ./description.txt

jira_api.py create-issue \
  --project SKYOPS \
  --issue-type Task \
  --summary "Issue summary" \
  --fields-file ./extra_fields.json
```

**Common `fields.json` shapes:**

Bug with priority and labels:
```json
{
  "priority": {"name": "High"},
  "labels": ["regression", "backend"]
}
```

Subtask with parent:
```json
{
  "parent": {"key": "SKYOPS-100"},
  "assignee": {"name": "jdoe"}
}
```

Story with Epic Link (get the custom field ID from `get-createmeta`):
```json
{
  "customfield_10014": "SKYOPS-50",
  "fixVersions": [{"name": "2.1.0"}],
  "components": [{"name": "API"}]
}
```

### Add comment

```bash
jira_api.py add-comment \
  --issue-key SKYOPS-12345 \
  --comment-file ./comment.txt
```

### Update fields

```bash
jira_api.py update-issue \
  --issue-key SKYOPS-12345 \
  --fields-file ./fields.json
```

### List transitions

```bash
jira_api.py list-transitions --issue-key SKYOPS-12345
```

Returns: `id`, `name`, `toStatus` per available transition.

### Transition issue

```bash
jira_api.py transition-issue \
  --issue-key SKYOPS-12345 \
  --transition-id 31
```

### Inspect metadata

```bash
jira_api.py get-editmeta --issue-key SKYOPS-12345
jira_api.py get-createmeta --project SKYOPS
```

---

## JQL recipes

```bash
# My open work
jira_api.py search --jql "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC"

# Current sprint
jira_api.py search --jql "project = SKYOPS AND sprint IN openSprints() ORDER BY priority ASC"

# Everything under an epic
jira_api.py search --jql "parent = SKYOPS-50 ORDER BY created ASC"
# or for older Jira Server using Epic Link:
jira_api.py search --jql '"Epic Link" = SKYOPS-50 ORDER BY created ASC'

# Stories not linked to any epic (orphans)
jira_api.py search --jql "project = SKYOPS AND issuetype = Story AND \"Epic Link\" IS EMPTY"

# Recently broken — status moved to Reopened or In Progress in last 7 days
jira_api.py search --jql "project = SKYOPS AND status CHANGED TO \"In Progress\" AFTER -7d"

# Overdue — due date passed, not done
jira_api.py search --jql "project = SKYOPS AND due < now() AND statusCategory != Done"

# Unassigned in current sprint
jira_api.py search --jql "project = SKYOPS AND sprint IN openSprints() AND assignee IS EMPTY"

# Issues I changed recently
jira_api.py search --jql "project = SKYOPS AND issueFunction IN updatedBy(\"currentUser()\", \"-7d\")"
```

---

## Edit workflow

Follow this sequence for every write operation:

1. Confirm the issue key — verify via `get-issue` or `search`.
2. Fetch current state with `get-issue`.
3. For field updates, inspect editable fields with `get-editmeta`.
4. Prepare a minimal payload — only the fields that need to change.
5. Apply the change.
6. Confirm with a follow-up `get-issue`.

Never skip step 2. Never modify fields the user didn't ask to change.

### Custom fields

Adobe Jira uses custom fields for Sprint, Story Points, Epic Link, and others. When a `400` references `customfield_XXXXX`:

1. Run `get-editmeta` (for updates) or `get-createmeta` (for creates) on the issue/project.
2. Find the field by name — the response maps display names to `customfield_` IDs.
3. Read `schema.type` and `allowedValues` to get the correct payload shape.

Common shapes:

| Field type | Payload shape |
|---|---|
| Select / status / priority | `{"name": "High"}` |
| Multi-select / labels | `["label-a", "label-b"]` |
| Array of objects (components, fixVersions) | `[{"name": "API"}]` |
| User (assignee, reporter) | `{"name": "jdoe"}` or `{"accountId": "..."}` |
| Issue link (parent, epic) | `{"key": "PROJ-123"}` |
| Number (story points) | `5` |
| String (text fields) | `"plain string"` |

Never hardcode a `customfield_` ID across projects — IDs differ per Jira instance and project.

---

## Safety rules

- Fetch before every write. No exceptions.
- Confirm the issue key before acting — never assume from a prior search.
- Prefer `--issue-key` over JQL-derived keys for writes.
- Do not make destructive updates unless explicitly requested.
- `create-issue` requires `--project`, `--issue-type`, and `--summary`.
- `update-issue` and `add-comment` require `--issue-key`.
- `transition-issue` requires a valid `--transition-id` from `list-transitions`.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token missing, expired, or invalid | Re-export `ADOBE_JIRA_PAT` |
| `403 Forbidden` | Token lacks project permissions | Request access or use correct token |
| `404 Not Found` | Bad issue key or inaccessible project | Verify key via `search` |
| `400 Bad Request` | Invalid field format or unsupported transition | Check field names with `get-editmeta` (for updates) or `get-createmeta` (for new issues) |

If repeated `401` errors occur, the account may be locked — unlock via Jira self-service tools.

---

## iPaaS note

For services calling Jira through Adobe's API gateway (iPaaS), the auth pattern differs:

- `Authorization: <IMS access token>`
- `x-authorization: Bearer <JIRA_PAT>`
- `Api_key: <iPaaS API key>`

This script uses direct PAT auth only. Keep the two modes separate.

---

## Success criteria

A task completed with this skill should meet all of these:

- Issue key was confirmed before any write (not assumed from search results).
- Current state was fetched before submitting any update.
- Only the fields the user asked to change were modified.
- The response includes the issue's `url`.
- The PAT never appeared in output, logs, or chat.

---

## Failure modes

- Assuming an issue key from a search result without confirming it via `get-issue` — search pagination can shift results.
- Sending a full field payload when the user asked to change one field — fetch and merge.
- Using `update-issue` for status changes — status requires `transition-issue` with a valid transition id.
- Treating a `400` as unrecoverable — inspect `get-editmeta` (for updates) or `get-createmeta` (for new issues) for the correct field format, then retry.
