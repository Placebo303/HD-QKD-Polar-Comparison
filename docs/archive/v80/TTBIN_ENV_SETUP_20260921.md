# TTBIN Environment Setup — Stage 0 Report (2026-09-21)

Stage 0 (environment) only. No `.ttbin` file was opened, parsed, or listed; no
pipeline/decoder/DE/`tools/*` script was run on data; no repo source file was
modified; no commit/push. Writes this turn: `pip install` into repo `.venv`
(explicitly approved) + this report file.

Reference working install: `/home/karel_303/.venvs/timetagger`
(Swabian-TimeTagger 2.22.6, numpy 2.5.3, `from Swabian import TimeTagger` OK).
Repo venv: `/mnt/d/Code/HD-QKD_Polar_Comparison/.venv` (Python 3.12.3).

---

## Task 1 — Repo's import form (read code, not run)

`src/qkd_io/ttbin_pipeline.py`, lines 91–96 (docstring, verbatim):

```python
def read_ttbin_events(ttbin_file: Path | str) -> TTBinEvents:
    """Read .ttbin using TimeTagger's FileReader if available.

    This function intentionally does not implement a binary parser for the .ttbin format.
    It relies on the official TimeTagger Python package when installed.
    """
```

Lines 147–150 (verbatim):

```python
    try:
        from TimeTagger import FileReader  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"TimeTagger package not available; cannot read .ttbin: {exc}") from exc
```

- Exact import statement: `from TimeTagger import FileReader` (top-level module).
- Exact `RuntimeError` message template:
  `TimeTagger package not available; cannot read .ttbin: {exc}`
- Form used: **top-level `TimeTagger`** (`from TimeTagger import ...`).
  NOT `from Swabian import TimeTagger`. No other import form in this file.
  The import is function-local (inside `read_ttbin_events`), so the module
  itself imports cleanly even when the package is absent.

Whole-repo grep `grep -rn "TimeTagger" --include='*.py'` — every distinct
**import** form found (comment/string mentions excluded):

| File:line | Verbatim import form |
|---|---|
| `src/qkd_io/ttbin_pipeline.py:148` | `from TimeTagger import FileReader  # type: ignore` |
| `openspec/changes/formal-ir-v56d1-raw-a2-diagnosis/diagnosis_raw_a2.py:243` | `_ilu.find_spec("TimeTagger")` (spec probe, no import) |
| `openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration.py:66` | `importlib.util.find_spec("TimeTagger")` (spec probe, no import) |
| `openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration.py:70` | `importlib.metadata.version("TimeTagger")` (metadata, no import) |
| `openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration.py:73` | `import TimeTagger` |
| `openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration.py:81` | `import TimeTagger as _tt` |
| `openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration.py:116` | `importlib.util.find_spec("TimeTagger")` (spec probe, no import) |
| `openspec/changes/formal-ir-v56d2-calibration/v56d2_calibration.py:118` | `import TimeTagger  # noqa: F401 — verify importable` |

All real imports assume a **top-level `TimeTagger` module**. The v56d2 script
additionally notes the historically successful env was
`D:\software\Miniforge3\python.exe` with driver
`C:\Program Files\Swabian Instruments\Time Tagger\driver\python\TimeTagger`
— i.e. the vendor Windows driver layout, which ships a top-level `TimeTagger`
package. No file anywhere uses `from Swabian import TimeTagger`.

---

## Task 2 — Both import forms in the user's working venv

Interpreter: `/home/karel_303/.venvs/timetagger/bin/python` (Python 3.12.3).

Verbatim outputs:

```
$ python -c "from Swabian import TimeTagger; print('OK from-Swabian', TimeTagger.__file__)"
OK from-Swabian /home/karel_303/.venvs/timetagger/lib/python3.12/site-packages/Swabian/TimeTagger/__init__.py
---EXIT:0
```

```
$ python -c "import TimeTagger; print('OK top-level', TimeTagger.__file__)"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'TimeTagger'
---EXIT:1
```

**Decisive result: the package exposes ONLY `Swabian.TimeTagger`; there is NO
top-level `TimeTagger` module.** `pip show Swabian-TimeTagger` (verbatim header):

```
Name: Swabian-TimeTagger
Version: 2.22.6
Summary: Python libraries for the Swabian Instruments Time Tagger
Author-email: Swabian Instruments GmbH <support@swabianinstruments.com>
Location: /home/karel_303/.venvs/timetagger/lib/python3.12/site-packages
Requires: numpy
Required-by:
```

