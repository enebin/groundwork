<p align="center">
  <img src="assets/hero.svg" alt="groundwork — 레포가 일하는 방식을 한 번에 정합니다. Claude Code와 Codex용 플러그인." width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2F6B5A"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-D97757">
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-1F1E1B">
  <img alt="Version 0.1.2" src="https://img.shields.io/badge/version-0.1.2-6E6C66">
</p>

<p align="center"><a href="README.md">English</a> · <b>한국어</b></p>

**groundwork**는 이 레포에서 AI 코딩 에이전트를 어떻게 굴릴지 세팅해 주는 Claude Code·Codex 플러그인입니다. 이슈 관리, 워크플로우, 브랜치·배포 전략, 아키텍처, AI 코드 리뷰, 화면 QA까지 한 번에 정하고 그 흐름대로 작업이 돌아가게 만듭니다.

`/groundwork:onboarding`을 실행하면 여덟 가지를 물어봅니다. 각 선택지는 **번들** 단위입니다. 서로 맞물려 돌아가는 규칙과 스킬을 묶어 둔 세트로, 장단점과 토큰 비용 그리고 현재 레포에 맞는 추천안이 함께 제시됩니다. 선택한 내용은 `GROUNDWORK.md`에 저장됩니다. 필수로 지켜야 할 구현·테스트 규칙은 선택한 규칙과 함께 `AGENTS.md`에, 아키텍처 규칙은 `ARCHITECTURE.md`에 들어갑니다. 나머지 groundwork 스킬들은 전부 이 파일을 읽고 움직이기 때문에 어떤 레포에 가져다 놔도 그 레포 규칙에 맞춰 돌아갑니다.

갓 `git init` 한 레포에 가장 좋습니다.

- 이제 막 시작한 사이드 프로젝트
- 내일 아침 9시 제출인 과제
- "일단 프로토타입만 빠르게"라던 해커톤 프로젝트
- 나만 볼 거라 대충 판 레포

첫 커밋 올리기 전에 깔아 두면 `최종_v2_진짜최종.py`부터 생기는 대신 규칙과 코드 리뷰, QA가 잡힌 상태로 시작할 수 있습니다. 이미 굴러가고 있는 레포에서 실행해도 똑같이 물어보며 기존 코드와 설정을 읽고 거기에 맞는 추천안을 골라 줍니다.

질문을 시작하기 전에 전체 단계와 추천 구성을 한눈에 먼저 보여 줍니다.

<p align="center">
  <img src="assets/overview.svg" alt="빈 레포에서의 onboarding: 첫 질문 전에 모든 단계와 추천 번들을 보여 줍니다." width="100%">
</p>

각 단계에서는 선택지별 장단점과 토큰 소모량을 비교해 볼 수 있습니다.

<p align="center">
  <img src="assets/choices.svg" alt="onboarding 8단계 중 3단계: 워크플로우 번들을 장단점과 토큰 비용으로 비교하고 추천 번들을 맨 앞에 둡니다." width="100%">
</p>

## 동작 방식

<p align="center">
  <img src="assets/how-it-works.svg" alt="onboarding이 GROUNDWORK.md, AGENTS.md, ARCHITECTURE.md를 쓰고 모든 groundwork 스킬과 리뷰어 에이전트가 이를 따릅니다." width="100%">
</p>

Claude Code와 Codex 모두 같은 스킬 세트를 공유하며 매니페스트만 다릅니다.

## 설치

Claude Code:

```
/plugin marketplace add enebin/groundwork
/plugin install groundwork@groundwork
```

세팅할 레포에서 아래 명령을 실행합니다:

```
/groundwork:onboarding
```

Claude Code에서는 하루 최대 한 번 GitHub의 새 버전을 확인하고 새 릴리스가 나오면 한 번 알려 줍니다. 업데이트할 때는 `claude plugin update groundwork@groundwork`를 실행한 뒤 Claude Code를 재시작하면 됩니다.

