# reloadsh Terminal Restart Implementation Plan

**Goal:** Keep the current terminal open unless a new terminal was requested without a detected startup failure and the user confirms it is usable.

**Architecture:** Keep launch diagnostics in `open_terminal`, executable discovery in `open_tabby_terminal`, and the interactive confirmation in `restart_windows_terminal`. Preserve the existing Python/PowerShell exit-code protocol and macOS behavior.

**Tech Stack:** Python standard library, questionary, PowerShell, unittest.

## Constraints

- No new runtime dependencies or changes to the installed Tabby application.
- Launch observation: 3 seconds; captured diagnostic tail: 8192 bytes.
- Exit 43 only after explicit confirmation; failures exit 10; cancellation exits 0.
- Never terminate a launched terminal application merely because observation timed out.
- Changes remain reviewable in the user's existing checkout; no commit or branch change is required.

## Task 1: Launch diagnostics and safe confirmation

- [x] Extend `public/_script/test_reloadsh.py` with real child-process tests for nonzero exit, fatal output with exit 0, warnings, large output and timeout; add discovery and interactive-flow cases.
- [x] Run the new failing cases and confirm the missing protections (7 tests, 8 assertion failures including subtests).
- [x] Update `public/_script/reloadsh.py`: capture output with a temporary file, bound observation, inspect diagnostic text, locate Tabby, and require an affirmative confirmation before exit 43.
- [x] Run the same test command and confirm all restart/discovery cases pass.

## Task 2: PowerShell wrapper and documentation

- [x] Add isolated PowerShell subprocess tests to `test_reloadsh.py` for exit 0/10/43, Python invocation exceptions and missing Python.
- [x] Run the wrapper tests and confirm exception/missing-command cases fail before changing the wrapper.
- [x] Update `Windows/MT_General/reloadsh.ps1` to resolve Python, reset the exit status before invocation, catch invocation errors, and report retention on failure.
- [x] Update `README.md` with startup diagnostics, default retention and confirmation semantics.
- [x] Run all `public/_script` unit tests, PowerShell parsing checks, and `git diff --check`; review the final diff for unrelated changes.

## Validation results

- 44 public-script tests passed, including real subprocess startup failures, early fatal output followed by large logs, and normal midline text at a former chunk boundary.
- PowerShell wrapper tests passed under both PowerShell 7.6 and Windows PowerShell 5.1; both versions also parsed the script successfully.
- Read-only review identified tail-only fatal classification; the new regression failed before the full-log scan and passed after it. A direct bytes-regex scan over the mapped log also preserves exact line and word boundaries.
- `git diff --check` passed. Terminal application windows were not opened or closed during tests.