Package directory listing:

```
site-packages/
  Swabian/                      <- only namespace dir; no top-level TimeTagger, no .pth
  numpy, numpy-2.5.3.dist-info, numpy.libs, pip, pip-24.0.dist-info
  swabian_timetagger-2.22.6.dist-info
Swabian/TimeTagger/
  _TimeTagger.so  __init__.py  __pycache__  firmware/  libTimeTagger.so  libokFrontPanel.so.1
```

Reference venv extras: `numpy==2.5.3`, `pip==24.0`,
`Swabian-TimeTagger==2.22.6` only; **pandas NOT installed**
(`ModuleNotFoundError: No module named 'pandas'`); `Python 3.12.3`.
`Swabian.TimeTagger` exposes `FileReader`:
`['FileReader', 'FileWriter', 'mergeStreamFiles', 'setCustomBitFileName']`;
`FileReader.__init__` signature: `(self, *args)` (docstring excerpt in Task 4).

---

## Task 3 — Install into the repo venv (APPROVED)

Baseline (before install), verbatim:

```
$ .venv/bin/python -c "import numpy, pandas, numba; print(numpy.__version__, pandas.__version__, numba.__version__)"
2.5.3 3.0.5 0.67.0
$ .venv/bin/python --version
Python 3.12.3
```

Before-freeze (`/tmp/opencode/repo_venv_before.txt`): contourpy 1.3.3,
cycler 0.12.1, fonttools 4.64.0, iniconfig 2.3.0, kiwisolver 1.5.1,
llvmlite 0.49.0, matplotlib 3.11.1, numba 0.67.0, numpy 2.5.3, packaging 26.3,
pandas 3.0.5, pillow 12.3.0, pip 26.2.1, pluggy 1.6.0, pyarrow 25.0.1,
Pygments 2.21.0, pyparsing 3.3.2, pypdf 6.19.0, pytest 9.1.1,
python-dateutil 2.9.0.post0, PyYAML 6.0.3, six 1.17.0, tqdm 4.70.0.
Note: repo venv numpy (2.5.3) already equals reference venv numpy (2.5.3),
so `--no-deps` was safe (`Requires: numpy` already satisfied).

Install — first attempt with `--no-deps` SUCCEEDED, no retry needed.
Full pip output (verbatim):

```
$ .venv/bin/pip install --no-deps Swabian-TimeTagger==2.22.6
Collecting Swabian-TimeTagger==2.22.6
  Using cached swabian_timetagger-2.22.6-cp38-abi3-manylinux_2_28_x86_64.whl.metadata (2.0 kB)
Using cached swabian_timetagger-2.22.6-cp38-abi3-manylinux_2_28_x86_64.whl (32.7 MB)
Installing collected packages: Swabian-TimeTagger
Successfully installed Swabian-TimeTagger-2.22.6
---EXIT:0
```

Post-install freeze diff vs before (verbatim `diff`):

```
22a23
> Swabian-TimeTagger==2.22.6
```

i.e. the ONLY change is the added package — **no numpy upgrade/downgrade,
no other dep touched** (the `WITHOUT --no-deps` retry was not needed).

---

## Task 4 — Verify after install (repo `.venv`), verbatim

```
$ .venv/bin/python -c "import TimeTagger; print('top-level OK', TimeTagger.__file__)"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'TimeTagger'
---EXIT:1
```

```
$ .venv/bin/python -c "from Swabian import TimeTagger; print('from-Swabian OK', TimeTagger.__file__)"
from-Swabian OK /mnt/d/Code/HD-QKD_Polar_Comparison/.venv/lib/python3.12/site-packages/Swabian/TimeTagger/__init__.py
---EXIT:0
```

Deps intact (verbatim):

```
$ .venv/bin/python -c "import numpy, pandas; print(numpy.__version__, pandas.__version__)"
2.5.3 3.0.5
$ .venv/bin/python -c "import numba; print(numba.__version__)"
0.67.0
```

FileReader presence (verbatim): `['FileReader', 'FileWriter',
'mergeStreamFiles', 'setCustomBitFileName']` — **`FileReader` exists**.
Three-level form also works (verbatim):
`from Swabian.TimeTagger import FileReader` →
`Swabian.TimeTagger.FileReader OK: <class 'Swabian.TimeTagger.FileReader'>`.

Signature/docs WITHOUT opening any file (verbatim):

