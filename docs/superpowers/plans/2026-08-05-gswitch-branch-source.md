# gswitch Branch Source Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `gswitch` visibly distinguish local and remote-tracking branches while preserving Enter-to-switch.

**Architecture:** `gswitch.py` builds testable display rows and writes a tab-delimited source payload. `git.ps1` routes local payloads to `git switch <branch>` and remote payloads to an existing local branch or `git switch --track <remote/ref>`.

**Tech Stack:** Python standard library, Questionary, Windows PowerShell 5.1, Git.

## Global Constraints

- Do not run `git fetch`; remote rows are cached remote-tracking refs.
- Show both `[本地] branch` and `[远端] origin/branch` when names overlap.
- Keep the current local branch first and marked with `*`.
- Keep direction-key selection and Enter-to-switch behavior.
- Do not change `gswitch <branch>` or its completer.

---

### Task 1: Produce labelled, source-aware menu rows

**Files:**
- Create: `public/_script/test_gswitch.py`
- Modify: `public/_script/gswitch.py`

**Interfaces:**
- Produces: `build_branch_items(current: str, locals_: list[str], remotes: list[str]) -> list[tuple[str, str, str]]`.
- Produces: `local\t<branch>` and `remote\t<remote>/<branch>` as values passed to `write_temp_file`.

- [ ] **Step 1: Write the failing test**

~~~python
import unittest

import gswitch


class BranchMenuTests(unittest.TestCase):
    def test_marks_local_and_remote_without_hiding_same_name(self):
        self.assertEqual(
            gswitch.build_branch_items(
                "main",
                ["feature/a", "main"],
                ["origin/HEAD", "origin/feature/a", "origin/release"],
            ),
            [
                ("main", "* [本地] main", "local\tmain"),
                ("feature/a", "  [本地] feature/a", "local\tfeature/a"),
                ("origin/feature/a", "  [远端] origin/feature/a", "remote\torigin/feature/a"),
                ("origin/release", "  [远端] origin/release", "remote\torigin/release"),
            ],
        )
~~~

- [ ] **Step 2: Confirm the test fails**

Run `python -m unittest test_gswitch -v` from `public/_script`.

Expected: FAIL because `build_branch_items` does not exist.

- [ ] **Step 3: Add the smallest builder and use it from `main()`**

~~~python
def build_branch_items(
    current: str, locals_: list[str], remotes: list[str]
) -> list[tuple[str, str, str]]:
    locals_sorted = sorted(locals_, key=lambda b: (b != current, b.lower()))
    remotes_sorted = sorted(
        (ref for ref in remotes if not ref.endswith("/HEAD")), key=str.lower
    )
    items = [
        (b, f"{'* ' if b == current else '  '}[本地] {b}", f"local\t{b}")
        for b in locals_sorted
    ]
    items.extend(
        (ref, f"  [远端] {ref}", f"remote\t{ref}")
        for ref in remotes_sorted
    )
    return items
~~~

In `main()`, call `build_branch_items(current, _list_locals(), _list_remotes())`; remove `_switch_arg_for_remote()` and the duplicate-remote filter.

- [ ] **Step 4: Run the focused test and commit**

Run `python -m unittest test_gswitch -v` from `public/_script`. Expected: 1 test passes.

~~~bash
git add public/_script/gswitch.py public/_script/test_gswitch.py
git commit -m "feat: 标识 gswitch 本地与远端分支"
~~~

### Task 2: Route the selection payload in PowerShell

**Files:**
- Modify: `Windows/MT_General/git.ps1:127-166`
- Test: `public/_script/test_gswitch.py`

**Interfaces:**
- Consumes: UTF-8 `local\t<branch>` or `remote\t<remote>/<branch>` from the temp file.
- Produces: `git switch <branch>` for local/existing branches, otherwise `git switch --track <remote/ref>`.

- [ ] **Step 1: Keep exact payload assertions in the Task 1 test**

The values must remain `local\tmain` and `remote\torigin/feature/a`; this prevents a label-only change that leaves PowerShell unable to choose the correct Git command.

- [ ] **Step 2: Confirm the producer contract**

Run `python -m unittest test_gswitch.BranchMenuTests.test_marks_local_and_remote_without_hiding_same_name -v` from `public/_script`.

Expected: PASS.

- [ ] **Step 3: Replace the current `$target` switch block**

~~~powershell
$selection = (Get-Content -Path $tempFile -Raw -Encoding UTF8 -ErrorAction SilentlyContinue).Trim()
$parts = $selection -split "`t", 2
if ($parts.Count -ne 2 -or [string]::IsNullOrWhiteSpace($parts[1])) {
    Write-Host "❌ 无效的分支选择结果" -ForegroundColor Red
    return
}

$source = $parts[0]
$ref = $parts[1]
if ($source -eq 'local') {
    git switch $ref
    return
}
if ($source -eq 'remote') {
    $localBranch = ($ref -split '/', 2)[1]
    if ([string]::IsNullOrWhiteSpace($localBranch)) {
        Write-Host "❌ 无效的远端分支: $ref" -ForegroundColor Red
        return
    }
    git show-ref --verify --quiet "refs/heads/$localBranch"
    if ($LASTEXITCODE -eq 0) { git switch $localBranch }
    else { git switch --track $ref }
    return
}
Write-Host "❌ 未知的分支来源: $source" -ForegroundColor Red
~~~

Leave the outer `finally` intact so the temporary file is removed after Enter triggers Git.

- [ ] **Step 4: Parse and manually check the switch flow**

~~~powershell
$tokens = $null; $errors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
  (Resolve-Path 'Windows\MT_General\git.ps1'), [ref]$tokens, [ref]$errors
) | Out-Null
if ($errors.Count) { $errors; exit 1 }
~~~

Then run `gswitch` in a Git repository, select the current `[本地]` item and press Enter. Expected: the branch remains/switches as before. Select a remote-only `[远端]` item. Expected: Git creates and switches to a tracking branch.

- [ ] **Step 5: Commit switch routing**

~~~bash
git add Windows/MT_General/git.ps1 public/_script/gswitch.py public/_script/test_gswitch.py
git commit -m "feat: 支持 gswitch 切换远端跟踪分支"
~~~

### Task 3: Run regressions

**Files:**
- Verify: `public/_script/test_common.py`, `public/_script/test_reloadsh.py`, `public/_script/test_gswitch.py`, `Windows/MT_Tool/src/test_license_paths.py`

- [ ] **Step 1: Run all public-script tests**

Run `python -m unittest discover -s . -p "test_*.py" -v` from `public/_script`.

Expected: existing 5 tests plus the new gswitch test pass.

- [ ] **Step 2: Run license-path regression tests**

Run `python -m unittest discover -s . -p "test_*.py" -v` from `Windows/MT_Tool/src`.

Expected: 2 tests pass.

- [ ] **Step 3: Check final changes**

Run `git diff --check` and `git status --short`.

Expected: no whitespace errors in gswitch files; report but do not stage unrelated changes.
