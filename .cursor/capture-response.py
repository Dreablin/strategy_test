import json
import os
import re
import sys
from pathlib import Path


def normalize_cursor_path(path_value: str | None) -> str | None:
    if not path_value:
        return None
    value = path_value.strip()
    m = re.match(r"^/([A-Za-z]:/.*)$", value)
    if m:
        value = m.group(1)
    return value.replace("/", "\\")


def get_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def get_project_dir(payload: dict) -> Path:
    roots = payload.get("workspace_roots")
    if isinstance(roots, list) and roots:
        p = normalize_cursor_path(str(roots[0]))
        if p:
            return Path(p)
    if isinstance(roots, str):
        p = normalize_cursor_path(roots)
        if p:
            return Path(p)

    env_dir = os.environ.get("CURSOR_PROJECT_DIR")
    p = normalize_cursor_path(env_dir)
    if p:
        return Path(p)

    return Path.cwd()


def main() -> int:
    payload = get_payload()
    project_dir = get_project_dir(payload)

    state_file = project_dir / ".cursor" / "ralph" / "scratchpad.md"
    done_flag = project_dir / ".cursor" / "ralph" / "done"

    if not state_file.exists():
        return 0

    try:
        content = state_file.read_text(encoding="utf-8")
    except Exception:
        return 0

    m = re.match(r"(?s)^---\s*(.*?)\s*---\s*(.*)$", content)
    if not m:
        return 0

    frontmatter = m.group(1)
    completion_promise_match = re.search(r'(?m)^completion_promise:\s*"(.*)"\s*$', frontmatter)
    completion_promise = completion_promise_match.group(1) if completion_promise_match else ""

    if not completion_promise or completion_promise == "null":
        return 0

    response_text = payload.get("text", "")
    if not isinstance(response_text, str) or not response_text.strip():
        return 0

    promise_match = re.search(r"(?s)<promise>(.*?)</promise>", response_text)
    if not promise_match:
        return 0

    promise_text = re.sub(r"\s+", " ", promise_match.group(1)).strip()

    if promise_text == completion_promise:
        done_flag.parent.mkdir(parents=True, exist_ok=True)
        done_flag.write_text("", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())