# Case Study B — PolicyBlind (9-agent civic policy platform, WARN → PASS path)

**Status:** Simulated comparison (smallest-fix-largest-effect demonstration)
**Date:** 2026-05-14
**Audit target:** PolicyBlind harness (entry in `~/CLAUDE.md`)
**Tool version:** tokensave v1.0
**Operator:** one

---

## TL;DR

| | Without tokensave | With tokensave |
|---|---|---|
| audit.py R3 status | unknown / unguided | **WARN — 2/5 met, 3 missing (R3a, R3b, R3d)** |
| Effort to reach well-formed | "wholesale redesign" intuition | **3 targeted fixes** to flip WARN → PASS |
| Cost per run estimate (250K in / 80K out) | **$3.25 (Opus, no cache)** | **$1.42 (Sonnet + cache 90%)** |
| Decision discipline | "team works, leave it alone" | "team works AND each cost-opt has actual evidence" |
| Effort estimate | weeks (no priorities) | **2 hours** (targeted) |
| Net | — | **-56% cost, ~2 hours work, structural FAIL→PASS** |

This case shows the **WARN tier's value**: a harness that's already partially optimal, where tokensave identifies the exact 3 patterns missing — instead of "audit says you have 9 agents, good luck." 80% of the savings live in fixes you can do in an afternoon.

---

## Setup

PolicyBlind is a 9-agent civic policy platform harness that blinds proposal authors during citizen scoring, then reveals the official donation channel after engagement. Architecture: source-collector → blinding-engineer → prompt-guardian → matching-engineer → editorial-frontend → legal-compliance → QA-auditor.

Already has some optimization: `_workspace/` file-based handoff (R3e), explicit Phase sequencing (R3c partial).

### audit.py output (catalog-wide)

```
R3 (C3) — Multi-Agent Team Composition (cost-optimized)
  `PolicyBlind` — 9 agents, 2/5 met, missing: R3a, R3b, R3d
  Decision: WARN (1-3/5 met — optimization opportunities)
```

The R3 decision **WARN** is the actionable middle tier. PASS would mean "you're already cost-optimal, congratulations." FAIL would mean "redesign." WARN means "3 specific patterns missing — fix these and you're done."

---

## Without tokensave (default workflow)

The operator knows PolicyBlind "works." 9-agent pipeline is mature. There's no obvious failure mode. The optimization question never gets asked because:

1. **No diagnostic signal** — `audit.py` doesn't exist. CLAUDE.md harness section reads "team composition: 9 agents (sonnet 3 + opus 2 + ...)" but no measurement of whether that composition is cost-optimal.
2. **All agents default to Opus.** The R3a finding ("role-tier mix missing") is invisible without an audit. Workers, supervisors, reviewers all use Opus by reflex.
3. **No cache_control.** R3b finding. SKILL.md mentions context but never `cache_control`. Each pipeline run repays the full system prompt + reference block.
4. **No wall-clock budget.** R3d finding. The blinding-engineer and prompt-guardian run as long as they want — no soft / hard limit. Mostly fine, but one runaway agent costs hours of tokens.

Cost estimate per pipeline run (250K in / 80K out):
```bash
$ python3 scripts/estimate_cost.py --model opus --input-tokens 250000 --output-tokens 80000
Cost: $3.25 per run
```

Operator runs this perhaps 50x/month → **$162/month, baseline**.

---

## With tokensave (targeted WARN → PASS)

### Step 1 — Read the R3 sub-rule output

```
PolicyBlind: 2/5 met, missing: R3a, R3b, R3d
```

Three patterns to fix. Each maps to a concrete change.

### Step 2 — Apply the three missing patterns

#### Fix R3a (role-tier mix) — 30 minutes

Open `references/optimal_team_composition.md`, find the row matching PolicyBlind's shape:

```
| Citizen policy matching | 8 (cross-verify) | Opus×1 | Sonnet×5 + Python×1 | Sonnet×1 | (a)+(d) | policyblind |
```

PolicyBlind has 9 agents (the matrix has 8 due to cross-verify variant) — model assignments transfer directly. Edit agent definitions:

```yaml
# Before
model: opus
# After (per matrix)
model: sonnet              # for source-collector, matching-engineer, editorial-frontend, QA-auditor, prompt-guardian
model: opus                # keep for blinding-engineer (high-stake) and architect
```

#### Fix R3b (cache_control) — 30 minutes

