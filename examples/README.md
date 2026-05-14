# examples/ — Baseline Contributions

This directory holds real-world tokensave audit data contributed by operators.
Each file represents one person's (or one team's) Claude Code catalog, audited
with `python3 scripts/audit.py`.

---

## What is here now

| File | Description |
|------|-------------|
| `personal_baseline.md` | One operator's 27-harness catalog (104 agents, 32 skills). The operator who built tokensave ran it against their own setup on 2026-05-14. Includes headline numbers, full 9-rule audit results, top-10 hotspot agents, and the HARNESS_PREFIX_MAP and cost scenario data that was factored out of the main codebase. |

---

## How to add your baseline

1. Run the audit against your catalog:

   ```bash
   python3 scripts/audit.py           # full scan
   python3 scripts/audit.py --json    # machine-readable output
   ```

2. Copy the output into a new file in this directory, e.g. `examples/my_catalog_baseline.md`.

3. Add a short header block at the top:

   ```markdown
   # Example: <N>-harness operator baseline

   > Audited with `python3 scripts/audit.py` on YYYY-MM-DD.
   > <N> harnesses, <N> agents, <N> skills.
   > Platform: <macOS / Linux / Windows>. Shell: <zsh / bash>.
   ```

4. If you want to keep harness names private, you can anonymize them (e.g., `harness-a`, `harness-b`).
   The hotspot agent names and rule decisions are the most useful data — names are optional.

5. Open a PR or share the file however the project accepts contributions.

---

## Format reference

A baseline file should include at least:

- **Catalog size** — total agents, skills, harnesses.
- **Headline numbers** — opus %, caching mentions, 5+ agent harness count, HD-003 risky count.
- **Audit table** — one row per rule (R1–R9), decision (FAIL/WARN/PASS/N/A), key evidence.
- **Hotspot top 10** — agent name, model, size, score, primary reason.

All sections from `personal_baseline.md` are optional except the header block.

---

## Notes on privacy

- Agent file names often encode project names (e.g., `pm-` = paper-maker pipeline).
  Anonymize if needed.
- Absolute paths (`/Users/yourname/...`) should be replaced with `<home>/...` or omitted.
- The numbers themselves (opus %, risky count, hotspot scores) contain no PII and are
  safe to share as-is.

---

Korean reference content is available alongside English in the main `SKILL.md` and
`references/` directory. Contributions in any language are welcome.
