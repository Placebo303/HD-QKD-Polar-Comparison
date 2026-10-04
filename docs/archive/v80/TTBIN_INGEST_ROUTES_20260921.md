# .ttbin ingest routes — WSL↔Windows feasibility reconnaissance (2026-09-21)

**Scope:** READ-ONLY feasibility. No `.ttbin` was parsed. No pipeline was run on any data.
No package was installed or downloaded. No writes outside `/tmp/opencode/` (probe scratch)
and this single report file. No commit/push. All probes run from WSL in
`/mnt/d/Code/HD-QKD_Polar_Comparison`.

**Background:** `src/qkd_io/ttbin_pipeline.py::read_ttbin_events` does
`from TimeTagger import FileReader` (line 148) and raises
`RuntimeError("TimeTagger package not available...")` when absent. Confirmed absent in WSL:
both the repo `.venv` (Python 3.12.3, numpy 2.5.3, pandas 3.0.5) and system python3 (3.12.3)
raise `ModuleNotFoundError: No module named 'TimeTagger'`.

---

## Task 1 — Can WSL invoke the Windows side at all? YES

- `ls /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe` → exists
  (`-r-xr-xr-x ... powershell.exe`, Sep 9). `pwsh.exe` NOT found (`which` empty).
- Bare `powershell.exe` is **not** on WSL `PATH`
  (`PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:...:/usr/lib/wsl/lib`;
  `powershell.exe -NoProfile ...` → `command not found`, exit 127).
- **Full-path invocation works.** `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
  -NoProfile -Command "echo hello"` → `hello`, EXIT 0. WSLInterop is `enabled`
  (`/proc/sys/fs/binfmt_misc/WSLInterop`). So WSL **can** invoke the Windows side;
  callers must use the full path (or full Windows-exe path), not the bare name.
- `powershell.exe -NoProfile -Command "python --version; python -c 'import sys;
  print(sys.executable)'"` → `Python 3.12.12` + `D:\software\Miniforge3\python.exe`.
- `where.exe python` (via full-path powershell) found, in order:
  1. `D:\software\Miniforge3\python.exe` (default `python`, 3.12.12)
  2. `D:\software\Anaconda3\python.exe` (3.13.9)
  3. `C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe` (3.11.9)
  4. `C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe` (3.12.10;
     `py -3 --version` → `Python 3.12.10`, i.e. `py -3` maps here)
  5. `C:\Users\admin\AppData\Local\Microsoft\WindowsApps\python.exe` (Store stub, not probed further)
- WSL-visible equivalents confirmed: `/mnt/d/software/Miniforge3`,
  `/mnt/d/software/Anaconda3`, `/mnt/c/Users/admin/AppData/Local/Programs/Python/{Python311,Python312}`.
  `C:\ProgramData` has no Anaconda/Miniconda; `/mnt/c/Users/admin/{anaconda3,miniconda3}` absent.
  Conda envs: Miniforge → `paper2slides`; Anaconda → `qkd_env`.

## Task 2 — Does the Windows python actually have TimeTagger? YES (4 interpreters)

Exact probe per interpreter (via full-path `powershell.exe`):
`& '<PY>' -c "import TimeTagger, sys; print('OK', getattr(TimeTagger,'__version__',
'version-attr-missing')); print(TimeTagger.__file__)"`

| Interpreter (Windows path) | Result |
|---|---|
| `D:\software\Miniforge3\python.exe` | `OK version-attr-missing` → `C:\Program Files\Swabian Instruments\Time Tagger\driver\python\TimeTagger\__init__.py`, EXIT 0 |
| `D:\software\Anaconda3\python.exe` | same `OK`, same `__file__`, EXIT 0 |
| `D:\software\Anaconda3\envs\qkd_env\python.exe` | `TT OK 2.20.2 True` via `Swabian.TimeTagger` (`getVersion()` + `hasattr FileReader`), EXIT 0 |
| `D:\software\Miniforge3\envs\paper2slides\python.exe` | `TT OK 2.20.2 True`, EXIT 0 |
| `...\Python311\python.exe` | FAIL: resolves the **same** `TimeTagger/__init__.py` path, then `ModuleNotFoundError: No module named 'numpy'` (line 12 `import numpy as _np`), EXIT 1 |
| `...\Python312\python.exe` | same FAIL (`No module named 'numpy'`), EXIT 1 |

