---
name: ⚖️ Quality regression report (★ most-wanted)
about: You downgraded a model (Opus → Sonnet → Haiku) and measured what happened. Help close the cost-vs-quality gap.
title: "regression: <agent name>, <Opus → X>, quality delta <±N%>"
labels: ["quality-regression", "evidence", "★ most-wanted"]
---

> The `task_to_model_matrix.md` says "downgrade is fine for X". This claim **cannot be trusted without measured quality delta** at the boundary.
> Quality regression reports are the most valuable evidence we currently lack.
> Even N=1 reports are accepted — they accumulate into a real boundary-case map.

## Agent / task

- **Agent or task name**: <e.g., `paper-citation-formatter` or `daily-news-summarizer`>
- **Workload pattern from matrix**: <e.g., "Verbatim 1:1 mapping" or "Standard prose drafting">
- **Original model**: <Opus 4.7 / Sonnet 4.6 / Opus 4>
- **Downgraded model**: <Sonnet 4.6 / Haiku 4.5 / Python>

## Quality measurement method

- **Golden task set size**: <e.g., 10 representative tasks>
- **Evaluation method**: <human rating / automated metric / fact-checker pass-rate / unit test pass-rate / N/A>
- **Quality metric used**: <accuracy / pass-rate / coherence rating / other>

## Results

| Metric | Original | Downgraded | Delta |
|--------|---------:|-----------:|------:|
| Cost per call | $__ | $__ | __ % |
| Quality score | __ | __ | __ % |
| Retry rate | __ % | __ % | __ pp |
| Wall-clock | __ s | __ s | __ % |

## Net effect

- [ ] **Net win** — quality acceptable, cost saved, no retry surge
- [ ] **Marginal** — small quality loss for small cost saving
- [ ] **Net loss** — quality regression triggered retries, overall cost equal or higher
- [ ] **Mixed** — fine for some tasks, fails on boundary cases

## Boundary case observations

<which sub-tasks degraded the most? what surprised you?>

## Recommendation

- **For this exact agent / task**: <stay / downgrade / re-evaluate at v1.x>
- **For matrix update**: <should the matrix row for this workload pattern be revised? how?>

## Reproducibility

- [ ] I can share the golden task set in a follow-up
- [ ] I can share quality measurement methodology
- [ ] I'd rather discuss in this issue

---

_These reports directly modify the `task_to_model_matrix.md`. Three converging regression reports on the same workload pattern → matrix row revised. One single counter-example → asterisk + caveat added._
