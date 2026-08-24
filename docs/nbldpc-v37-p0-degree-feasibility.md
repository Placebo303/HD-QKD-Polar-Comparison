# V37-P0 Finite-Length Degree Feasibility Analysis Report

**Date**: 2026-08-24  
**Scope**: Read-only scientific tooling (`comparison_bench/src/comparison_bench/formal_ir/v37_degree_feasibility.py`)  
**Status**: `IMPLEMENTATION_CANDIDATE` (Tooling complete; no scientific execution authorized)

---

## 1. Motivation

In V36, the candidate distribution $\lambda_2=0.85, \lambda_4=0.15$ was selected by DE screening. However, finite graph construction (A2) generated graphs with $2288\text{--}3002$ 4-cycles and degree-2 cycle ranks of $779\text{--}801$, failing the zero-cycle structural gate.

V37-P0 implements a deterministic finite-length degree feasibility analyzer to verify the topological realizability of candidate variable-node degree distributions before attempting graph construction or DE screening.

---

## 2. Mathematical Formulation

1. **Edge-to-Node Perspective Conversion**:
   $$\bar{d}_v = \frac{1}{\sum_j \frac{\lambda_j}{j}}, \quad L_i = \frac{\lambda_i / i}{\sum_j \frac{\lambda_j}{j}}$$

2. **Integer Node Apportionment**:
   Exact apportionment $N_i$ summing to $n$ via largest-remainder (Hamilton) method:
   $$\sum_i N_i = n$$

3. **Total Edge Sockets & Check-Side Degree Allocation**:
   Total variable sockets: $E = \sum_i i \cdot N_i$.
   Mean check degree: $\bar{d}_c(m) = \frac{E}{m}$.
   The unique integer check-degree allocation on adjacent degrees $\{d_{\text{floor}}, d_{\text{ceil}}\} = \{\lfloor E/m \rfloor, \lceil E/m \rceil\}$ is:
   $$n_{\text{checks\_ceil}} = E \pmod m, \quad n_{\text{checks\_floor}} = m - n_{\text{checks\_ceil}}$$
   $$d_{\text{max}} = d_{\text{ceil}} \quad (\text{if } n_{\text{checks\_ceil}} > 0 \text{ else } d_{\text{floor}})$$

4. **Degree-2 Forest Upper Bound & Cycle Rank Lower Bound**:
   A degree-2 variable node corresponds to an edge in the check-node multigraph $G_c = (V_c, E_c)$ where $|V_c| = m$ and $|E_c| = N_2$.
   - Any cycle-free subgraph (forest) on $m$ vertices contains at most $m - 1$ edges:
     $$\text{forest\_bound} = m - 1$$
   - The unavoidable cycle rank (cyclomatic number) lower bound is:
     $$\gamma_2 \ge \max(0, N_2 - (m - 1))$$
   - When $N_2 > m - 1$, a cycle-free degree-2 subgraph is mathematically impossible.

---

## 3. Verification on V36 Candidate

For $n=1024$ and $\lambda = \{\text{degree } 2: 0.85, \text{degree } 4: 0.15\}$:
- Node distribution: $L_2 = \frac{34}{37} \approx 91.89\%$, $L_4 = \frac{3}{37} \approx 8.11\%$.
- Node counts: $N_2 = 941$, $N_4 = 83$ ($\sum = 1024$).
- Total sockets: $E = 2214$.

### Check-Side Allocation for $E = 2214$:
- **1M ($m=184$)**: $178$ degree-12 checks $+ 6$ degree-13 checks ($\bar{d}_c \approx 12.0326$, $d_{\text{max}} = 13$).
- **1p5M ($m=190$)**: $66$ degree-11 checks $+ 124$ degree-12 checks ($\bar{d}_c \approx 11.6526$, $d_{\text{max}} = 12$).
- **2M ($m=192$)**: $90$ degree-11 checks $+ 102$ degree-12 checks ($\bar{d}_c \approx 11.5312$, $d_{\text{max}} = 12$).

### Degree-2 Feasibility & Cycle Rank Analysis:

| Source | $m$ | Forest Upper Bound ($m-1$) | $N_2$ | Unavoidable Cycle Rank Lower Bound | V36 Observed Degree-2 Cycle Rank | Excess Cycles Above Lower Bound |
|---|---|---|---|---|---|---|
| **1M** | 184 | 183 | 941 | **758** | 801 | +43 |
| **1p5M** | 190 | 189 | 941 | **752** | 785 | +33 |
| **2M** | 192 | 191 | 941 | **750** | 779 | +29 |

**Scientific Observation**:
The chosen degree distribution forces a degree-2 cycle-rank lower bound of 758/752/750 for m=184/190/192, so a zero-cycle degree-2 subgraph is mathematically impossible. The observed ranks 801/785/779 exceed these lower bounds by 43/33/29 respectively; those excess cycles are not explained by the lower bound alone.

---

## 4. Usage

CLI entrypoint:
```powershell
python -m comparison_bench.src.comparison_bench.cli.run_v37_degree_feasibility --lambda '{"2": 0.85, "4": 0.15}' --n 1024 --m 184,190,192
```

---

## 5. Scientific Claim Boundary

- **Tooling Scope Only**: V37-P0 provides a read-only analytical filter for degree distribution realizability.
- **No Algorithm / Success Claims**: No algorithm performance improvement or V37 success is claimed.
- **No Causal Overclaim**: Cycle rank is a topological graph property; it is not claimed that cycle rank causally explains decoder failure.
- **Execution Authority**: Execution authorization for subsequent stages (V37-P1+) remains **NOT GRANTED**.