- Mechanism: system-wide `PYTHONPATH=C:\Program Files\Swabian Instruments\Time Tagger\driver\python`
  (confirmed via `$env:PYTHONPATH` in powershell; appears as first `sys.path` entry in both
  Miniforge and Anaconda). No Swabian `.pth` in Miniforge site-packages (grep over `*.pth` no match).
  Consequence: **every** Windows python sees the vendor wrapper; only ones with numpy can import it.
- **Windows-only conclusion:** the resolved module path is under `C:\Program Files\...`
  (`/mnt/c/...` from WSL) and the compiled backend is a Windows `.pyd`/DLL (Task 3).
  It is **NOT loadable by WSL Linux python** — confirmed empirically by the WSL
  `ModuleNotFoundError` above. Stated explicitly as required.

## Task 3 — Version + binary portability: Windows-only, NOT portable to WSL

- Full versions (Windows): Miniforge base `3.12.12 | packaged by conda-forge | (main, Oct 22 2025,
  23:13:34) [MSC v.1944 64 bit (AMD64)]`; Anaconda base `3.13.9 | packaged by Anaconda, Inc. |
  (main, Oct 21 2025, 19:09:58) [MSC v.1929 64 bit (AMD64)]`; `qkd_env` `3.11.14`
  (conda-forge, MSC v.1944); `paper2slides` `3.12.12` (conda-forge).
- Safe version probe `Swabian.TimeTagger.getVersion()` → **`2.20.2`** on both Miniforge and
  Anaconda; `getCompilerVersion()` → `MSVC 19.44.35217.0 (MSVC: 1944)`; wrapper header notes
  `SWIG 4.3.0`. `TimeTagger.__version__` attribute is absent (`version-attr-missing`); use
  `getVersion()`. Safe API surface (attribute listing only, no file I/O): `FileReader`,
  `FileWriter`, `getVersion`, `getCompilerVersion`, `mergeStreamFiles` all present.
- Package layout: `driver/python/` contains only `Swabian/TimeTagger/{__init__.py,
  _TimeTagger.cxx, _TimeTagger.h}` + legacy shim `TimeTagger/__init__.py`
  (`from Swabian.TimeTagger import *` with deprecation warning). **No `.pyd`/`.so` beside the
  wrapper.** The compiled backend is loaded at import from the Windows registry
  `HKLM\SOFTWARE\Swabian Instruments\Time Tagger` (`BaseDirectory`+`DllSubDirectory`) with a
  non-Windows fallback that re-raises — i.e. Linux import cannot succeed by design.
- Binaries: `driver/x64/_TimeTagger.pyd` (2,268,480 B, Dec 17 2025) and
  `driver/x86/_TimeTagger.pyd` (2,219,840 B), alongside `TimeTagger.dll`, `libTimeTagger.dll`,
  `okFrontPanel.dll`, .NET `SwabianInstruments.TimeTagger.dll` + policy assemblies.
  Extensions are **`.pyd` (Windows), zero `.so`**. It **cannot** be copied to WSL; a Linux
  interpreter cannot load a `.pyd`/Win DLL.
- License-ish filenames (names only, contents not read): `documentation/Third Party
  Licenses.txt`, `driver/{x64,x86}/LicenseRequestGenerator.exe`, `examples/license.txt`,
  `Time Tagger Lab/licenses/`, `Time Tagger Lab/Syncfusion.Licensing.dll`. No `TimeTagger`
  `dist-info` in Miniforge/Anaconda site-packages (the `timetagger-26.1.1.dist-info` found there
  is the **unrelated** Almar Klein time-tracker, GPL-3.0 — see Task 6).

## Task 4 — Usable Windows env for THIS repo? YES (conda side; repo .venv is Linux-only)

- Repo `.venv/` contains **Linux** artifacts: `bin/python{,3,3.12}`, `lib/`, `lib64 -> lib`,
  `pyvenv.cfg` (`home = /usr/bin`, `version = 3.12.3`); `Scripts/python.exe` **absent**.
  It is a WSL venv, not usable from Windows.
