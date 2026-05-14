# Optimal Team Composition Matrix (★ headline #3 — SECONDARY OPTIMIZATION)

> **Pareto position.** This matrix is the **secondary** lever (~30% multiplier on top of well-matched model tiers). The **primary** lever is `references/task_to_model_matrix.md` — get the tier right first (~70-80% of savings), then apply these five team-composition patterns. Optimizing the team while the base tier is wrong is fractions of nothing.
>
> **tokensave does not discourage multi-agent harnesses.** Multi-agent is justified — when 5 cost-optimization patterns are applied. This matrix is the prescription. `audit.py` rule R3 sub-rules (R3a~R3e) map 1:1 to the 5 patterns; `SKILL.md` MODE 1 Step 3 is the pre-flight self-check.
>
> Generated: 2026-05-14 · scope: Claude Code 5+ agent harnesses · companion: `references/anti_patterns_atlas.md` C3 cards (1:1 mapping)

---

## 1. When 5+ team is justified

Multi-agent design pays for its 7×~15× per-session multiplier [A003][S-B003] when at least one of these conditions holds. Listed in rough order of how cleanly they justify the multiplier.

| # | Justification | Example pattern | Source |
|---|--------------|-----------------|--------|
| **(a)** | **Independent reasoning domains** — same input, two different lenses, no shared blind spot | strict-reviewer + adversarial-reviewer run on the same draft without seeing each other's notes; editor-chief reconciles | [S-C04] reflexive vs hierarchical Pareto |
| **(b)** | **Context isolation** — subagent protects the main thread from large/noisy inputs | A `source-fetcher` reads 50 MB of HTML and returns 2 KB of structured rows; main context never sees the HTML | [A023] Anthropic subagent design |
| **(c)** | **Genuine parallelism** — independent work where wall-clock collapse > spawn overhead | 6 chapter-writers fan out in background; without parallelism the same work takes 6× wall-clock | [A003][A035] |
| **(d)** | **Tool / permission boundary** — security or capability isolation | A `deploy-engineer` agent has Vercel CLI permission; the writer agent does not | [A019][A023] |
| **(e)** | **Persona specialization** — single-call register-shifts don't follow reliably | `economic-reviewer` vs `ai-tech-reviewer` reviewing the same speech with different domain registers | one operator's `policy-speech` v1 |

If none of (a)~(e) applies, the team likely shouldn't be 5+. Merge mergeable agents.

## 2. When 5+ team is NOT justified

- Same-domain reasoning split for "more thorough" feel — two reviewers who would produce 90% overlapping notes are mergeable
- All agents on the same model tier — no role differentiation means no specialization payoff
- Common context (system prompt, SKILL.md, large references) re-paid on every call — `cache_control` at 0
- Serial when parallel possible (or reverse) — execution mode is accidental, not designed
- SendMessage flood between agents — token leakage replaces what context isolation was supposed to buy

---

## 3. Team composition matrix (operator-grounded examples)

Workload pattern → team size → suggested composition → which justification clause(s) apply → real-world reference in one operator's catalog (28 harnesses). The "Real-world reference" column is N=1 evidence per row; the cost-optimization patterns themselves are validated by external N≥2 sources (see `_workspace/03_patterns/taxonomy.json`).

| Workload pattern | Team size | Orchestrator | Worker pool | Reviewer | Justification | Real-world reference |
|------------------|----------:|--------------|-------------|----------|---------------|----------------------|
| Top-tier academic/policy paper (peer-review must pass) | 15-16 (hierarchical) | Opus ×1 | Sonnet ×6~8 + Python ×2 (citation-formatter, evidence-curator) | Opus ×2 independent (strict + adversarial) + Opus ×1 editor-chief | (a) + (b) + (e) | paper-maker v1.4 (15 agents) |
| Daily news ingestion + curation + delivery | 7 (pipeline) | — (sequential phases) | Python ×3 (source clipper, dedup, deliver) + Sonnet ×3 (curator, frontend builder, admin) | Sonnet ×1 (qa-reviewer) | (b) + (c) | ainews-daily (7 agents) |
| Citizen policy blinding + cross-verify + matching | 8 (cross-verify) | Opus ×1 (architect) | Sonnet ×5 (collector, blinding, matching, prompt-guardian, editorial-frontend) + Python ×1 (legal-compliance scanner) | Sonnet ×1 (qa-auditor) | (a) + (d) | policyblind v0.1.0 (8 agents) |
| 50-page infographic deck assembly | 9 (mixed parallel + sequential) | Sonnet ×1 (structure-mapper) | Python ×3 + Sonnet ×3 (visual-readers parallel ×3, narrative-editor, slide-generator, deck-assembler) | Sonnet ×1 (fidelity-qa, twice) | (c) + (e) | book-infographic-deck (9 agents) |
| Policy speech (econ + AI dual review) | 5 (review-heavy) | — | Sonnet ×3 (archivist, writer, fact-checker) | Opus ×2 independent (econ-reviewer + ai-tech-reviewer) | (a) + (e) | policy-speech v1 (5 agents) |
| Local issue research (4-channel parallel) | 7 (fan-out collectors + curator) | Opus ×1 (research-architect) | Sonnet ×4 collectors (media, SNS, blog, civil-petition) — parallel | Sonnet ×2 (issue-curator + insight-composer) | (b) + (c) | busan-bukgu-research v1 (7 agents) |
| UAP 161-case analysis (skepticism-gated) | 8 (3-axis parallel + gate) | — | Python ×2 (fetcher, parser) + Sonnet ×3 parallel (pattern, context, fact-checker) + Sonnet ×1 (composer) + Python ×1 (pdf-builder) | Opus ×1 (skeptic-reviewer — gate) | (a) + (b) + (d) | uap-161-analysis v1 (8 agents) |
| WikiBrain v1.0 SaaS (frontend + backend + ops) | 10-11 (Phase-parallel) | Opus ×1 (v1-architect) | Sonnet ×4 backend Phase B parallel (invite-gate, social-feed, quota, ingest) + Sonnet ×1 (frontend, supabase, mcp, deploy each) | Sonnet ×1 (qa-engineer) | (b) + (c) + (d) | WikiBrain v1.0 (~11 agents) |
| Single-domain classification (no isolation need) | 1 (single-call) | — | Haiku 단독 | — | unjustified split | — |