```
$ .venv/bin/python -c "from Swabian import TimeTagger; import inspect; print(inspect.signature(TimeTagger.FileReader.__init__)); print((TimeTagger.FileReader.__doc__ or '')[:1200])"
(self, *args)

    This class allows you to read data files store with `FileReader`.
    The `FileReader` reads a data block of the specified size into a `TimeTagStreamBuffer` object and
    returns this object. The returned data object is exactly the same as returned by the `TimeTagStream` measurement
    and allows you to create a custom data processing algorithms that will work both,
    for reading from a file and for the on-the-fly processing.

    The `FileReader` will automatically recognize if the files were split and read them too one by one.

    Example:

    .. code-block:: python

        # Lets assume we have following files created with the FileWriter
        #  measurement.ttbin     # sequence header file with no data blocks
        #  measurement.1.ttbin   # the first file with data blocks
        #  measurement.2.ttbin
        #  measurement.3.ttbin
        #  measurement.4.ttbin
        #  another_meas.ttbin
        #  another_meas.1.ttbin

        # Read all files in the sequence 'measurement'
        fr = FileReader("measurement.ttbin")

        # Read only the first data file
        fr = FileReader("measurement.1.ttbin")

        # Read only the first two files
        fr
```

(Identical signature/docstring in both venvs — same 2.22.6 wheel.)

---

## Task 5 — Repo loader import-level check (NO file touched)

`src/qkd_io/__init__.py` is empty (0 lines), so the module path used was
`sys.path.insert(0,'src'); import qkd_io.ttbin_pipeline`. Verbatim:

```
$ .venv/bin/python -c "import sys; sys.path.insert(0,'src'); import qkd_io.ttbin_pipeline as m; print('module imports OK')"
module imports OK
---EXIT:0
```

`read_ttbin_events` was NOT called. Note: the module imports only because the
`from TimeTagger import FileReader` is function-local; the direct probe still
fails in the repo venv (verbatim):

```
$ .venv/bin/python -c "import sys; sys.path.insert(0,'src'); from TimeTagger import FileReader"
ModuleNotFoundError: No module named 'TimeTagger'
```

So the loader module is importable, but **calling `read_ttbin_events` today
would raise `RuntimeError: TimeTagger package not available; cannot read
.ttbin: No module named 'TimeTagger'`** — the installed `Swabian.TimeTagger`
does not satisfy the `from TimeTagger import ...` form.

---

## Task 6 — Resource sanity (no file reading)

