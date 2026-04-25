# Ralph Turn Prompt — Isometric Strategy Game

You are working on a Pygame isometric economy strategy game. Do exactly ONE
task per turn following strict TDD.

1. **Read `progress.md`**. Find the FIRST task that is `- [ ]` (unchecked).
   That is your task for this turn. If you cannot find one, see step 6.
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
4. **Update `progress.md`**: change `- [ ]` to `- [x]` for the completed task,
   update the Current Status block (Last Completed, Next Task, Total Progress).
5. **Commit**: `git add -A && git commit -m "feat: T{XX} - {short description}"`
6. **Done check**: if EVERY task in `progress.md` is `[x]`, output exactly:
   `<promise>ALL_TASKS_COMPLETE</promise>` and stop.

Rules:
- Never skip tests. Never modify `PRD.md`.
- One task per turn. If stuck on the same task 3 turns in a row, mark it
  `- [!]` and add a note in the Issues & Blockers table, then move on.
- Keep modules small; follow the directory tree in `PRD.md` §2.
