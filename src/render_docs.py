"""Render docs/kpi_definitions.md from config/kpi_definitions.yml (single source of truth)."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
kpis = yaml.safe_load((ROOT / "config/kpi_definitions.yml").read_text())["kpis"]
lines = ["# KPI Definitions", "",
         "_Generated from `config/kpi_definitions.yml` by `src/render_docs.py`. Edit the YAML, not this file._", "",
         "| KPI | Formula | Source model | Notes |", "|---|---|---|---|"]
for k in kpis:
    lines.append(f"| {k['name']} | `{k['formula']}` | `{k['source']}` | {k['notes']} |")
(ROOT / "docs/kpi_definitions.md").write_text("\n".join(lines) + "\n")
print("wrote docs/kpi_definitions.md")
