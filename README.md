# Pulse

**Version:** v0.2 – Trust Foundations

Pulse is a symbolic-capital foresight simulator that models emotional overlays, strategic fragility, capital exposure forks, and trust-weighted forecast generation.
It's goal is to ingest real-time market, social, political, ecological, etc. data, run monte carlo simulations, state retrodiction, forecast retrodiction, etc. to generate confidence on probabilistic outcomes. 

---

## 🧬 Project Identity

Pulse is a modular simulation intelligence engine designed for recursive forecasting, retrodiction, and capital/narrative strategy synthesis.  
It operates by combining emotional-symbolic overlays, trust scoring, and adaptive rule evolution to generate and validate optimal timelines.  
Memory and trace persistence are core: all simulation cycles are scored, pruned, and iteratively improved.

---

## 🔧 Features

- Emotional overlays: Hope, Despair, Rage, Fatigue, Trust
- Capital fork logic: NVDA, MSFT, IBIT, SPY
- Forecast generator with symbolic decay and exposure deltas
- Trust engine scoring confidence from 0.0–1.0
- Fragility index based on symbolic tension and volatility
- Strategos Digest: grouped, sorted, and labeled forecast output
- PFPA forecast memory with confidence, fragility, and trace IDs
- Digest export system (`digest.txt`)
- Modular, fully readable code (Python 3.10+)

---

## 🚀 Quickstart

    cd pulse
    python main.py

- Outputs 5 forecast cycles by default
- Prints Strategos Digest grouped by trust level
- Saves optional `digest.txt` if logging is enabled

---

## 📂 Module Overview

Pulse/
│
├── core/                  # Central config, registry, and path management
│   ├── __init__.py
│   ├── pulse_config.py
│   ├── path_registry.py
│   └── module_registry.py
│
├── simulation_engine/     # Core simulation modules
│   ├── __init__.py
│   ├── worldstate.py
│   ├── turn_engine.py
│   ├── state_mutation.py
│   └── rules/
│       ├── __init__.py
│       ├── rule_fingerprint_expander.py
│       └── reverse_rule_engine.py
│
├── forecast_engine/       # Forecasting logic, batch, and export
│   ├── __init__.py
│   ├── forecast_exporter.py
│   ├── forecast_log_viewer.py
│   └── ...
│
├── forecast_output/       # Output formatting, digest, and logging
│   ├── __init__.py
│   ├── forecast_licenser.py
│   ├── pfpa_logger.py
│   └── ...
│
├── foresight_architecture/  # Digest, compression, and related tools
│   ├── __init__.py
│   ├── digest_exporter.py
│   ├── digest_logger.py
│   └── strategos_digest_builder.py
│
├── memory/                # Forecast memory and audit
│   ├── __init__.py
│   ├── forecast_memory.py
│   └── pulse_memory_audit_report.py
│
├── symbolic_system/       # Symbolic overlays, drift, scoring
│   ├── __init__.py
│   └── symbolic_memory.py
│
├── capital_engine/        # Capital fork logic
│   ├── __init__.py
│   └── asset_forks.py
│
├── diagnostics/           # Self-checks, audits, and stubs
│   ├── __init__.py
│   └── plia_stub.py
│
├── operator_interface/    # CLI, UI, dashboards, prompt logger
│   ├── __init__.py
│   ├── pulse_prompt_logger.py
│   └── strategos_digest.py
│
├── utils/                 # Shared utilities
│   ├── __init__.py
│   ├── log_utils.py
│   ├── error_utils.py
│   └── performance_utils.py
│
├── dev_tools/             # Dev scripts, code analysis, migration
│   ├── __init__.py
│   ├── generate_pulse_modules.py
│   ├── pulse_shell_autohook.py
│   ├── pulse_scan_hooks.py
│   ├── hook_utils.py
│   └── module_dependency_map.py
│
├── tests/                 # Unit tests and fixtures
│   ├── __init__.py
│   └── test_forecast_memory.py
│
├── quarantine/            # Quarantined/legacy files for review
│   └── ...
│
├── docs/                  # Documentation, API reference, deprecation policy
│   └── ...
│
├── main.py                # Main entry point
├── pulse_ui_shell.py      # UI shell entry point
├── README.md
├── README.txt
└── .gitignore

---

## 🆕 New Features

- **Rule Fingerprinting:**  
  - See `simulation_engine/rules/reverse_rule_mapper.py` and `rules/rule_fingerprints.json`.
  - CLI: `python simulation_engine/rules/reverse_rule_mapper.py --validate` or `--match key1=val1 key2=val2`
- **Simulation Trace Viewer:**  
  - CLI: `python simulation_engine/utils/simulation_trace_viewer.py <trace.jsonl> [--summary] [--plot] [--plot-var var] [--plot-tags] [--export-summary out.txt]`
- **Memory Audit & Coherence Check:**  
  - Available in UI and interactive shell (`memory-audit`, `coherence-check`).
- **Interactive Shell Help:**  
  - Type `help` for a list of commands and usage.

---

## 🆕 Strategos Digest CLI & Live UI

- **CLI:**  
  Build a digest from compressed forecasts or prompt filter:
  ```
  python -m forecast_output.strategos_digest_builder --from-prompt "AI" --export markdown --output digest.md
  ```
- **Live UI:**  
  Call `live_digest_ui(memory, prompt="AI", n=10, export_fmt="markdown")` to generate and display digest interactively.

---

## 🛣 Roadmap & Module Status

| Area                    | Status      | Gaps/Recommendations                                 |
|-------------------------|------------|------------------------------------------------------|
| Digest Compression      | Partial     | Add narrative clustering, top-N, driver summary      |
| Forecast Belief Chain   | Missing     | Implement ancestry, drift, tree, divergence          |
| Reverse Rule Evolution  | Partial     | Add ranking, rule suggestion, robust scoring         |
| Regret Engine           | Missing     | Implement regret analysis, feedback loop             |
| Utility Add-ons         | Missing     | Add replay, lineage viewer, digest comparison        |

---

## 🛣 Roadmap

- **v0.3** → Input signal horizon, retrodiction engine
- **v0.4** → Forecast compression, memory decay, strategic prioritization
- **v1.0** → Autonomous simulation intelligence, UI, agent modeling

---

## ⚠️ Status

Pulse v0.2 is functional but experimental.  
All forecasts are scored and labeled, but **licensing, memory pruning, and backtest scoring are still under construction.**

This is an interpretability-first build: every module is readable, auditable, and designed for modular iteration.

---

## Directory Structure

- `simulation_engine/` — Core simulation modules
- `utils/` — Shared utilities (logging, error, file, performance)
- `tests/` — Unit tests and fixtures
- `quarantine/` — Quarantined files and review script
- `docs/` — Documentation, deprecation policy, API reference

---

## Centralized Configuration

All file paths and key configuration values are now managed in `core/path_registry.py` and `core/pulse_config.py`.  
Modules should import from these files instead of hardcoding paths or constants.

Example:
```python
from core.path_registry import PATHS
from core.pulse_config import CONFIDENCE_THRESHOLD
```

---

## Coding Standards

- Use type annotations and docstrings in all new code.
- Shared logic must go in `utils/`.
- Add/maintain tests for each module in `tests/`.
- Use `@profile` from `utils/performance_utils.py` for performance-critical code.

---

## Deprecation & Milestone Policy

See `docs/deprecation_policy.md`.
