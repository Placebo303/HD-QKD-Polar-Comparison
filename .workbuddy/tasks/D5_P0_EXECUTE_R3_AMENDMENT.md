# AMENDMENT — D5-P0-EXECUTE-R3 (amends R2; R2 is otherwise still in force)

Issued by the packet author after `LOADER_FIX_REVIEW_R1` returned
`LOADER_FIX_REVIEW_PASS`. Read this together with
`D5_P0_EXECUTE_R2_TASK_PACKET.md`. Everything in R2 stays in force except the
two items superseded below.

## A.0 Why

Two defects in R2, both the author's:

1. **The STEP 2 reachability probe did not reproduce the condition it was
   meant to test.** Run via `python -c` from the repository root, `sys.path[0]`
   is `''` — the repository root — so the package import that broke R1 would
   have succeeded anyway. The reviewer's independent probe went further and
   explicitly inserted the repository root into `sys.path`. Neither run proved
   anything about script launch. A probe that cannot fail for the original
   cause is not a gate.

2. **R2's `E6 clean tracked tree` gate cannot pass and should not be asked
   to.** At `2026-09-07T17:22:29` every tracked file's mtime changed and
   `git status` now flags ~1887 paths, while `git diff --numstat` reports zero
   content change across the repository — the difference is line-ending
   representation only, with `core.autocrlf=true` and no `.gitattributes`.
   Commit `299416ae` carries none of it. The review judged this cosmetic, not
   blocking, and recommended narrowing cleanliness gates to real content
   differences. That recommendation is adopted.

## A.1 SUPERSEDED — R2 STEP 2 probe

The R2 STEP 2 command is void. Replace it with A.2. Do not run the R2 version.

## A.2 NEW — STEP 2' reachability under the real launch condition

The probe must run from a script file **outside** the repository, so that
`sys.path[0]` is that file's directory and the repository root is absent from
`sys.path`, while the working directory remains the repository root. Do not
insert the repository root into `sys.path`. Do not run it with `python -c`.

Write the probe to a path outside the repository, for example under your
system temp directory, then run it with the repository as the working
directory:

```python
# reach_probe.py  — place OUTSIDE the repository
import sys, os, pathlib, tempfile, importlib.util, traceback
REPO = pathlib.Path("D:/Code/HD-QKD_Polar_Comparison")
print("sys.path[0]=", repr(sys.path[0]))
print("cwd=", os.getcwd())
print("repo_root_on_sys_path=",
      any(pathlib.Path(p).resolve() == REPO for p in sys.path if p))
try:
    import comparison_bench  # noqa: F401
    print("package_import_available= True")
except Exception as e:
    print("package_import_available= False", type(e).__name__)

core = REPO / "comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py"
spec = importlib.util.spec_from_file_location("core_probe", str(core))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class Probe(Exception): pass
calls = []
def probe(*a, **k):
    calls.append(1); raise Probe("REACHED_FIRST_DECODER_CALL")

tmp = tempfile.mkdtemp(prefix="reach_true_")
try:
    m.run_p0_cost_synthetic(authorized=True, decode_fn=probe, out_dir=tmp)
    print("REACH_UNEXPECTED_COMPLETION")
except Probe as e:
    print("REACH_OK", e, "probe_calls", len(calls))
except Exception as e:
    print("REACH_FAIL", type(e).__name__, e); traceback.print_exc()
print("tmp_contents", sorted(p.name for p in pathlib.Path(tmp).iterdir()))
print("p0_root", (REPO/"workspace/v72p2d5_p0_cost/20260906_r1").exists(),
      "g2_root", (REPO/"workspace/v72p2d5_g2/20260906_r1").exists())
```

**Required outcome — all five, or STOP:**

- `repo_root_on_sys_path= False`
- `package_import_available= False ModuleNotFoundError` — this is what proves
  the probe is running under the condition that broke R1. **If this prints
  `True`, the probe is invalid; fix the launch condition, not the code, and
  re-run before proceeding.**
- `REACH_OK REACHED_FIRST_DECODER_CALL probe_calls 1`
- `tmp_contents []`
- `p0_root False g2_root False`

`REACH_FAIL` → STOP, flip nothing, report the traceback verbatim. No
authorization is consumed, which is the point of this step.

For reference, the author obtained exactly this outcome on `299416ae` at
authoring time. **Reproduce it yourself; do not cite the author's run.**

## A.3 SUPERSEDED — R2 STEP 1 gate E6

R2's `E6 clean tracked tree` is void. Replace it with E6':

```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git diff --numstat 2>/dev/null | awk '$1!="0"||$2!="0"{c++} END{print "files_with_content_change:", c+0}'
```

Required: `files_with_content_change: 0`. Line-ending-only differences are
expected and are **not** a failure.

Additionally record, for the authorization record only, the raw count:
```bash
cd "D:/Code/HD-QKD_Polar_Comparison" && git status --porcelain=v1 | grep -cE "^ M|^M "
```
This number is informational. Do not act on it, and do not attempt to reduce
it. **`git checkout`, `git add --renormalize`, `git clean`, and `git reset`
remain forbidden.** Repository-side line-ending normalization is a separate
matter and is explicitly not a P0 precondition.

## A.4 Also record in the authorization record

Add to `P0_AUTHORIZATION_RECORD_R2.md`, alongside what R2 already requires:

- the literal STEP 2' output including the two condition lines
  (`repo_root_on_sys_path`, `package_import_available`);
- the E6' content-change count and the informational raw modified count;
- a note that `LOADER_FIX_REVIEW_R1` returned `LOADER_FIX_REVIEW_PASS`, that
  its own probe ran with the repository root on `sys.path` and was therefore
  not conclusive about script launch, and that STEP 2' supersedes it.

## A.5 Everything else

Unchanged from R2: GATE ZERO, the authorization gate, all hard prohibitions,
the watchdog rehearsal, the single invocation, immediate revocation, the
operator return, the addendum A1 file, and the report format. The frozen
`P0_EXECUTION_PACKET.md` stays byte-identical.
