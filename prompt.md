# Ralph Turn Prompt — Isometric Strategy Game

You are working on a Pygame isometric economy strategy game. Keep exactly ONE
active task at a time and continue it across turns until fully complete.

1. **Read `progress.md`**.
   - If there is a task marked `- [~]` (in progress), continue that same task.
   - Otherwise find the FIRST task that is `- [ ]` (unchecked), mark it `- [~]`,
     and start it.
   - Do not start another task until the active one is completed (`[x]`) or
     blocked (`[!]`).
2. **Read `PRD.md`** sections relevant to the task. Do NOT modify `PRD.md`.
3. **TDD**:
   - If the task is a *test* task: write the tests in `tests/test_*.py`, run
     `pytest -q`, confirm they FAIL with the expected error (module/feature
     missing), commit.
   - If the task is an *implementation* task: write the production code in
     `src/game/...`, run `pytest -q`, confirm previously-failing tests now
     pass AND the full suite is green.
   - If the task has no test counterpart (UI / packaging), write the code and
     run a sanity check (`python -c "import game.<module>"` or smoke run with
     `SDL_VIDEODRIVER=dummy python -m game.main` for ≤2 s).
4. **Update `progress.md`**:
   - Keep active task as `- [~]` while it is still in progress.
   - Change active task to `- [x]` only when fully complete and verified.
   - If blocked after 3 attempts, mark `- [!]` and log blocker.
   - Update Current Status block each turn.
5. **Commit**: `git add -A && git commit -m "feat: T{XX} - {short description}"`
6. **Done check**: if EVERY task in `progress.md` is `[x]`:
   - Create the file `.cursor/ralph/done` (empty content) — this hard-stops
     the loop via `stop-hook.py` regardless of message parsing.
   - THEN output the completion promise on its own line. The wrapper tags are
     **mandatory** (the `capture-response.py` hook only matches the regex
     `<promise>(.*?)</promise>`). Output literally, including the angle
     brackets:

     `<promise>ALL_TASKS_COMPLETE</promise>`

   - Do NOT output the bare string `ALL_TASKS_COMPLETE` without the
     `<promise>` … `</promise>` wrapper — the loop will keep iterating.

Rules:
- Never skip tests. Never modify `PRD.md`.
- Exactly one active task at a time. A task may span multiple iterations.
- Use statuses consistently: `[ ]` not started, `[~]` in progress, `[x]` done, `[!]` blocked.
- If stuck on the same task 3 turns in a row, mark it `- [!]` and add a note
  in the Issues & Blockers table, then move on.
- Keep modules small; follow the directory tree in `PRD.md` §2.