The matrix is intentionally **prescriptive, not exhaustive**: pick the closest workload pattern, then verify your composition against the 5 cost-optimization patterns in §4.

---

## 4. The 5 cost-optimization patterns (apply to any team ≥ 5)

Each pattern maps 1:1 to an `audit.py` R3 sub-rule (R3a~R3e). Run `python3 scripts/audit.py /path/to/harness --rules R3` to check your harness against all five at once.

### P1 — Role-tier model mix (audit R3a · C3.1)

Orchestrators, workers, and reviewers should not all run on the same model. Different roles have different cost/quality elasticities.

- **Orchestrator**: Opus when it does meta-judgment (e.g., patch reconciliation, editor-chief role); Sonnet when it only routes
- **Worker pool**: Sonnet for natural-language structured output; **Python** for deterministic transforms (cf. HD-003 trap, C2)
- **Reviewer**: Opus when high-stake (peer-review pass criterion); Sonnet when the review is standard checks
- **Measurement**: `grep -h '^model:' agents/*.md | sort | uniq -c` — at least 2 distinct values
- **Savings**: -40% per Sonnet teammate, -80% per Haiku scout, -99% per deterministic step moved to Python
- **Source**: [A001] · [A002] · [A013] · [S-B017] · [S-C02] · [S-C05]

### P2 — Common-context cache_control (audit R3b · C3.2)

The SKILL.md, system prompt, and large reference files are paid once per invocation when `cache_control` is absent. With caching, reads cost 10% of base [A005]. For a 5-agent harness invoked 10 times, that is roughly the difference between paying for the SKILL.md 50 times versus once.

- **Where to place breakpoints (up to 4)**: system prompt block · SKILL.md body · large reference files (taxonomy.json, big matrices) · accumulated session context
- **Minimum lengths**: Sonnet 1,024 tokens · Opus 4,096 tokens
- **Measurement**: `grep -r 'cache_control\|prompt cach' .claude/ SKILL.md` — zero hits = the pattern is missing
- **Savings**: -90% input cost at 90% hit rate
- **Source**: [A004] · [A005] · [S-B006] · [S-B028]

### P3 — Parallel / sequential intentional declaration (audit R3c · C3.3)

Execution mode should be a design decision, not an accident. State it in the harness SKILL.md.

- **Parallel without cap**: 49-process bursts at 887K tokens/min [S-B003] — declare `background_tasks: N` or wave size
- **Sequential when parallel possible**: wall-clock balloons; declare `cascade` or `pipeline` only when there's a real dependency
- **Hybrid is fine — say so**: paper-maker v1.4 "Phase 3 백그라운드 병렬, Phase 5 순차" is exemplary
- **Measurement**: keyword grep on the harness section — `병렬`/`순차`/`background`/`parallel`/`sequential`/`cascade`/`pipeline`/`하이브리드`
- **Source**: [A003] · [S-B003] · [S-B004] · [S-C04]

### P4 — Per-agent wall-clock + per-call output cap (audit R3d · C3.4)

A single agent can burn an entire session if uncapped. The 91-minute citation-formatter trap (HD-003, [S-C09]) and the 7K-character single drafter call (C9.1, [S-C05]) are both wall-clock failures.

- **Wall-clock**: each agent gets `soft: 30min` / `hard: 50min` or similar
- **Per-call output cap for writers**: `per_call_cap: 4000자`, with auto-split rule `섹션 > 4K → 2 sub-call`
- **Retry cap**: `iter ≤ 3` or `재시도 max N` — without it, reflexive architecture hits 2.3× cost for 89% accuracy gain [S-C04]
- **Reference**: paper-maker v1.3.1 explicitly added "patch verification ≤ 2회, 3차 FAIL 3종 분기" after observing infinite-loop risk
- **Savings**: -28.4% cost-of-pass [S-C05] + runaway prevention

### P5 — File-based handoff (audit R3e · C3.5)

