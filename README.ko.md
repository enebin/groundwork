<p align="center">
  <img src="assets/hero.svg" alt="groundwork — 레포가 일하는 방식을 한 번에 정합니다. Claude Code와 Codex용 플러그인." width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2F6B5A"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-D97757">
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-1F1E1B">
  <img alt="Version 0.1.0" src="https://img.shields.io/badge/version-0.1.0-6E6C66">
</p>

<p align="center"><a href="README.md">English</a> · <b>한국어</b></p>

**groundwork**는 AI 코딩 에이전트가 레포에서 일하는 방식을 정해 주는 Claude Code·Codex 플러그인입니다. 이슈 관리, 워크플로우, 배포 전략, 아키텍처, AI 코드 리뷰, 렌더링 QA까지 정한 뒤, 그 워크플로우를 직접 돌려 줍니다.

`/groundwork:onboarding`은 질문 여덟 개를 던집니다. 각 답은 **번들**입니다. 함께 동작하는 규칙과 스킬을 묶은 것으로, 장단점과 토큰 비용, 그리고 이 레포에 맞는 추천안이 같이 나옵니다. 답은 `GROUNDWORK.md`에 들어갑니다. 꼭 지켜야 할 구현·테스트 규칙은 고른 규칙과 함께 레포의 `AGENTS.md`에, 아키텍처는 `ARCHITECTURE.md`에 들어갑니다. 다른 groundwork 스킬은 모두 이 파일을 읽기 때문에, 같은 플러그인이 어느 레포에서든 그 레포에 맞게 동작합니다.

방금 `git init` 한 무언가에 꽂을 첫 플러그인으로 딱입니다.

- 이번엔 진짜 끝낼 사이드 프로젝트
- 내일 아침 9시 마감인 과제
- "그냥 프로토타입"이라던 해커톤 프로젝트
- 아무도 안 볼 쓰레기 레포 (결국 프로덕션에 올라갑니다)

첫 커밋 전에 설치하면, 레포가 `최종_v2_진짜최종.py` 대신 규칙, 리뷰, QA를 갖추고 시작합니다. 이미 있는 레포도 같은 질문을 받고, 추천은 그 레포에 이미 있는 것을 보고 정합니다.

첫 질문 전에, onboarding이 전체 경로와 단계별 추천을 먼저 보여 줍니다.

<p align="center">
  <img src="assets/overview.svg" alt="빈 레포에서의 onboarding: 첫 질문 전에 모든 단계와 추천 번들을 보여 줍니다." width="100%">
</p>

각 단계에서는 모든 번들을 장단점과 토큰 비용으로 비교합니다.

<p align="center">
  <img src="assets/choices.svg" alt="onboarding 8단계 중 3단계: 워크플로우 번들을 장단점과 토큰 비용으로 비교하고, 추천 번들을 맨 앞에 둡니다." width="100%">
</p>

## 동작 방식

<p align="center">
  <img src="assets/how-it-works.svg" alt="onboarding이 GROUNDWORK.md, AGENTS.md, ARCHITECTURE.md를 쓰고, 모든 groundwork 스킬과 리뷰어 에이전트가 이를 따릅니다." width="100%">
</p>

두 도구는 같은 스킬 세트를 씁니다. 다른 건 매니페스트뿐입니다.

## 설치

Claude Code:

```
/plugin marketplace add enebin/groundwork
/plugin install groundwork@groundwork
```

그다음, 설정할 레포에서:

```
/groundwork:onboarding
```

Claude Code에서 groundwork는 하루에 한 번까지 GitHub에서 새 버전을 확인하고, 릴리스마다 한 번 알려 줍니다. 업데이트하려면 `claude plugin update groundwork@groundwork`를 실행하고 Claude Code를 다시 시작하세요.

