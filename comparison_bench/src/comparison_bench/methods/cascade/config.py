"""CascadeSingleConfig — frozen single-kernel config (DESIGN_FROZEN.md S2)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field


class ConfigError(ValueError):
    pass


DEPRECATED_KEYS = {
    "variant", "method_variant", "cascade_lite", "cascade_formal_v1",
    "mode", "lookback_enabled", "lookback_depth_cap", "adaptation",
    "cascade", "variant_lite", "variant_formal",
}
DEPRECATED_HINT = (
    "variant is deprecated — use cascade_single_kernel.block_size_policy (fixed|adaptive) "
    "with lookback=fifo, verification=toeplitz, seed_policy=domain-separated, q_handling=auto. "
    "Preset mapping: lite->adaptive, formal->fixed. See DESIGN_FROZEN.md S3."
)
DEPRECATED_TOP_HINT = "cascade_lite is deprecated — use cascade_single_kernel"
FIXED_PASSES = [16, 32, 64, 128]
DEFAULT_CAPS = {"per_frame_s": 5, "max_events": 100000, "max_corrections": 4096, "max_queue_pops": 10000}


@dataclass
class CascadeSingleConfig:
    kernel: str = "single"
    block_size_policy: str = "fixed"  # fixed|adaptive
    block_size_adaptive_coeff: float = 0.73
    block_size_caps: dict = field(default_factory=lambda: {"min": 8, "max_factor": 0.5})
    lookback: str = "fifo"
    verification: str = "toeplitz"
    seed_policy: str = "domain-separated"
    q_handling: str = "auto"
    num_passes: int = 4
    passes_block_sizes: list[int] = field(default_factory=lambda: list(FIXED_PASSES))
    base_seed: int = 2026072522
    caps: dict = field(default_factory=lambda: dict(DEFAULT_CAPS))

    # alias for DESIGN_FROZEN `passes` key
    @property
    def passes(self) -> list[int]:
        return self.passes_block_sizes

    @passes.setter
    def passes(self, v: list[int]) -> None:
        self.passes_block_sizes = list(v)


def _fail_unknown(key: str) -> None:
    raise ConfigError(f"unknown key '{key}'")


def _fail_deprecated(key: str) -> None:
    if key in ("variant", "method_variant"):
        raise ConfigError(f"variant is deprecated — {DEPRECATED_HINT}")
    if key in ("cascade_lite", "cascade_formal_v1"):
        raise ConfigError(f"{key} is deprecated — use cascade_single_kernel — {DEPRECATED_HINT}")
    raise ConfigError(f"'{key}' is deprecated — use cascade_single_kernel.block_size_policy (fixed|adaptive) with lookback=fifo, verification=toeplitz, seed_policy=domain-separated, q_handling=auto. Preset mapping: lite->adaptive, formal->fixed. See DESIGN_FROZEN.md S3.")


ALLOWED_TOP = {
    "kernel", "block_size_policy", "block_size_adaptive_coeff", "block_size_caps",
    "lookback", "verification", "seed_policy", "q_handling",
    "num_passes", "passes_block_sizes", "passes", "base_seed", "caps",
}


def _validate(cfg: CascadeSingleConfig) -> None:
    if cfg.kernel != "single":
        raise ConfigError("kernel must be single")
    if cfg.block_size_policy not in ("fixed", "adaptive"):
        raise ConfigError("block_size_policy must be fixed|adaptive")
    if cfg.lookback != "fifo":
        raise ConfigError("lookback must be fifo")
    if cfg.verification != "toeplitz":
        raise ConfigError("verification must be toeplitz")
    if cfg.seed_policy != "domain-separated":
        raise ConfigError("seed_policy must be domain-separated")
    if cfg.q_handling != "auto":
        raise ConfigError("q_handling must be auto")
    # strict type: reject bool (bool is subclass of int)
    if type(cfg.base_seed) is not int or not (0 <= cfg.base_seed < 2**31):
        raise ConfigError("base_seed must be int in [0, 2^31)")
    if type(cfg.num_passes) is not int or cfg.num_passes < 1 or cfg.num_passes > 16:
        raise ConfigError("num_passes must be int 1..16")
    # passes / passes_block_sizes
    pbs = list(cfg.passes_block_sizes)
    if not pbs:
        raise ConfigError("passes_block_sizes must be non-empty")
    if any(type(x) is not int or x < 1 for x in pbs):
        raise ConfigError("passes_block_sizes must be list[int] >0")
    if cfg.block_size_policy == "fixed" and pbs != FIXED_PASSES:
        raise ConfigError("fixed policy requires passes=[16,32,64,128]")
    # caps validation — strict int, no float truncation
    if not isinstance(cfg.caps, dict):
        raise ConfigError("caps must be dict")
    for k in cfg.caps:
        if k not in DEFAULT_CAPS:
            _fail_unknown(k)
    for k, default in DEFAULT_CAPS.items():
        if k not in cfg.caps:
            raise ConfigError(f"caps missing key '{k}'")
        v = cfg.caps[k]
        if type(v) is not int or v <= 0:
            raise ConfigError(f"caps.{k} must be int >0 (no float truncation)")
        if cfg.block_size_policy == "fixed" and v != int(default):
            raise ConfigError(f"fixed policy requires caps.{k}={default}")
        if v > int(default):
            raise ConfigError(f"caps.{k} must be <= {default} (no loosening)")
    # block_size_caps
    if not isinstance(cfg.block_size_caps, dict):
        raise ConfigError("block_size_caps must be dict")
    for k in cfg.block_size_caps:
        if k not in ("min", "max_factor"):
            _fail_unknown(k)
    if "min" not in cfg.block_size_caps or "max_factor" not in cfg.block_size_caps:
        raise ConfigError("block_size_caps requires min and max_factor")
    if type(cfg.block_size_caps["min"]) is not int or cfg.block_size_caps["min"] < 1:
        raise ConfigError("block_size_caps.min must be int >=1")
    mf = cfg.block_size_caps["max_factor"]
    if not isinstance(mf, (int, float)) or isinstance(mf, bool) or not (0 < float(mf) <= 1):
        raise ConfigError("block_size_caps.max_factor must be in (0,1]")
    # coeff
    if not isinstance(cfg.block_size_adaptive_coeff, (int, float)) or isinstance(cfg.block_size_adaptive_coeff, bool) or not (0 < float(cfg.block_size_adaptive_coeff) < 5):
        raise ConfigError("block_size_adaptive_coeff must be in (0,5)")


def validate_top_level_yaml(data: dict) -> None:
    """Fail-fast check for deprecated/unknown keys at full YAML top level (B4)."""
    if not isinstance(data, dict):
        return
    for k in data:
        if k in DEPRECATED_KEYS:
            _fail_deprecated(k)
        # also check nested method stanzas if present
    # check methods list
    for m in data.get("methods", []) if isinstance(data.get("methods"), list) else []:
        if isinstance(m, dict):
            for k in m:
                if k in DEPRECATED_KEYS:
                    _fail_deprecated(k)
            # check cascade_single_kernel sub-block deprecated too
            sub = m.get("cascade_single_kernel")
            if isinstance(sub, dict):
                for k in sub:
                    if k in DEPRECATED_KEYS:
                        _fail_deprecated(k)


def load_cascade_single_config(data: dict) -> CascadeSingleConfig:
    """Load from dict (e.g. yaml `cascade_single_kernel:` block). Fail-fast."""
    if not isinstance(data, dict):
        raise ConfigError("cascade_single_kernel config must be dict")
    # global deprecated check even when called directly
    for k in data:
        if k in DEPRECATED_KEYS:
            _fail_deprecated(k)
        if k not in ALLOWED_TOP:
            _fail_unknown(k)
        # legacy verification true/false
        if k == "verification" and isinstance(data[k], bool):
            raise ConfigError("verification is deprecated — use verification=toeplitz")
    # also detect deprecated aliases inside flat dict that might have been nested incorrectly
    # e.g. variant at top of this block
    kwargs: dict = {}
    # handle passes alias — strict list[int]
    raw_passes = data.get("passes_block_sizes", data.get("passes", None))
    if raw_passes is not None:
        if isinstance(raw_passes, str):
            raise ConfigError("passes must be list[int]")
        if not isinstance(raw_passes, (list, tuple)):
            raise ConfigError("passes must be list[int]")
        # strictly validate elements are int (reject float truncation)
        for x in list(raw_passes):
            if type(x) is not int:
                raise ConfigError("passes must be list[int] (no float truncation)")
        kwargs["passes_block_sizes"] = list(raw_passes)
    for key in ("kernel", "block_size_policy", "lookback", "verification", "seed_policy", "q_handling"):
        if key in data:
            # strict string type
            if not isinstance(data[key], str):
                raise ConfigError(f"{key} must be str")
            kwargs[key] = data[key]
    if "block_size_adaptive_coeff" in data:
        v = data["block_size_adaptive_coeff"]
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            raise ConfigError("block_size_adaptive_coeff must be number")
        kwargs["block_size_adaptive_coeff"] = float(v)
    if "block_size_caps" in data:
        if not isinstance(data["block_size_caps"], dict):
            raise ConfigError("block_size_caps must be dict")
        kwargs["block_size_caps"] = dict(data["block_size_caps"])
    if "num_passes" in data:
        if type(data["num_passes"]) is not int:
            raise ConfigError("num_passes must be int (no float truncation)")
        kwargs["num_passes"] = int(data["num_passes"])
    if "base_seed" in data:
        if type(data["base_seed"]) is not int:
            raise ConfigError("base_seed must be int (no float truncation)")
        kwargs["base_seed"] = int(data["base_seed"])
    if "caps" in data:
        if not isinstance(data["caps"], dict):
            raise ConfigError("caps must be dict")
        # strict int check per key
        for ck, cv in data["caps"].items():
            if type(cv) is not int:
                raise ConfigError(f"caps.{ck} must be int (no float truncation)")
        kwargs["caps"] = dict(data["caps"])
    cfg = CascadeSingleConfig(**kwargs)
    _validate(cfg)
    return cfg


def validate_cascade_single_config(cfg: CascadeSingleConfig) -> None:
    _validate(cfg)
