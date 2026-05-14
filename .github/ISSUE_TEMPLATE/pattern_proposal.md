---
name: 🔍 New pattern proposal
about: Propose a new anti-pattern or optimization pattern for the catalog (N≥2 evidence required)
title: "pattern: <one-line, e.g., 'Tool definition cache miss across re-spawn'>"
labels: ["pattern-proposal", "needs-evidence"]
---

> The catalog rule: **a pattern enters the taxonomy only when ≥2 independent external sources confirm it.**
> This is what keeps the catalog honest as it grows.

## Pattern in one sentence

<e.g., "Subagent re-spawn after context compaction re-pays the entire tool definition block.">

## Proposed taxonomy slot

- **Category**: <C1 Model Tier / C2 Deterministic-LLM / C3 Multi-Agent / C4 Context / C5 Caching / C6 Spawn / C7 Tool / C8 Output / C9 Cap / C10 Architecture / NEW>
- **Suggested rule ID**: <e.g., R10 or extend C6.x>
- **Severity**: <S1 Blocker / S2 Major / S3 Minor>

## Evidence (≥2 independent sources required)

### Source 1
- **Type**: <Anthropic docs / community / academic / engineering blog / verbatim user report>
- **URL or citation**:
- **Verbatim quote** (no paraphrase):

> 

### Source 2
- **Type**:
- **URL or citation**:
- **Verbatim quote**:

> 

### Source 3 (optional but stronger)
- ...

## Detection method

- **Static (regex / file scan)**: <what audit.py rule would catch this>
- **Runtime (hook / log)**: <if it must be observed at runtime>
- **N/A**: <if only manual inspection works>

## Real-world impact

- **Observed magnitude** (if measured): <e.g., +200% input tokens per spawn>
- **Frequency** (if estimable): <e.g., every Task tool call after /compact>

## Mitigation

<concrete fix recommendation — what the user should do once the pattern is detected>

## Why this is not already covered

<which existing rules might overlap and why this is distinct>

---

_Triage: Maintainer will check the N≥2 rule, attempt independent reproduction, and either (a) accept into next minor release, (b) hold for additional evidence, or (c) reject as duplicate or insufficient. Please be patient — incorrect adoption hurts the catalog more than slow adoption._
