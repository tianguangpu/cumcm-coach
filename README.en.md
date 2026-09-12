<div align="center">

# cumcm-coach

**A competition-grade paper generation system for CUMCM (China Undergraduate Mathematical Contest in Modeling)**

Turn a problem statement into a submittable paper: problem typing → modeling & solving → figures → typesetting → four-level review.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/tianguangpu/cumcm-coach/actions/workflows/ci.yml/badge.svg)](https://github.com/tianguangpu/cumcm-coach/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-89%20passed-brightgreen.svg)](tests/)
[![Algorithms](https://img.shields.io/badge/algorithms-36%20modules-informational.svg)](algorithms/)

[中文](README.md) · English · [Quick Start](#quick-start) · [Architecture](#architecture)

</div>

---

## What is this

A full-pipeline paper-generation toolchain for CUMCM, distributed as a [Claude Code](https://claude.com/claude-code) Skill.

The competition gives you 72 hours, but your score is decided by three things: **whether your model is genuinely novel, whether your validation is rigorous, and whether your paper has fatal flaws**. Those are exactly the things that get sacrificed under time pressure.

This tool turns what judges actually look for into **automatable checks**: every sub-problem must complete a six-part structure, every figure must carry a conclusion, every number must be traceable, and every novelty claim must be backed by an ablation study.

> **Note**: The tool's own documentation, prompts, and paper templates are in Chinese, since CUMCM submissions are written in Chinese. This English README covers installation and usage for the code components.

### Design principles

| Principle | Implementation |
|-----------|---------------|
| **No fabricated numbers** | Every value must be registered in `result_registry.py` before it may appear in the paper |
| **No self-verification loops** | Models are compared against **strong** baselines (not weak greedy heuristics) |
| **No bare plots** | Each figure must layer at least one visualization technique over plain `plot` / `bar` |
| **No hidden weaknesses** | Assumption errors are quantified item by item; sensitivity analysis must name sensitive parameters |
| **Compliance first** | CUMCM has required an AI-usage declaration since 2024; the pipeline logs AI interactions and generates the declaration automatically |

---

## Core capabilities

| Capability | Detail |
|-----------|--------|
| **Adaptive problem typing** | Auto-classifies into A (mechanistic) / B (optimization) / C (evaluation) / D (data), then into 12 sub-types driving algorithm selection |
| **36 algorithm modules** | Optimization, prediction, evaluation, graph theory, mechanistic, statistics, game theory, ecology, validation |
| **Multi-solver routing** | LP → HiGHS ｜ MIP/CSP → OR-Tools CP-SAT ｜ NLP → SciPy ｜ continuous → built-in SA-PSO / GA / DE |
| **Mandatory four-fold validation** | Goodness-of-fit + Sobol global sensitivity + Monte Carlo (≥200 runs) + assumption-error quantification (≥3 items) |
| **Publication-grade figures** | 300 dpi PNG + 600 dpi vector PDF, 5 academic palettes, 10 visualization techniques |
| **Four-level review (L1–L4)** | Automated → cross-validation → adversarial → red-team, including page limit, AI-declaration placement, and AIGC risk checks |

---

## Quick start

### Requirements

| Dependency | Version | Required |
|-----------|---------|----------|
| Python | 3.9+ | **Yes** |
| LaTeX (XeLaTeX + biber) | TeX Live / MiKTeX | Either one |
| Typst | 0.11+ | Either one |
| MATLAB | R2024a+ | Optional (advanced figures) |

### Installation

```bash
git clone https://github.com/tianguangpu/cumcm-coach.git
cd cumcm-coach

# Core dependencies
pip install -e .

# All optional features (solvers + sensitivity + plot styles + literature search)
pip install -e ".[full]"

# Development (testing + code-quality tools)
pip install -e ".[dev]"
```

### Verify in 5 minutes

```bash
# 1. Initialize a project (creates directory structure and state files)
python scripts/init_project.py --team "202600001" --members "A,B,C" --type B

# 2. Dry-run the full pipeline (no solving; validates wiring)
python scripts/run_all.py --dry

# 3. Run the test suite
pytest tests/ -q

# 4. List available commands
make help
```

### As a Claude Code Skill

This repository is also a Claude Code Skill. Clone it into your skills directory to invoke it via `/cumcm-coach-skill-v7`:

```bash
git clone https://github.com/tianguangpu/cumcm-coach.git \
  ~/.claude/skills/cumcm-coach-skill-v7
```

---

## Architecture

### Pipeline

```
Problem statement
   │
   ├─▶ ① Problem analysis ── ambiguity detection / implicit constraints / dependency graph
   │
   ├─▶ ② Problem typing ──── A / B / C / D  →  innovation planning + strong-baseline advice
   │
   ├─▶ ③ Modeling & solving ─ algorithm selection → solver routing → self-verification
   │       └─▶ code/ + results/ + ANALYSIS_MODELING_REPORT.md
   │
   ├─▶ ④ Figure generation ── regular / advanced / flowchart tracks
   │       └─▶ figures/{png,pdf}/ + RESULTS_REPORT.md
   │
   ├─▶ ⑤ Paper writing ────── LaTeX or Typst
   │       └─▶ paper/main.{tex,typ} + sections/
   │
   └─▶ ⑥ Four-level review ── L1 automated → L2 cross-check → L3 adversarial → L4 red-team
           └─▶ VERIFY_REPORT.md  (any FAIL sends the stage back for rework)
```

### Repository layout

```
cumcm-coach/
├── SKILL.md                  # Full process specification
├── README.md / README.en.md  # Chinese / English docs
├── pyproject.toml            # Installable package + tool config
│
├── algorithms/               # 36 modules across 9 domains
│   ├── optimization/         #   GA / DE / SA-PSO / AHO / PSO variants / VRP / JobShop
│   ├── prediction/           #   TAM / ARIMA / MLP / GM(1,1)
│   ├── evaluation/           #   AHP+entropy+TOPSIS / VIKOR / GRA
│   ├── mechanistic/          #   FDM 1D/2D / FEM / ODE
│   ├── validation/           #   Sobol / Monte Carlo / assumption error / SHAP
│   ├── network/              #   Dijkstra / Kruskal / max-flow
│   ├── stats/                #   t / ANOVA / chi-square / non-parametric
│   ├── game/                 #   Pure & mixed-strategy Nash equilibria
│   ├── ecology/              #   Lotka-Volterra / SIR / SEIR
│   └── misc/                 #   Problem analyzer / innovation guide
│
├── scripts/                  # 30 CLI tools
├── templates/                # Paper templates (4 problem types × LaTeX/Typst)
├── references/               # 20 specification documents
├── vault/                    # Obsidian knowledge base
├── tests/                    # Test suite
└── state/                    # Runtime state and decision log
```

---

## Usage examples

### Optimization

```python
from algorithms.optimization.ga import GA

result = GA(
    objective=lambda x: sum(xi**2 for xi in x),
    dim=3,
    bounds=[(-5, 5)] * 3,
    pop_size=50,
    max_gen=200,
)
print(f"optimum {result['x_opt']}  value {result['f_opt']}")
```

### Comprehensive evaluation

```python
from algorithms.evaluation.ahp_entropy_topsis import ComprehensiveEvaluation

data = [[7, 9, 9], [8, 6, 8], [9, 4, 7]]
ev = ComprehensiveEvaluation(data, benefit_cols=[0, 1, 2], cost_cols=[])
weights = ev.run_entropy()      # objective (entropy) weighting
ranking = ev.topsis()           # TOPSIS ranking
```

### Automatic solver routing

```python
from scripts.solver_router import SolverRouter

router = SolverRouter()
result = router.solve({
    "type": "vrp",
    "dist": distance_matrix,
    "demands": demands,
    "capacity": 100,
    "n_vehicles": 5,
})
```

### Verifiable numbers (anti-fabrication)

```bash
python scripts/result_registry.py init
python scripts/result_registry.py add --id r1 --value 123.45 --status PASS
python scripts/result_registry.py verify
```

---

## Known limitations

Stated honestly, so you don't misuse them:

- `algorithms/optimization/nsga2.py` segfaults in some environments; its test is marked `skip` pending a fix.
- `algorithms/prediction/tam.py` requires `pip install tam` for full functionality; it falls back to a simplified additive decomposition otherwise, which must be disclosed in the paper.
- MATLAB-dependent features require a local MATLAB R2024a+; they fall back to Python plotting when unavailable.
- All MCP tools (fetch / tavily / matlab / …) are **optional enhancements**. The pipeline falls back to built-in implementations and never blocks on a missing tool.

---

## Contributing

Issues and PRs are welcome — please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

```bash
pip install -e ".[dev]"
pre-commit install      # install code-quality hooks
make test               # confirm the suite passes
```

---

## License

[MIT License](LICENSE)

---

## Acknowledgements

- [CUMCMThesis](https://github.com/latexstudio/CUMCMThesis) — LaTeX template reference
- [PuLP](https://github.com/coin-or/pulp) / [OR-Tools](https://github.com/google/or-tools) / [HiGHS](https://github.com/ERGO-Code/HiGHS) — optimization solvers
- [SALib](https://github.com/SALib/SALib) — global sensitivity analysis
- [scikit-learn](https://github.com/scikit-learn/scikit-learn) — API design reference

<div align="center">

**[⬆ Back to top](#cumcm-coach)**

</div>
