---
name: 📊 Baseline submission
about: Share your `audit.py` results — help grow the catalog from N=1 toward N≥3 operators
title: "baseline: <one-line summary, e.g., '40-harness setup, 60% Opus, 2 HD-003 RISKY'>"
labels: ["baseline", "evidence"]
---

> This is how `plz-save-token` grows from a one-operator catalog to a community catalog.
> The numbers in your audit are the **evidence we lack most**.
> All fields optional; submit what you can.

## Setup overview

- **Number of harnesses operated**: <e.g., 14>
- **Total agents across all harnesses**: <e.g., 67>
- **Total skills**: <e.g., 18>
- **Primary use case**: <e.g., academic writing / data ingestion / customer support / coding assistant / mixed>
- **How long running**: <e.g., 3 months>

## Audit results

Run: `python3 scripts/audit.py /path/to/your/harness/root` (or catalog-wide without args).

Paste the **Summary** section + **Findings** rule summary below.

```
<paste audit.py output here>
```

## Key numbers (compared to N=1 reference)

| Metric | Reference (one-operator catalog) | Yours |
|--------|----------------------------------|-------|
| Opus % | 99.0% (103/104) | __ |
| 5+ agent harnesses | 25/27 (93%) | __ |
| Cache_control 0 / total | 27/27 (100%) | __ |
| HD-003 RISKY agents | 20 | __ |
| Writer per-call cap missing | 13/14 | __ |

## Observations

- **What surprised you about your own numbers?**
- **What patterns does the catalog miss for your shape?**
- **Are there optimization opportunities the matrix doesn't capture?**

## Permission

- [ ] You may anonymize and aggregate my numbers into the README "Real-world baseline" table.
- [ ] Credit me in `examples/contributed_baselines/` (optional).
- [ ] Keep private — discuss in this issue only.

---

_Submitting moves the catalog from N=1 → N=2. We track contributors in `examples/contributed_baselines/INDEX.md`._
