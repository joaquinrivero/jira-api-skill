#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any

import requests

PROG = os.path.basename(sys.argv[0])


@dataclass
class Client:
    base_url: str
    headers: dict[str, str]
    verify_ssl: bool


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        print(f"{PROG}: missing variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def _send(method: str, url: str, **kwargs) -> requests.Response:
    try:
        return requests.request(method, url, **kwargs)
    except requests.RequestException as e:
        print(f"{PROG}: {e}", file=sys.stderr)
        sys.exit(1)


def require_ok(resp: requests.Response) -> dict[str, Any]:
    if resp.status_code >= 400:
        print(f"{PROG}: HTTP {resp.status_code}", file=sys.stderr)
        try:
            print(json.dumps(resp.json(), indent=2), file=sys.stderr)
        except ValueError:
            print(resp.text, file=sys.stderr)
        sys.exit(1)

    if not resp.text.strip():
        return {}

    try:
        return resp.json()
    except ValueError:
        print(f"{PROG}: HTTP {resp.status_code}: expected JSON, got: {resp.text[:200]}", file=sys.stderr)
        sys.exit(1)


def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        print(f"{PROG}: {path}: {e.strerror}", file=sys.stderr)
        sys.exit(1)


def read_json(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        print(f"{PROG}: {path}: {e.strerror}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{PROG}: {path}: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print(f"{PROG}: {path}: expected JSON object, got {type(data).__name__}", file=sys.stderr)
        sys.exit(1)
    return data


def get_issue(client: Client, issue_key: str, expand: str | None = None) -> None:
    url = f"{client.base_url}/rest/api/2/issue/{issue_key}"
    params: dict[str, str] = {}
    if expand:
        params["expand"] = expand

    resp = _send("GET", url, headers=client.headers, params=params, timeout=60, verify=client.verify_ssl)
    data = require_ok(resp)

    fields = data.get("fields") or {}
    result = {
        "key": data.get("key"),
        "id": data.get("id"),
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "issueType": (fields.get("issuetype") or {}).get("name"),
        "assignee": (fields.get("assignee") or {}).get("displayName"),
        "reporter": (fields.get("reporter") or {}).get("displayName"),
        "project": (fields.get("project") or {}).get("key"),
        "description": fields.get("description"),
        "url": f"{client.base_url}/browse/{issue_key}",
    }
    print(json.dumps(result, indent=2))


def search_issues(client: Client, jql: str, limit: int, start_at: int) -> None:
    url = f"{client.base_url}/rest/api/2/search"
    payload = {
        "jql": jql,
        "startAt": start_at,
        "maxResults": limit,
        "fields": ["summary", "status", "issuetype", "assignee", "reporter", "project", "updated"],
    }

    resp = _send("POST", url, headers=client.headers, json=payload, timeout=60, verify=client.verify_ssl)
    data = require_ok(resp)

    results = []
    for issue in data.get("issues", []):
        fields = issue.get("fields") or {}
        results.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "status": (fields.get("status") or {}).get("name"),
            "issueType": (fields.get("issuetype") or {}).get("name"),
            "assignee": (fields.get("assignee") or {}).get("displayName"),
            "reporter": (fields.get("reporter") or {}).get("displayName"),
            "project": (fields.get("project") or {}).get("key"),
            "updated": fields.get("updated"),
            "url": f"{client.base_url}/browse/{issue.get('key')}",
        })

    print(json.dumps({
        "startAt": data.get("startAt"),
        "maxResults": data.get("maxResults"),
        "total": data.get("total"),
        "issues": results,
    }, indent=2))


def create_issue(client: Client, project: str, issue_type: str, summary: str, description_file: str | None, fields_file: str | None) -> None:
    fields: dict[str, Any] = {
        "project": {"key": project},
        "issuetype": {"name": issue_type},
        "summary": summary,
    }

    if description_file:
        fields["description"] = read_file(description_file)

    if fields_file:
        fields.update(read_json(fields_file))

    resp = _send("POST", f"{client.base_url}/rest/api/2/issue", headers=client.headers, json={"fields": fields}, timeout=60, verify=client.verify_ssl)
    data = require_ok(resp)

    print(json.dumps({
        "id": data.get("id"),
        "key": data.get("key"),
        "url": f"{client.base_url}/browse/{data.get('key')}",
    }, indent=2))


def add_comment(client: Client, issue_key: str, comment_file: str) -> None:
    resp = _send(
        "POST",
        f"{client.base_url}/rest/api/2/issue/{issue_key}/comment",
        headers=client.headers,
        json={"body": read_file(comment_file)},
        timeout=60,
        verify=client.verify_ssl,
    )
    data = require_ok(resp)

    print(json.dumps({
        "id": data.get("id"),
        "issueKey": issue_key,
        "url": f"{client.base_url}/browse/{issue_key}",
    }, indent=2))


def update_issue(client: Client, issue_key: str, fields_file: str) -> None:
    resp = _send(
        "PUT",
        f"{client.base_url}/rest/api/2/issue/{issue_key}",
        headers=client.headers,
        json={"fields": read_json(fields_file)},
        timeout=60,
        verify=client.verify_ssl,
    )
    require_ok(resp)

    print(json.dumps({
        "updated": True,
        "issueKey": issue_key,
        "url": f"{client.base_url}/browse/{issue_key}",
    }, indent=2))


def list_transitions(client: Client, issue_key: str) -> None:
    resp = _send(
        "GET",
        f"{client.base_url}/rest/api/2/issue/{issue_key}/transitions",
        headers=client.headers,
        timeout=60,
        verify=client.verify_ssl,
    )
    data = require_ok(resp)

    print(json.dumps({
        "issueKey": issue_key,
        "transitions": [
            {"id": t.get("id"), "name": t.get("name"), "toStatus": (t.get("to") or {}).get("name")}
            for t in data.get("transitions", [])
        ],
    }, indent=2))


def transition_issue(client: Client, issue_key: str, transition_id: str) -> None:
    resp = _send(
        "POST",
        f"{client.base_url}/rest/api/2/issue/{issue_key}/transitions",
        headers=client.headers,
        json={"transition": {"id": transition_id}},
        timeout=60,
        verify=client.verify_ssl,
    )
    require_ok(resp)

    print(json.dumps({
        "transitioned": True,
        "issueKey": issue_key,
        "transitionId": transition_id,
        "url": f"{client.base_url}/browse/{issue_key}",
    }, indent=2))


def get_editmeta(client: Client, issue_key: str) -> None:
    # raw metadata for human inspection; shape differs from other commands by design
    resp = _send(
        "GET",
        f"{client.base_url}/rest/api/2/issue/{issue_key}/editmeta",
        headers=client.headers,
        timeout=60,
        verify=client.verify_ssl,
    )
    print(json.dumps(require_ok(resp), indent=2))


def get_createmeta(client: Client, project: str) -> None:
    # raw metadata for human inspection; shape differs from other commands by design
    resp = _send(
        "GET",
        f"{client.base_url}/rest/api/2/issue/createmeta",
        headers=client.headers,
        params={"projectKeys": project, "expand": "projects.issuetypes.fields"},
        timeout=60,
        verify=client.verify_ssl,
    )
    print(json.dumps(require_ok(resp), indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adobe Jira REST API client")
    sub = parser.add_subparsers(dest="command", required=True)

    p_get = sub.add_parser("get-issue", help="fetch an issue by key")
    p_get.add_argument("--issue-key", required=True, metavar="KEY")
    p_get.add_argument("--expand", metavar="FIELDS")

    p_search = sub.add_parser("search", help="search issues with JQL")
    p_search.add_argument("--jql", required=True, metavar="JQL")
    p_search.add_argument("--limit", type=int, default=10, metavar="N")
    p_search.add_argument("--start-at", type=int, default=0, metavar="N")

    p_create = sub.add_parser("create-issue", help="create a new issue")
    p_create.add_argument("--project", required=True, metavar="KEY")
    p_create.add_argument("--issue-type", required=True, metavar="TYPE")
    p_create.add_argument("--summary", required=True, metavar="TEXT")
    p_create.add_argument("--description-file", metavar="FILE")
    p_create.add_argument("--fields-file", metavar="FILE")

    p_comment = sub.add_parser("add-comment", help="add a comment to an issue")
    p_comment.add_argument("--issue-key", required=True, metavar="KEY")
    p_comment.add_argument("--comment-file", required=True, metavar="FILE")

    p_update = sub.add_parser("update-issue", help="update issue fields")
    p_update.add_argument("--issue-key", required=True, metavar="KEY")
    p_update.add_argument("--fields-file", required=True, metavar="FILE")

    p_list_t = sub.add_parser("list-transitions", help="list available transitions")
    p_list_t.add_argument("--issue-key", required=True, metavar="KEY")

    p_transition = sub.add_parser("transition-issue", help="transition an issue to a new status")
    p_transition.add_argument("--issue-key", required=True, metavar="KEY")
    p_transition.add_argument("--transition-id", required=True, metavar="ID")

    p_editmeta = sub.add_parser("get-editmeta", help="get edit metadata for an issue")
    p_editmeta.add_argument("--issue-key", required=True, metavar="KEY")

    p_createmeta = sub.add_parser("get-createmeta", help="get create metadata for a project")
    p_createmeta.add_argument("--project", required=True, metavar="KEY")

    return parser


def main() -> None:
    args = build_parser().parse_args()

    client = Client(
        base_url=get_env("ADOBE_JIRA_URL").rstrip("/"),
        headers={
            "Authorization": f"Bearer {get_env('ADOBE_JIRA_PAT')}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        verify_ssl=get_env("ADOBE_JIRA_VERIFY_SSL", "true").lower() == "true",
    )

    if args.command == "get-issue":
        get_issue(client, args.issue_key, args.expand)
    elif args.command == "search":
        search_issues(client, args.jql, args.limit, args.start_at)
    elif args.command == "create-issue":
        create_issue(client, args.project, args.issue_type, args.summary, args.description_file, args.fields_file)
    elif args.command == "add-comment":
        add_comment(client, args.issue_key, args.comment_file)
    elif args.command == "update-issue":
        update_issue(client, args.issue_key, args.fields_file)
    elif args.command == "list-transitions":
        list_transitions(client, args.issue_key)
    elif args.command == "transition-issue":
        transition_issue(client, args.issue_key, args.transition_id)
    elif args.command == "get-editmeta":
        get_editmeta(client, args.issue_key)
    elif args.command == "get-createmeta":
        get_createmeta(client, args.project)


if __name__ == "__main__":
    main()
