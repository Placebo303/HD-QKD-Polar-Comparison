# Addendum Acceptance Record: V72P1-ADP

**Repository**: `HD-QKD_Polar_Comparison`
**Branch**: `formal-ir-v72p1-addendum-clean` (isolated acceptance worktree)
**Authority**: 用户/主审采纳独立 addendum re-review PASS
**Record Time**: 2026-09-02

---

## Acceptance fields

- **reviewed_addendum_sha**: `b0d551054e3481c08068fd9a2c58363c44eb9bfa`
- **sha_verification**: `VERIFIED`（worktree HEAD == origin/formal-ir-v72p1-addendum-clean == `b0d55105...`，`git ls-remote` 复核一致）
- **verdict**: `ADDENDUM_ACCEPTED`
- **R1–R9**: PASS（全部闭合：R1 数值来源与新冻结工程数值标注、R2 residual trajectory 口径、R3 输出清单恰四文件、R4 T1-9..T1-15 语义测试、R5 P1D 命令、R6 int32 tobytes byte-identity、R7 ADDENDUM_ACCEPTED_SHA/REQUIRED_IMPLEMENTATION_BASE_SHA + 四步授权、R8 CHANGED_FILES/DATA_INCLUDED 分列、R9 tag `sha256(bits.tobytes())[:8]` V72P0 复用）
- **clean base**: `ea82423fe313c2ce3ef532fb48c87dc34e752e5a`（cherry-pick 基线，禁改文件 diff = 0）
- **candidate range**: 该 addendum 修订版仅修改 `docs/research_cycles/V72P1-ADP/EXECUTION_PACKET_ADDENDUM.md`（+35/−22，`git diff --check` 干净）
- **accepted_scope**: `implementation_and_synthetic_qualification_only`
- **formal_execution_authorized**: false
- **real_data_authorized**: false
- **run_01_authorized**: false

## Implementation gate

- **required_implementation_base_sha**: 本 acceptance record 提交自身 SHA（实现提交必须以其为祖先，`HEAD == origin` 40 位重核后开工）
- **next_gate**: `IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION`（3 文件实现 + T0/T1 + P1A–P1D synthetic smoke，SYNTHETIC_ONLY）
- pre-EXECUTE / pre-RESULT 双重 review 门禁在 formal run_01 之前仍然强制适用。