- numpy/pandas per candidate (`python -c "import numpy, pandas; ..."` via powershell):
  Miniforge base numpy **2.4.0** / pandas **2.3.3**; Anaconda base numpy **2.3.5** / pandas
  **2.3.3**; `qkd_env` numpy **2.3.4** / pandas **2.3.3**; `paper2slides` numpy **2.4.1** /
  pandas **2.3.3**. All four import `Swabian.TimeTagger` OK. The two Python.org installs have
  **no numpy** → TimeTagger import fails. So "run ingest on Windows" is practical with any of
  the four conda interpreters (numpy+pandas+TimeTagger all present).
- Note: Miniforge `sys.path` also contains `D:\Code\JTI_extract_clean\src` and an editable
  `jti_extract-0.1.0` install — someone's active Windows project; do not disturb.

## Task 5 — WSL→Windows data path sanity (no writes outside approved scratch)

- `/mnt/d/` writability was **not** directly tested with a write (task hard constraint allows
  writes only under `/tmp/opencode/` + this report). Read access from WSL is confirmed
  throughout (all listings above). `/` (`/dev/sdd`) hosts `/tmp`.
- Free space (`df -h`): `/mnt/d` (D:\, 932G) **413G avail** (56% used); `/mnt/c` (C:\, 930G)
  **600G avail** (36% used); `/` (1007G) 922G avail. Space is ample.
- **Size/space arithmetic (explicit assumptions, no measurement — no .ttbin parsed):**
  assume a ~40 MiB ttbin (`40×2²⁰ = 41,943,040 B`) holds T timetags at `b` bytes/event on disk,
  so `T ≈ 41.9MB / b`. Extracted in memory as int64 timetag (8 B) + channel (4 B as int32,
  up to 8 B with alignment/padding in a structured array), i.e. ~12–16 B/event:
  - `b=8` → ~5.2M events → **~62–83 MB** in memory (two arrays or one structured array);
  - `b=12` → ~3.5M events → **~42–56 MB**;
  - `b=16` → ~2.6M events → **~31–42 MB**.
  Same order for `.npz`/`.parquet` on disk. A text/CSV export (~20–30 chars/event) would be
  **~100–150+ MB**. Even a 10× blow-up (~400 MB) is <0.1% of the 413G free on D:\.
  **Flag: space is not tight; no capacity risk for single-file or small-batch extracts.**
  Streaming via `FileReader` blocks bounds peak RAM regardless.
- Write speed: 50 MiB (`50×2²⁰` zero bytes) to `/tmp/opencode/tt_probe/speedtest_50m.bin`
  took **0.059 s wall** (~850 MB/s WSL-local); probe file removed afterwards.
  Cross-OS (`/mnt/d`) write timing is **deliberately untested** (would require a write outside
  the approved scratch). Expect it to be slower than WSL-local but irrelevant at these sizes.

## Task 6 — Any other route?

- **PyPI route: NO — and hazardous.** Per hard constraints (no installs/downloads/network),
  `pip download` was not attempted and `pip index versions TimeTagger` was **deliberately not
  run** (network query; install-adjacent). It is also unnecessary: Miniforge site-packages
  contains `timetagger-26.1.1.dist-info` whose METADATA is `Name: timetagger, Version: 26.1.1,
  Summary: Tag your time..., Home-page: github.com/almarklein/timetagger, License: GPL-3.0` —
  **an unrelated open-source time-tracker**. `pip install TimeTagger`/`timetagger` in WSL would
  fetch the **wrong package** (plus violate the no-install constraint). The vendor package is
  supplied via the Swabian installer + system `PYTHONPATH`, not PyPI.
- **Swabian CLI/GUI utilities:** `ls "/mnt/c/Program Files/"` shows `Swabian Instruments`
  (only match for `swabian|time`); `(x86)` has no match. Inside:
  `Time Tagger/{TimeTaggerServer/,Time Tagger Lab/,driver/,examples/,documentation/}`.
  `TimeTaggerServer/TimeTaggerServer.exe` exists (a bundled server app, ships its own
  cp38 `.pyd`s), `examples/{python,cpp,csharp,Matlab,LabView}` include e.g.
  `12b_File_Replay_With_Virtual_TimeTagger.vi` and python `1-Quickstart…9-Coincidences`
  folders; no standalone file-export CLI was identified by name search. A GUI/server-assisted
  export is **possible but unverified** — the scripted `FileReader` route below dominates it.

