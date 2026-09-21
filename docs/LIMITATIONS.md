
---

# 7. `docs/LIMITATIONS.md`

```markdown
# RIPPLE — Limitations

This document records limitations honestly.

A limitation must not be hidden merely because it makes the project look less complete.

---

# 1. Academic Prototype

RIPPLE is an academic prototype.

It must not be represented as a production banking credit decision system.

---

# 2. Synthetic Relationships

Business relationship data is synthetic.

Synthetic relationships do not represent actual commercial relationships.

Any network-derived result must disclose this.

---

# 3. Dataset Population

Training datasets may not perfectly represent the intended Indian SME population.

Differences may include:

- geography
- regulation
- industry distribution
- company size
- financial reporting practices
- default behaviour

---

# 4. Free-Tier Infrastructure

The system depends on free-tier services.

Potential limitations include:

- service sleeping
- cold starts
- storage limits
- compute limits
- API limits
- database limits

---

# 5. Model Limitations

Model performance depends on:

- dataset quality
- feature availability
- target definition
- class imbalance
- temporal coverage
- population mismatch

---

# 6. Calibration

Calibration performance must be reported empirically.

No claim of calibrated probability should be made until calibration has actually been evaluated.

---

# 7. GNN Limitations

Graph performance depends heavily on:

- graph quality
- synthetic relationship generation
- network density
- relationship realism
- label propagation effects

If GNN does not provide useful improvement, this must be reported honestly.

---

# 8. Scenario Analysis

Scenario outputs are:

- model-based estimates
- not forecasts
- not causal estimates

They should not be interpreted as guaranteed future outcomes.

---

# 9. Explainability

SHAP explains the tabular model.

It does not automatically explain the GNN.

---

# 10. Fairness

Fairness must be evaluated using the available data.

Absence of a detected issue does not prove absence of bias.

---

# 11. Production Readiness

Before production use, additional work would be required around:

- larger infrastructure
- monitoring
- security
- compliance
- model governance
- fairness
- auditability
- real-world relationship data
- independent validation
- disaster recovery
- access management

---

# 12. Open Limitations

| ID | Limitation | Impact | Status |
|---|---|---|---|
| LIM-001 | | | OPEN |