선택 사항: [skeptic-review](https://github.com/enebin/skeptic-review)를 함께 설치하면 리뷰어가 잡은 내용을 사용자에게 보여 주기 전에 실제로 맞는 지적일지 한 번 더 걸러 줍니다. 설치하지 않으면 리뷰 결과에 `SkepticReview: OFF`로 표시됩니다.

## onboarding에서 정하는 것

| 단계 | 항목 | 선택지 | 새 프로젝트 기본값 |
|---|---|---|---|
| 1 | 언어 | 대화 언어 / 산출물 언어 | 사용자 언어 / 영어 (토큰 절약) |
| 2 | 이슈 트래커 | local files, GitHub Projects, Linear, Jira | local files |
| 3 | 워크플로우 | step-loop, design-first, tdd-loop, quick, review-only; 이슈별 worktree | step-loop, 이슈별 worktree |
| 4 | 배포 전략 | develop + release, main only; 머지 방식 | develop + release |
| 5 | 아키텍처 | unidirectional, mvvm, layered-service, layered-web, none | 기술 스택에 따라 추천 |
| 6 | 리뷰 | app, sdk, service, product, light | 프로젝트 성격에 따라 추천 |
| 7 | 화면 검사 | UX: 매 PR, 릴리스 전, 수동; 코드 기반 또는 실제 앱. QA: 매 PR, 릴리스 전, 수동 | UX: 매 PR, 코드 기반. QA: 수동 |
| 8 | 추가 규칙 | 자유 입력 | 없음 |

첫 질문에 들어가기 전에 현재 레포에 맞춘 추천 표가 먼저 나오고 귀찮으면 추천안대로 한 번에 넘길 수도 있습니다. 다만 한 번 정해 두면 계속 그 방식대로 굴러가니 웬만하면 하나씩 보고 고르는 걸 권합니다.

테스트는 취향에 따라 켜고 끄는 옵션이 아니라 구현의 기본 단계로 들어갑니다. onboarding이 레포의 빌드·테스트 명령과 필요한 검증 항목을 찾아서 미리 보여 준 뒤 [기본 구현 규칙](plugins/groundwork/reference/implementation.md)을 `AGENTS.md`에 적어 둡니다.

`eco / normal / sport`는 작업 강도를 조절하는 별도 프리셋이며 기본값은 `normal`입니다. 모델의 reasoning effort 설정과 비슷하게 검증 깊이, 리뷰 반복 횟수, 화면 검사 범위를 한꺼번에 조절합니다(사용할 모델 자체를 바꾸진 않습니다). 화면 검사에서는 `eco`와 `normal`이 변경 가능성이 있는 화면만, `sport`가 모든 화면을 검사합니다. 실행할 때 `--mode`로 그때그때 바꿀 수 있고 나중에 세부 설정만 따로 고쳐도 됩니다. 화면 검사를 언제 돌릴지는 여전히 7단계에서 고른 빈도를 따릅니다.

각 번들의 장단점과 실제로 문서에 기록되는 상세 규칙은 [`plugins/groundwork/catalog/`](plugins/groundwork/catalog/)에서 볼 수 있습니다.

## 스킬

| 스킬 | 설명 |
|---|---|
| `onboarding` | `GROUNDWORK.md` 초기 설정 및 변경 |
| `plan` | 큰 작업을 상위 이슈 하나와 세부 단계 이슈들로 쪼개기 |
| `step` | 단계 하나 실행: 구현 후 확인된 🔴/🟠 이슈가 남지 않을 때까지 검증 → 리뷰 → 수정 반복 |
| `takeoff` | 끝난 단계를 rebase하고 push한 뒤 PR 열기 |
| `landing`, `rejoin` | 머지 후 정리, 또는 브랜치를 worktree 밖으로 옮기기 |
| `release`, `autoland` | 릴리스 생성 및 CI 통과 시 자동 머지 |
| `review-and-fix`, `commit-push` | 빠르게 치고 빠지는 quick 워크플로우 |
| `review` | 선택한 리뷰어들을 병렬로 돌려 결과 취합 |
| `ux-review` | 지정한 사용자 페르소나 기준으로 코드 또는 실제 앱에서 사용성 리뷰 (화면 검사 설정에 따라 자동 실행 또는 직접 호출) |
| `ui-qa` | 실제 앱을 띄워 자동 테스트가 놓치는 UI 항목 점검 (화면 검사 설정에 따라 자동 실행 또는 직접 호출) |

변경 사항이 생길 때마다 돌 수 있는 코드 리뷰어는 `architecture-reviewer`, `code-quality-reviewer`, `security-reviewer`, `writing-reviewer`, `dx-reviewer` 다섯 가지입니다. `dx-reviewer`는 앱을 띄우지 않고 코드만 따라가며 라이브러리나 HTTP·RPC API, CLI를 가져다 쓰는 개발자 입장에서 불편한 점을 봅니다. `ux-flow-reviewer`는 같은 방식으로 앱 사용자의 동선(불필요한 단계, 빠진 상태 처리, 막다른 화면)을 보며, 7단계에서 UX를 매 PR·코드 기반으로 고르면 리뷰 라운드마다 함께 돕니다. 각 리뷰어는 플러그인 기본 체크리스트에 더해 `GROUNDWORK.md`의 `## Review focus: <reviewer>`에 적힌 레포 전용 기준을 함께 확인합니다.

화면 변경은 매번 스크린샷을 남기는 UI 테스트로 검증하며 구현을 맡은 에이전트가 찍힌 스크린샷을 직접 열어서 눈으로 확인합니다. [화면 검사](plugins/groundwork/catalog/screen-checks.md)는 두 가지로 나뉩니다. UX는 사용자 페르소나가 작업을 끝낼 수 있는지를 코드 기반(빠르지만 정확도가 낮을 수 있음) 또는 시뮬레이터·브라우저(느리지만 실제와 가장 비슷함)로 확인합니다. QA는 앱을 띄워 화면이 요구사항과 디자인에 맞는지 봅니다. 각각 매 PR(`continuous`), 릴리스 직전(`release`), 직접 부를 때만(`manual`) 중에서 고릅니다. 실제 앱으로 하는 검사는 시간이 오래 걸리고 토큰을 많이 쓸 수 있습니다. 자동화된 테스트만으로 확인하기 어려운 항목은 UI 커버리지 문서(`docs/ui-coverage.md`)에 따로 적어 두고 관리합니다.

웹 프로젝트는 대개 브라우저 도구로 화면 요소를 바로 찍어 볼 수 있어서 빠릅니다. 반면 iOS 시뮬레이터나 Android 에뮬레이터는 빌드하고 설치해서 띄우는 시간과 UI 제어 도구의 한계 때문에 시간이 더 걸릴 수 있고 웹이라도 스크린샷 위주로 확인하면 느려질 수 있습니다. 실제 걸리는 시간과 토큰 소모량은 커버리지 범위, 페르소나 수, 사용 도구, 재시도 횟수에 따라 달라집니다.

리뷰에서 나온 지적 사항은 `fixer` 에이전트가 넘겨받아 고칩니다. 깨끗한 컨텍스트에서 새로 시작해 확인된 문제만 고치고 관련 테스트를 다시 돌리기 때문에 원래 작업 중이던 메인 컨텍스트에는 짧은 수정 결과 요약만 남습니다.

## GROUNDWORK.md

설정 파일의 상세 규약은 [`plugins/groundwork/reference/config.md`](plugins/groundwork/reference/config.md)에 정의되어 있습니다. 설정 키는 새로 추가만 될 뿐 기존 키의 이름이 바뀌거나 삭제되지 않습니다. 구조 자체가 바뀌어야 할 때는 스키마 버전을 올리고 onboarding이 기존 파일을 새 버전에 맞게 마이그레이션합니다.

`GROUNDWORK.md`와 onboarding이 만들어 준 문서들은 레포에 그대로 커밋해 두세요. 다른 팀원들은 플러그인만 깔면 바로 같은 규칙으로 작업할 수 있고 각자 onboarding을 다시 돌릴 필요가 없습니다.

## 라이선스

MIT
