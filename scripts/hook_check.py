#!/usr/bin/env python3
"""
tokensave — hook_check.py

settings.json hook으로 등록 가능한 런타임 가드.
PreToolUse (Agent 호출 직전 모델 적정성 경고) + UserPromptSubmit (LLM-overuse
키워드 자동 탐지) 두 종류 지원.

출력: stderr에 경고만, exit 0 (블로킹 안 함 — 가이드 전용).

Usage:
  python3 hook_check.py pretooluse       # Claude Code가 stdin으로 payload 전달
  python3 hook_check.py userprompt
  python3 hook_check.py --self-test      # 샘플 payload로 자체 테스트

settings.json 예제:
{
  "hooks": {
    "PreToolUse": [{"matcher": "Task",
      "hooks": [{"type": "command",
        "command": "python3 /path/to/tokensave/scripts/hook_check.py pretooluse"}]}],
    "UserPromptSubmit": [{
      "hooks": [{"type": "command",
        "command": "python3 /path/to/tokensave/scripts/hook_check.py userprompt"}]}]
  }
}

표준 라이브러리만.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# model_selector import (가능하면)
sys.path.insert(0, str(Path(__file__).parent.resolve()))
try:
    from model_selector import (
        DETERMINISTIC_KEYWORDS, OPUS_KEYWORDS, HAIKU_KEYWORDS,
        SONNET_KEYWORDS, recommend,
    )
    HAS_MODEL_SELECTOR = True
except ImportError:
    HAS_MODEL_SELECTOR = False


# ─── 룰 1: PreToolUse Task — Agent spawn 직전 ────────────────────────────────

def check_pretooluse(payload: dict) -> list[str]:
    """Claude Code PreToolUse hook payload 분석.

    Task tool payload 예시 (subset):
      {"tool_name": "Task", "tool_input": {"subagent_type": "...",
       "description": "...", "prompt": "..."}}
    """
    warnings = []
    tool_name = payload.get("tool_name", "")
    if tool_name != "Task":
        return warnings  # Task 아니면 통과

    tool_input = payload.get("tool_input", {})
    desc = str(tool_input.get("description", "")) + " " + str(tool_input.get("prompt", ""))
    subagent_type = tool_input.get("subagent_type", "")

    # 1. 결정적 keyword 검출
    if HAS_MODEL_SELECTOR:
        for pattern, reason, matrix_ref in DETERMINISTIC_KEYWORDS:
            if re.search(pattern, desc, re.IGNORECASE):
                warnings.append(
                    f"[tokensave PRE-FLIGHT] 결정적 keyword 감지: '{reason}' (matrix {matrix_ref}). "
                    f"Python 분기 검토. 확신하면 진행."
                )
                break

    # 2. opus 명시 + 작은 작업 검출
    text_lower = desc.lower()
    if "opus" in text_lower and any(kw in text_lower for kw in
                                     ["grep", "탐색", "카운트", "boilerplate", "read-only", "짧은"]):
        warnings.append(
            "[tokensave PRE-FLIGHT] opus + 탐색/짧은 작업 — Haiku 가능 [task_to_model_matrix #2·22]"
        )

    # 3. 5+ agent fan-out 검출 (description에 다중 spawn 의도)
    multi_spawn_signals = re.findall(r"(\d+)\s*(?:인|명|agent)", desc)
    if multi_spawn_signals:
        for n_str in multi_spawn_signals:
            try:
                n = int(n_str)
                if n >= 5:
                    warnings.append(
                        f"[tokensave PRE-FLIGHT] {n}+ agent fan-out — "
                        "단일 세션 가능성 점검? [A003 7× cost]"
                    )
                    break
            except ValueError:
                pass

    # 4. 결정 트리: 모델 추천 자동 호출 (가능 시)
    if HAS_MODEL_SELECTOR and desc.strip() and len(desc) > 30:
        try:
            r = recommend(desc[:500])  # 너무 길면 자름
            if r.recommended_model == "python":
                warnings.append(
                    f"[tokensave model_selector] 이 작업은 Python으로 처리 가능 "
                    f"(matrix {r.matrix_row}, {r.rationale}). 절감 -100% (LLM 0회)."
                )
            elif r.recommended_model in ("haiku", "sonnet") and "opus" in str(subagent_type).lower():
                warnings.append(
                    f"[tokensave model_selector] 추천 {r.recommended_model}, "
                    f"vs Opus 절감 {r.cost_vs_opus_pct:+.1f}% (matrix {r.matrix_row})"
                )
        except Exception:
            pass

    return warnings


# ─── 룰 2: UserPromptSubmit — 사용자 입력 LLM-overuse 키워드 탐지 ───────────

OVERUSE_KEYWORDS_PATTERNS = [
    (r"\b모두\s*opus\b|\b전부\s*opus\b|\b전체\s*opus\b",
     "모든 agent을 opus로 — anti-pattern [C1.1, 사용자 99.0% 안 됨]"),
    (r"\b5\s*인\s*팀\b|\b10\s*인\s*팀\b|\b15\s*인\s*팀\b",
     "5+ 인 팀 — 7×~15× cost multiplier [C3.1]. 진입 전 단일 세션 가능성 자문"),
    (r"\b에이전트\s*팀\b.*\b추가\b|\b신규\s*하네스\b",
     "신규 하네스 — 기존 하네스로 충분한가? spawn 20K~85K 회수 가능한가? [C6.1]"),
    (r"\b모두\s*병렬\b|\b전체\s*병렬\b|\b무제한\s*병렬\b",
     "병렬 무제한 — fanout cap (3~5) 권고 [C3.2]"),
    (r"\b1시간\b.*\b세션\b|\b장시간\s*세션\b",
     "Kitchen-sink session 위험 [C4.4]. /clear, /compact 60% 전"),
    (r"\bopus\b.*\b(grep|탐색|파일\s*카운트|boilerplate)\b",
     "Opus + 탐색/카운트 — Haiku 가능 [task #2·22]"),
    (r"\bregex\b.*\bopus\b|\bopus\b.*\bregex\b",
     "Opus + regex — Python 분기 우선 [C2.1 HD-003, S-C09]"),
    (r"\bBibTeX\b.*\bopus\b|\b인용\s*정규화\b.*\bopus\b",
     "Opus + BibTeX/인용 정규화 — pybtex 우선 [C2.2]"),
]


def check_userprompt(payload: dict) -> list[str]:
    """UserPromptSubmit hook payload 분석.

    Claude Code payload 예시:
      {"prompt": "사용자 입력 텍스트..."}
    """
    warnings = []
    prompt = str(payload.get("prompt", "")) or str(payload.get("user_prompt", ""))
    if not prompt:
        return warnings

    for pattern, msg in OVERUSE_KEYWORDS_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            warnings.append(f"[tokensave OVERUSE] {msg}")

    # 결정적 작업 keyword 탐지
    if HAS_MODEL_SELECTOR:
        for pattern, reason, matrix_ref in DETERMINISTIC_KEYWORDS:
            if re.search(pattern, prompt, re.IGNORECASE):
                warnings.append(
                    f"[tokensave OVERUSE] '{reason}' — Python 분기 권고 "
                    f"(matrix {matrix_ref})"
                )
                break

    # 컨텍스트 비대 신호
    if len(prompt) > 30000:
        warnings.append(
            f"[tokensave OVERUSE] 사용자 입력 {len(prompt):,}자 — "
            "컨텍스트 폭주 위험. 파일 분리 + Read tool 사용 권고 [C4.4]"
        )

    return warnings


# ─── self-test ───────────────────────────────────────────────────────────────

SAMPLE_PRETOOLUSE = {
    "tool_name": "Task",
    "tool_input": {
        "subagent_type": "pm-citation-formatter (opus)",
        "description": "BibTeX 생성하고 cross-reference 정규화",
        "prompt": "verbatim 1:1 매핑으로 인용 형식 변환"
    },
}

SAMPLE_USERPROMPT = {
    "prompt": "5인 팀 만들어서 모두 opus로 BibTeX 생성하고 grep으로 결정적 변환 작업해줘",
}


def self_test() -> int:
    print("=== Self Test 1: PreToolUse with deterministic keyword ===", file=sys.stderr)
    for w in check_pretooluse(SAMPLE_PRETOOLUSE):
        print(w, file=sys.stderr)
    print("", file=sys.stderr)
    print("=== Self Test 2: UserPromptSubmit with overuse signals ===", file=sys.stderr)
    for w in check_userprompt(SAMPLE_USERPROMPT):
        print(w, file=sys.stderr)
    return 0


# ─── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="tokensave hook_check — PreToolUse / UserPromptSubmit guard. "
                    "Reads payload from stdin, emits warnings to stderr, exit 0."
    )
    ap.add_argument("mode", choices=["pretooluse", "userprompt", "self-test"])
    args = ap.parse_args()

    if args.mode == "self-test":
        return self_test()

    # stdin에서 JSON payload 읽기
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # 비-JSON이면 plain 텍스트로 취급
        payload = {"prompt": raw}
    except Exception:
        payload = {}

    if args.mode == "pretooluse":
        warnings = check_pretooluse(payload)
    else:
        warnings = check_userprompt(payload)

    for w in warnings:
        print(w, file=sys.stderr)

    return 0  # 항상 통과 — 가이드만


if __name__ == "__main__":
    raise SystemExit(main())
