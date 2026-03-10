# High-Dimensional QKD via Adaptive Polar Codes

This repository contains the official End-to-End (E2E) decoding and reconciliation pipeline for our paper on **High-Dimensional Quantum Key Distribution (HD-QKD)**. 

By leveraging 5G-standardized Polar codes (CA-SCL decoding) and an adaptive dimensionality framework, our system dynamically extracts secure keys across variable channel losses, achieving record-breaking Practical Information Efficiency (PIE) in ultra-high dimensions (up to $d=4096$).

## 🗂️ Repository Structure

- `src/`: Core algorithm modules.
  - `qkd_io/`: High-performance time-tagger (`.ttbin`) parsing engines.
  - `workflow/`: Joint sequence extraction and timing alignment (FFT-based).
  - `reconciliation/`: Information reconciliation utilizing a highly optimized C++ Polar code wrapper (CA-SCL).
- `experiments/`: Main drivers to reproduce the results presented in the paper.
- `tools/`: Utility scripts for data visualization and metric aggregation.

## ⚙️ Prerequisites

- Python 3.9+
- Standard data science stack: `numpy`, `pandas`, `scipy`
- **C++ Decoder**: A pre-compiled `ca_scl.dll` (Windows) / `.so` (Linux) is included in `src/reconciliation/cpp_polar/`. Ensure you have the appropriate C++ redistributables installed.

## 🚀 Quick Start (Smoke Test)

To verify that the E2E pipeline and the C++ Polar decoder are configured correctly, you can run a lightweight smoke test using a short acquisition time:

```bash
# Ensure you are in the root of the repository
python experiments/run_e2e_pipeline.py \
    --ttbin "PATH_TO_YOUR_DATA.ttbin" \
    --dims 1024 \
    --bws 150 \
    --acq-time 0.1
Expected Output: The script will parse the time-tags, perform frame synchronization, call the C++ Polar decoder, and output the Secure Key Rate (SKR) and Practical Information Efficiency (PIE).
```
📊 Reproducing Paper Results
To reproduce the full performance sweeps (Heatmaps, Dimension vs. PIE curves) across different attenuation levels (6dB, 10dB, 16dB, 20dB), use the provided sweeping drivers:

```Bash
python experiments/run_golden_sweep_four_datasets.py
(Note: Full sweeps require access to the complete raw .ttbin datasets and may take several hours depending on your CPU constraints).
```
📝 Citation
If you find this code or our conceptual framework useful in your research, please consider citing our paper:

(Citation details will be updated upon publication)

📜 License
This project is licensed under the MIT License.

***
