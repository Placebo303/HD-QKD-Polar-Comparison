# H0.4 解释器契约（双轨方案与验证命令）

> 单页记录。来源：`docs/EXECUTION_PLAN_20260922.md` **PLAN:103**（H0.4 行）。
> 本文件为文档变更，无 track gate；不修改 AGENTS.md / README.md / EXECUTION_PLAN / NOW.md，不授权任何执行或 commit/push。

## 1. 现状与矛盾

- **WSL 侧**：repo venv `.venv/bin/python` 可用（numpy / pytest / pandas / pyarrow / yaml 齐全）。
- **Windows 侧**：缺 `.venv/Scripts/python.exe`，现走 **Miniforge (conda)** 环境。
- 这与 `AGENTS.md` **§8**“Interpreter: use repo venv `.venv/` only”直接矛盾——§8 只覆盖 WSL 轨，未覆盖 Windows 轨。

## 2. 双轨方案（当前生效的运行契约）

| 轨道 | 解释器 | 说明 |
|---|---|---|
| **WSL (Linux)** | `.venv/bin/python` | repo venv，完整依赖，日常命令以此为准 |
| **Windows** | Miniforge (conda) `python` | `.venv` 无 Windows Scripts；在 Miniforge 环境中运行 |

两条轨互不替代；任一环境验证通过即可进入后续工作。

## 3. 验证命令（实测记录，2026-09-22，WSL）

冻结包仅授权以下一条验证命令：

```bash
.venv/bin/python -c "import numpy,pytest; print(numpy.__version__)"
```

**输出**（exit code 0）：

```text
2.5.3
```

辅助记录（非验证命令）：

```text
$ ls .venv/bin/python*
.venv/bin/python
.venv/bin/python3
.venv/bin/python3.12
```

Windows 轨验证（在 Miniforge 提示符下，与 WSL 命令等价）：

```bat
python -c "import numpy,pytest; print(numpy.__version__)"
```

## 4. 后续二选一（未决，需另行决策）

H0.4 验收要求“与 §8 不再矛盾”，二选一择一执行（本包不执行）：

1. **重建 venv**：为 Windows 侧重建含 `Scripts/python.exe` 的 `.venv`，使 §8“repo venv only”对两轨同时成立。
2. **改 AGENTS/README**：修改 AGENTS §8（及 README 对应段），写明 Windows=conda Miniforge、WSL=`.venv`，消除矛盾。

当前 H0.4 解释器契约按 **选项 2 的文档形态**（本文件）先行记录双轨现状；最终落点待决策后由相应变更完成。

## 5. 引用

- `AGENTS.md` **§8 Execution Environment**（解释器约束原文）。
- `docs/EXECUTION_PLAN_20260922.md` **PLAN:103**（H0.4 行：修复解释器契约）。