선택 사항: [skeptic-review](https://github.com/enebin/skeptic-review)를 설치하면 리뷰 결과를 보기 전에 한 번 더 검증합니다. 없으면 리뷰에 `SkepticReview: OFF`가 표시됩니다.

## onboarding이 묻는 것

| 단계 | 정하는 것 | 선택지 | 새 프로젝트 기본값 |
|---|---|---|---|
| 1 | 언어 | 대화 / 산출물 | 사용자 언어 / 영어 (토큰 절약) |
| 2 | 이슈 트래커 | local files, GitHub Projects, Linear, Jira | local files |
| 3 | 워크플로우 | step-loop, design-first, tdd-loop, flight, quick, review-only | step-loop |
| 4 | 배포 전략 | develop + release, main only; 머지 방식 | develop + release |
| 5 | 아키텍처 | unidirectional, mvvm, layered-service, layered-web, none | 스택에 따라 다름 |
| 6 | 리뷰 | app, sdk, service, product, light; Skeptic 정책 | 프로젝트 종류에 따라 다름 |
| 7 | QA | manual, release, continuous | manual |
| 8 | 그 밖에 | 자유 입력 | 없음 |

첫 질문 전에 이 표가 레포에 맞게 채워진 채로 나오고, 추천을 한 번에 다 받을 수도 있습니다. 웬만하면 그러지 마세요. 여기서 고른 건 오래 갑니다.

테스트는 onboarding 선택지가 아니라 구현의 일부입니다. onboarding은 빌드·테스트 명령과 적용할 검사를 찾아 미리 보여 준 뒤, [기본 구현 규칙](plugins/groundwork/reference/implementation.md)을 `AGENTS.md`에 씁니다.

`eco / normal / sport`는 별도의 전체 노력 프리셋이고, 기본값은 `normal`입니다. reasoning effort 설정처럼 검증 범위, 리뷰 반복 횟수, 적용할 QA 범위를 함께 조절합니다. 모델을 고르지는 않습니다. 실행마다 `--mode`로 바꿀 수 있고, 개별 설정은 나중에 직접 고칠 수 있습니다. 렌더링 QA를 언제 돌릴지는 여전히 QA 번들이 정합니다.

모든 번들의 장단점과 실제로 쓰는 규칙은 [`plugins/groundwork/catalog/`](plugins/groundwork/catalog/)에 있습니다.

## 스킬

| 스킬 | 용도 |
|---|---|
| `onboarding` | `GROUNDWORK.md` 설정 또는 변경 |
| `plan` | 작업을 상위 이슈 하나와 단계 이슈들로 나누기 |
| `step` | 단계 하나 실행: 구현한 뒤, 확인된 🔴/🟠가 없어질 때까지 검증 → 리뷰 → 수정 반복 |
| `boarding`, `door-closing`, `taxiing`, `takeoff`, `landing`, `rejoin` | flight 워크플로우, 이슈 하나씩 |
| `release`, `autoland` | 릴리스 만들기; CI 통과 후 자동 머지 |
| `review-and-fix`, `commit-push` | quick 워크플로우 |
| `review` | 고른 리뷰어를 병렬로 돌리고 결과 합치기 |
| `ux-review` | 고른 최종 사용자 페르소나 기준 사용성 리뷰 (QA 정책에 따라 또는 요청 시) |
| `ui-qa` | 실행 중인 앱에서 테스트가 못 덮는 UI 검사 확인 (QA 정책에 따라 또는 요청 시) |

모든 변경에 돌아가는 코드 리뷰어: `architecture-reviewer`, `code-quality-reviewer`, `security-reviewer`, `writing-reviewer`, `dx-reviewer`, `ux-flow-reviewer`. 마지막 둘은 아무것도 실행하지 않고 코드에서 페르소나의 작업 흐름을 따라갑니다. `ux-flow-reviewer`는 앱의 최종 사용자(불필요한 단계, 빠진 상태, 막다른 길)를, `dx-reviewer`는 라이브러리, HTTP·RPC API, CLI 위에서 개발하는 개발자를 봅니다. 리뷰어마다 플러그인에 일반 체크리스트가 있고, 레포별 검사는 `GROUNDWORK.md`의 `## Review focus: <reviewer>`에서 읽습니다.

화면은 모든 변경마다 스크린샷을 첨부하는 UI 테스트로 확인하고, 구현한 쪽이 그 스크린샷을 직접 열어 봅니다. 별도의 렌더링 QA는 [QA 단계](plugins/groundwork/catalog/qa.md)에서 정합니다. 요청할 때만(`manual`, 기본값), 릴리스 전에(`release`), 또는 구현할 때마다(`continuous`) 돌립니다. UI 커버리지 장부(`docs/ui-coverage.md`)에는 테스트로 확인할 수 없는 것을 적습니다.

웹 도구는 보통 페이지 요소를 바로 찾습니다. iOS 시뮬레이터와 Android 에뮬레이터는 빌드, 설치, 실행, 쓸 수 있는 UI 도구 때문에 더 오래 걸릴 수 있습니다. 스크린샷 기반 웹 QA도 느릴 수 있습니다. 실제 시간과 토큰 사용량은 커버리지, 페르소나, 도구, 재시도에 따라 다르고, 플랫폼별로 정해진 배수는 없습니다.

리뷰 수정은 `fixer` 에이전트가 맡습니다. 새 컨텍스트에서 시작해 확인된 문제를 고치고 관련 테스트를 다시 돌립니다. 그래서 구현 이후 단계 자체의 컨텍스트에는 짧은 보고서만 쌓입니다.

## GROUNDWORK.md

규약은 [`plugins/groundwork/reference/config.md`](plugins/groundwork/reference/config.md)에 있습니다. 키는 추가만 되고, 이름이 바뀌거나 지워지지 않습니다. 구조를 바꿔야 할 때는 스키마 버전을 올리고, onboarding이 파일을 옮겨 줍니다.

`GROUNDWORK.md`와 그것이 쓴 문서를 커밋하세요. 그러면 팀원은 플러그인만 설치하면 되고, onboarding을 다시 돌릴 필요가 없습니다.

## 라이선스

MIT
