#!/usr/bin/env python3
"""
tokensave — model_selector.py  ★ HEADLINE

자연어 작업 설명을 받아 추천 모델(Python/Haiku/Sonnet/Opus) + 근거 + 예상 비용을
출력하는 완전 결정적 CLI. LLM 호출 0회.

결정 트리는 taxonomy.md §3 Task→Model 매트릭스 24행을 인코딩한다.

Usage:
  python3 model_selector.py --task "PDF에서 표 추출 후 CSV로 정규화"
  python3 model_selector.py --task "주간 IT 칼럼 5000자 집필" --tokens 8000 --quality high
  python3 model_selector.py --task "agent 정의에서 결정적 키워드 grep" --tokens 200
  python3 model_selector.py --task "..." --json

표준 라이브러리만. 가격은 estimate_cost.py PRICING SSOT 사용.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

# 같은 디렉토리에서 estimate_cost 모듈 import
sys.path.insert(0, str(Path(__file__).parent.resolve()))
try:
    from estimate_cost import estimate_cost, compare_all_models, PRICING
except ImportError as e:
    print(f"error: cannot import estimate_cost.py: {e}", file=sys.stderr)
    print("       ensure estimate_cost.py is in the same directory.", file=sys.stderr)
    sys.exit(2)


# ─── 결정적 키워드 (Python 분기 트리거) ───────────────────────────────────────
#
# 출처: taxonomy.md §C2 + Task→Model 매트릭스 #1·18·19·24

DETERMINISTIC_KEYWORDS: list[tuple[str, str, str]] = [
    # (정규식, 이유, 매트릭스 행 참조)
    # 주의: 한국어 텍스트에는 \b (word boundary) 가 안 먹는다 (Unicode 문자).
    # 영문은 \b 유지, 한국어는 단순 문자열 매칭으로.
    (r"\bregex\b|정규\s*표현", "regex 변환 — 결정적", "#1"),
    (r"\bverbatim\b", "verbatim 1:1 매핑 — 결정적", "#1"),
    (r"1:1\s*매핑|\b1:1\s+mapping\b", "1:1 매핑 — 결정적", "#1"),
    (r"\bBibTeX\b", "BibTeX 생성/변환 — pybtex로 결정적", "#1"),
    (r"\bcitation\b.*(변환|normalize|정규)|인용\s*(정규화|변환|포맷)",
     "citation 정규화 — csl-json", "#1"),
    (r"\bCSV\b.*(JSON|변환|정규)|CSV\s*(로|→|->|으로)\s*(정규|변환|JSON)",
     "CSV→JSON — pandas", "#18"),
    (r"JSON\s*정규화|\bJSON\s+normaliz", "JSON 정규화 — 결정적", "#1"),
    (r"\b(PDF|pdf)\b.*(표|table|추출|extract)|PDF에서\s*(표|데이터|텍스트)",
     "PDF 표 추출 — pypdf/pdfplumber", "#18"),
    (r"\bHTML\b.*(추출|스크래핑|파싱)", "HTML 파싱 — BeautifulSoup/readability", "#18"),
    (r"\bdead[\s\-]?link\b|링크\s*유효성", "dead link 체크 — requests + linkchecker", "#1"),
    (r"\bsha256\b|해시\s*(계산|생성)", "해시 계산 — hashlib", "#1"),
    (r"파일\s*카운트|\bfile\s*count\b", "파일 카운트 — wc / os.listdir", "#19"),
    (r"\bgrep\b|파일\s*검색", "grep — shell/re 모듈", "#24"),
    (r"\bdate.*(format|정규|normalize)\b|날짜\s*포맷", "날짜 포맷 — dateutil", "#1"),
    (r"\bcross[\s\-]?reference\b.*(매칭|matching|해결|resolve)",
     "cross-ref 매칭 — dict lookup", "#1"),
    (r"로그.*(압축|filter|grep)|\blog\b.*(grep|filter)", "log 압축 — grep/awk", "#24"),
    (r"카탈로그.*점검|\bmeta.*\bintegrity\b", "메타 정합성 점검 — Python", "#19"),
    (r"\bword[\s\-]?count\b|분량\s*카운트|문자수\s*카운트", "문자수 카운트 — wc/len", "#1"),
]

# Haiku 분기 키워드 (탐색·짧은 분류)
HAIKU_KEYWORDS: list[tuple[str, str, str]] = [
    (r"탐색|\bexplore\b|파일\s*찾", "코드베이스 탐색 — Haiku 빌트인", "#22"),
    (r"짧은.*분류|룰.*분류|\bshort.*classification\b",
     "짧은 룰 기반 분류 — Haiku 충분", "#3"),
    (r"짧은.*요약|1\s*단락|\bone[\s\-]?paragraph\b",
     "짧은 요약 (≤ 1 단락) — Haiku 충분", "#4"),
    (r"보일러플레이트|\bboilerplate\b", "boilerplate — Haiku", "#23"),
    (r"\bFAQ\b|짧은\s*응답", "짧은 도메인 응답 — Haiku", "#20"),
    (r"\bread[\s\-]?only\b|읽기\s*전용", "read-only 작업 — Haiku", "#22"),
    (r"패턴\s*매칭.*짧은", "패턴 매칭 (짧은 입력) — Haiku", "#3"),
]

# Sonnet 분기 키워드 (표준 자연어 출력·코드)
SONNET_KEYWORDS: list[tuple[str, str, str]] = [
    (r"JSON\s*생성|정형\s*출력|표\s*생성",
     "자연어 정형 출력 (JSON/표) — Sonnet", "#5"),
    (r"코드\s*(작성|디버깅|debug)|디버깅",
     "표준 코드 작성/디버깅 — Sonnet", "#6"),
    (r"코드\s*리뷰|\bcode\s*review\b",
     "코드 리뷰 — Sonnet 충분", "#7"),
    (r"번역(?!.*문학)(?!.*격조)", "실용 번역 — Sonnet", "#14"),
    (r"팩트체크(?!.*학술)(?!.*high)", "일반 팩트체크 — Sonnet", "#12"),
    (r"팀원|조정\s*작업|\bteammate\b",
     "에이전트 팀 팀원 — Sonnet (Anthropic 권고)", "#21"),
    (r"\bESL\b|언어\s*교육", "ESL 언어 교육 — Sonnet", "#16"),
    (r"이미지\s*프롬프트|시각\s*프롬프트|\bimage\s*prompt\b",
     "시각/이미지 프롬프트 설계 — Sonnet", "#17"),
]

# Opus 분기 키워드 (창의·아키텍처·high-stake)
OPUS_KEYWORDS: list[tuple[str, str, str]] = [
    (r"아키텍처|\barchitecture\b|설계.*결정",
     "깊은 reasoning · 아키텍처 결정 — Opus 정당", "#10"),
    (r"학술\s*페이퍼|정책\s*페이퍼|\bpaper\b.*(NeurIPS|ACL|CHI|KCI)",
     "학술/정책 페이퍼 (high-stake) — Opus 정당", "#9"),
    (r"창의.*(5000자|5K|10000자)|자유\s*생성.*톤",
     "창의 자유 생성 (5K+자, 톤 중요) — Opus 정당", "#11"),
    (r"\bhigh[\s\-]?stake\b.*팩트체크|학술\s*팩트체크",
     "학술 팩트체크 (high-stake) — Opus 정당", "#13"),
    (r"문학\s*번역|격조.*번역",
     "문학/격조 번역 — Opus 정당", "#15"),
    (r"\borchestrator\b|오케스트레이터",
     "orchestrator 역할 — Opus 정당", "#10"),
]

# 문자 분량 기반 추정 (--tokens 미제공 시 fallback)
DEFAULT_TOKENS_BY_TYPE = {
    "python": 200,        # Python 분기는 LLM 호출 없음 (참고용만)
    "haiku": 2000,
    "sonnet": 6000,
    "opus": 10000,
}


# ─── 데이터 클래스 ────────────────────────────────────────────────────────────

@dataclass
class Recommendation:
    task: str
    recommended_model: str
    matched_keyword: Optional[str]
    matrix_row: Optional[str]
    rationale: str
    sources: list[str]
    quality_input: str
    quality_adjusted: bool
    quality_adjustment_note: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost_usd: float
    cost_vs_opus_pct: float
    cost_vs_opus_usd: float
    secondary_options: list[dict]


# ─── 결정 트리 ────────────────────────────────────────────────────────────────

def first_match(task: str, keyword_list: list[tuple[str, str, str]]) -> Optional[tuple[str, str, str]]:
    """keyword_list의 정규식 중 첫 매칭을 반환."""
    for pattern, reason, matrix_ref in keyword_list:
        if re.search(pattern, task, re.IGNORECASE):
            return (pattern, reason, matrix_ref)
    return None


def select_model(task: str, quality: str = "medium") -> tuple[str, Optional[tuple[str, str, str]]]:
    """
    결정 트리 (완전 결정적):
      1. 결정적 keyword → Python (LLM 0회)
      2. Haiku keyword → Haiku
      3. Opus keyword → Opus  (high-stake가 명시되면 Haiku/Sonnet keyword보다 우선해야 함 — 이를 위해 Opus 먼저 검사)
      4. Sonnet keyword → Sonnet
      5. 기본값: Sonnet (Anthropic 공식 — 대다수 작업)
    quality 조정:
      - low + Sonnet/Opus → Haiku 검토 신호 (조정 노트만 추가)
      - high + Sonnet → Opus 검토 신호
      - high + Haiku → Sonnet 검토 신호
    """
    # 1. 결정적 keyword 우선
    det = first_match(task, DETERMINISTIC_KEYWORDS)
    if det:
        return ("python", det)

    # 2. Opus keyword를 Haiku/Sonnet 검사보다 먼저 — high-stake 명시는 강한 신호
    opus_match = first_match(task, OPUS_KEYWORDS)
    if opus_match:
        return ("opus", opus_match)

    # 3. Haiku keyword
    haiku_match = first_match(task, HAIKU_KEYWORDS)
    if haiku_match:
        return ("haiku", haiku_match)

    # 4. Sonnet keyword
    sonnet_match = first_match(task, SONNET_KEYWORDS)
    if sonnet_match:
        return ("sonnet", sonnet_match)

    # 5. 기본값
    return ("sonnet", None)


def apply_quality_adjustment(model: str, quality: str) -> tuple[str, bool, str]:
    """
    quality 플래그에 따른 모델 조정 신호 (직접 변경 안 하고 노트만).
    Returns: (adjusted_model, was_adjusted, note)
    """
    if quality not in ("low", "medium", "high"):
        return (model, False, "")

    if model == "python":
        return (model, False, "")

    if quality == "low":
        if model == "opus":
            return ("sonnet", True, "quality=low → Sonnet으로 다운그레이드 (-40%)")
        if model == "sonnet":
            return ("haiku", True, "quality=low → Haiku 검토 (-67% vs sonnet, -80% vs opus)")
        return (model, False, "")
    if quality == "high":
        if model == "haiku":
            return ("sonnet", True, "quality=high → Sonnet 상향 검토")
        if model == "sonnet":
            return ("opus", True, "quality=high → Opus 상향 검토 (정당화 필요)")
        return (model, False, "")
    return (model, False, "")


def recommend(task: str, tokens: Optional[int] = None, quality: str = "medium") -> Recommendation:
    """전체 추천 파이프라인."""
    model, match = select_model(task, quality)

    # quality 조정
    adjusted_model, adjusted, adj_note = apply_quality_adjustment(model, quality)
    final_model = adjusted_model

    # 매트릭스 행 / 근거
    if match:
        matched_kw = match[0]
        rationale = match[1]
        matrix_row = match[2]
    else:
        matched_kw = None
        rationale = "기본값 — 자연어 정형 출력·표준 코딩은 Sonnet (Anthropic 공식 권고 [A001])"
        matrix_row = "기본값"

    # 출처
    if final_model == "python":
        sources = ["S-C07", "S-C08", "S-C09"]
    elif final_model == "haiku":
        sources = ["A013", "S-B016", "S-B031"]
    elif final_model == "sonnet":
        sources = ["A001", "A002", "S-B017", "S-B018"]
    elif final_model == "opus":
        sources = ["A001", "S-C09"]
    else:
        sources = []

    # 토큰 추정
    input_tokens = tokens if tokens else DEFAULT_TOKENS_BY_TYPE.get(final_model, 4000)
    output_tokens = max(int(input_tokens * 0.5), 500)  # 입력의 50% 기본값

    # 비용 추정
    estimate = estimate_cost(final_model, input_tokens, output_tokens)
    cost = estimate.total_cost_usd

    # vs Opus 비교
    opus_estimate = estimate_cost("opus", input_tokens, output_tokens)
    opus_cost = opus_estimate.total_cost_usd
    if opus_cost > 0:
        vs_pct = round((opus_cost - cost) / opus_cost * 100, 1)
        vs_usd = round(opus_cost - cost, 4)
    else:
        vs_pct = 0.0
        vs_usd = 0.0

    # 보조 옵션 (대안 2개)
    alternatives = []
    for alt in ["python", "haiku", "sonnet", "opus"]:
        if alt == final_model:
            continue
        alt_est = estimate_cost(alt, input_tokens, output_tokens)
        alternatives.append({
            "model": alt,
            "estimated_cost_usd": alt_est.total_cost_usd,
            "delta_vs_recommended_usd": round(alt_est.total_cost_usd - cost, 4),
        })
    # 비용 오름차순
    alternatives.sort(key=lambda x: x["estimated_cost_usd"])

    return Recommendation(
        task=task,
        recommended_model=final_model,
        matched_keyword=matched_kw,
        matrix_row=matrix_row,
        rationale=rationale,
        sources=sources,
        quality_input=quality,
        quality_adjusted=adjusted,
        quality_adjustment_note=adj_note,
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        estimated_cost_usd=cost,
        cost_vs_opus_pct=vs_pct,
        cost_vs_opus_usd=vs_usd,
        secondary_options=alternatives,
    )


# ─── 렌더링 ───────────────────────────────────────────────────────────────────

def render_md(r: Recommendation) -> str:
    lines = []
    lines.append(f"# tokensave model_selector 결과")
    lines.append("")
    lines.append(f"**작업:** {r.task}")
    lines.append(f"**quality 입력:** {r.quality_input}")
    lines.append("")
    lines.append(f"## ★ 추천 모델: **{r.recommended_model.upper()}**")
    lines.append("")
    if r.recommended_model == "python":
        lines.append("→ **LLM 호출 0회 — Python 스크립트로 처리**")
    lines.append("")
    lines.append(f"- **근거:** {r.rationale}")
    if r.matched_keyword:
        lines.append(f"- **매칭 키워드:** `{r.matched_keyword}`")
    lines.append(f"- **task_to_model_matrix.md 참조 행:** {r.matrix_row}")
    lines.append(f"- **출처 ID:** {', '.join(r.sources)}")
    if r.quality_adjusted:
        lines.append(f"- **quality 조정:** {r.quality_adjustment_note}")
    lines.append("")
    lines.append("## 예상 비용")
    lines.append("")
    lines.append(f"- 추정 입력 토큰: {r.estimated_input_tokens:,}")
    lines.append(f"- 추정 출력 토큰: {r.estimated_output_tokens:,}")
    lines.append(f"- **추천 모델 비용:** ${r.estimated_cost_usd:.4f}")
    if r.recommended_model != "opus":
        lines.append(f"- **vs Opus 절감:** {r.cost_vs_opus_pct:+.1f}% (${r.cost_vs_opus_usd:.4f})")
    lines.append("")
    lines.append("## 대안 비용 비교 (오름차순)")
    lines.append("")
    lines.append("| 모델 | 비용 (USD) | 차이 vs 추천 |")
    lines.append("|------|----------:|------------:|")
    for alt in r.secondary_options:
        delta_str = f"{alt['delta_vs_recommended_usd']:+.4f}"
        lines.append(f"| {alt['model']} | ${alt['estimated_cost_usd']:.4f} | ${delta_str} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_본 추천은 LLM 호출 0회의 결정적 키워드 매칭 결과다. 더 깊은 판단은 task_to_model_matrix.md 24행 전체와 references/anti_patterns_atlas.md를 참조._")
    return "\n".join(lines)


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="tokensave model_selector — 자연어 작업 → 모델 추천 (결정적, LLM 0회)"
    )
    ap.add_argument("--task", required=True, help="작업 설명 (자연어)")
    ap.add_argument("--tokens", type=int, help="입력 토큰 추정치 (미제공 시 default)")
    ap.add_argument("--quality", choices=["low", "medium", "high"], default="medium")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    args = ap.parse_args()

    r = recommend(args.task, args.tokens, args.quality)

    if args.json:
        print(json.dumps(asdict(r), indent=2, ensure_ascii=False))
    else:
        print(render_md(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
