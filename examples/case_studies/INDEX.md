# Case studies

Measured ROI cases — model downgrades, Python phase splits, prompt caching applications — with before/after numbers and quality deltas.

> Submit via [quality_regression_report issue template](../../.github/ISSUE_TEMPLATE/quality_regression_report.md).
> Even N=1 reports are accepted. The matrix gets revised when ≥3 converging reports cover the same workload pattern.

## Most-wanted (currently unfilled by measurement)

| Workload pattern | Original → Target | Measurement status |
|------------------|-------------------|-------------------|
| Verbatim 1:1 mapping (HD-003) | Opus → Python phase | **simulated (Case A)**, real-measurement pending |
| Standard academic prose | Opus → Sonnet | simulated (Case A), real pending |
| Civic policy multi-agent workers | Opus → Sonnet + cache | **simulated (Case B)**, real-measurement pending |
| Multi-language translation | Opus → Sonnet | seeking |
| Fact-checker (high-stake) | Opus → Sonnet | seeking |
| Code review | Opus → Sonnet | seeking |

## Published

| ID | Harness | Type | Result | Date |
|----|---------|------|--------|------|
| [Case A](A_paper_maker_retrospective.md) | paper-maker (16-agent academic) | Retrospective + simulated | -72% cost, -180× on worst agent (HD-003 trap caught at design time) | 2026-05-14 |
| [Case B](B_policyblind_warn_to_pass.md) | PolicyBlind (9-agent civic policy) | Simulated WARN → PASS demo | -56% cost, ~2-hour fix effort, $1,099/year saved at 50 runs/month | 2026-05-14 |

Both cases are **simulated using `estimate_cost.py` projections, not real before/after measurements**. They demonstrate the decision discipline tokensave introduces. Real measured case studies are the next step — see each case's "Recommendation for next action" section.

## How a case study modifies the matrix

- **Single net-win report** → matrix row gets confidence increment
- **Single net-loss report** → matrix row gets caveat asterisk
- **Three converging reports (same direction)** → matrix row revised
- **Three reports diverging** → matrix row split by sub-context
