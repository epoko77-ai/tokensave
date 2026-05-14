# Hook Examples — settings.json 등록 예제

생성: 2026-05-14 · 출처: Anthropic Claude Code hook 공식 + `scripts/hook_check.py` 자체

## MODE 4 개요

Claude Code의 hook 시스템은 settings.json에 정의된 외부 명령을 특정 이벤트마다 실행한다. tokensave는 두 종류의 hook을 제공:

1. **PreToolUse (Agent 호출 직전)** — Task tool payload에서 결정적 keyword·opus 남용·5+ fan-out 감지 → stderr 경고.
2. **UserPromptSubmit (사용자 입력 시)** — overuse keyword·결정적 작업·컨텍스트 비대 감지 → stderr 경고.

**핵심 원칙:** stderr 경고만, exit 0 (블로킹 ❌). 사용자가 결정. tokensave는 가이드 역할.

## 1. 설치 위치

### Option A: 사용자 전역 (~/.claude/settings.json)

모든 Claude Code 세션에서 활성화. 권고.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/tokensave/scripts/hook_check.py pretooluse"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/tokensave/scripts/hook_check.py userprompt"
          }
        ]
      }
    ]
  }
}
```

### Option B: 프로젝트별 (.claude/settings.json)

특정 하네스 프로젝트에서만 활성화. 사용자 베이스라인 측정 단계에 권고.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/tokensave/scripts/hook_check.py pretooluse"
          }
        ]
      }
    ]
  }
}
```

## 2. 검출되는 패턴 (PreToolUse Task)

`hook_check.py pretooluse` 가 검출:

| 패턴 | 검출 keyword | 출력 |
|------|-------------|------|
| 결정적 keyword + opus | `regex`, `verbatim`, `BibTeX`, `CSV→JSON`, ... | `[tokensave PRE-FLIGHT] 결정적 keyword 감지: '<reason>' (matrix #N). Python 분기 검토.` |
| opus + 작은 작업 | `opus` + `grep`/`탐색`/`boilerplate` | `[tokensave PRE-FLIGHT] opus + 탐색/짧은 작업 — Haiku 가능 [task_to_model_matrix #2·22]` |
| 5+ agent fan-out | description에 "5인", "8인", "10명" | `[tokensave PRE-FLIGHT] N+ agent fan-out — 단일 세션 가능성 점검? [A003 7× cost]` |
| model_selector 추천 | 자동 호출 결과 | `[tokensave model_selector] 추천 <model>, vs Opus 절감 N%` |

## 3. 검출되는 패턴 (UserPromptSubmit)

`hook_check.py userprompt` 가 검출:

| 패턴 | 검출 정규식 | 출력 |
|------|------------|------|
| All-opus | `모두\s*opus`, `전부\s*opus` | `[tokensave OVERUSE] 모든 agent을 opus로 — anti-pattern [C1.1, 사용자 99.0% 안 됨]` |
| 5+ 팀 | `5\s*인\s*팀`, `10\s*인\s*팀` | `5+ 인 팀 — 7×~15× cost multiplier [C3.1]. 진입 전 단일 세션 자문` |
| 신규 하네스 | `신규\s*하네스`, `에이전트\s*팀.*추가` | `기존 하네스로 충분한가? spawn 회수 가능? [C6.1]` |
| 병렬 무제한 | `모두\s*병렬`, `무제한\s*병렬` | `병렬 무제한 — fanout cap (3~5) 권고 [C3.2]` |
| 장시간 세션 | `1시간\s*세션`, `장시간\s*세션` | `Kitchen-sink session 위험 [C4.4]` |
| opus + 결정적 | `opus.*regex`, `BibTeX.*opus` | `Python 분기 우선 [C2.1 HD-003, S-C09]` |
| 컨텍스트 비대 | prompt > 30000자 | `사용자 입력 N자 — 컨텍스트 폭주 위험 [C4.4]` |

## 4. 자체 테스트

설치 전 자체 테스트:

```bash
# Self-test (샘플 payload)
python3 /path/to/tokensave/scripts/hook_check.py self-test

# 실제 payload 흐름 시뮬레이션 (stdin)
echo '{"tool_name":"Task","tool_input":{"description":"BibTeX 생성"}}' | \
  python3 /path/to/tokensave/scripts/hook_check.py pretooluse

# UserPromptSubmit 시뮬레이션
echo '{"prompt":"5인 팀 만들어서 opus로 regex 작업"}' | \
  python3 /path/to/tokensave/scripts/hook_check.py userprompt
```

## 5. 비활성화 / 일시 정지

settings.json에서 해당 hook 블록 삭제 또는 주석 처리 (JSON은 주석 미지원 → 별도 파일로 백업 후 삭제).

또는 일시 비활성화:

```bash
# Claude Code 세션 환경변수
export TOKENSAVE_HOOK_DISABLE=1
```

(이 기능을 hook_check.py에 추가하려면 `os.environ.get("TOKENSAVE_HOOK_DISABLE")` 체크 후 즉시 return.)

## 6. 메타 원칙 (hook 자체도 토큰 절약)

hook 실행 자체가 토큰 낭비가 되어선 안 된다:

- **LLM 호출 0회** — hook_check.py는 정규식 매칭만. 외부 API 호출 없음.
- **stderr 경고만** — 메시지 짧게 (각 ≤ 120자), 사용자가 한눈에 파악.
- **exit 0** — 블로킹 시 사용자 흐름 끊김 = UX 망가짐 + 우회 비용.
- **빠른 실행** — `python3 hook_check.py userprompt` 1초 미만 (정규식만이므로).

## 7. 향후 확장 후보

- **PreToolUse Bash**: Bash 도구 호출 시 raw log 출력 크기 경고 (C4.2).
- **PostToolUse**: Read 결과 크기 경고 (C7.1 — 전체 Read 대신 offset/limit).
- **SessionStart**: 모델 고정 확인 (C1.3 — 캐시 무효화 회피).
- **PreCompact**: /compact 직전 SKILL.md/CLAUDE.md 비대 점검 (C4.1/4.5).

## 8. 디버깅

hook 실행 안 되거나 에러 시:

```bash
# 1. Python 경로 확인
which python3

# 2. 스크립트 실행 권한
chmod +x /path/to/tokensave/scripts/hook_check.py

# 3. 의존 모듈 확인
python3 -c "from /path/to/tokensave/scripts/model_selector import recommend"

# 4. Claude Code hook 로그
# settings.json에 "hooks": [...] 등록 후 Claude Code 재시작 필요
```

## 인접 참고

- `scripts/hook_check.py` — 본 hook 구현체 (300줄)
- `scripts/model_selector.py` — hook이 의존하는 결정 트리
- `references/anti_patterns_atlas.md` — hook이 검출하는 패턴 카드 29개
- Anthropic 공식: `docs.anthropic.com/en/docs/claude-code/hooks`
