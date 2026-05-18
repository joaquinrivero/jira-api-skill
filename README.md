# jira-api-skill

A Claude Code skill and CLI script for reading and writing Jira issues via Personal Access Token auth.

## Prerequisites

### Option A — uv (recommended)

The script manages its own dependencies via [PEP 723](https://peps.python.org/pep-0723/) inline metadata. Install `uv` once and the script handles the rest:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

No virtualenv, no `pip install` needed.

### Option B — plain Python

If you prefer not to use `uv`, install the one dependency manually:

```bash
pip install requests
```

Then invoke with `python jira_api.py` instead of `./jira_api.py`.

## Setup

```bash
export JIRA_URL="https://jira.example.com"
export JIRA_PAT="your-personal-access-token"
```

Optional:
```bash
export JIRA_VERIFY_SSL="true"   # default: true; set to false for self-signed certs
```

## Usage

With `uv` (shebang runs automatically):
```bash
./jira_api.py get-issue --issue-key PROJ-123
```

Explicit `uv run`:
```bash
uv run jira_api.py get-issue --issue-key PROJ-123
```

Plain Python:
```bash
python jira_api.py get-issue --issue-key PROJ-123
```

See [example_usage.md](./example_usage.md) for all subcommands with examples.

## Subcommands

| Subcommand | What it does |
|---|---|
| `get-issue` | Fetch an issue by key |
| `search` | Search issues with JQL |
| `create-issue` | Create a new issue |
| `add-comment` | Add a comment to an issue |
| `update-issue` | Update issue fields |
| `list-transitions` | List available status transitions |
| `transition-issue` | Move an issue to a new status |
| `get-editmeta` | Inspect editable fields for an issue |
| `get-createmeta` | Inspect creatable fields for a project |

## Claude Code skill

When installed as a Claude Code skill, the LLM reads `SKILL.md` and drives `jira_api.py` automatically. Set `JIRA_URL` and `JIRA_PAT` in your environment and Claude will handle the rest.
