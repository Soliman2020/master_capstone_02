# Module Summary

**Project 02 — Statistical Analysis (concise overview)**

---

## Project Overview

This module performs a two-test statistical analysis of the synthetic surveillance and access-control data. The goal is to validate (or invalidate) two signals that the downstream rule engine will use to score incidents:

- Whether the **restrictiveness of a zone** correlates with denial rate.
- Whether **event confidence** separates intrusion from normal motion.

---

## Methods

- **Chi-square test of independence** for zone type vs. access outcome (Agresti, 2002).
- **Independent-samples t-test** for intrusion vs. normal motion confidence (Student, 1908; Ruxton, 2006).
- **Cramér's V** reported as a chi-square effect size (Cohen, 1988).

---

## Key Numbers

| Test | Statistic | *p*-value | Effect Size |
|---|---|---|---|
| Chi-square (zone type × outcome) | χ²(1, N=9,173) = 4.491 | 0.0341 | Cramér's V = 0.0221 (negligible) |
| t-test (intrusion vs. normal confidence) | t(778) = 7.852 | 1.36 × 10⁻¹⁴ | Δ ≈ 0.21 (21 percentage points) |

- Intrusion mean confidence = **0.825**; normal motion mean = **0.612**.

---

## Plain-Language Findings

Yes, restricted zones show a *slightly* higher denial rate, but the effect is so small (Cramér's V ≈ 0.02; Cohen, 1988) that the rule engine should not lean on it. Meanwhile, intrusion events really do stand out from normal motion in their confidence score (about 21 percentage points higher), which is a strong signal (Student, 1908) — though the specific `confidence > 0.85` cutoff should still be validated against real precision/recall before deployment.

---

## Visualizations

### Figure 1: Access Outcome Rate by Zone Type

![Access outcome rate by zone type](viz1_access_by_zone.png)

### Figure 2: Confidence Score Distribution by Event Type

![Confidence score distribution by event type](viz2_confidence_by_event.png)

### Figure 3: Access Log Volume by Hour of Day

![Access log volume by hour of day](viz3_access_by_hour.png)

---

## Limitations

- **Synthetic data**: The generator explicitly injects a uniform timestamp distribution, so the after-hours rule is not validated here (Agresti, 2002).
- **Effect sizes**: Cramér's V and Cohen's d should be reported alongside p-values to avoid over-interpreting statistical significance (Cohen, 1988).
- **No bias audit yet**: An outcome-parity / precision-recall breakdown by zone or site should be added before production.
- **Restricted-zone definition**: Currently imported from `RESTRICTED_ZONES` in the Project 01 generator; a schema change to a `zones.is_restricted` column would require updating the import.

---

## Reproducibility

- `SEED = 42` is set in the first code cell.
- Processed datasets in `data/processed/` are deterministic outputs of the Project 01 generator.
- `requirements.txt` is frozen from the active venv.

---

## Takeaway

The data supports using classifier confidence as a **strong signal** for flagging intrusion events. The zone-restrictiveness signal exists but is **too weak** to drive the rule engine on its own. Both findings should be re-tested against operational data before production deployment.

---

## References

- Agresti, A. (2002). *Categorical Data Analysis* (2nd ed.). Wiley. [https://onlinelibrary.wiley.com/doi/book/10.1002/0471249688](https://onlinelibrary.wiley.com/doi/book/10.1002/0471249688)
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates. [https://pmc.ncbi.nlm.nih.gov/articles/PMC6736231/#r1](https://pmc.ncbi.nlm.nih.gov/articles/PMC6736231/#r1)
- Ruxton, G. D. (2006). The unequal variance t-test is an underused alternative to Student's t-test and the Mann–Whitney U test. *Behavioral Ecology*, 17(4), 688–690. [https://academic.oup.com/beheco/article-abstract/17/4/688/215960](https://academic.oup.com/beheco/article-abstract/17/4/688/215960)
- Student (1908). The probable error of a mean. *Biometrika*, 6(1), 1–25. [https://www.jstor.org/stable/2331554](https://www.jstor.org/stable/2331554)