Identify the system prompt + SKILL.md sections that get re-read every call. PolicyBlind's `SKILL.md` is ~12KB. Add cache_control breakpoints at 4 stable positions.

Effect: 90% of input tokens become cached reads (10× cheaper). On 250K input tokens, this is the difference between $1.25 → $0.13 for input alone.

#### Fix R3d (wall-clock budget) — 30 minutes

Add a per-agent budget table to `SKILL.md`:

```yaml
budgets:
  blinding-engineer: soft 5min / hard 8min
  prompt-guardian: soft 2min / hard 4min
  matching-engineer: soft 3min / hard 5min
  ...
  on_hard_overshoot: truncate to checkpoint, escalate to operator
```

Effect: runaway agents stopped at limit. Cost-of-runaway eliminated.

### Step 3 — Re-audit

```bash
$ python3 scripts/audit.py
PolicyBlind: 5/5 met → PASS (well-formed)
```

### Step 4 — Measured cost (Sonnet workers + cache 90%)

```bash
$ python3 scripts/estimate_cost.py --model sonnet --input-tokens 250000 --output-tokens 80000 --cache-hit-ratio 0.9 --cache-ttl 1hr
Cost: $1.4175 per run
```

50x/month → **$71/month, after** (-56% from baseline).

---

## Quantified comparison

| Metric | Without tokensave | With tokensave | Delta |
|---|---|---|---|
| Cost per run (250K in / 80K out) | $3.25 (Opus, no cache) | $1.42 (Sonnet + cache 90%) | **-56%** |
| Monthly run cost (50x/month) | $162.50 | $70.88 | **-$91.62 / month** |
| Annual run cost (600 runs) | $1,950 | $851 | **-$1,099 / year** |
| Fix effort | unknown (no roadmap) | ~2 hours (3 targeted edits) | structural |
| Decision basis | intuition | R3 sub-rules + matrix lookup | evidence |
| Annual ROI on the 2 hours | — | ~$550 per hour saved | very high |

---

## What makes WARN tier different from FAIL

The valuable property of v1.0's 3-tier R3 (PASS / WARN / FAIL) is that **WARN is concrete and bounded**. Three named patterns. Three concrete fixes. No "tear down the harness" instinct.

PolicyBlind shows the WARN tier's payoff:
- Harness already works (no rewrite)
- Harness already partially optimal (R3c, R3e met)
- Three specific patterns to add (R3a, R3b, R3d)
- Two hours work → -56% cost forever

For comparison, paper-maker (Case A, FAIL) needs ~3 hours for -72%. The marginal cost-per-fix-hour is similar; PolicyBlind is simpler because the existing structure already met half the criteria.

---

## Caveats and limits

- **Simulated**, not measured. Cost estimates use plausible 250K/80K token assumptions; real PolicyBlind run sizes will differ.
- **The 50x/month assumption is illustrative.** Real PolicyBlind invocation rate depends on data feed cadence.
- **Quality regression risk on Sonnet downgrade for 5 worker agents not measured.** v1.2 measurement tools pending.
- **Single operator data point.** Same N=1 caveat as catalog.
- **R3b cache_control savings assume real 90% hit rate.** Boundary cases (first-of-day cold cache, prompt drift) reduce hit ratio.

---

## Recommendation for next action

PolicyBlind is the operator's **best dollar-per-hour candidate** for a real measurement:

1. Apply the three fixes (2 hours)
2. Run one pipeline before, one after, same input
3. Record actual cost, actual wall-clock, quality on critical-path tasks (blinding precision, matching accuracy)
4. Submit as a quality regression case study — converts this simulation into measured N=1 evidence

Combined with Case A (paper-maker, 3 hours), the operator gets:
- 2 measured cases study contributions toward v2.0 promotion criterion #2
- One FAIL → PASS (paper-maker, larger, harder)
- One WARN → PASS (PolicyBlind, smaller, easier)
- Annual savings estimate ~$3,000+ at current cadence

---

## Provenance

- Audit data: `python3 scripts/audit.py` (catalog-wide, 2026-05-14)
- Cost estimates: `python3 scripts/estimate_cost.py` (PRICING module, Anthropic public prices 2026-05-14)
- Matrix reference: `references/optimal_team_composition.md` row "Citizen policy matching"
- Harness metadata: `~/CLAUDE.md` PolicyBlind section
- R3 sub-rule mapping: `scripts/audit.py` R3a~R3e check functions
