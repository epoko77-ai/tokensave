# Example: 27-Harness Operator Baseline

> One operator's Claude Code setup, audited with `python3 scripts/audit.py` on 2026-05-14.
> Numbers, harness names, and hotspot agents are reported as-is from a real catalog.
> This is a single data point — the operator who built tokensave ran it against their own
> `~/.claude/agents`, `~/.claude/skills`, and `~/CLAUDE.md`. Broader community baselines welcome
> (see `examples/README.md` for contribution format).

---

## Catalog Size

| Item | Count |
|------|------:|
| Agents total | 104 |
| Harnesses total | 27 |
| Skills total | 32 |
| Avg SKILL.md size | 8,692 chars |

---

## Headline Numbers (the "shock facts" that motivated tokensave)

| # | Fact | Rule hit |
|---|------|----------|
| H1 | **Opus 99.0%** (103/104 agents) — single-model strategy | R1 FAIL |
| H2 | **Prompt caching mentioned 0 times** across all 27 harnesses and 32 skills | R5 FAIL |
| H3 | **5+ agent harnesses: 93%** (25/27). 8+ agent harnesses: 52%. Largest team: 15 agents (Paper Maker) | R3 FAIL |
| H4 | **HD-003 RISKY: 20 agents** — deterministic keyword found, zero code-phase split | R2 FAIL |
| H5 | **SKILL.md average 8,693 chars**, max 32,987 chars (`skill-creator`), combined 278K chars of always-on context pressure | R4 FAIL/WARN |

---

## Audit Results (9-rule static scan)

| Rule | Category | Decision | Key evidence |
|------|----------|----------|--------------|
| R1 | C1.1 All-Opus | **FAIL** | 103/104 agents = 99.0% opus |
| R2 | C2.x HD-003 | **FAIL** | 20 risky agents, 0 code-phase splits |
| R3 | C3.1 5+ Agent | **FAIL** | 25/27 harnesses ≥ 5 agents |
| R4 | C4.1 Bloat | **FAIL** | CLAUDE.md 393 lines; 5 SKILL.md files > 8K chars |
| R5 | C5.1 Caching | **FAIL** | 0 cache_control mentions in 32 skills + CLAUDE.md |
| R6 | C7.1 Read Pattern | N/A | SKILL.md not found in scope |
| R7 | C8.1 HD-010 | N/A | < 3 phases in scope |
| R8 | C9.1 HD-011 | **FAIL** | 13/14 writer agents lack per-call cap |
| R9 | C4.5 Non-actionable | **WARN** | 8 SKILL.md files > 5K chars with 0 Phase/decision-tree keywords |

**Summary: 6 FAIL · 1 WARN · 0 PASS · 2 N/A**

---

## Top Hotspot Agents

Scored by the audit's hotspot algorithm (HD-003 RISKY +5, opus+5K+non-writer +3, writer+5K +2).

| # | Agent | Model | Size (chars) | Score | Primary reason |
|---|-------|-------|-------------:|------:|----------------|
| 1 | `pm-section-drafter.md` | opus | 7,018 | 7 | HD-003 RISKY (det_kw=2) + writer + large definition |
| 2 | `pm-pdf-composer.md` | opus | 5,749 | 7 | HD-003 RISKY (det_kw=2) + writer + large definition |
| 3 | `uap-report-composer.md` | opus | 5,176 | 7 | HD-003 RISKY (det_kw=1) + writer + large definition |
| 4 | `uap-case-parser.md` | opus | 10,840 | 5 | HD-003 RISKY (det_kw=2) — largest agent in catalog |
| 5 | `pm-editor-chief.md` | opus | 7,933 | 5 | HD-003 RISKY (det_kw=2) |
| 6 | `pm-argument-architect.md` | opus | 6,792 | 5 | HD-003 RISKY (det_kw=1) |
| 7 | `pm-scope-architect.md` | opus | 6,581 | 5 | HD-003 RISKY (det_kw=1) |
| 8 | `pm-prose-stylist.md` | opus | 5,534 | 5 | HD-003 RISKY (det_kw=2) |
| 9 | `policyblind-architect.md` | opus | 4,560 | 5 | HD-003 RISKY (det_kw=1) |
| 10 | `uap-fact-checker.md` | opus | 4,133 | 5 | HD-003 RISKY (det_kw=1) |

Agent name prefixes reflect the harness they belong to:
`pm-` = paper-maker harness (15-agent academic paper pipeline),
`uap-` = uap-161-analysis harness (8-agent DoD UAP case report),
`policyblind-` = policyblind harness (8-agent policy card platform).

---

## Harness-level HARNESS_PREFIX_MAP

The operator's `audit.py` used this prefix mapping in single-harness mode to locate agents in
`~/.claude/agents/`. It is reproduced here as example data; the OSS version resolves this via
the `TOKENSAVE_HARNESS_PREFIX_MAP` environment variable.

```json
{
  "paper-maker":    ["pm-"],
  "papermaker":     ["pm-"],
  "ai-news-daily":  ["ainews-"],
  "ainews":         ["ainews-"],
  "wikibrain":      ["wikibrain-"],
  "llmwiki-easy":   ["wikibrain-"],
  "policydonation": ["policyblind-"],
  "policyblind":    ["policyblind-"],
  "uap161":         ["uap-"],
  "ai-wealth7":     ["nlm-", "chapter-", "deck-", "book-"],
  "aienglish":      ["english-", "ai-cloud-", "esl-", "conversation-", "reading-"]
}
```

---

## Cost Scenarios (operator's representative harnesses)

Static token estimates used by `estimate_cost.py --scenario`. Reproduced here as example data;
the OSS `SCENARIOS` dict contains only two generic placeholders.

| Scenario | Agents | Model | Est. calls | Notes |
|----------|-------:|-------|----------:|-------|
| paper-maker | 15 | opus | 40 | 8 phase × 5 call/phase, worst case |
| ainews-daily | 7 | opus | 20 | daily newsletter clip + curate + publish |
| policyblind | 8 | opus | 30 | Fetch→Classify→Extract→Verify→Blind→Publish cycle |
| uap-161-analysis | 8 | opus | 25 | 161 cases, skeptic gate loop |
| busan-policy-pledges | 8 | opus | 22 | 6 domain experts + pledge strategist + pdf builder |
| tokensave-self | 5 | mixed | 12 | sonnet 3 + opus 2, single build |

---

## How to Reproduce

```bash
# Clone or download tokensave, then from its root:
python3 scripts/audit.py                # full catalog scan (~/.claude + ~/CLAUDE.md)
python3 scripts/audit.py --top 10       # hotspot top 10
python3 scripts/audit.py --json         # machine-readable output
python3 scripts/audit.py /path/to/harness  # single-harness scan
```

The numbers above were produced on a macOS system with 104 agent `.md` files in `~/.claude/agents/`
and 32 skills in `~/.claude/skills/`.