`df -h /tmp /mnt/d /home` (verbatim):

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdd       1007G   34G  922G   4% /
D:\             932G  519G  413G  56% /mnt/d
/dev/sdd       1007G   34G  922G   4% /
```

(/tmp and /home share /dev/sdd: 922 GiB free; /mnt/d: 413 GiB free.)

Memory estimate for `(time_ps int64, channel int32)` expansion, assumption
stated: on-disk `.ttbin` tags average ~8–10 B/event (Swabian stream encoding
order-of-magnitude; NOT measured — no file was touched), so
~40 MiB ≈ ~4–5 M events. In-memory: 8 B (int64 time) + 4 B (int32 channel)
= **12 B/event** → ~40 MiB file ≈ **~50–60 MB**; with optional
`event_type` int64 (+8 B/event) worst case ≈ **~90–100 MB**. Largest file
(Jan-13 SHG ~57 MiB) ≈ ~6–7 M events → **~70–85 MB** typical,
**~130–140 MB** worst case with event_type. Verdict: free space/RAM pressure
is a non-issue (hundreds of GiB free); no constraint on ingest.

Alternative interpreter: `/home/karel_303/.venvs/timetagger` has NO pandas
(verified `ModuleNotFoundError`), so it **cannot** run repo pipeline code that
needs pandas. It is usable only for raw `Swabian.TimeTagger.FileReader`
probes returning numpy arrays (numpy 2.5.3 present), with handoff via `.npz`.
Since the repo `.venv` now carries the identical 2.22.6 wheel + full deps,
the repo `.venv` should be the ingest interpreter once the import form is
fixed — no need for the two-env dance.

---

## Bottom line

- **Import form: MISMATCH → shim/adapter needed (REPORTED, not applied).**
  Repo needs top-level `TimeTagger` (`from TimeTagger import FileReader`,
  `src/qkd_io/ttbin_pipeline.py:148`); the PyPI `Swabian-TimeTagger==2.22.6`
  wheel provides ONLY `Swabian.TimeTagger` (proven in BOTH venvs:
  `import TimeTagger` → `ModuleNotFoundError`, `from Swabian import
  TimeTagger` → OK with `FileReader` present). The vendor Windows driver
  layout (top-level `TimeTagger` dir) is what the repo code was written
  against (cf. v56d2 calibration script notes); the PyPI wheel uses the
  `Swabian` namespace instead.
- **Install result: clean.** `pip install --no-deps Swabian-TimeTagger==2.22.6`
  succeeded first try from local wheel cache; freeze diff = one added line;
  **numpy 2.5.3 / pandas 3.0.5 / numba 0.67.0 all unchanged**; `FileReader`
  present with signature `(self, *args)`.
- **Stage 0: CONDITIONAL PASS (env ready, loader NOT yet functional).**
  Package + deps are in place, but `read_ttbin_events` would still raise the
  `RuntimeError` above until the import is adapted.
- **Remaining blocker + recommended minimal fix (needs orchestrator approval,
  NOT applied):** one-file change in `src/qkd_io/ttbin_pipeline.py`
  `read_ttbin_events` — try `from TimeTagger import FileReader` first
  (preserves vendor-driver envs), fall back to
  `from Swabian.TimeTagger import FileReader` (covers the PyPI wheel);
  keep the existing `RuntimeError` if both fail. Alternatively a
  `sys.modules` alias shim, but the try/except import is smaller and local.
  After the fix, re-verify with the Task 4/5 probes (still no file reads).

---

## Stage 0 verification (2026-09-21, post-install)

No `.ttbin` file was opened, parsed, or listed this turn; no
pipeline/decoder/DE/`tools/*` script was run on data; no file under `src/`
was modified; no commit/push. Writes this turn: one new compat module
(`comparison_bench/src/comparison_bench/io/ttbin_compat.py`) + this appended
section. Chosen route (per packet): `sys.modules` alias — no frozen file
touched, so the try/except edit proposed in the Bottom line above was NOT
applied.

### Task 1 — Alias proof (verbatim)

```
$ .venv/bin/python -c "
import sys
from Swabian import TimeTagger as _tt
sys.modules['TimeTagger'] = _tt
from TimeTagger import FileReader
print('ALIAS OK ->', FileReader)
print('getVersion ->', _tt.getVersion() if hasattr(_tt,'getVersion') else 'n/a')
print('FileReader attrs ->', [n for n in dir(FileReader) if not n.startswith('_')][:40])
"
ALIAS OK -> <class 'Swabian.TimeTagger.FileReader'>
getVersion -> 2.22.6
FileReader attrs -> ['getChannelList', 'getConfiguration', 'getData', 'getLastMarker', 'hasData', 'thisown']
---EXIT:0
```

**ALIAS OK.** `getVersion()` → `2.22.6` (matches the installed wheel).

### Task 2 — Frozen loader past its import gate (deliberately nonexistent path)

```
$ .venv/bin/python -c "
import sys
from Swabian import TimeTagger as _tt
sys.modules['TimeTagger'] = _tt
sys.path.insert(0,'src')
from qkd_io.ttbin_pipeline import read_ttbin_events
try:
    read_ttbin_events('/tmp/opencode/definitely_not_a_real_file.ttbin')
except RuntimeError as e:
    print('RuntimeError still raised ->', str(e)[:300])
except Exception as e:
    print(type(e).__name__, '->', str(e)[:300])
"
RuntimeError still raised -> FileReader could not open file '/tmp/opencode/definitely_not_a_real_file.ttbin'.
```

Interpretation: the message is NO LONGER "TimeTagger package not available"
— it is the vendor `FileReader` constructor itself rejecting the missing
file. **The alias WORKED; the frozen loader reached the vendor reader.**

Baseline without alias preserved (verbatim):

```
$ .venv/bin/python -c "
import sys; sys.path.insert(0,'src')
from qkd_io.ttbin_pipeline import read_ttbin_events
try:
    read_ttbin_events('/tmp/opencode/nope.ttbin')
except RuntimeError as e: print('BASELINE RuntimeError ->', str(e)[:200])
"
BASELINE RuntimeError -> TimeTagger package not available; cannot read .ttbin: No module named 'TimeTagger'
```

### Task 3 — FileReader surface (no file)

- `inspect.signature(FileReader.__init__)` → `(self, *args)`
- `__init__` docstring (full, verbatim): describes reading data blocks into a
  `TimeTagStreamBuffer` ("exactly the same as returned by the `TimeTagStream`
  measurement"), auto-recognition of split-file sequences, and `FileReader`
  constructor forms (`FileReader("measurement.ttbin")`,
  `FileReader("measurement.1.ttbin")`, list forms). Same text as Task 4 of the
  pre-install section — identical wheel.
- `hasattr` checks on `FileReader`: `hasData` True, `getData` True,
  `getChannelList` True, `getConfiguration` True, `getLastMarker` True;
  `getChannels`/`getTimestamps`/`getEventTypes`/`getMissedEvents` False on
  `FileReader` — those live on the `TimeTagStreamBuffer` returned by
  `getData()` (all four confirmed present there; buffer also has `getOverflows`,
  `hasOverflows`, `size`, `tGetData`, `tStart`). This matches the frozen
  loader, which calls them on `data = reader.getData(...)`, not on the reader.
- Complete public attribute list of `FileReader`:
  `['getChannelList', 'getConfiguration', 'getData', 'getLastMarker',
  'hasData', 'thisown']`
- Method signatures/docs of note:
  - `getData(self, n_events: 'uint64_t') -> 'TimeTagStreamBuffer'` — "Reads the
    next *n_events* ... If less than *n_elements* are returned, the reader has
    reached the end of the last file"; `hasData() -> bool` is the convenient
    end-of-data check.
  - `getChannelList(self) -> std::vector<int>` — "All channels available
    within the input file."
  - `getConfiguration(self) -> std::string` — "A JSON formatted string (`dict`
    in Python) that contains the Time Tagger configuration at the time of file
    creation."
  - `getLastMarker(self) -> std::string` — "The last processed marker from the
    file (see also `FileWriter::setMarker()`)."

**Metadata-accessor question — ANSWERED DIFFERENTLY from earlier.**
The pre-install conclusion ("no metadata/header accessor", "PM/EB
unrecoverable") came from reading our repo code, not the real API. Against the
actual bound API it is REVISED: `FileReader` exposes `getConfiguration()`
(device-configuration JSON at file-creation time), `getChannelList()`, and
`getLastMarker()`. Whether that JSON contains anything bearing on the PM/EB /
acquisition-protocol question (channel roles, trigger/gate settings, marker
strings, timestamps) is UNKNOWN until a real file header is read — that read
is explicitly out of scope for this turn. So: accessor EXISTS (proven above),
payload relevance UNPROVEN (needs a future authorized real-file probe of
`getConfiguration()` output shape, still no event parsing required).

### Task 4 — Compat module

- Checked `comparison_bench/src/comparison_bench/io/`: contains
  `dataset_builder.py`, `pairs_loader.py`, `polar_existing_bridge.py`,
  `table_store.py` (no `__init__.py`; namespace subpackage — in-package
  relative imports are the house style, e.g. `from ..io.table_store import
  ...`; tests import as `comparison_bench.src.comparison_bench.io.X` from repo
  root). House style sampled from `table_store.py`: `from __future__ import
  annotations`, plain imports, no machinery. New module follows it.
- Created: `comparison_bench/src/comparison_bench/io/ttbin_compat.py`
  (~25 lines): single function `install_timetagger_alias()` — returns the
  already-registered `sys.modules['TimeTagger']` if present (idempotent),
  else imports `Swabian.TimeTagger`, registers it, returns it. No
  try/except swallows, no logging, no caching.
- Working import command (verbatim):
  ```
  $ .venv/bin/python -c "from comparison_bench.src.comparison_bench.io.ttbin_compat import install_timetagger_alias; m=install_timetagger_alias(); print('compat OK', m)"
  compat OK <module 'Swabian.TimeTagger' from '/mnt/d/Code/HD-QKD_Polar_Comparison/.venv/lib/python3.12/site-packages/Swabian/TimeTagger/__init__.py'>
  ```
- End-to-end via compat (verbatim): compat install then frozen
  `read_ttbin_events` on the nonexistent path →
  `via-compat RuntimeError -> FileReader could not open file
  '/tmp/opencode/definitely_not_a_real_file.ttbin'.` — vendor reader reached.

No ingest script was written beyond this compat module; nothing was run
against data.

### Verdict

**Stage 0 PASS.** Env ready AND loader functional via the alias: `ALIAS OK`
(getVersion 2.22.6), frozen `read_ttbin_events` reaches the vendor
`FileReader` (error flips from import-gate `RuntimeError` to vendor
"could not open file" on a nonexistent path), baseline-without-alias
behavior unchanged, compat module created + verified. Bonus revision:
`FileReader.getConfiguration()` exists — the "no header/metadata accessor"
conclusion is overturned at the accessor level; payload relevance to PM/EB
awaits a future authorized probe.
