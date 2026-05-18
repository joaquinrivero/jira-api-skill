# Example Usage

All examples use the full path. Add `~/.claude/skills/jira-api-skill` to `$PATH` to use bare `~/.claude/skills/jira-api-skill/jira_api.py`.

## Environment

```bash
export ADOBE_JIRA_URL="https://jira.corp.adobe.com"
export ADOBE_JIRA_PAT="paste-your-jira-pat-here"
```

## Get an issue

```bash
~/.claude/skills/jira-api-skill/jira_api.py get-issue --issue-key SKYOPS-12345
```

## Search with JQL

```bash
~/.claude/skills/jira-api-skill/jira_api.py search \
  --jql "project = SKYOPS AND assignee = currentUser() ORDER BY updated DESC" \
  --limit 5
```

## Create an issue

`description.txt`:
```
This issue was created through the Adobe Jira API skill.
```

```bash
~/.claude/skills/jira-api-skill/jira_api.py create-issue \
  --project SKYOPS \
  --issue-type Task \
  --summary "Test issue from Jira API skill" \
  --description-file ./description.txt
```

## Add a comment

`comment.txt`:
```
Test comment added through the Adobe Jira API skill.
```

```bash
~/.claude/skills/jira-api-skill/jira_api.py add-comment \
  --issue-key SKYOPS-12345 \
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
  --issue-key SKYOPS-12345 \
  --fields-file ./fields.json
```

## Transition an issue

List available transitions first:
```bash
~/.claude/skills/jira-api-skill/jira_api.py list-transitions --issue-key SKYOPS-12345
```

Then apply one:
```bash
~/.claude/skills/jira-api-skill/jira_api.py transition-issue \
  --issue-key SKYOPS-12345 \
  --transition-id 31
```

## Inspect metadata

```bash
~/.claude/skills/jira-api-skill/jira_api.py editmeta --issue-key SKYOPS-12345
~/.claude/skills/jira-api-skill/jira_api.py createmeta --project SKYOPS
```
