"""Write descriptive MSD information-budget rows from accepted R1 TRAIN histograms."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from comparison_bench.src.comparison_bench.formal_ir.msd_information_budget import (
    finite_length_scenario,
    validate_counts,
)


ALPHABET_SIZE = 1024
SOURCE_IDS = ("T2-1M", "T2-1.5M", "T2-2M")
ENCODINGS = ("NATURAL", "GRAY")
ORDERS = ("LSB_FIRST", "MSB_FIRST")
BLOCK_LENGTHS = (1024, 16384)
JOINT_FAILURE_ASSUMPTION = 0.01
SHARED_TAG_BITS = 64
EC_BUDGET_BITS_PER_1024 = 1040


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _input_path(source: str) -> Path:
    return (
        _repo_root()
        / "workspace"
        / "r1_histogram_5e2a91c4"
        / f"{source}_N_ab_train_sparse.npz"
    )


def _load_train_counts(path: Path) -> tuple[np.ndarray, int]:
    with np.load(path, allow_pickle=False) as sparse:
        shape_values = np.asarray(sparse["shape"])
        row = np.asarray(sparse["row"])
        col = np.asarray(sparse["col"])
        count = np.asarray(sparse["count"])
        n_train_values = np.asarray(sparse["N_train"])

    if shape_values.shape != (2,) or tuple(int(v) for v in shape_values) != (
        ALPHABET_SIZE,
        ALPHABET_SIZE,
    ):
        raise ValueError(f"{path}: sparse shape must be (1024, 1024)")
    arrays = (row, col, count)
    if any(array.ndim != 1 or not np.issubdtype(array.dtype, np.integer) for array in arrays):
        raise ValueError(f"{path}: row, col, and count must be one-dimensional integer arrays")
    if row.shape != col.shape or row.shape != count.shape:
        raise ValueError(f"{path}: row, col, and count lengths differ")
    if np.any(row < 0) or np.any(row >= ALPHABET_SIZE):
        raise ValueError(f"{path}: Alice row index is outside [0, 1024)")
    if np.any(col < 0) or np.any(col >= ALPHABET_SIZE):
        raise ValueError(f"{path}: Bob column index is outside [0, 1024)")
    if np.any(count < 0):
        raise ValueError(f"{path}: counts must be nonnegative")
    if n_train_values.size != 1 or not np.issubdtype(n_train_values.dtype, np.integer):
        raise ValueError(f"{path}: N_train metadata must be one integer")

    dense = np.zeros((ALPHABET_SIZE, ALPHABET_SIZE), dtype=np.int64)
    np.add.at(dense, (row, col), count)
    n_train = int(n_train_values.item())
    reconstructed_total = int(np.sum(dense, dtype=np.int64))
    if n_train <= 0 or reconstructed_total != n_train:
        raise ValueError(
            f"{path}: reconstructed count sum {reconstructed_total} != N_train metadata {n_train}"
        )
    return validate_counts(dense), n_train


def _encoding_counts(counts: np.ndarray, encoding: str) -> np.ndarray:
    if encoding == "NATURAL":
        return counts
    gray = np.arange(ALPHABET_SIZE, dtype=np.int64)
    gray ^= gray >> 1
    relabeled = np.zeros_like(counts)
    relabeled[np.ix_(gray, gray)] = counts
    return relabeled


def _projected_budget_bits(n_symbols: int) -> float:
    return EC_BUDGET_BITS_PER_1024 * n_symbols / 1024 + SHARED_TAG_BITS


def _scenario(counts: np.ndarray, order: str, n_symbols: int) -> dict[str, object]:
    budget = _projected_budget_bits(n_symbols)
    result = finite_length_scenario(
        counts,
        order,
        N=n_symbols,
        joint_failure_assumption=JOINT_FAILURE_ASSUMPTION,
        tag_bits=SHARED_TAG_BITS,
        budget_bits=budget,
    )
    result["budget_projection"] = {
        "formula": "1040*N_symbols/1024 + 64 shared tag bits",
        "bits": budget,
        "ec_bits_assumed": EC_BUDGET_BITS_PER_1024 * n_symbols / 1024,
        "shared_tag_bits": SHARED_TAG_BITS,
        "status": "planning projection; not an observed long-block baseline",
    }
    return result


def _write_row(
    output_root: Path,
    source: str,
    input_path: Path,
    n_train: int,
    encoding: str,
    order: str,
    counts: np.ndarray,
    n_symbols: tuple[int, ...],
) -> Path:
    from comparison_bench.src.comparison_bench.formal_ir.msd_information_budget import (
        analyze_joint_counts,
    )

    analysis = analyze_joint_counts(counts, order)
    scenarios = [_scenario(counts, order, n) for n in n_symbols]
    row = {
        "source": source,
        "input_path": input_path.relative_to(_repo_root()).as_posix(),
        "source_role": "TRAIN",
        "N_train": n_train,
        "encoding": encoding,
        "encoding_definition": (
            "NATURAL uses x; GRAY uses g(x)=x^(x>>1), applying the same bijection "
            "to Alice rows and Bob columns."
        ),
        "same_source_practical_code_gap": "UNKNOWN",
        "analysis": analysis,
        "scenarios": scenarios,
    }
    filename = f"{source}_{encoding}_{order}.json"
    destination = output_root / filename
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(row, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return destination


def _output_root(value: str) -> Path:
    repo = _repo_root()
    root = Path(value)
    if not root.is_absolute():
        root = repo / root
    root = root.resolve()
    allowed_parent = (repo / "workspace" / "msd_p1").resolve()
    try:
        relative = root.relative_to(allowed_parent)
    except ValueError as exc:
        raise ValueError("--output-root must be a fresh child of workspace/msd_p1") from exc
    if not relative.parts:
        raise ValueError("--output-root must name a fresh child of workspace/msd_p1")
    if root.exists():
        raise FileExistsError(f"output root already exists: {root}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute descriptive MSD information-budget rows from R1 TRAIN histograms."
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="fresh additive workspace/msd_p1/<uuid> root",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="only T2-2M, GRAY, MSB_FIRST, N=1024",
    )
    args = parser.parse_args(argv)

    output_root = _output_root(args.output_root)
    sources = ("T2-2M",) if args.smoke else SOURCE_IDS
    if args.smoke:
        combinations = (("GRAY", "MSB_FIRST", (1024,)),)
    else:
        combinations = tuple(
            (encoding, order, BLOCK_LENGTHS)
            for encoding in ENCODINGS
            for order in ORDERS
        )
    source_paths = {source: _input_path(source) for source in sources}
    missing = [str(path) for path in source_paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing accepted TRAIN histogram(s): " + ", ".join(missing))

    output_root.mkdir(parents=True, exist_ok=False)
    for source, input_path in source_paths.items():
        counts, n_train = _load_train_counts(input_path)
        for encoding, order, block_lengths in combinations:
            encoded_counts = _encoding_counts(counts, encoding)
            result_path = _write_row(
                output_root,
                source,
                input_path,
                n_train,
                encoding,
                order,
                encoded_counts,
                block_lengths,
            )
            print(result_path.relative_to(_repo_root()).as_posix(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
