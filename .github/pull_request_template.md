<!--
Thanks for contributing to tokensave. A few quick checks before submission.
-->

## What kind of PR is this?

- [ ] **Bug fix** (audit.py, model_selector.py, etc.)
- [ ] **Catalog addition** — new pattern in taxonomy
- [ ] **Catalog edit** — refine existing pattern
- [ ] **Adapter** — new framework support (CrewAI, LangGraph, etc.)
- [ ] **Case study** — examples/case_studies/
- [ ] **Doc / README**
- [ ] **Other** (specify):

## Summary

<one paragraph — what changes and why>

## For catalog additions / edits (delete if not applicable)

- [ ] N≥2 independent external sources cited (per project rule)
- [ ] Verbatim quotes — no paraphrase
- [ ] taxonomy.json + taxonomy.md + anti_patterns_atlas.md kept in sync
- [ ] audit.py rule added or amended if statically detectable

## For audit.py rule changes (delete if not applicable)

- [ ] Standard library only (no new deps)
- [ ] Tested against `examples/personal_baseline.md` — output diff explained
- [ ] At least one external sample (Anthropic Cookbook / LangChain / CrewAI) re-audited if rule affects framework-agnostic detection

## For adapter PRs (delete if not applicable)

- [ ] Framework detection logic added in `discover_paths()` or `scan_agents()`
- [ ] At least 2 sample harnesses from that framework audited and report attached
- [ ] No breaking change to existing `.md`-based detection

## Meta-principle self-check

- [ ] Deterministic work in this PR was done in code, not LLM
- [ ] Model tier choice (if any) justified
- [ ] No SKILL.md / CLAUDE.md bloat introduced (≤200 lines preferred)

---

_Closes #_
