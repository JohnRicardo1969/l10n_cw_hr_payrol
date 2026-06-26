# Verification review — decisions reality-checked, not asserted from memory

**Verdict:** Pass with one flagged seed item. No invariant rests on stale or invented tech.

- **Salary-rule Python context** (`employee/contract/payslip/categories/rules/inputs/worked_days`, assign `result`) — verified against Odoo 19 payroll docs. AD-3's reference discipline rests on a real API. ✔
- **Stack pinned**: Odoo 19.0, module `19.0.0.1.0`, OPL-1, country `cw`. ✔
- **`compute_tax`** is the module's own method on `hr.tax.bracket`, not a framework API — no external version risk. (But see adversarial review: its read contract for non-progressive rates is underspecified.)
- **FLAG (seed, non-blocking)**: `'countries': ['cw']` manifest key — correct for localization manifests (~Odoo 17+), but confirm at implementation against the Odoo 19 manifest reference. It is seed, not a spine invariant.
- **Statutory 2026 values** (brackets, ceilings, thresholds) are data sourced from the Belastingdienst/SVB PDFs in `docs/` — out of scope for spine-level reverification; they live as dated records per AD-5.
