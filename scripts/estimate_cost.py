#!/usr/bin/env python3
"""
tokensave — estimate_cost.py

가격 데이터 SSOT 및 토큰/비용 추정 CLI.
다른 tokensave 스크립트 (audit.py, model_selector.py, hook_check.py) 가
가격 상수를 이 모듈에서 import 한다.

표준 라이브러리만 사용. 외부 의존 0.

Usage:
  python3 estimate_cost.py --model opus --input-tokens 50000 --output-tokens 8000
  python3 estimate_cost.py --model sonnet --input-tokens 50000 --output-tokens 8000 \\
                            --cache-hit-ratio 0.9
  python3 estimate_cost.py --compare --input-tokens 50000 --output-tokens 8000
  python3 estimate_cost.py --scenario example-large-pipeline
  python3 estimate_cost.py --scenario example-mixed-model --json

가격 SSOT 출처: Anthropic 공식 docs (A005) — 분류학 sources_external 매핑.
v1 가격은 2026-05-14 기준. 정책 변동 시 본 파일 PRICING 상수만 수정.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional


# ─── 가격 데이터 SSOT (Anthropic 공식 [A005]) ─────────────────────────────────
#
# 단위: USD per 1,000,000 tokens (per MTok)
# 출처: taxonomy.json §headline_facts H5
# 작성 시점: 2026-05-14
# 변경 시: 본 파일 PRICING 상수 한 곳만 수정 → audit.py · model_selector.py ·
#          hook_check.py · references/* 모두 자동 반영

PRICING: dict[str, dict[str, float]] = {
    "opus": {
        "input": 5.00,
        "output": 25.00,
        # 캐시 쓰기/읽기 가격은 input base의 배수 (Anthropic 공식 [A005])
        "cache_write_5min_multiplier": 1.25,
        "cache_write_1hr_multiplier": 2.00,
        "cache_read_multiplier": 0.10,
    },
    "sonnet": {
        "input": 3.00,
        "output": 15.00,
        "cache_write_5min_multiplier": 1.25,
        "cache_write_1hr_multiplier": 2.00,
        "cache_read_multiplier": 0.10,
    },
    "haiku": {
        "input": 1.00,
        "output": 5.00,
        "cache_write_5min_multiplier": 1.25,
        "cache_write_1hr_multiplier": 2.00,
        "cache_read_multiplier": 0.10,
    },
    # Python 대안 비용 = 0 (LLM 호출 0회)
    "python": {
        "input": 0.0,
        "output": 0.0,
        "cache_write_5min_multiplier": 0.0,
        "cache_write_1hr_multiplier": 0.0,
        "cache_read_multiplier": 0.0,
    },
}


# ─── 사전 정의 시나리오 ──────────────────────────────────────────────────────
#
# Generic example scenarios. Add your own harness scenarios here, or load them
# from a JSON file via the --scenario flag.
#
# For a real-world 27-harness example (paper-maker·ainews-daily·policyblind etc.)
# see examples/personal_baseline.md §cost-scenarios.
#
# Estimation method: avg SKILL.md chars + agent_size × team_size + call_count.
# These are static estimates — calibrate against your actual usage logs.

SCENARIOS: dict[str, dict] = {
    # Example: a large multi-phase document pipeline (15 agents, all opus)
    "example-large-pipeline": {
        "agents": 15,
        "model": "opus",
        "input_tokens_per_call": 12000,
        "output_tokens_per_call": 4000,
        "calls_estimated": 40,
        "notes": "Example: 15-agent pipeline, 8 phases × 5 calls/phase, worst case",
    },
    # Example: a mixed-model meta harness (sonnet 3 + opus 2)
    "example-mixed-model": {
        "agents": 5,
        "model": "mixed",  # sonnet_calls + opus_calls split below
        "input_tokens_per_call": 4000,
        "output_tokens_per_call": 1500,
        "calls_estimated": 12,
        "notes": "Example: mixed model — sonnet 3 + opus 2, single build",
        "mixed_breakdown": {"sonnet_calls": 7, "opus_calls": 5},
    },
    # Add your own harness scenarios below:
    # "your-harness": {
    #     "agents": N,
    #     "model": "opus",   # or "sonnet", "haiku", "mixed"
    #     "input_tokens_per_call": ...,
    #     "output_tokens_per_call": ...,
    #     "calls_estimated": ...,
    #     "notes": "...",
    # },
}


# ─── 데이터 클래스 ────────────────────────────────────────────────────────────

@dataclass
class CostEstimate:
    model: str
    input_tokens: int
    output_tokens: int
    cache_hit_ratio: float
    cache_ttl: str  # "5min" or "1hr"
    input_cost_usd: float
    output_cost_usd: float
    cache_read_cost_usd: float
    cache_write_cost_usd: float
    total_cost_usd: float
    notes: str = ""


@dataclass
class ComparisonResult:
    base_model: str
    input_tokens: int
    output_tokens: int
    estimates: dict[str, dict]  # model → cost breakdown
    savings_vs_opus: dict[str, dict]  # model → {pct, usd_saved}


# ─── 핵심 함수 ────────────────────────────────────────────────────────────────

def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_hit_ratio: float = 0.0,
    cache_ttl: str = "5min",
) -> CostEstimate:
    """단일 호출 비용 추정.

    cache_hit_ratio: 0.0~1.0. input_tokens 중 캐시 hit 비율.
                     hit된 토큰은 cache_read_multiplier × base input price.
                     miss된 토큰 중 일부가 cache_write로 적재 (단순화: hit_ratio > 0 이면 미스토큰 전체 캐시 적재).
    cache_ttl: "5min" 또는 "1hr".
    """
    if model not in PRICING:
        raise ValueError(f"Unknown model: {model}. Choices: {list(PRICING)}")
    p = PRICING[model]

    # python 경로는 비용 0
    if model == "python":
        return CostEstimate(
            model="python",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_hit_ratio=0.0,
            cache_ttl="N/A",
            input_cost_usd=0.0,
            output_cost_usd=0.0,
            cache_read_cost_usd=0.0,
            cache_write_cost_usd=0.0,
            total_cost_usd=0.0,
            notes="Python 분기 — LLM 호출 0회",
        )

    # 토큰을 MTok 단위로 환산
    input_mtok = input_tokens / 1_000_000
    output_mtok = output_tokens / 1_000_000

    if cache_hit_ratio <= 0:
        input_cost = input_mtok * p["input"]
        output_cost = output_mtok * p["output"]
        cache_read_cost = 0.0
        cache_write_cost = 0.0
    else:
        # 캐시 hit 토큰: read multiplier 적용
        hit_tokens = input_tokens * cache_hit_ratio
        miss_tokens = input_tokens * (1 - cache_hit_ratio)
        hit_mtok = hit_tokens / 1_000_000
        miss_mtok = miss_tokens / 1_000_000

        cache_read_cost = hit_mtok * p["input"] * p["cache_read_multiplier"]
        input_cost = miss_mtok * p["input"]
        output_cost = output_mtok * p["output"]

        # 캐시 write: miss 토큰 일부가 적재됐다고 가정 — 단순화: hit_ratio > 0 이면
        # 미스 토큰 50%가 cache_write 비용으로 한 번 청구 (실측은 사용 패턴에 좌우)
        write_mult_key = "cache_write_5min_multiplier" if cache_ttl == "5min" else "cache_write_1hr_multiplier"
        write_mtok = miss_mtok * 0.5
        cache_write_cost = write_mtok * p["input"] * p[write_mult_key]

    total = input_cost + output_cost + cache_read_cost + cache_write_cost
    return CostEstimate(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_hit_ratio=cache_hit_ratio,
        cache_ttl=cache_ttl if cache_hit_ratio > 0 else "N/A",
        input_cost_usd=round(input_cost, 4),
        output_cost_usd=round(output_cost, 4),
        cache_read_cost_usd=round(cache_read_cost, 4),
        cache_write_cost_usd=round(cache_write_cost, 4),
        total_cost_usd=round(total, 4),
    )


def compare_all_models(
    input_tokens: int,
    output_tokens: int,
    cache_hit_ratio: float = 0.0,
    cache_ttl: str = "5min",
) -> ComparisonResult:
    """Opus·Sonnet·Haiku·Python 4가지 옵션의 비용 비교."""
    models = ["opus", "sonnet", "haiku", "python"]
    estimates: dict[str, dict] = {}
    opus_total = None

    for m in models:
        e = estimate_cost(m, input_tokens, output_tokens, cache_hit_ratio, cache_ttl)
        estimates[m] = asdict(e)
        if m == "opus":
            opus_total = e.total_cost_usd

    savings: dict[str, dict] = {}
    if opus_total and opus_total > 0:
        for m in models:
            tot = estimates[m]["total_cost_usd"]
            usd_saved = round(opus_total - tot, 4)
            pct = round((opus_total - tot) / opus_total * 100, 1) if opus_total else 0
            savings[m] = {"pct_saved_vs_opus": pct, "usd_saved_vs_opus": usd_saved}

    return ComparisonResult(
        base_model="opus",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimates=estimates,
        savings_vs_opus=savings,
    )


def estimate_scenario(name: str, cache_hit_ratio: float = 0.0) -> dict:
    """사전 정의 하네스 시나리오 비용 추정.

    mixed model 시나리오(tokensave-self 같은)는 sonnet_calls + opus_calls 분리 계산.
    """
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}. Choices: {list(SCENARIOS)}")
    sc = SCENARIOS[name]
    calls = sc["calls_estimated"]
    inp_per = sc["input_tokens_per_call"]
    out_per = sc["output_tokens_per_call"]

    if sc["model"] == "mixed":
        # mixed_breakdown 사용
        breakdown = sc.get("mixed_breakdown", {})
        sonnet_calls = breakdown.get("sonnet_calls", 0)
        opus_calls = breakdown.get("opus_calls", 0)
        sonnet_est = estimate_cost("sonnet", inp_per * sonnet_calls, out_per * sonnet_calls, cache_hit_ratio)
        opus_est = estimate_cost("opus", inp_per * opus_calls, out_per * opus_calls, cache_hit_ratio)
        total = sonnet_est.total_cost_usd + opus_est.total_cost_usd
        # 비교: 만약 동일 작업을 전부 opus로 했다면?
        all_opus = estimate_cost("opus", inp_per * calls, out_per * calls, cache_hit_ratio)
        # 만약 전부 sonnet으로 했다면?
        all_sonnet = estimate_cost("sonnet", inp_per * calls, out_per * calls, cache_hit_ratio)
        return {
            "scenario": name,
            "model": "mixed",
            "agents": sc["agents"],
            "calls_estimated": calls,
            "input_tokens_total": inp_per * calls,
            "output_tokens_total": out_per * calls,
            "mixed_cost_usd": round(total, 4),
            "all_opus_cost_usd": all_opus.total_cost_usd,
            "all_sonnet_cost_usd": all_sonnet.total_cost_usd,
            "savings_vs_all_opus_pct": round((all_opus.total_cost_usd - total) / all_opus.total_cost_usd * 100, 1)
                if all_opus.total_cost_usd else 0,
            "breakdown": {
                "sonnet": asdict(sonnet_est),
                "opus": asdict(opus_est),
            },
            "notes": sc["notes"],
        }
    else:
        # 단일 모델
        total_inp = inp_per * calls
        total_out = out_per * calls
        primary = estimate_cost(sc["model"], total_inp, total_out, cache_hit_ratio)

        # 비교 alternatives
        sonnet_alt = estimate_cost("sonnet", total_inp, total_out, cache_hit_ratio)
        haiku_alt = estimate_cost("haiku", total_inp, total_out, cache_hit_ratio)

        return {
            "scenario": name,
            "model": sc["model"],
            "agents": sc["agents"],
            "calls_estimated": calls,
            "input_tokens_total": total_inp,
            "output_tokens_total": total_out,
            "primary_cost_usd": primary.total_cost_usd,
            "if_sonnet_cost_usd": sonnet_alt.total_cost_usd,
            "if_haiku_cost_usd": haiku_alt.total_cost_usd,
            "sonnet_savings_pct": round((primary.total_cost_usd - sonnet_alt.total_cost_usd)
                                         / primary.total_cost_usd * 100, 1) if primary.total_cost_usd else 0,
            "haiku_savings_pct": round((primary.total_cost_usd - haiku_alt.total_cost_usd)
                                        / primary.total_cost_usd * 100, 1) if primary.total_cost_usd else 0,
            "primary_breakdown": asdict(primary),
            "notes": sc["notes"],
        }


# ─── 렌더링 ───────────────────────────────────────────────────────────────────

def render_estimate_md(e: CostEstimate) -> str:
    lines = []
    lines.append(f"## 비용 추정 — {e.model}")
    lines.append("")
    lines.append(f"- 입력 토큰: **{e.input_tokens:,}** ({e.input_tokens/1_000_000:.4f} MTok)")
    lines.append(f"- 출력 토큰: **{e.output_tokens:,}** ({e.output_tokens/1_000_000:.4f} MTok)")
    if e.cache_hit_ratio > 0:
        lines.append(f"- 캐시 hit ratio: {e.cache_hit_ratio:.0%} (TTL {e.cache_ttl})")
    lines.append("")
    lines.append("| 항목 | 비용 (USD) |")
    lines.append("|------|----------:|")
    lines.append(f"| Input (miss) | ${e.input_cost_usd:.4f} |")
    lines.append(f"| Output | ${e.output_cost_usd:.4f} |")
    if e.cache_read_cost_usd > 0:
        lines.append(f"| Cache read | ${e.cache_read_cost_usd:.4f} |")
    if e.cache_write_cost_usd > 0:
        lines.append(f"| Cache write | ${e.cache_write_cost_usd:.4f} |")
    lines.append(f"| **합계** | **${e.total_cost_usd:.4f}** |")
    if e.notes:
        lines.append("")
        lines.append(f"_{e.notes}_")
    return "\n".join(lines)


def render_comparison_md(c: ComparisonResult) -> str:
    lines = []
    lines.append("## 모델별 비용 비교")
    lines.append("")
    lines.append(f"- 입력 토큰: {c.input_tokens:,}")
    lines.append(f"- 출력 토큰: {c.output_tokens:,}")
    lines.append("")
    lines.append("| 모델 | 총 비용 (USD) | vs Opus 절감 (%) | vs Opus 절감 (USD) |")
    lines.append("|------|-------------:|----------------:|------------------:|")
    for m in ["opus", "sonnet", "haiku", "python"]:
        tot = c.estimates[m]["total_cost_usd"]
        sv = c.savings_vs_opus.get(m, {})
        pct = sv.get("pct_saved_vs_opus", 0)
        usd = sv.get("usd_saved_vs_opus", 0)
        lines.append(f"| {m} | ${tot:.4f} | {pct:+.1f}% | ${usd:.4f} |")
    lines.append("")
    lines.append("**핵심 룰:** 작업이 Python으로 표현 가능하면 무료. 자연어 정형/표준 코드면 Sonnet(-40%). 복잡 reasoning만 Opus.")
    return "\n".join(lines)


def render_scenario_md(d: dict) -> str:
    lines = []
    lines.append(f"## 시나리오 — {d['scenario']}")
    lines.append("")
    lines.append(f"- 모델: **{d['model']}**")
    lines.append(f"- 에이전트 수: {d['agents']}")
    lines.append(f"- 추정 호출 횟수: {d['calls_estimated']}")
    lines.append(f"- 총 입력 토큰: {d['input_tokens_total']:,}")
    lines.append(f"- 총 출력 토큰: {d['output_tokens_total']:,}")
    lines.append("")
    if d["model"] == "mixed":
        lines.append(f"- **mixed 실측 비용:** ${d['mixed_cost_usd']:.2f}")
        lines.append(f"- 만약 전부 Opus였다면: ${d['all_opus_cost_usd']:.2f}")
        lines.append(f"- 만약 전부 Sonnet이었다면: ${d['all_sonnet_cost_usd']:.2f}")
        lines.append(f"- **vs all-opus 절감: {d['savings_vs_all_opus_pct']:.1f}%**")
    else:
        lines.append(f"- **현재 ({d['model']}) 비용:** ${d['primary_cost_usd']:.2f}")
        lines.append(f"- 만약 Sonnet 사용: ${d['if_sonnet_cost_usd']:.2f} (절감 {d['sonnet_savings_pct']:.1f}%)")
        lines.append(f"- 만약 Haiku 사용: ${d['if_haiku_cost_usd']:.2f} (절감 {d['haiku_savings_pct']:.1f}%)")
    lines.append("")
    lines.append(f"_{d['notes']}_")
    return "\n".join(lines)


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="tokensave estimate_cost — 모델별·시나리오별 토큰 비용 추정. "
                    "가격 SSOT (다른 tokensave 스크립트가 import 함)."
    )
    ap.add_argument("--model", choices=list(PRICING),
                    help="모델 선택 (opus/sonnet/haiku/python)")
    ap.add_argument("--input-tokens", type=int, default=0)
    ap.add_argument("--output-tokens", type=int, default=0)
    ap.add_argument("--cache-hit-ratio", type=float, default=0.0,
                    help="0.0~1.0. 캐시 hit 비율 적용")
    ap.add_argument("--cache-ttl", choices=["5min", "1hr"], default="5min")
    ap.add_argument("--compare", action="store_true",
                    help="Opus·Sonnet·Haiku·Python 4가지 모두 비교")
    ap.add_argument("--scenario",
                    help="사전 정의 하네스 시나리오 (예: example-large-pipeline)")
    ap.add_argument("--list-scenarios", action="store_true",
                    help="사전 정의 시나리오 목록 출력")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    args = ap.parse_args()

    # 시나리오 목록 모드
    if args.list_scenarios:
        if args.json:
            print(json.dumps(list(SCENARIOS.keys()), ensure_ascii=False))
        else:
            print("# 사전 정의 시나리오")
            for name, sc in SCENARIOS.items():
                print(f"- **{name}** — {sc['agents']} agents · {sc['model']} · {sc['notes']}")
        return 0

    # 시나리오 모드
    if args.scenario:
        name = args.scenario.split("=")[-1] if "=" in args.scenario else args.scenario
        try:
            d = estimate_scenario(name, args.cache_hit_ratio)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(d, indent=2, ensure_ascii=False))
        else:
            print(render_scenario_md(d))
        return 0

    # 비교 모드
    if args.compare:
        if not args.input_tokens:
            print("error: --compare requires --input-tokens", file=sys.stderr)
            return 2
        c = compare_all_models(args.input_tokens, args.output_tokens,
                               args.cache_hit_ratio, args.cache_ttl)
        if args.json:
            print(json.dumps(asdict(c), indent=2, ensure_ascii=False))
        else:
            print(render_comparison_md(c))
        return 0

    # 단일 모델 추정 모드
    if not args.model:
        print("error: --model required (or use --compare / --scenario / --list-scenarios)",
              file=sys.stderr)
        ap.print_help(sys.stderr)
        return 2
    if not args.input_tokens:
        print("error: --input-tokens required", file=sys.stderr)
        return 2

    e = estimate_cost(args.model, args.input_tokens, args.output_tokens,
                      args.cache_hit_ratio, args.cache_ttl)
    if args.json:
        print(json.dumps(asdict(e), indent=2, ensure_ascii=False))
    else:
        print(render_estimate_md(e))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
