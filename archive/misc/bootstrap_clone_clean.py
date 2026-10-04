#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _patch_text(path: Path, replacements: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")


def build_release(old_root: Path, new_root: Path) -> None:
    for path in [
        new_root,
        new_root / "src",
        new_root / "src" / "workflow",
        new_root / "src" / "reconciliation",
        new_root / "src" / "qkd_io",
        new_root / "experiments",
    ]:
        path.mkdir(parents=True, exist_ok=True)

    copy_map = {
        old_root / "tools" / "run_e2e_pipeline.py": new_root / "experiments" / "run_e2e_pipeline.py",
        old_root / "tools" / "run_real_polar_max_pie.py": new_root / "experiments" / "run_real_polar_max_pie.py",
        old_root / "tools" / "run_golden_sweep_driver.py": new_root / "experiments" / "run_golden_sweep_driver.py",
        old_root / "tools" / "run_golden_sweep_four_datasets.py": new_root / "experiments" / "run_golden_sweep_four_datasets.py",
        old_root / "tools" / "coarse_grain_joint.py": new_root / "src" / "workflow" / "coarse_grain_joint.py",
        old_root / "tools" / "llr_from_joint.py": new_root / "src" / "workflow" / "llr_from_joint.py",
        old_root / "tools" / "export_joint_sequence_sidecar.py": new_root / "src" / "workflow" / "export_joint_sequence_sidecar.py",
        old_root / "tools" / "cpp_scl_wrapper.py": new_root / "src" / "reconciliation" / "cpp_scl_wrapper.py",
        old_root / "tools" / "real_polar_sc_rescue.py": new_root / "src" / "reconciliation" / "real_polar_sc_rescue.py",
        old_root / "tools" / "run_nbldpc_demo_point.py": new_root / "src" / "reconciliation" / "run_nbldpc_demo_point.py",
        old_root / "src" / "qkd_io" / "ttbin_pipeline.py": new_root / "src" / "qkd_io" / "ttbin_pipeline.py",
    }
    for src, dst in copy_map.items():
        _copy_file(src, dst)

    src_cpp = old_root / "tools" / "cpp_polar"
    dst_cpp = new_root / "src" / "reconciliation" / "cpp_polar"
    if dst_cpp.exists():
        shutil.rmtree(dst_cpp)
    shutil.copytree(src_cpp, dst_cpp)

    for init_file in [
        new_root / "src" / "__init__.py",
        new_root / "src" / "workflow" / "__init__.py",
        new_root / "src" / "reconciliation" / "__init__.py",
        new_root / "src" / "qkd_io" / "__init__.py",
    ]:
        init_file.parent.mkdir(parents=True, exist_ok=True)
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")

    (new_root / "README.md").write_text(
        "# HD-QKD Polar Release\n\nPublication-ready cleaned code release.\n",
        encoding="utf-8",
    )
    (new_root / "requirements.txt").write_text(
        "numpy\npandas\nnumba\ntqdm\n",
        encoding="utf-8",
    )

    _patch_text(
        new_root / "experiments" / "run_e2e_pipeline.py",
        [
            ("from export_joint_sequence_sidecar import (", "from src.workflow.export_joint_sequence_sidecar import ("),
            (
                "from run_nbldpc_demo_point import _read_ttbin_timetags",
                "from src.reconciliation.run_nbldpc_demo_point import _read_ttbin_timetags",
            ),
            (
                "str(REPO_ROOT / \"tools\" / \"run_real_polar_max_pie.py\")",
                "str(REPO_ROOT / \"experiments\" / \"run_real_polar_max_pie.py\")",
            ),
        ],
    )
    _patch_text(
        new_root / "experiments" / "run_real_polar_max_pie.py",
        [
            ("from cpp_scl_wrapper import PolarSCLDecoder", "from src.reconciliation.cpp_scl_wrapper import PolarSCLDecoder"),
            ("from real_polar_sc_rescue import (", "from src.reconciliation.real_polar_sc_rescue import ("),
        ],
    )
    _patch_text(
        new_root / "experiments" / "run_golden_sweep_driver.py",
        [("str(REPO_ROOT / \"tools\" / \"run_e2e_pipeline.py\")", "str(REPO_ROOT / \"experiments\" / \"run_e2e_pipeline.py\")")],
    )
    _patch_text(
        new_root / "experiments" / "run_golden_sweep_four_datasets.py",
        [("str(REPO_ROOT / \"tools\" / \"run_e2e_pipeline.py\")", "str(REPO_ROOT / \"experiments\" / \"run_e2e_pipeline.py\")")],
    )
    _patch_text(
        new_root / "src" / "workflow" / "export_joint_sequence_sidecar.py",
        [
            ("REPO_ROOT = Path(__file__).resolve().parents[1]", "REPO_ROOT = Path(__file__).resolve().parents[2]"),
            (
                "from coarse_grain_joint import coarse_grain_sparse_joint, dense_from_sparse",
                "from src.workflow.coarse_grain_joint import coarse_grain_sparse_joint, dense_from_sparse",
            ),
            (
                "from llr_from_joint import load_joint_counts_sparse_from_metrics",
                "from src.workflow.llr_from_joint import load_joint_counts_sparse_from_metrics",
            ),
            ("from run_nbldpc_demo_point import (", "from src.reconciliation.run_nbldpc_demo_point import ("),
        ],
    )
    _patch_text(
        new_root / "src" / "reconciliation" / "cpp_scl_wrapper.py",
        [
            ("Path(__file__).resolve().parents[1]", "Path(__file__).resolve().parents[2]"),
            (
                "self._repo_root / \"tools\" / \"cpp_polar\" / \"main.cpp\"",
                "self._repo_root / \"src\" / \"reconciliation\" / \"cpp_polar\" / \"main.cpp\"",
            ),
            (
                "self._repo_root / \"tools\" / \"cpp_polar\" / f\"ca_scl{ext}\"",
                "self._repo_root / \"src\" / \"reconciliation\" / \"cpp_polar\" / f\"ca_scl{ext}\"",
            ),
        ],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Build clean HD-QKD publication repository by copy-and-patch.")
    ap.add_argument("--old-root", default=r"D:\Code\hdqkd_cleanroom_20260124")
    ap.add_argument("--new-root", default=r"D:\Code\HD-QKD_Polar_Release")
    args = ap.parse_args()

    old_root = Path(args.old_root)
    new_root = Path(args.new_root)
    build_release(old_root=old_root, new_root=new_root)
    print(f"[OK] built release repository at: {new_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
