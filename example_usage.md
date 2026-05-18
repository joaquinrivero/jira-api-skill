# Example Usage

All examples use the full path. Add `~/.claude/skills/jira-api-skill` to `$PATH` to use bare `jira_api.py`.

## Environment

```bash
export JIRA_URL="https://jira.example.com"
export JIRA_PAT="paste-your-jira-pat-here"
```

## Get an issue

```bash
~/.claude/skills/jira-api-skill/jira_api.py get-issue --issue-key PROJ-12345
```

## Search with JQL

```bash
~/.claude/skills/jira-api-skill/jira_api.py search \
  --jql "project = PROJ AND assignee = currentUser() ORDER BY updated DESC" \
  --limit 5
```

## Create an issue

`description.txt`:
```
This issue was created through the Jira API skill.
```

```bash
~/.claude/skills/jira-api-skill/jira_api.py create-issue \
  --project PROJ \
  --issue-type Task \
  --summary "Test issue from Jira API skill" \
  --description-file ./description.txt
```

## Add a comment

`comment.txt`:
```
Test comment added through the Jira API skill.
```

```bash
~/.claude/skills/jira-api-skill/jira_api.py add-comment \
  --issue-key PROJ-12345 \
  --comment-file ./comment.txt
```

## Update fields

`fields.json`:
```json
{
  "summary": "Updated summary from API skill",
  "labels": ["api-test", "automation"]
}
```

```bash
~/.claude/skills/jira-api-skill/jira_api.py update-issue \
  --issue-key PROJ-12345 \
  --fields-file ./fields.json
```

## Transition an issue

List available transitions first:
```bash
~/.claude/skills/jira-api-skill/jira_api.py list-transitions --issue-key PROJ-12345
```

Then apply one:
```bash
~/.claude/skills/jira-api-skill/jira_api.py transition-issue \
  --issue-key PROJ-12345 \
  --transition-id 31
```

## Inspect metadata

```bash
~/.claude/skills/jira-api-skill/jira_api.py get-editmeta --issue-key PROJ-12345
~/.claude/skills/jira-api-skill/jira_api.py get-createmeta --project PROJ
```
