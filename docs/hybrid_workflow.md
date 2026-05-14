# Hybrid workflow: harness-diagnostic + tokensave

> Two complementary tools for multi-agent Claude Code harnesses. Diagnose structurally with harness-diagnostic (HD), then act on cost and runtime gaps with tokensave.

Same authoring lineage (`paper-maker` observations); complementary detection surface. HD catches gaps invisible at file level; tokensave catches cost traps invisible at the structural-gap level.

---

## Why hybrid

| Tool | Question it answers | Output |
|------|---------------------|--------|
| [harness-diagnostic](https://github.com/epoko77-ai/harness-diagnostic) | "What is structurally missing in my harness pipeline?" | 21 gaps × PASS/FAIL/WARN report, 5-layer model |
| [tokensave](https://github.com/epoko77-ai/tokensave) | "Where is my harness burning tokens and what do I do about it?" | 9 rules × cost-impact audit, model decision tree, cost estimator, runtime hook |

The two tools measure different things at the same level of abstraction — the harness as a system, not any single file. Running only one leaves half the picture dark.

---

## Recommended pipeline

```bash
# Step 1 — structural gap report (HD)
python3 harness-diagnostic/cli/diagnose.py /path/to/your/harness

# Step 2 — cost-impact audit (tokensave)
python3 tokensave/scripts/audit.py /path/to/your/harness

# Step 3 — read tokensave fix_plan output, prioritize by ROI
python3 tokensave/scripts/model_selector.py --task "<agent role description>"

# Step 4 — apply fixes, then re-run both and measure delta
python3 harness-diagnostic/cli/diagnose.py /path/to/your/harness
python3 tokensave/scripts/audit.py /path/to/your/harness
```

Both tools are standard library only (Python 3.10+), no `pip install`.

---

## Coverage matrix

Where the two tools overlap and where they diverge:

| Pattern | HD rule | tokensave rule | Coverage |
|---------|---------|----------------|----------|
| Deterministic work in LLM | HD-003 ★ (Tier 1) | R2 (C2.x) | Both — reliability bug AND cost bug |
| Report-first convention missing | HD-010 (Tier 1) | R7 (C8.1) | Both |
| Per-call output cap missing | HD-011 (Tier 1) | R8 (C9.1) | Both |
| Uniform model assignment | HD-020 (Tier 3) | R1 (C1.1) | Both |
| cache_control breakpoints absent | — | R5 (C5.1) | tokensave only |
| Multi-agent 7x multiplier | — | R3 (C3.1) | tokensave only |
| Full file read vs offset/limit | — | R6 (C7.1) | tokensave only |
| SKILL.md / CLAUDE.md body bloat | — | R4 (C4.1), R9 (C4.5) | tokensave only |
| FAIL gate without cascade actor | HD-001 (Tier 2) | — | HD only |
| Per-agent action item dispatch | HD-002 (Tier 2) | — | HD only |
| Scope field gate missing | HD-006 (Tier 2) | — | HD only |
| Wall-clock budget per agent | HD-009 (Tier 2) | — | HD only |
| No progress instrumentation | HD-018 (Tier 2) | — | HD only |
| Parallel fanout not size-parameterized | HD-007 (Tier 1) | — | HD only (partial overlap C3.2) |

The 4 overlapping patterns (HD-003, HD-010, HD-011, HD-020) are both reliability bugs and cost bugs — HD names the structural absence, tokensave names the cost class. Expect overlapping FAIL signals on those four when running both tools.

---

## Adoption story

When building tokensave's taxonomy, patterns from harness-diagnostic were evaluated against the N>=2 external-corroboration rule: a pattern enters the tokensave catalog only if two or more independent external sources confirm it.

Result:

| HD gap | Adopted into tokensave? | Reason |
|--------|------------------------|--------|
| HD-003 (det-in-LLM) | **Yes → R2** | N>=2: Augment Code, Martin Fowler, arXiv 2604.08906 |
| HD-010 (report-first) | **Yes → R7** | N>=2: Anthropic docs, paper-maker empirical |
| HD-011 (per-call cap) | **Yes → R8** | N>=2: Efficient Agents study, paper-maker empirical |
| HD-020 (uniform model) | **Yes → R1** | N>=2: Anthropic A001/A013, community benchmarks |
| HD-001, HD-007, HD-016, HD-018 | Partial | Structural overlap only; cost impact class not independently confirmed at N>=2 |
| Remaining 13 HD rules | Not yet | Standard reliability practices; awaiting independent cost-impact corroboration |

HD users running tokensave on top should expect:
- **Overlapping FAIL signals** on HD-003/010/011/020 — this is expected, not noise.
- **Complementary signals** on R5/R3 (caching, multi-agent multiplier) — these have no HD counterpart.
- **Complementary signals** on HD-001/006/009/018 — these have no tokensave counterpart.

---

## Signal interpretation

When both tools flag the same harness location:

```
HD-003 FAIL + R2 FAIL on the same agent
  → confirmed cost bug (structural absence + cost class both confirmed)
  → fix priority: highest

HD-001 FAIL only (no tokensave counterpart)
  → reliability gap; cost impact not independently measured
  → fix based on reliability requirements

R5 FAIL only (no HD counterpart)
  → pure cost optimization; no structural absence
  → fix based on invocation frequency × SKILL.md size
```

---

## Quick reference: tool commands

```bash
# harness-diagnostic
python3 cli/diagnose.py /path/to/harness             # text report
python3 cli/diagnose.py /path/to/harness --json      # machine-readable
# also available: NL diagnostic prompt (_workspace/diagnose.prompt.md)

# tokensave
python3 scripts/audit.py                             # full ~/.claude catalog
python3 scripts/audit.py /path/to/harness            # single harness
python3 scripts/audit.py --json | jq .findings       # structured output
python3 scripts/model_selector.py --task "..."       # model recommendation
python3 scripts/estimate_cost.py --compare-all       # cost comparison
```
