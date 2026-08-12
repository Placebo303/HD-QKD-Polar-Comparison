"""Shared, additive contract helpers for formal offline IR methods."""

from .shared import FORMAL_ARTIFACTS, FORMAL_STATUSES, formal_bp_osd_params, preflight_ldpc, toeplitz_tag
from .cascade import run_cascade_formal
from .ldpc import run_ldpc_formal
from .ldpc_v2 import run_ldpc_formal_v2
from .nonbinary_field import FieldSpec, GF2mField, get_field_spec, preflight_nonbinary_field
from .nonbinary_codebook import gf_rank, build_nonbinary_codebook_family, verify_nonbinary_codebook_family
from .nonbinary_qspa import (
    qsc_symbol_priors, nonbinary_syndrome, decode_nonbinary_fft_qspa,
    symbols_to_msb_bits, nonbinary_disclosure_accounting, verify_nonbinary_symbols,
)

__all__ = ["FORMAL_ARTIFACTS", "FORMAL_STATUSES", "formal_bp_osd_params", "preflight_ldpc", "toeplitz_tag", "run_cascade_formal", "run_ldpc_formal", "run_ldpc_formal_v2", "FieldSpec", "GF2mField", "get_field_spec", "preflight_nonbinary_field", "gf_rank", "build_nonbinary_codebook_family", "verify_nonbinary_codebook_family", "qsc_symbol_priors", "nonbinary_syndrome", "decode_nonbinary_fft_qspa", "symbols_to_msb_bits", "nonbinary_disclosure_accounting", "verify_nonbinary_symbols"]
