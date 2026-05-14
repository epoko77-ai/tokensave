# Case studies

Measured ROI cases — model downgrades, Python phase splits, prompt caching applications — with before/after numbers and quality deltas.

> Submit via [quality_regression_report issue template](../../.github/ISSUE_TEMPLATE/quality_regression_report.md).
> Even N=1 reports are accepted. The matrix gets revised when ≥3 converging reports cover the same workload pattern.

## Most-wanted (currently unfilled)

| Workload pattern | Original → Target | Measurement status |
|------------------|-------------------|-------------------|
| Verbatim 1:1 mapping (HD-003) | Opus → Python phase | seeking |
| Standard academic prose | Opus → Sonnet | seeking |
| Multi-language translation | Opus → Sonnet | seeking |
| Fact-checker (high-stake) | Opus → Sonnet | seeking |
| Code review | Opus → Sonnet | seeking |

## Submitted

(empty — start the first case study via the issue template)

## How a case study modifies the matrix

- **Single net-win report** → matrix row gets confidence increment
- **Single net-loss report** → matrix row gets caveat asterisk
- **Three converging reports (same direction)** → matrix row revised
- **Three reports diverging** → matrix row split by sub-context