Agents should hand off via files in `_workspace/`, not via SendMessage. SendMessage chains leak tokens across agents and defeat the context-isolation justification (b) above.

- **Convention**: SKILL.md declares a 산출물 트리 (artifact tree), e.g., `_workspace/01_scope.json` → `_workspace/02_literature.md` → ... → `_workspace/15_build/`
- **Read on the consumer side**: the next agent reads from disk and writes its own file; orchestrator stitches the trail
- **Anti-pattern signal**: high SendMessage volume + zero `_workspace/` writes
- **Reference**: paper-maker `_workspace/01_scope ~ 15_build/` · busan-bukgu-research `_workspace/01_plan ~ 05_report/` · policyblind `_workspace/01_architecture ~ 08_qa/` — all exemplary
- **Source**: [A023] subagent context isolation · [S-C03] tokenomics file-based

---

## 5. Anti-pattern detection (audit.py R3 mapping)

`audit.py` rule R3 applies the 5 sub-rules to every 5+ agent harness and aggregates with a 3-tier decision.

| Sub-rule | Pattern card | What it detects | Severity |
|---------|--------------|-----------------|---------:|
| **R3a** | C3.1 | 5+ team with all-same model tier (no orchestrator/worker/reviewer mix) | S1 |
| **R3b** | C3.2 | 5+ team without `cache_control` / "prompt cach*" / "캐싱" in the section or main SKILL.md | S1 |
| **R3c** | C3.3 | 5+ team without parallel/sequential/background/cascade declaration keywords | S2 |
| **R3d** | C3.4 | 5+ team without wall-clock / timeout / per-call cap / retry-cap keywords | S2 |
| **R3e** | C3.5 | 5+ team without `_workspace/` / file-based / 산출물 트리 keywords | S2 |

3-tier decision (per harness):

- **5/5 met** → **PASS** — well-formed multi-agent harness
- **3-4/5 met** → **WARN** — optimization opportunity; apply missing sub-rules from the matrix above
- **0-2/5 met** → **FAIL** — unjustified multiplier (cost without optimization); apply the 5 patterns from scratch

Aggregate decision across the catalog: **worst-case priority**. Any FAIL in any harness → catalog R3 FAIL. Any WARN with no FAILs → catalog R3 WARN. All PASS → catalog R3 PASS.

---

## 6. How to use this matrix

1. **Before designing a new 5+ harness** — pick the closest row in §3 by workload pattern. Adapt agent count + composition.
2. **For an existing harness** — run `python3 scripts/audit.py /path/to/harness --rules R3` and read the "X/5 met, missing: …" output. Apply missing sub-rules from §4.
3. **When reviewing the catalog overall** — run `python3 scripts/audit.py` with no args. The R3 finding aggregates across all harnesses and lists the 5 worst by `met` count.
4. **When the user asks "why is my harness expensive"** — start with R3b (cache_control) because it gives the largest single multiplier (-90% input). Then R3a (role-tier mix). Then R3d (caps).

---

## 7. Sources

- **A###** = Anthropic official (docs, blog, cookbook) — A001 model selection, A002 Sonnet for teammates, A003 7× multi-agent measurement, A004/A005 prompt caching, A013 Haiku for explore, A023 subagent design, A035 parallel tool calls
- **S-B###** = community (X, Reddit, blogs, GitHub) — S-B003 49-process burst, S-B004 5-parallel = Pro 15min, S-B006 90% hit rate measurement, S-B017 community model-tier validation, S-B028 60~90% production cache rates
- **S-C##** = academic / empirical — S-C02 SkillReducer, S-C03 tokenomics, S-C04 hierarchical vs reflexive Pareto, S-C05 Efficient Agents (28.4% cost-of-pass), S-C09 paper-maker HD-003 + HD-011 measurements
- **HD-###** = `_reference/harness-diagnostic/` — HD-003 (C2 deterministic-in-LLM, 91min→30sec), HD-011 (per-call cap)

Full source citations → `_workspace/03_patterns/taxonomy.json` `sources_external` arrays.

---

## 8. Companion documents

- `references/anti_patterns_atlas.md` C3 section — 6 cards (C3.1~C3.6), 1:1 mapped to this matrix
- `_workspace/03_patterns/taxonomy.md` §2 C3 — full pattern definitions with all sources
- `_workspace/03_patterns/taxonomy.json` C3 — machine-readable schema (audit.py consumes)
- `references/task_to_model_matrix.md` — headline #1, 24-row task → model lookup (for P1 worker assignments)
- `references/prompt_caching_checklist.md` — for P2 implementation details
- `references/parallel_patterns.md` — for P3 background/wave execution details
- `scripts/audit.py` R3 — implementation of the 5 sub-rules
- `SKILL.md` MODE 1 Step 3 — pre-flight self-check using this matrix

---

## 9. Version

- **v1.0** (2026-05-14) — initial publication; companion to tokensave v1.0 release C3 reframe. Operator-grounded examples drawn from one 28-harness catalog (paper-maker, ainews-daily, policyblind, book-infographic-deck, policy-speech, busan-bukgu-research, uap-161-analysis, WikiBrain v1.0).
