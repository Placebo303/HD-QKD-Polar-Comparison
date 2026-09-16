# D5-G1-RSS-ABI-FIX-R1 — repair the live Windows ctypes RSS call

## 0. Why this repair exists

Commit `614aab9e` passes fake tests but fails the real Windows ABI call:

```text
_rss_bytes() -> None
```

Independent read-only diagnosis:

```text
default_handle -1
default GetProcessMemoryInfo ok 0, WorkingSetSize 0
typed GetProcessMemoryInfo ok 1, WorkingSetSize 15978496
sizeof PROCESS_MEMORY_COUNTERS 72
```

Cause: ctypes defaults were used without declaring `GetCurrentProcess.restype`
or `GetProcessMemoryInfo.argtypes/restype`. On 64-bit Windows, explicit WinAPI
types are required. This makes every real G1 run resource-fail, so it blocks
code review and Pre-EXECUTE readiness.

## 1. Scope

Modify only:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
- `openspec/changes/v72p2d5-g1-readiness-rework/tasks.md`

No other file. No new OpenSpec change: the scientific behavior is unchanged;
this is a narrow correction to T2's existing Windows implementation.

## 2. Hard prohibitions

- No decoder and no `--phase` invocation.
- No Model-F prepare/verify and no CAL/VAL/parquet-row read.
- No workspace evidence write/change; proposed G1 and G2 roots stay absent.
- No authorization or lifecycle-state change.
- No dependency, psutil, process-tree monitor, fallback framework, retry, hash,
  or manifest.
- No push/reset/stash/checkout/clean/rebase/amend/broad staging.
- Do not hide failure by returning a fabricated RSS value.

## 3. Required code correction

Inside the existing Windows fallback:

1. use `ctypes.wintypes` (or exactly equivalent fixed WinAPI ctypes types);
2. keep `PROCESS_MEMORY_COUNTERS.cb` and `PageFaultCount` as DWORD and the
   remaining size fields as `c_size_t`;
3. set:

```python
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
psapi.GetProcessMemoryInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
    wintypes.DWORD,
]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
```

4. call with `cb=ctypes.sizeof(PROCESS_MEMORY_COUNTERS)`;
5. return positive integer `WorkingSetSize` only on a true API result;
6. preserve `None` for genuine unavailable/false/exception paths;
7. preserve the Unix `resource` path byte-for-byte except unavoidable context.

Do not alter RSS sampling, outcome precedence, root, signal rule, metrics, or
any other frozen G1 behavior.

## 4. Tests

Repair fake API objects so they support and allow inspection of
`argtypes/restype`; a fake that ignores signatures is no longer sufficient.

Add tests proving:

- HANDLE/BOOL/DWORD/pointer signatures are assigned before the API call;
- fake success returns its working-set integer;
- fake false and unavailable paths return `None`;
- a direct live `_rss_bytes()` smoke returns a positive integer on the current
  host. The test may be platform-conditional only if it checks the Unix
  `resource` path on non-Windows; it must execute the real Windows branch on
  `sys.platform == "win32"` and may not monkeypatch that live-smoke call.

The live smoke is read-only and runs no decoder.

Update `tasks.md` additively with `T2-R1` recording the ABI correction and its
live-smoke evidence. Do not rewrite the original T2 history.

## 5. Verification

Before and after:

- stat retained G1, P0, G0, G0-recovery, Model-F, structure roots;
- confirm proposed G1 `20260907_r2` and G2 roots absent;
- confirm all nine authorization keys false and gate unchanged.

Run:

1. `py_compile` for core and both D5 scripts;
2. focused RSS tests, including the unpatched live smoke;
3. complete three-file D5 suite using a fresh task-specific basetemp under
   `workspace/` and `-p no:cacheprovider`;
4. one operator-level direct import/file-load of the core followed by
   `_rss_bytes()`, requiring `type=int` and value `>0` on this Windows host.

Zero test failures. The known `cache_dir` warning is benign. Remove only this
task's verified basetemp. Roots must be unchanged.

## 6. Commit

Stage exactly the three allowed files and print the staged list. Commit:

```text
fix(v72p2d5): declare WinAPI ctypes signatures for live G1 RSS

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

Do not push.

## 7. Return

Report:

1. exact diff and why fake tests missed the ABI defect;
2. assigned signatures and `sizeof(PROCESS_MEMORY_COUNTERS)`;
3. live pre-fix reference (`None`) and post-fix positive RSS value;
4. focused/full pytest literal lines;
5. pre/post root equality and lifecycle state;
6. commit SHA/status;
7. true/false prohibitions.

End:

`Windows RSS ABI blocker 已修复，等待独立代码评审；G1 未授权、未执行；新 G1 根与 G2 根仍不存在。`

