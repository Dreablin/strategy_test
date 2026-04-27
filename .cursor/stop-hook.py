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


def remove_loop_files(state_file: Path, done_flag: Path) -> None:
    for path in (state_file, done_flag):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            pass


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
        remove_loop_files(state_file, done_flag)
        return 0

    frontmatter = m.group(1)
    prompt_text = m.group(2).strip()

    iteration_match = re.search(r"(?m)^iteration:\s*(\d+)\s*$", frontmatter)
    max_iterations_match = re.search(r"(?m)^max_iterations:\s*(\d+)\s*$", frontmatter)
    completion_promise_match = re.search(r'(?m)^completion_promise:\s*"(.*)"\s*$', frontmatter)

    if not iteration_match or not max_iterations_match:
        remove_loop_files(state_file, done_flag)
        return 0

    iteration = int(iteration_match.group(1))
    max_iterations = int(max_iterations_match.group(1))
    completion_promise = completion_promise_match.group(1) if completion_promise_match else ""

    if done_flag.exists():
        remove_loop_files(state_file, done_flag)
        return 0

    if max_iterations > 0 and iteration >= max_iterations:
        remove_loop_files(state_file, done_flag)
        return 0

    if not prompt_text:
        remove_loop_files(state_file, done_flag)
        return 0

    next_iteration = iteration + 1
    updated_content = re.sub(r"(?m)^iteration:\s*\d+\s*$", f"iteration: {next_iteration}", content, count=1)

    try:
        state_file.write_text(updated_content, encoding="utf-8")
    except Exception:
        return 0

    if completion_promise and completion_promise != "null":
        header = f"[Ralph loop iteration {next_iteration}. To complete: output {completion_promise} ONLY when genuinely true.]"
    else:
        header = f"[Ralph loop iteration {next_iteration}.]"

    followup = f"{header} {prompt_text}"
    sys.stdout.write(json.dumps({"followup_message": followup}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())