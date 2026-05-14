# plz-save-token

> **Cost-optimization lint for multi-agent Claude Code harnesses.**
> Helps you build well-formed multi-agent teams. Catches misallocated team compositions and burning cost patterns — not the multi-agent design itself.
> Companion to [harness-diagnostic](https://github.com/epoko77-ai/harness-diagnostic): one diagnoses, the other reduces.

**TL;DR.** I audited my own 27-harness Claude Code setup: 99% of agents on Opus, 0 of 27 harnesses using prompt caching, 20 agents routing regex through an LLM, 93% spinning up 5+ agent teams. The teams are mostly fine — paper-maker, ainews-daily, policyblind are well-formed hierarchical/pipeline harnesses. The problem is paying the 7×~15× multiplier without applying the five cost-optimization patterns that make multi-agent worth it. `plz-save-token` is the catalog, audit script, decision tree, and optimal team composition matrix I built to make multi-agent harnesses well-formed instead of just expensive. Standard library only. Run `python3 scripts/audit.py` on your `~/.claude` to see your numbers in under five seconds.

---

## The problem

Multi-agent Claude Code teams do cost 7×~15× per session — and they are often worth it. paper-maker's 16-agent hierarchical reviewer setup catches things a single session never would. ainews-daily's 7-stage pipeline buys real wall-clock collapse. policyblind's 8-agent cross-verify is exactly the kind of independent-reasoning isolation that justifies the multiplier.

The trap is paying that multiplier **without the five cost-optimization patterns** that make it justifiable. `plz-save-token` catches the missing patterns, not the team itself. Each `SKILL.md` and each agent definition is usually fine internally. The failures live *between* files, in the team's composition:

- **Model-tier misallocation across the team.** Every agent — orchestrator, worker, reviewer — defaults to Opus. Read-only scouts, regex classifiers, boilerplate writers all pay Opus prices to do work Sonnet or Haiku finishes at 40-80% less. The multi-agent multiplier compounds the wrong choice.
- **Deterministic work routed through an LLM (the HD-003 trap).** Verbatim 1:1 mapping, BibTeX, CSV-to-JSON parsing, citation formatting — provably regex-plus-dictionary work — gets sent to an LLM that loops 91 minutes on tool calls. Same work in Python: 30 seconds.
- **Common context re-paid every call.** Cached input reads cost 10% of base. A 23 KB `SKILL.md` × 5 agents × 10 invocations = paying for the SKILL.md 50 times instead of once. Nobody notices because savings only show up when you opt in to `cache_control`.
- **No parallel/sequential intent, no caps, no file-based handoff.** Execution mode is accidental; runaway risk is uncapped; agents leak tokens through SendMessage instead of writing to `_workspace/`. The five patterns together turn a 7×~15× multiplier into something the harness actually deserves.
- **SKILL.md and CLAUDE.md bloat.** Average SKILL.md in one operator's catalog: 8,693 chars. Largest: 32,987. Most of that is decoration — changelogs, roadmaps, philosophy — not phase definitions the agent needs at runtime.

All invisible to file-level linters like agnix. Visible only when you measure the harness as a system. The optimal team composition matrix (`references/optimal_team_composition.md`) is the prescription.

## A real-world baseline (the why)

Numbers from one operator's 27-harness Claude Code catalog, 2026-05-14 static audit:

| # | Finding | Value | Rule |
|---|---------|-------|------|
| H1 | Opus model share across all agents | **99.0% (103/104)** | R1 FAIL |
| H2 | Harnesses mentioning prompt caching | **0/27** | R5 FAIL |
| H3 | Multi-agent (5+ team) harnesses missing 3+ of 5 cost-optimization patterns | **~15/25 of 5+-team harnesses (60%)** | R3 FAIL |
| H4 | Agents routing deterministic work through LLM (HD-003) | **20 RISKY** | R2 FAIL |
| H5 | Writer/drafter agents with no per-call output cap | **13/14** | R8 FAIL |

Footnote: numbers from one operator's `~/.claude` (27 harnesses, 104 agents, 32 skills). Full data in `examples/personal_baseline.md`. Broader inbound diagnostics welcome — see Contributing. H1 (99% Opus) is the kind of uniform-tier choice you would never make at the file level but is the default when no one is looking at the system.

## What plz-save-token gives you

Four modes, three headline artifacts.

| Mode | What it does | Cost |
|------|--------------|------|
| **Pre-flight** | `model_selector.py` — natural-language task → recommended model + rationale + cost. | 0 LLM calls |
| **Authoring** | 9 forbidden-pattern checklist + 24-row task-to-model matrix for writing new SKILL.md / agents | passive |
| **Audit** | `audit.py` — 9 static rules across your `~/.claude`. JSON output supported. | ~5 sec, 0 LLM calls |
| **Hook** | `settings.json` runtime guard on `PreToolUse:Task` and `UserPromptSubmit`. Never blocks. | 0 blocking |

Three headline artifacts:

1. **`references/task_to_model_matrix.md`** — 24-row matrix mapping task types to Python / Haiku / Sonnet / Opus with source citations and cost-versus-Opus delta.
2. **`scripts/model_selector.py`** — same matrix as a CLI decision tree. Zero LLM calls. Answers "what model for this task?" in under a second.
3. **`references/optimal_team_composition.md`** — multi-agent well-formed matrix. 8 operator-grounded workload patterns × 5 cost-optimization patterns (role-tier mix, common-context caching, parallel/sequential declaration, wall-clock + per-call cap, file-based handoff). `audit.py` R3 sub-rules (R3a~R3e) map 1:1 to the 5 patterns. The thing that makes a 5+ team worth the multiplier instead of just expensive.

## Quick start (3 minutes)

```bash
git clone https://github.com/epoko77-ai/plz-save-token
cd plz-save-token

# Audit your entire ~/.claude catalog (9 rules, ~5 seconds)
python3 scripts/audit.py
python3 scripts/audit.py --top 10                       # priority hotspots
python3 scripts/audit.py /path/to/harness/root          # single harness
python3 scripts/audit.py --json | jq .

# Ask the decision tree what model to use
python3 scripts/model_selector.py --task "extract tables from PDF, normalize to CSV"
python3 scripts/model_selector.py --task "weekly tech column, 5000 words" --tokens 8000 --quality high

# Compare model costs
python3 scripts/estimate_cost.py --compare-all --input-tokens 30000 --output-tokens 5000
```

Standard library only. No `pip install`. Python 3.10+.

**Single-harness mode with custom prefix mapping** — `audit.py` discovers agents by matching harness name against a prefix map. The default map contains generic placeholders. Customize without touching code:

```bash
export PLZ_SAVE_TOKEN_HARNESS_PREFIX_MAP='{"my-harness":["mh-"],"another":["an-"]}'
python3 scripts/audit.py /path/to/my-harness
```

A full 27-harness example mapping is in `examples/personal_baseline.md §harness-mapping`.

## How it was built (4-axis evidence, N>=2 rule)

The pattern catalog was assembled by three parallel research scouts plus one static measurement pass:

- **Scout A — Anthropic official.** 40 citations from `docs.anthropic.com`, engineering blog, API docs, Claude Code docs. Covers caching, model selection, context, agent SDK, subagents, hooks.
- **Scout B — Community.** 32 citations from X, Reddit, HN, engineering blogs, GitHub. Quantitative where possible — token deltas, cost percentages, reproductions.
- **Scout C — Academic and empirical.** 9 citations from arXiv (Zhang et al. 2026 on 409 agentic bugs), Augment Code, Martin Fowler, OpenAI's harness-engineering note, plus static measurement of one operator's 104-agent, 32-skill, 33-CLAUDE.md catalog.
- **Adoption rule.** A pattern is registered only if **two or more independent external sources confirm it** (N>=2). User-baseline-only patterns are marked "hotspot, awaiting external corroboration" and kept separate.

Result: **10 categories, 31 sub-patterns** in `_workspace/03_patterns/taxonomy.md`. Of [`harness-diagnostic`](https://github.com/epoko77-ai/harness-diagnostic)'s 21 gaps, 4 met the bar and were adopted: **HD-003** (deterministic work routed through an LLM — the 91-minute trap), **HD-010** (report-first convention silently losing artifacts), **HD-011** (writer agent with no per-call output cap), and **HD-020** (uniform model tier across all roles). 4 were partially adopted, 11 were not adopted yet. This rule is the difference between "yet another LLM cost tool" and a catalog that stays honest as it grows.

## Headline 1 — Task-to-model matrix (excerpt)

Full 24 rows in `references/task_to_model_matrix.md`. First 8:

| # | Task type | Recommended | Source | vs Opus |
|---|-----------|-------------|--------|--------:|
| 1 | Deterministic transform (regex, 1:1, BibTeX, format normalization) | **Python** | S-C07, S-C09 | free |
| 2 | File search, grep, codebase exploration | **Haiku** | A013, S-B016 | -80% |
| 3 | Pattern matching, rule-based classification (short input) | **Haiku** | A013, S-B017 | -80% |
| 4 | Short structured summary (one paragraph) | **Haiku** | S-B031 | -80% |
| 5 | Natural-language structured output (JSON, tables) | **Sonnet** | A001, S-B017 | -40% |
| 6 | Standard code, debugging | **Sonnet** | A001, S-B016 | -40% |
| 7 | Document drafting (up to 5,000 words) | **Sonnet** | A001, S-B018 | -40% |
| 8 | Academic / policy paper (5K+ words, high-stake) | **Opus** | S-C09 | 0% justified |

Core rule: deterministic → Python. Natural-language structured output or standard code → Sonnet. Only deep reasoning, high-stake creative writing, architectural decisions justify Opus.

## Headline 2 — model_selector.py

Sample CLI output, verbatim from real scenarios:

```
$ python3 scripts/model_selector.py --task "extract tables from PDF and normalize to CSV"
  Recommendation: Python (0 LLM calls)
  Rationale:      deterministic keyword "PDF, CSV, normalize" (S-C07, S-B024)
  Matrix row:     task_to_model_matrix.md #18
  Estimated cost: $0. If sent to Opus instead, ~$0.72 for 12K input tokens.

$ python3 scripts/model_selector.py --task "weekly tech column, 5000 words" --tokens 8000 --quality high
  Recommendation: Sonnet
  Rationale:      natural-language structured output, drafting <=5K words (A001, S-B018)
  Matrix row:     task_to_model_matrix.md #7
  Estimated cost: Sonnet $0.114 (8K in + 6K out) · vs Opus $0.190 — 40% saved

$ python3 scripts/model_selector.py --task "grep agent definitions for deterministic keywords" --tokens 200
  Recommendation: Python (0 LLM calls)
  Rationale:      grep, deterministic-keyword detection (S-C07)
  Matrix row:     task_to_model_matrix.md #24
```

Decision tree encoded directly in Python. Zero LLM calls per query.

## What audit.py catches (9 rules)

| Rule | Detection | Severity |
|------|-----------|---------:|
| R1 (C1.1) | `model: opus` >= 80% across agents | S1 |
| R2 (C2.x HD-003) | Deterministic keyword + no code-split phase | S1 |
| R3 (C3) | 5+ agent team missing cost-optimization patterns (R3a role-tier mix / R3b cache_control / R3c parallel-or-serial declared / R3d wall-clock + cap / R3e file-based handoff). 3-tier: 5/5 met = PASS, 3-4/5 = WARN, 0-2/5 = FAIL. | S1 |
| R4 (C4.1) | CLAUDE.md or SKILL.md > 200 lines / 8K chars | S1 |
| R5 (C5.1) | No `cache_control` or "prompt caching" mention | S1 |
| R6 (C7.1) | Repeated full-file reads (static heuristic) | S2 |
| R7 (C8.1 HD-010) | No `.checkpoints/` or report-first convention | S1 |
| R8 (C9.1 HD-011) | Writer/drafter agent with no per-call output cap | S1 |
| R9 (C4.5) | SKILL.md > 5K chars with 0 phase / 0 tree markers | S2 |

R6 and R7 are partial under static detection — pair with the NL diagnostic prompt or Hook-mode runtime instrumentation. Each finding ships with file:line evidence, suggested fix, source IDs, and decision (FAIL / WARN / PASS / N/A).

## File tree

```
plz-save-token/
├── README.md · LICENSE · SKILL.md        # SKILL.md = orchestrator skill, loaded by Claude Code
├── scripts/
│   ├── audit.py                          # MODE 3 — 9 static rules, JSON supported
│   ├── model_selector.py                 # MODE 1 — decision tree, 0 LLM calls (HEADLINE)
│   ├── estimate_cost.py                  # pricing SSOT, shared by both above
│   └── hook_check.py                     # MODE 4 — runtime warning hook
├── references/
│   ├── task_to_model_matrix.md           # 24-row matrix (HEADLINE #1)
│   ├── optimal_team_composition.md       # multi-agent well-formed matrix (HEADLINE #3)
│   ├── anti_patterns_atlas.md            # 31 sub-pattern cards (C3 reframed)
│   ├── python_vs_llm_tree.md · prompt_caching_checklist.md
│   ├── parallel_patterns.md · hook_examples.md
│   └── meta_self_check.md                # 9-step self-compliance checklist
├── examples/
│   ├── personal_baseline.md              # real-world 27-harness audit data (N=1 operator)
│   ├── case_studies/                     # measured + simulated cost-vs-quality comparisons
│   │   ├── A_paper_maker_retrospective.md   # FAIL → PASS, -72% cost (simulated)
│   │   └── B_policyblind_warn_to_pass.md    # WARN → PASS, -56% cost, 2-hour fix (simulated)
│   ├── contributed_baselines/            # community-submitted baselines (empty — be first)
│   └── README.md                         # how to read / contribute your own baseline
└── _workspace/                            # research notes, audit baseline (read-only, gitignored)
```

## Companion: harness-diagnostic

`plz-save-token` and [`harness-diagnostic`](https://github.com/epoko77-ai/harness-diagnostic) are by the same operator and are designed to be used together:

- `harness-diagnostic` answers **"what is structurally missing in my harness?"** — 21 gaps across five architectural layers, Python prototype detects 8 via regex.
- `plz-save-token` answers **"where is my harness burning money and what do I do about it?"** — 31 sub-patterns, static audit, model decision tree, cost estimator, optimal team composition matrix, runtime hook.

Hybrid workflow: run `harness-diagnostic` first for structural gaps, then `plz-save-token audit.py` for cost gaps. 4 of harness-diagnostic's 21 gaps overlap (HD-003, HD-010, HD-011, HD-020) — those are both reliability bugs and cost bugs.

## Limitations and caveats

- **Single-operator baseline.** The headline numbers (99% Opus, 0/27 caching) come from one person's 27-harness catalog. The taxonomy is built on N>=2 external sources, but baseline calibration is N=1. Inbound diagnostics are invited.
- **Claude Code specific.** Detection rules look for `model: opus` frontmatter, `~/.claude/agents/` layout, and SKILL.md conventions. LangChain, CrewAI, AutoGen need an adapter layer — planned for v1.1. **External validation (2026-05-14):** `audit.py` was run against three external frameworks (Anthropic Cookbook, LangChain Academy, CrewAI examples). R5 (cache_control absence) fired as a true positive in all three automatically. R2, R3, R8 were confirmed present by manual inspection but require an adapter — projected 7/9 rules with v1.1 adapters for Python-class harnesses, LangGraph StateGraph, and CrewAI YAML.
- **Pricing is point-in-time.** Cost estimates use Anthropic per-MTok prices as of 2026-05-14, encoded as a single constant in `scripts/estimate_cost.py`. Update one constant when prices change; every downstream script picks it up.
- **R6 and R7 are partial under static detection.** Repeated-read patterns and report-first convention violations are detectable with higher fidelity at runtime. The Hook mode covers some of this; a fully instrumented runtime collector is future work.
- **Korean reference content alongside English.** The project began bilingual; internal research notes remain in Korean. All user-facing artifacts (README, SKILL.md, references/) are English.
- **The skill is a meta-skill.** `SKILL.md` itself exceeds the body-bloat warning R9 would flag — by design. Frontmatter declares `meta_skill: true` and `audit.py` excludes meta-skills from R9. Body is four modes + headline matrix + decision tree — all actionable.

## Quality regression risk (the most important caveat)

The `task_to_model_matrix.md` 24 rows are recommendations, not guarantees. The matrix says "Sonnet is fine for standard prose drafting" — but **saved tokens are not the same as saved cost** if downgrading triggers quality regression that forces retries, fact-checker re-runs, or human rework. A downgrade that looks like -80% can land at +20% net cost once retry loops are counted.

This boundary is currently underspecified in the catalog. Before any production downgrade, apply this discipline:

1. **Keep a golden task set.** Five to ten representative tasks for the agent in question. Measure pass-rate, retry rate, and (where applicable) human acceptance on both the original and the downgraded model.
2. **Escalate on failure.** If the downgraded run fails a golden task or triggers a retry, route the work back to the original tier. Single-direction downgrades without escalation are how saved tokens become net losses.
3. **Trust the matrix least at the boundaries.** Rows marked Sonnet that touch high-stakes reasoning, novel domains, or formal register (legal, academic, regulated) are the most likely to surprise. Treat the matrix as a prior, not a verdict.
4. **Report what you measured.** Even N=1 case studies modify the matrix — see [`examples/case_studies/INDEX.md`](examples/case_studies/INDEX.md) and the [quality regression issue template](.github/ISSUE_TEMPLATE/quality_regression_report.md). Three converging reports on the same workload pattern → matrix row revised. One counter-example → asterisk + caveat added.

A measurement framework (`quality_delta` scoring tool, golden task harness, retry-cost calculator) is on the v1.2 roadmap. Until then, the matrix is honest about its limits and the burden of evaluation sits with the operator. **This is the single biggest unresolved risk in adopting `plz-save-token` recommendations.**

## Roadmap

- **v1.1** — framework adapters for LangChain/LangGraph StateGraph, CrewAI YAML, and Python-class harnesses. External validation (2026-05-14) confirms R2, R3, R8 present in external frameworks; adapters will promote them to auto-fire alongside R5. Broader inbound harness diagnostics; N>=2 confirmation promotes hotspots to registered rules.
- **v1.2** — quality measurement: `quality_delta` scoring tool, golden-task harness, retry-cost calculator. Closes the most important gap in `task_to_model_matrix.md`. Also: `model_selector.py` tree fix for `grep`/`count` keywords.
- **v1.3** — `audit.py --json` hotspot key bug fix (top-10 hotspots render in text but not yet JSON). SKILL.md additional slimming with headline matrices fully delegated to `references/`.
- **v2.0** — full cross-framework coverage; community-contributed baselines aggregated; matrix rows revised by converging case studies.

### v2.0 promotion criteria — community-validated catalog

v1.0 ships as a usable first-cut release. The path to v2.0 — where the catalog earns the claim to generalization — has three concrete gates:

1. **N ≥ 3 external operator baselines** accepted via the [baseline issue template](.github/ISSUE_TEMPLATE/baseline_submission.md). The first one moves the project from "one operator's catalog" to a catalog.
2. **≥ 1 quality regression case study** with measured cost-vs-quality delta on a real workload. The first one converts the matrix from "advisory" to "evidence-anchored."
3. **≥ 1 framework adapter shipped** (CrewAI YAML is the simplest first target).

Without these, the catalog stays useful but proprietary in shape. With them, it becomes a community-validated cost-optimization standard. The slow path is the honest one.

## Contributing

The catalog grows by inbound evidence. If you ran `audit.py` on your harness and found:

- A **new pattern** not in the taxonomy, with two or more independent corroborating sources — open an issue with symptom, file evidence, and sources.
- A **rule that misfired** on your harness — open an issue describing your harness shape and what was missed or mis-flagged.
- A **cost outcome** from applying a remediation ("downgrading 14 agents from Opus to Sonnet saved $X per run") — those numbers harden the cost column.
- A **hotspot** not in the taxonomy — even N=1 entries are logged as "hotspot, awaiting external corroboration."

Catalog evolution is the entire point. The N>=2 rule is the gate, not a wall.

## License

MIT. See [LICENSE](./LICENSE).

## Acknowledgements

- [`harness-diagnostic`](https://github.com/epoko77-ai/harness-diagnostic) for the five-layer model and the HD-003 / HD-010 / HD-011 / HD-020 gap definitions.
- Anthropic's docs, engineering blog, and Claude Code docs for 40 cited references including the 7x multi-agent measurement and the cache-read-equals-10-percent pricing.
- Zhang et al. (arXiv 2604.08906) on 409 agentic bugs — the academic spine of the five-layer model.
- Augment Code, Martin Fowler, OpenAI for the "deterministic versus inferential work" boundary that HD-003 codifies.
- Standard library only. No third-party Python dependencies.
