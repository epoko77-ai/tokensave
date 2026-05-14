#!/usr/bin/env python3
"""
tokensave — audit.py

기존 하네스 정적 감사. baseline_collect.py (사용자 베이스라인 수집) +
harness-diagnostic/cli/diagnose.py (HD-003/010/011 룰) 통합 확장.

9개 룰 적용:
  R1 (C1.1) Model Tier — opus 비율 >= 80% 이면 FAIL
  R2 (C2.x HD-003) Deterministic-in-LLM — det_kw + code_split=0 이면 FAIL
  R3 (C3.1) 5+ agent 하네스 — fanout 게이트 점검
  R4 (C4.1) CLAUDE.md/SKILL.md 200+ lines / 8K+ chars 비대
  R5 (C5.1) cache_control / "prompt caching" 언급 0회 FAIL
  R6 (C7.1) Read pattern (정적: 동일 파일 반복 위험 추정)
  R7 (C8.1 HD-010) .checkpoints/ 또는 "output-first" 부재 FAIL
  R8 (C9.1 HD-011) writer/drafter agent에 cap 부재 FAIL
  R9 (C4.5) SKILL.md 본문 비실행 콘텐츠 60%+ 의심

Usage:
  python3 audit.py                          # 전수 모드 (~/.claude 전체)
  python3 audit.py /path/to/harness         # 단일 하네스
  python3 audit.py --top 10                 # 우선순위 hotspot top 10
  python3 audit.py --json
  python3 audit.py --rules R1,R2,R5         # 일부 룰만 적용

표준 라이브러리만. estimate_cost.py PRICING 사용.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# 같은 디렉토리에서 가격 SSOT import
sys.path.insert(0, str(Path(__file__).parent.resolve()))
try:
    from estimate_cost import PRICING, estimate_cost
except ImportError:
    PRICING = None  # 가격 비교는 옵션
    estimate_cost = None


# ─── taxonomy.json 매핑 (룰 ID·심각도·출처) ──────────────────────────────────
#
# audit.py는 taxonomy.json을 직접 로드 시도. 없으면 fallback (인라인 정의).

TAXONOMY_FALLBACK = {
    "R1": {"category": "C1.1", "title": "All-Opus Anti-pattern", "severity": "S1",
           "sources": ["A001", "A013", "S-B017", "S-C02", "S-C05"]},
    "R2": {"category": "C2.x (HD-003)", "title": "Deterministic Work in LLM", "severity": "S1",
           "sources": ["S-C07", "S-C08", "S-C01", "S-C09"]},
    "R3": {"category": "C3", "title": "Multi-Agent Team Composition (cost-optimized)", "severity": "S1",
           "sources": ["A003", "S-B003", "S-B004", "A004", "S-C04"]},
    "R4": {"category": "C4.1", "title": "Bloated CLAUDE.md / SKILL.md", "severity": "S1",
           "sources": ["A017", "A024", "S-B004", "S-B005"]},
    "R5": {"category": "C5.1", "title": "cache_control Absence", "severity": "S1",
           "sources": ["A004", "A005", "S-B006", "S-B028"]},
    "R6": {"category": "C7.1", "title": "Full File Read When Offset Possible", "severity": "S2",
           "sources": ["A005", "A039", "S-B005"]},
    "R7": {"category": "C8.1 (HD-010)", "title": "Report-First Convention Absent", "severity": "S1",
           "sources": ["S-C09", "S-C03"]},
    "R8": {"category": "C9.1 (HD-011)", "title": "Per-Call Cap Missing", "severity": "S1",
           "sources": ["S-C02", "S-C05", "S-C09"]},
    "R9": {"category": "C4.5", "title": "SKILL.md Non-actionable Body Bloat", "severity": "S2",
           "sources": ["S-C02"]},
}


def load_taxonomy() -> dict:
    """taxonomy.json 시도 로드. 실패 시 fallback."""
    candidates = [
        Path(__file__).parent.parent / "_workspace" / "03_patterns" / "taxonomy.json",
        Path(__file__).parent.parent / "03_patterns" / "taxonomy.json",
        Path.home() / "tokensave" / "_workspace" / "03_patterns" / "taxonomy.json",
    ]
    for c in candidates:
        if c.is_file():
            try:
                return json.loads(c.read_text())
            except Exception:
                pass
    return {}  # fallback to TAXONOMY_FALLBACK


# ─── 키워드 상수 ──────────────────────────────────────────────────────────────

DETERMINISTIC_KEYWORDS = [
    r"\bverbatim\b",
    r"\b1:1\s*매핑\b",
    r"\b1:1\s+mapping\b",
    r"\bBibTeX\b",
    r"\bformat\s+normalization\b",
    r"\bcross-?reference\b",
    r"\bdead[ -]?link\b",
    r"\bregex\s+transformation\b",
    r"\b결정적\b.*\b변환\b",
    r"\bJSON\s*정규화\b",
    r"\bsha256\b",
    r"\b해시\b",
]

CODE_SPLIT_KEYWORDS = [
    r"\bPython\b.*\b(스크립트|script|phase)\b",
    r"\bBash\b.*\b(스크립트|script)\b",
    r"code[- ]?phase",
    r"deterministic.*pass.*code",
    r"phase.*5c-1",
]

WRITER_AGENT_PATTERNS = [
    r"writer", r"drafter", r"집필자", r"composer", r"section",
    r"keynote-archivist", r"reading-chapter-writer", r"conversation-chapter-writer",
]

OUTPUT_FIRST_KEYWORDS = [
    r"\.checkpoints?/", r"output[- ]?first", r"report[- ]?after",
    r"산출물\s*우선", r"산출물\s*경로\s*먼저",
    r"checkpoint.*\{file_path,?\s*line_count,?\s*sha256",
]

PER_CALL_CAP_KEYWORDS = [
    r"per[- ]?call.*cap", r"output.*cap", r"\bmax\s*words\b",
    r"\bcap:\s*\d", r"분량\s*한도", r"한\s*호출.*한도",
    r"섹션\s*>.*sub[- ]?call", r"자동\s*분할",
]


# ─── 데이터 클래스 ────────────────────────────────────────────────────────────

@dataclass
class Finding:
    rule_id: str
    category: str
    title: str
    severity: str
    decision: str  # PASS / FAIL / WARN / N/A
    evidence: list[str] = field(default_factory=list)
    reasoning: str = ""
    suggested_fix: str = ""
    sources: list[str] = field(default_factory=list)


@dataclass
class AgentSummary:
    name: str
    path: str
    model: str
    size: int
    det_kw_count: int
    code_split_count: int
    is_writer: bool


@dataclass
class HarnessSummary:
    name: str
    agent_count: int
    agent_names: list[str] = field(default_factory=list)
    section_text: str = ""  # raw markdown of the 하네스 section (~3K chars)


@dataclass
class AuditReport:
    scope: str  # "all" or path
    findings: list[Finding] = field(default_factory=list)
    agent_summaries: list[AgentSummary] = field(default_factory=list)
    harness_summaries: list[HarnessSummary] = field(default_factory=list)
    skill_summaries: list[dict] = field(default_factory=list)
    overall_stats: dict = field(default_factory=dict)
    hotspot_top10: list[dict] = field(default_factory=list)


# ─── 헬퍼 ─────────────────────────────────────────────────────────────────────

def grep_count(text: str, pattern: str, flags: int = re.IGNORECASE) -> int:
    return len(re.findall(pattern, text, flags))


def grep_bool(text: str, pattern: str, flags: int = re.IGNORECASE) -> bool:
    return bool(re.search(pattern, text, flags))


def grep_lines(text: str, pattern: str, flags: int = re.IGNORECASE) -> list[tuple[int, str]]:
    rx = re.compile(pattern, flags)
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        if rx.search(line):
            out.append((i, line.strip()))
    return out


def normalize_model(raw: str) -> str:
    r = raw.strip().lower()
    for m in ("opus", "sonnet", "haiku", "general-purpose"):
        if m in r:
            return m
    return r or "none"


def cite(path: Path, line_no: int, snippet: str, root: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        try:
            rel = Path("~") / path.resolve().relative_to(Path.home())
        except ValueError:
            rel = path
    snip = snippet.strip()
    if len(snip) > 140:
        snip = snip[:137] + "..."
    return f"`{rel}:{line_no}` — {snip}"


def is_writer_agent(name: str, text: str) -> bool:
    """writer/drafter 류 agent 식별."""
    name_lower = name.lower()
    for pat in WRITER_AGENT_PATTERNS:
        if re.search(pat, name_lower):
            return True
    # 본문 키워드도 검사
    if grep_bool(text, r"\b(드래프트|draft|writer|작성자|집필).*\b(에이전트|agent)\b"):
        return True
    return False


# ─── 스캔 함수 ────────────────────────────────────────────────────────────────

def scan_agents(agent_paths: list[Path]) -> list[AgentSummary]:
    summaries = []
    for p in agent_paths:
        try:
            text = p.read_text(errors="replace")
        except Exception:
            continue
        m = re.search(r"^model:\s*(\S+)", text, re.MULTILINE | re.IGNORECASE)
        raw_model = m.group(1) if m else "none"
        model = normalize_model(raw_model)
        det_count = sum(1 for kw in DETERMINISTIC_KEYWORDS if grep_bool(text, kw))
        code_count = sum(1 for kw in CODE_SPLIT_KEYWORDS if grep_bool(text, kw))
        summaries.append(AgentSummary(
            name=p.name,
            path=str(p),
            model=model,
            size=len(text),
            det_kw_count=det_count,
            code_split_count=code_count,
            is_writer=is_writer_agent(p.name, text),
        ))
    return summaries


def scan_harnesses(claude_md_text: str) -> list[HarnessSummary]:
    summaries = []
    names = re.findall(r"^##\s+하네스:\s+(.+)", claude_md_text, re.MULTILINE)
    for name in names:
        idx = claude_md_text.find(f"## 하네스: {name}")
        if idx == -1:
            continue
        snippet = claude_md_text[idx:idx + 3000]
        team_m = re.search(r"\*\*팀\s*구성.*?\*\*.*", snippet)
        agent_names = []
        if team_m:
            agent_names = re.findall(r"`([^`]+)`", team_m.group(0))
        summaries.append(HarnessSummary(
            name=name,
            agent_count=len(agent_names),
            agent_names=agent_names,
            section_text=snippet,
        ))
    return summaries


def scan_skills(skills_dir: Path) -> list[dict]:
    skills = []
    if not skills_dir.is_dir():
        return skills
    for sub in sorted(skills_dir.iterdir()):
        sm = sub / "SKILL.md"
        if not sm.is_file():
            continue
        text = sm.read_text(errors="replace")
        phases = grep_count(text, r"^#+\s*Phase\s+\d", re.MULTILINE | re.IGNORECASE)
        decision_trees = grep_count(text, r"결정\s*트리|decision\s*tree", re.IGNORECASE)
        examples = grep_count(text, r"```|예시|example", re.IGNORECASE)
        # frontmatter YAML에서 meta_skill: true 감지 — 메타 스킬 예외 처리
        meta_skill = False
        if text.startswith("---"):
            fm_end = text.find("\n---", 4)
            if fm_end > 0:
                fm = text[3:fm_end]
                if re.search(r"^\s*meta_skill\s*:\s*true\s*$", fm, re.MULTILINE | re.IGNORECASE):
                    meta_skill = True
        skills.append({
            "name": sub.name,
            "size": len(text),
            "phase_count": phases,
            "decision_tree_count": decision_trees,
            "example_count": examples,
            "meta_skill": meta_skill,
            "path": str(sm),
        })
    return skills


def discover_paths(root: Optional[Path]) -> dict:
    """root가 None이면 전수 모드 (HOME/.claude/* + HOME/CLAUDE.md). 아니면 단일 하네스.

    HOME defaults to Path.home(). Override by passing an explicit root path.
    Set TOKENSAVE_HARNESS_PREFIX_MAP (JSON) to customize single-harness agent lookup.
    """
    if root is None:
        # 전수 모드
        home = Path.home()
        agents_dir = home / ".claude" / "agents"
        skills_dir = home / ".claude" / "skills"
        claude_md = home / "CLAUDE.md"
        agent_paths = sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []
        return {
            "mode": "all",
            "root": home,
            "agent_paths": agent_paths,
            "skills_dir": skills_dir,
            "claude_md": claude_md,
            "skill_path": None,
        }
    # 단일 하네스 모드
    agent_paths: list[Path] = []
    p_local = root / ".claude" / "agents"
    if p_local.is_dir():
        agent_paths.extend(sorted(p_local.glob("*.md")))
    p_alt = root / "agents"
    if p_alt.is_dir():
        agent_paths.extend(sorted(p_alt.glob("*.md")))
    # ~/.claude/agents 에서 hint prefix로 일부
    # Harness-name → agent-prefix mapping.
    # Customize via TOKENSAVE_HARNESS_PREFIX_MAP env var (JSON object) or edit in place.
    # Example: export TOKENSAVE_HARNESS_PREFIX_MAP='{"my-harness":["mh-"]}'
    # A full example mapping from a real 27-harness catalog is in
    #   examples/personal_baseline.md §harness-mapping
    import os as _os, json as _json
    _DEFAULT_PREFIX_MAP: dict[str, list[str]] = {
        # Generic examples — replace with your own harness names and prefixes.
        "my-harness": ["mh-"],
        "another-harness": ["ah-"],
    }
    try:
        _env_map = _os.environ.get("TOKENSAVE_HARNESS_PREFIX_MAP", "")
        HARNESS_PREFIX_MAP: dict[str, list[str]] = (
            _json.loads(_env_map) if _env_map.strip() else _DEFAULT_PREFIX_MAP
        )
    except Exception:
        HARNESS_PREFIX_MAP = _DEFAULT_PREFIX_MAP
    home_agents = Path.home() / ".claude" / "agents"
    if home_agents.is_dir():
        hint = root.name.lower()
        prefixes = []
        if hint in HARNESS_PREFIX_MAP:
            prefixes.extend(HARNESS_PREFIX_MAP[hint])
        else:
            if "-" in hint:
                prefixes.append(hint.split("-")[0][:3] + "-")
        for f in home_agents.glob("*.md"):
            for pref in prefixes:
                if f.name.startswith(pref):
                    agent_paths.append(f)
                    break
    # dedup
    agent_paths = sorted(set(agent_paths))
    skill_path = None
    p_skill_local = root / ".claude" / "skills"
    if p_skill_local.is_dir():
        for sub in p_skill_local.iterdir():
            sm = sub / "SKILL.md"
            if sm.is_file():
                skill_path = sm
                break
    if not skill_path:
        s = root / "SKILL.md"
        if s.is_file():
            skill_path = s
    claude_md = root / "CLAUDE.md"
    return {
        "mode": "single",
        "root": root,
        "agent_paths": agent_paths,
        "skills_dir": None,
        "claude_md": claude_md if claude_md.is_file() else None,
        "skill_path": skill_path,
    }


# ─── 룰 ───────────────────────────────────────────────────────────────────────

def rule_R1_model_tier(agents: list[AgentSummary], taxonomy: dict, root: Path) -> Finding:
    meta = taxonomy.get("R1", TAXONOMY_FALLBACK["R1"])
    total = len(agents)
    if total == 0:
        return Finding(rule_id="R1", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="N/A",
                       reasoning="No agents found.", sources=meta["sources"])
    opus_count = sum(1 for a in agents if a.model == "opus")
    pct = opus_count / total * 100
    sample = []
    for a in agents[:5]:
        if a.model == "opus":
            sample.append(f"`{Path(a.path).name}` — model: opus")
    if pct >= 80:
        downgrade_candidates = sum(1 for a in agents
                                    if a.model == "opus" and a.size >= 5000
                                    and a.det_kw_count == 0 and not a.is_writer)
        return Finding(
            rule_id="R1",
            category=meta["category"],
            title=meta["title"],
            severity=meta["severity"],
            decision="FAIL",
            evidence=sample,
            reasoning=f"Opus 비율 {pct:.1f}% ({opus_count}/{total}). HD-020 anti-pattern. "
                      f"5K+ 다운그레이드 후보 추정 {downgrade_candidates}개.",
            suggested_fix="read-only/탐색은 Haiku, 정형 출력·코드·일반 집필은 Sonnet, "
                          "아키텍처·high-stake reasoning만 Opus 유지. "
                          "절감 -40% (Sonnet) ~ -80% (Haiku) per agent.",
            sources=meta["sources"],
        )
    elif pct >= 50:
        return Finding(rule_id="R1", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="WARN",
                       evidence=sample,
                       reasoning=f"Opus 비율 {pct:.1f}% — 임계 미만이나 모니터링 필요.",
                       sources=meta["sources"])
    else:
        return Finding(rule_id="R1", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="PASS",
                       reasoning=f"Opus 비율 {pct:.1f}% — 적정 범위.",
                       sources=meta["sources"])


def rule_R2_hd003(agents: list[AgentSummary], taxonomy: dict, root: Path) -> Finding:
    meta = taxonomy.get("R2", TAXONOMY_FALLBACK["R2"])
    risky = [a for a in agents if a.det_kw_count > 0 and a.code_split_count == 0]
    safe = [a for a in agents if a.det_kw_count > 0 and a.code_split_count > 0]
    if not risky and not safe:
        return Finding(rule_id="R2", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="N/A",
                       reasoning="No agents mention deterministic keywords.",
                       sources=meta["sources"])
    if risky:
        evidence = []
        sorted_risky = sorted(risky, key=lambda a: -a.det_kw_count)[:5]
        for a in sorted_risky:
            evidence.append(f"`{Path(a.path).name}` — det_kw={a.det_kw_count}, "
                            f"code_split=0, size={a.size:,} ({a.model})")
        return Finding(
            rule_id="R2",
            category=meta["category"],
            title=meta["title"],
            severity=meta["severity"],
            decision="FAIL",
            evidence=evidence,
            reasoning=f"{len(risky)}개 agent가 결정적 작업(verbatim·BibTeX·정규화)을 LLM에 위임. "
                      f"code-phase 분리 0건. 91분→30초 트랩 패턴 [S-C09].",
            suggested_fix="해당 agent를 두 단계로 분할: "
                          "(1) Python 결정적 변환 phase, (2) LLM 짧은 review (≤ 10 edge case). "
                          "절감 -99% per agent.",
            sources=meta["sources"],
        )
    return Finding(rule_id="R2", category=meta["category"], title=meta["title"],
                   severity=meta["severity"], decision="PASS",
                   reasoning=f"{len(safe)}개 agent가 code-split 보유 — HD-003 안전.",
                   sources=meta["sources"])


def _check_role_tier_mix(harness: HarnessSummary, agents: list[AgentSummary]) -> tuple[bool, str]:
    """R3a: 5+ team 의 agent 모두 동일 model 선언 → FAIL. 일부 분기 → 일부 충족 (True with note).

    Returns (sufficient, note).
    'sufficient' = True if role-tier mix exists (>=2 distinct models among matched agents)
    'note' = human-readable evidence
    """
    matched: list[AgentSummary] = []
    name_set = {n.strip().strip("`") for n in harness.agent_names}
    for a in agents:
        stem = Path(a.path).stem
        if stem in name_set or a.name.replace(".md", "") in name_set:
            matched.append(a)
    if not matched:
        # Cannot verify — treat as inconclusive but not a fail signal on its own
        return (True, "agent definitions not co-located (cannot verify)")
    models = {a.model for a in matched if a.model not in ("none", "general-purpose")}
    if len(models) >= 2:
        return (True, f"role-tier mix detected: {sorted(models)}")
    if len(models) == 1:
        only = next(iter(models))
        return (False, f"all {len(matched)} matched agents use `model: {only}` — no role-tier mix")
    return (True, "agent models unannotated (cannot verify)")


def _check_cache_control(harness: HarnessSummary, claude_md_text: str,
                          skill_text: str) -> tuple[bool, str]:
    """R3b: 5+ team 하네스 메인 SKILL.md / CLAUDE.md 섹션에 cache_control 키워드 0회 → FAIL signal."""
    pat = r"cache_control|prompt\s*cach|캐싱\s*breakpoint"
    section_hits = grep_count(harness.section_text, pat)
    skill_hits = grep_count(skill_text or "", pat)
    total = section_hits + skill_hits
    if total > 0:
        return (True, f"cache_control mention {total}× (section={section_hits}, skill={skill_hits})")
    return (False, "no cache_control / prompt caching mention in harness section or SKILL.md")


def _check_parallel_serial_declaration(harness: HarnessSummary) -> tuple[bool, str]:
    """R3c: 5+ team인데 병렬·직렬·background·cascade·sequential 등 의도적 선언 키워드 0 → WARN."""
    keywords = [
        r"\b병렬\b", r"\b직렬\b", r"\b순차\b",
        r"\bparallel\b", r"\bsequential\b", r"\bbackground\b",
        r"\bcascade\b", r"\bfan[- ]?out\b", r"\bfan[- ]?in\b",
        r"\bwave\b", r"\bpipeline\b",
        r"하이브리드", r"\bhybrid\b",
    ]
    hits = []
    for kw in keywords:
        if grep_bool(harness.section_text, kw):
            hits.append(kw.strip(r"\b"))
    if hits:
        return (True, f"execution mode declared: {hits[:4]}")
    return (False, "no explicit parallel/sequential/background/cascade declaration")


def _check_wall_clock_cap(harness: HarnessSummary) -> tuple[bool, str]:
    """R3d: 5+ team에 wall-clock budget·timeout·per-call cap 키워드 0 → WARN."""
    keywords = [
        r"wall[- ]?clock", r"\btimeout\b", r"\bbudget\b",
        r"per[- ]?call.*cap", r"output.*cap",
        r"분량\s*한도", r"\b한도\b", r"\bcap:\s*\d",
        r"\b루프\s*최대\b", r"재시도\s*max", r"iter.*?cap",
        r"≤\s*\d+\s*(회|min|분|시간)",
    ]
    hits = []
    for kw in keywords:
        if grep_bool(harness.section_text, kw):
            hits.append(kw)
    if hits:
        return (True, f"wall-clock/cap declared: {len(hits)} matches")
    return (False, "no wall-clock budget / per-call cap / retry limit keywords")


def _check_file_based_handoff(harness: HarnessSummary) -> tuple[bool, str]:
    """R3e: 5+ team에 _workspace/ · file-based · 산출물 트리 키워드 0 → WARN (SendMessage 남용 위험)."""
    keywords = [
        r"_workspace/", r"file[- ]?based", r"파일\s*기반",
        r"산출물\s*트리", r"산출물\s*경로", r"중간\s*산출물",
        r"\.checkpoints?/", r"output[- ]?first",
    ]
    hits = []
    for kw in keywords:
        if grep_bool(harness.section_text, kw):
            hits.append(kw)
    if hits:
        return (True, f"file-based handoff: {len(hits)} signal(s)")
    return (False, "no _workspace/ or file-based handoff convention")


def _audit_harness_composition(h: HarnessSummary, agents: list[AgentSummary],
                                 claude_md_text: str, skill_text: str) -> dict:
    """5 sub-criteria per harness. Returns dict with per-rule (sufficient, note) + summary."""
    results = {
        "R3a_role_tier_mix": _check_role_tier_mix(h, agents),
        "R3b_cache_control": _check_cache_control(h, claude_md_text, skill_text),
        "R3c_parallel_serial": _check_parallel_serial_declaration(h),
        "R3d_wall_clock_cap": _check_wall_clock_cap(h),
        "R3e_file_handoff": _check_file_based_handoff(h),
    }
    met = sum(1 for v in results.values() if v[0])
    missing = [k for k, v in results.items() if not v[0]]
    return {
        "harness": h.name,
        "agent_count": h.agent_count,
        "met": met,
        "missing": missing,
        "details": results,
    }


def rule_R3_team_size(harnesses: list[HarnessSummary], taxonomy: dict, root: Path,
                       agents: Optional[list[AgentSummary]] = None,
                       claude_md_text: str = "",
                       skill_text: str = "") -> Finding:
    """R3 — Multi-Agent Team Composition (cost-optimized).

    Three-tier decision for each 5+ team harness:
      - PASS (well-formed)  if 5/5 sub-criteria met
      - WARN (optimization) if 3~4/5 met
      - FAIL (unjustified)  if 0~2/5 met

    Aggregate harness-level results into a single Finding for the catalog.
    Multi-agent itself is NOT penalized — only missing optimization patterns are.
    """
    meta = taxonomy.get("R3", TAXONOMY_FALLBACK["R3"])
    agents = agents or []
    total = len(harnesses)
    if total == 0:
        return Finding(rule_id="R3", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="N/A",
                       reasoning="No harnesses detected.", sources=meta["sources"])

    five_plus = [h for h in harnesses if h.agent_count >= 5]
    if not five_plus:
        return Finding(rule_id="R3", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="N/A",
                       reasoning=f"No 5+ agent harnesses ({total} small teams) — "
                                 "R3 only audits multi-agent composition.",
                       sources=meta["sources"])

    audits = [_audit_harness_composition(h, agents, claude_md_text, skill_text)
              for h in five_plus]

    well_formed = [a for a in audits if a["met"] == 5]
    optimization = [a for a in audits if 3 <= a["met"] <= 4]
    unjustified = [a for a in audits if a["met"] <= 2]

    # Aggregate decision: worst-case priority.
    # If any harness has 0~2/5, overall = FAIL (unjustified multiplier somewhere).
    # Else if any has 3~4/5, overall = WARN.
    # Else (all 5/5), PASS.
    if unjustified:
        decision = "FAIL"
    elif optimization:
        decision = "WARN"
    else:
        decision = "PASS"

    # Evidence: top-5 worst harnesses, with their missing sub-rules
    worst_sorted = sorted(audits, key=lambda x: (x["met"], -x["agent_count"]))[:5]
    evidence = []
    for a in worst_sorted:
        missing_short = [m.split("_", 1)[0].replace("R3", "R3") for m in a["missing"]]
        evidence.append(
            f"`{a['harness']}` — {a['agent_count']} agents, {a['met']}/5 met, "
            f"missing: {','.join(missing_short) or '—'}"
        )

    if decision == "PASS":
        reasoning = (f"All {len(five_plus)} multi-agent harnesses meet 5/5 cost-optimization "
                     "patterns (role-tier mix · cache_control · parallel/serial declared · "
                     "wall-clock cap · file-based handoff). Well-formed multi-agent design.")
        suggested_fix = ""
    elif decision == "WARN":
        reasoning = (f"{len(five_plus)} multi-agent harnesses: "
                     f"well-formed {len(well_formed)} / optimization-opportunity {len(optimization)} / "
                     f"unjustified {len(unjustified)}. "
                     "Multi-agent is justified — multiplier 7×~15× [A003][S-B003] needs 5 patterns "
                     "to pay for itself. WARN harnesses miss 1~2 patterns.")
        suggested_fix = ("Apply missing patterns from `references/optimal_team_composition.md`. "
                         "Priority order: R3b (cache_control) → R3a (role-tier mix) → "
                         "R3e (file-based) → R3c (parallel/serial) → R3d (wall-clock cap).")
    else:  # FAIL
        reasoning = (f"{len(unjustified)} harness(es) miss 3+ of 5 cost-optimization patterns — "
                     f"multi-agent multiplier (7×~15×) is paid without justification. "
                     f"Other: well-formed {len(well_formed)}, WARN {len(optimization)}. "
                     "Multi-agent itself is NOT the issue — missing optimization is.")
        suggested_fix = ("Apply 5 cost-optimization patterns from "
                         "`references/optimal_team_composition.md`: "
                         "(P1) role-tier model mix · (P2) common-context cache_control · "
                         "(P3) parallel/sequential intentional declaration · "
                         "(P4) per-agent wall-clock + per-call cap · "
                         "(P5) file-based handoff (avoid SendMessage overuse).")

    return Finding(
        rule_id="R3",
        category=meta["category"],
        title=meta["title"],
        severity=meta["severity"],
        decision=decision,
        evidence=evidence,
        reasoning=reasoning,
        suggested_fix=suggested_fix,
        sources=meta["sources"],
    )


def rule_R4_bloat(claude_md_text: str, claude_md_path: Optional[Path],
                  skills: list[dict], taxonomy: dict, root: Path) -> Finding:
    meta = taxonomy.get("R4", TAXONOMY_FALLBACK["R4"])
    evidence = []
    issues = []
    if claude_md_path:
        lines = claude_md_text.count("\n")
        if lines > 200:
            evidence.append(f"`{claude_md_path.name}` — {lines} lines ({len(claude_md_text):,} chars)")
            issues.append(f"CLAUDE.md {lines} lines")
    # meta_skill: true frontmatter 인 스킬은 R4 예외 (R9와 동일 정책)
    bloated_skills = [s for s in skills if s["size"] > 8000 and not s.get("meta_skill", False)]
    for s in sorted(bloated_skills, key=lambda x: -x["size"])[:5]:
        evidence.append(f"`{s['name']}/SKILL.md` — {s['size']:,} chars")
        issues.append(f"{s['name']} {s['size']:,}자")
    if not evidence:
        return Finding(rule_id="R4", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="PASS",
                       reasoning="CLAUDE.md & SKILL.md 모두 임계 미만.",
                       sources=meta["sources"])
    decision = "FAIL" if len(bloated_skills) >= 5 else "WARN"
    return Finding(
        rule_id="R4",
        category=meta["category"],
        title=meta["title"],
        severity=meta["severity"],
        decision=decision,
        evidence=evidence,
        reasoning=f"비대 파일 {len(evidence)}개. " + ", ".join(issues[:3]),
        suggested_fix="CLAUDE.md: 운영만 본문, 이력은 changelog 분리. "
                      "SKILL.md: 장식·역사 references/ 이전. 절감 -50% 세션 고정 비용 [S-B004][S-B005].",
        sources=meta["sources"],
    )


def rule_R5_caching(claude_md_text: str, skills: list[dict],
                    taxonomy: dict, root: Path) -> Finding:
    meta = taxonomy.get("R5", TAXONOMY_FALLBACK["R5"])
    cache_pat = r"cache_control|캐싱|prompt\s*cach"
    claude_hits = grep_count(claude_md_text, cache_pat) if claude_md_text else 0
    skill_hits = 0
    skill_with_cache = []
    for s in skills:
        try:
            t = Path(s["path"]).read_text(errors="replace")
            n = grep_count(t, cache_pat)
        except Exception:
            n = 0
        skill_hits += n
        if n > 0:
            skill_with_cache.append(s["name"])
    total_hits = claude_hits + skill_hits
    if total_hits == 0:
        biggest_skill = max(skills, key=lambda x: x["size"]) if skills else None
        target = f" 1순위: `{biggest_skill['name']}/SKILL.md` ({biggest_skill['size']:,}자)" if biggest_skill else ""
        return Finding(
            rule_id="R5",
            category=meta["category"],
            title=meta["title"],
            severity=meta["severity"],
            decision="FAIL",
            evidence=[f"caching 언급 0회 / {len(skills)} skill + CLAUDE.md"],
            reasoning=f"전 카탈로그 cache_control / 캐싱 / prompt cache 언급 0회. "
                      f"평균 SKILL.md {sum(s['size'] for s in skills)//max(len(skills),1):,}자 "
                      f"반복 입력 미캐싱.{target}",
            suggested_fix="system prompt + SKILL.md + 큰 reference 파일에 cache_control "
                          "4 breakpoint 적용. Sonnet 1024 / Opus 4096 최소 토큰. "
                          "절감 -80% input tokens (hit ratio 90% 시) [A004][A005][S-B006].",
            sources=meta["sources"],
        )
    return Finding(
        rule_id="R5", category=meta["category"], title=meta["title"],
        severity=meta["severity"], decision="WARN" if total_hits < 5 else "PASS",
        evidence=[f"caching 언급 {total_hits}회 / {len(skill_with_cache)} skill"],
        reasoning=f"caching 언급 {total_hits}회. 모두 cache_control 실제 적용 여부는 검증 필요.",
        sources=meta["sources"],
    )


def rule_R6_read_pattern(skill_path: Optional[Path], skill_text: str,
                          taxonomy: dict, root: Path) -> Finding:
    """정적으로는 reliably 검출 어려움 — Read 호출 패턴은 runtime. 정적 휴리스틱:
    SKILL.md에 '매번 다시 읽기' 같은 부주의 표현 / Read tool 반복 권유 검출.
    """
    meta = taxonomy.get("R6", TAXONOMY_FALLBACK["R6"])
    if not skill_text:
        return Finding(rule_id="R6", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="N/A",
                       reasoning="SKILL.md 미발견 — 룰 적용 안 함.",
                       sources=meta["sources"])
    bad_patterns = [
        r"매번\s*(다시\s*)?읽", r"전체\s*Read\s*먼저", r"항상\s*Read\b",
        r"re-?read\s+each\s+time", r"always\s+read\s+full",
    ]
    hits = []
    for p in bad_patterns:
        if grep_bool(skill_text, p):
            hits.append(p)
    if hits:
        return Finding(
            rule_id="R6", category=meta["category"], title=meta["title"],
            severity=meta["severity"], decision="WARN",
            evidence=hits,
            reasoning="SKILL.md에 '매번 다시 읽기' 류 표현 — runtime에 동일 파일 반복 Read 위험.",
            suggested_fix="grep으로 라인 찾고 주변만 Read(offset/limit). 한 번 읽은 파일은 메모화.",
            sources=meta["sources"],
        )
    return Finding(rule_id="R6", category=meta["category"], title=meta["title"],
                   severity=meta["severity"], decision="PASS",
                   reasoning="명시적 '반복 Read' 패턴 미검출.",
                   sources=meta["sources"])


def rule_R7_output_first(skill_path: Optional[Path], skill_text: str,
                          agents: list[AgentSummary], taxonomy: dict, root: Path) -> Finding:
    meta = taxonomy.get("R7", TAXONOMY_FALLBACK["R7"])
    phases = grep_count(skill_text, r"^#+\s*Phase\s+\d", re.MULTILINE) if skill_text else 0
    if phases < 3:
        return Finding(rule_id="R7", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="N/A",
                       reasoning="Phase 3 미만 — 룰 적용 미달.",
                       sources=meta["sources"])
    hits = []
    for kw in OUTPUT_FIRST_KEYWORDS:
        m = grep_lines(skill_text, kw)
        if m:
            hits.append(f"line {m[0][0]}: `{kw}`")
            break
    if not hits:
        return Finding(
            rule_id="R7", category=meta["category"], title=meta["title"],
            severity=meta["severity"], decision="FAIL",
            evidence=[f"phases={phases}, output-first 키워드 0건"],
            reasoning=f"Phase {phases}개 파이프라인에 'output-first / .checkpoints/ / 산출물 우선' 컨벤션 부재. "
                      "drafter가 보고 텍스트 끊기면 산출물 유실 후 재실행 비용.",
            suggested_fix="SKILL.md에 'output-first, report-after' 컨벤션 추가: "
                          "(1) 산출물 디스크 저장 → (2) checkpoint {file_path, line_count, sha256} → "
                          "(3) 보고 ≤ 200~300자.",
            sources=meta["sources"],
        )
    return Finding(rule_id="R7", category=meta["category"], title=meta["title"],
                   severity=meta["severity"], decision="PASS",
                   evidence=hits,
                   reasoning="output-first / checkpoint 컨벤션 검출.",
                   sources=meta["sources"])


def rule_R8_per_call_cap(agents: list[AgentSummary], taxonomy: dict, root: Path) -> Finding:
    meta = taxonomy.get("R8", TAXONOMY_FALLBACK["R8"])
    writers = [a for a in agents if a.is_writer]
    if not writers:
        return Finding(rule_id="R8", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="N/A",
                       reasoning="writer/drafter agent 미검출.",
                       sources=meta["sources"])
    writers_without_cap = []
    for a in writers:
        try:
            text = Path(a.path).read_text(errors="replace")
        except Exception:
            continue
        has_cap = any(grep_bool(text, kw) for kw in PER_CALL_CAP_KEYWORDS)
        if not has_cap:
            writers_without_cap.append(a)
    if writers_without_cap:
        evidence = [f"`{Path(a.path).name}` — size {a.size:,}, cap 키워드 0건"
                    for a in sorted(writers_without_cap, key=lambda x: -x.size)[:5]]
        return Finding(
            rule_id="R8", category=meta["category"], title=meta["title"],
            severity=meta["severity"], decision="FAIL",
            evidence=evidence,
            reasoning=f"writer/drafter agent {len(writers_without_cap)}/{len(writers)}에 "
                      "per-call output cap / 자동 분할 룰 부재.",
            suggested_fix="각 writer agent에 `cap: 4000자/call` 또는 "
                          "`섹션 > 4K → 2 sub-call 자동 분할` 룰 명시. "
                          "절감 -28.4% cost-of-pass [S-C05].",
            sources=meta["sources"],
        )
    return Finding(rule_id="R8", category=meta["category"], title=meta["title"],
                   severity=meta["severity"], decision="PASS",
                   reasoning=f"{len(writers)}개 writer 모두 cap 보유.",
                   sources=meta["sources"])


def rule_R9_nonactionable(skills: list[dict], taxonomy: dict, root: Path) -> Finding:
    meta = taxonomy.get("R9", TAXONOMY_FALLBACK["R9"])
    if not skills:
        return Finding(rule_id="R9", category=meta["category"], title=meta["title"],
                       severity=meta["severity"], decision="N/A",
                       reasoning="No SKILL.md found.", sources=meta["sources"])
    # 휴리스틱: SKILL.md > 5000자 + phase_count=0 + decision_tree_count=0 → 비실행 콘텐츠 의심
    # 단 frontmatter meta_skill: true 인 메타 스킬은 R9 예외 (4모드+매트릭스 본문 활성화 필요)
    suspicious = []
    for s in skills:
        if s.get("meta_skill", False):
            continue
        if s["size"] > 5000 and s["phase_count"] == 0 and s["decision_tree_count"] == 0:
            suspicious.append(s)
    if suspicious:
        evidence = [f"`{s['name']}/SKILL.md` — {s['size']:,} chars, phase=0, tree=0"
                    for s in sorted(suspicious, key=lambda x: -x["size"])[:5]]
        return Finding(
            rule_id="R9", category=meta["category"], title=meta["title"],
            severity=meta["severity"], decision="WARN",
            evidence=evidence,
            reasoning=f"{len(suspicious)}개 SKILL.md가 5K+자인데 Phase·결정 트리 키워드 0 — "
                      "SkillReducer '60%+ non-actionable' 가설 적용 시 비실행 장식 의심.",
            suggested_fix="본문은 Phase·결정 트리·예시만. 장식·역사·메타는 references/ 분리.",
            sources=meta["sources"],
        )
    return Finding(rule_id="R9", category=meta["category"], title=meta["title"],
                   severity=meta["severity"], decision="PASS",
                   reasoning="SKILL.md 본문에 Phase / 결정 트리 키워드 존재.",
                   sources=meta["sources"])


# ─── 종합 ────────────────────────────────────────────────────────────────────

ALL_RULES = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9"]


def run_audit(root: Optional[Path], rules: list[str]) -> AuditReport:
    paths = discover_paths(root)
    taxonomy_json = load_taxonomy()
    if taxonomy_json:
        # taxonomy.json에서 룰 메타 추출 시도 (없으면 fallback)
        # 현재는 fallback 사용 (taxonomy.json은 category 구조이므로 매핑 어렵 — fallback 우선)
        taxonomy = TAXONOMY_FALLBACK
    else:
        taxonomy = TAXONOMY_FALLBACK

    agents = scan_agents(paths["agent_paths"])
    claude_text = ""
    claude_path = paths.get("claude_md")
    if claude_path and claude_path.is_file():
        claude_text = claude_path.read_text(errors="replace")
    harnesses = scan_harnesses(claude_text) if claude_text else []

    skill_path = paths.get("skill_path")
    skill_text = ""
    if skill_path and skill_path.is_file():
        skill_text = skill_path.read_text(errors="replace")

    skills_dir = paths.get("skills_dir")
    if skills_dir:
        skills = scan_skills(skills_dir)
    elif skill_path:
        skills = scan_skills(skill_path.parent.parent)
    else:
        skills = []

    root_for_cite = paths["root"] if paths["root"] else Path.home()

    findings: list[Finding] = []
    for r in rules:
        if r == "R1":
            findings.append(rule_R1_model_tier(agents, taxonomy, root_for_cite))
        elif r == "R2":
            findings.append(rule_R2_hd003(agents, taxonomy, root_for_cite))
        elif r == "R3":
            findings.append(rule_R3_team_size(
                harnesses, taxonomy, root_for_cite,
                agents=agents, claude_md_text=claude_text, skill_text=skill_text,
            ))
        elif r == "R4":
            findings.append(rule_R4_bloat(claude_text, claude_path, skills, taxonomy, root_for_cite))
        elif r == "R5":
            findings.append(rule_R5_caching(claude_text, skills, taxonomy, root_for_cite))
        elif r == "R6":
            findings.append(rule_R6_read_pattern(skill_path, skill_text, taxonomy, root_for_cite))
        elif r == "R7":
            findings.append(rule_R7_output_first(skill_path, skill_text, agents, taxonomy, root_for_cite))
        elif r == "R8":
            findings.append(rule_R8_per_call_cap(agents, taxonomy, root_for_cite))
        elif r == "R9":
            findings.append(rule_R9_nonactionable(skills, taxonomy, root_for_cite))

    # 통계
    total_agents = len(agents)
    opus_count = sum(1 for a in agents if a.model == "opus")
    overall_stats = {
        "agents_total": total_agents,
        "opus_count": opus_count,
        "opus_pct": round(opus_count / total_agents * 100, 1) if total_agents else 0,
        "harnesses_total": len(harnesses),
        "five_plus_harnesses": sum(1 for h in harnesses if h.agent_count >= 5),
        "skills_total": len(skills),
        "avg_skill_size": (sum(s["size"] for s in skills) // len(skills)) if skills else 0,
        "fail_count": sum(1 for f in findings if f.decision == "FAIL"),
        "warn_count": sum(1 for f in findings if f.decision == "WARN"),
        "pass_count": sum(1 for f in findings if f.decision == "PASS"),
        "na_count": sum(1 for f in findings if f.decision == "N/A"),
    }

    # Hotspot top10 — agent 단위
    hotspots = []
    for a in agents:
        score = 0
        reasons = []
        if a.model == "opus" and a.size >= 5000 and a.det_kw_count == 0 and not a.is_writer:
            score += 3
            reasons.append("opus + 5K+ + 비결정적·비-writer → Sonnet 강력 후보")
        if a.det_kw_count > 0 and a.code_split_count == 0:
            score += 5
            reasons.append(f"HD-003 RISKY (det_kw={a.det_kw_count})")
        if a.is_writer and a.size >= 5000:
            score += 2
            reasons.append("writer + 큰 정의 — per-call cap 점검")
        if score > 0:
            hotspots.append({
                "agent": Path(a.path).name,
                "model": a.model,
                "size": a.size,
                "score": score,
                "reasons": reasons,
            })
    hotspots.sort(key=lambda x: (-x["score"], -x["size"]))

    return AuditReport(
        scope=str(paths["root"]) if paths.get("mode") == "single" else "all (~/.claude + ~/CLAUDE.md)",
        findings=findings,
        agent_summaries=agents,
        harness_summaries=harnesses,
        skill_summaries=skills,
        overall_stats=overall_stats,
        hotspot_top10=hotspots[:10],
    )


# ─── 렌더링 ───────────────────────────────────────────────────────────────────

def render_md(report: AuditReport, show_top: int = 10) -> str:
    lines = []
    lines.append("# tokensave Audit Report")
    lines.append("")
    lines.append(f"**Scope:** `{report.scope}`")
    lines.append("")
    lines.append("## Summary")
    s = report.overall_stats
    lines.append("")
    lines.append("| 항목 | 값 |")
    lines.append("|------|---:|")
    lines.append(f"| Agents 총 | {s['agents_total']} |")
    lines.append(f"| Opus 비율 | {s['opus_pct']}% ({s['opus_count']}) |")
    lines.append(f"| Harnesses 총 | {s['harnesses_total']} |")
    lines.append(f"| 5+ agent 하네스 | {s['five_plus_harnesses']} |")
    lines.append(f"| Skills 총 | {s['skills_total']} |")
    lines.append(f"| 평균 SKILL.md 크기 | {s['avg_skill_size']:,} chars |")
    lines.append("")
    lines.append("| 판정 | 룰 수 |")
    lines.append("|------|---:|")
    for k in ("FAIL", "WARN", "PASS", "N/A"):
        v = s.get(f"{k.lower().replace('/', '')}_count", 0)
        # 키 보정
        if k == "FAIL":
            v = s["fail_count"]
        elif k == "WARN":
            v = s["warn_count"]
        elif k == "PASS":
            v = s["pass_count"]
        elif k == "N/A":
            v = s["na_count"]
        lines.append(f"| {k} | {v} |")
    lines.append("")

    lines.append("## Findings")
    for f in report.findings:
        lines.append("")
        emoji = {"FAIL": "🔴", "WARN": "🟡", "PASS": "✅", "N/A": "—"}.get(f.decision, "")
        lines.append(f"### {f.rule_id} ({f.category}) — {f.title} {emoji}")
        lines.append(f"- **Decision:** {f.decision}")
        lines.append(f"- **Severity:** {f.severity}")
        lines.append(f"- **Sources:** {', '.join(f.sources)}")
        if f.evidence:
            lines.append("- **Evidence:**")
            for e in f.evidence:
                lines.append(f"    - {e}")
        lines.append(f"- **Reasoning:** {f.reasoning}")
        if f.suggested_fix:
            lines.append(f"- **Suggested fix:** {f.suggested_fix}")

    if report.hotspot_top10:
        lines.append("")
        lines.append(f"## Hotspot Top {min(show_top, len(report.hotspot_top10))}")
        lines.append("")
        lines.append("| # | Agent | Model | Size | Score | Reasons |")
        lines.append("|---|-------|-------|-----:|------:|---------|")
        for i, h in enumerate(report.hotspot_top10[:show_top], start=1):
            lines.append(f"| {i} | `{h['agent']}` | {h['model']} | {h['size']:,} | {h['score']} | {'; '.join(h['reasons'])} |")

    lines.append("")
    lines.append("---")
    lines.append("_본 감사는 정적 룰 기반 (LLM 호출 0회). runtime 패턴(C4.4 kitchen-sink session, C7.4 sequential calls 등)은 별도 감사 필요._")
    return "\n".join(lines)


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="tokensave audit — 정적 9 룰 기반 하네스 감사."
    )
    ap.add_argument("root", nargs="?",
                    help="하네스 root 경로 (생략 시 전수 모드 ~/.claude + ~/CLAUDE.md)")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    ap.add_argument("--top", type=int, default=10, help="hotspot 표시 개수 (default 10)")
    ap.add_argument("--rules", help="콤마 구분 룰 ID (예: R1,R2,R5). 미지정 시 전체")
    args = ap.parse_args()

    root = None
    if args.root:
        root = Path(args.root).expanduser().resolve()
        if not root.is_dir():
            print(f"error: {root} is not a directory", file=sys.stderr)
            return 2

    if args.rules:
        rules = [r.strip().upper() for r in args.rules.split(",") if r.strip()]
        invalid = [r for r in rules if r not in ALL_RULES]
        if invalid:
            print(f"error: unknown rules: {invalid}. Valid: {ALL_RULES}", file=sys.stderr)
            return 2
    else:
        rules = ALL_RULES

    report = run_audit(root, rules)

    if args.json:
        print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    else:
        print(render_md(report, show_top=args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