---

## Bottom-line ROUTES table

| # | Route | Feasibility | Requires | Cost / risk | What stays in WSL |
|---|---|---|---|---|---|
| R1 | **Windows ingest script → portable arrays** with `D:\software\Miniforge3\python.exe` (`FileReader` → `.npz`/`.parquet` on D:\), analyze in WSL repo `.venv` | **YES** (proven import + numpy/pandas) | Small exporter script run on Windows side (manual double-click or `powershell`/`python.exe` call); agreed output dir + naming (append-only, never overwrite raw) | Low. Version-pinned note (`getVersion 2.20.2`, py 3.12.12, numpy 2.4.0). Must keep exporter minimal; no repo changes needed beyond reader of `.npz` | All analysis, comparison bench, plotting, statistics |
| R1b | Same via `D:\software\Anaconda3\envs\qkd_env\python.exe` (py 3.11.14, numpy 2.3.4) | **YES** | Same as R1 | Low; name suggests QKD relevance — check with owner before adopting | Same as R1 |
| R2 | Drive it from WSL via interop (`/mnt/d/software/Miniforge3/python.exe ...` or full-path `powershell.exe`) | **YES** (proven: direct `.exe` call from WSL printed `3.12.12 ... D:\software\Miniforge3\python.exe`) | Quoting care (spaces in `Program Files` avoided since interpreter lives on D:\); Windows-style paths for data args | Low; thin wrapper only. Still executes on Windows — same semantics as R1 | Orchestration + analysis |
| R3 | Copy vendor package/`.pyd` to WSL | **NO** | — | Windows `.pyd`/DLL + registry DLL-path + MSVC runtime; wrapper re-raises off-Windows by design | — |
| R4 | `pip install TimeTagger` in WSL | **NO** | — | Wrong package on PyPI (`timetagger` 26.1.1 = Almar Klein time-tracker); vendor ships via installer, not PyPI; installs forbidden | — |
| R5 | `TimeTaggerServer.exe` / Lab GUI export | **LIKELY but UNVERIFIED** | Manual GUI steps or server protocol work | Medium; opaque, hard to reproduce/version; not probed (would need interactive session) | Analysis only |
| R6 | Fix Python.org Windows pythons (add numpy) and use them | POSSIBLE but pointless | Would need installs on Windows side | Unneeded — four working conda interpreters already exist; avoid touching them | — |

**Which parts stay in WSL under R1/R2:** everything except the one Windows-side `FileReader`
loop: WSL keeps dataset building, frame assembly, Polar baselines, comparison bench, and all
result outputs. The Windows step emits content-addressed portable arrays (`.npz` with
`time_ps: int64`, `channel: int32` + JSON sidecar recording `getVersion()`, command, input
name/size, row count) into a staging/output dir; WSL never needs `TimeTagger`.

## Recommendation

**Adopt R1 driven via R2, on `D:\software\Miniforge3\python.exe` (default `python`).**
Why: (a) import of `Swabian.TimeTagger` (`getVersion 2.20.2`, `FileReader` present) proven in
this exact interpreter; (b) numpy 2.4.0 + pandas 2.3.3 already present, so the exporter can do
block reads → `numpy` arrays → `.npz`/`.parquet` without new installs; (c) it is the default
`python` on the Windows side and directly invocable from WSL
(`/mnt/d/software/Miniforge3/python.exe`), enabling a thin reproducible bridge; (d) copying
binaries (R3) is impossible (`.pyd`/DLL/registry design) and PyPI (R4) is a name-collision trap;
(e) space is ample (413G free on D:\) and single-file extracts are ~30–80 MB by the
assumption-explicit arithmetic above, so staging on D:\ is trivially affordable.
Keep `qkd_env` (R1b) as fallback. Next step (needs DECIDE authorization, not done here): a
minimal Windows exporter + a WSL reader check on a staged copy, with checksums/row-counts
recorded in the sidecar — no `.ttbin` touched until that authorization exists.

---
*Constraints obeyed: no `.ttbin` parsed, no pipeline executed, no package installed/downloaded,
no network pip query (PyPI conclusion drawn from on-disk dist-info instead), no writes outside
`/tmp/opencode/` scratch (since cleaned) and this report, no commit/push.*
