<p align="center">
  <img src="assets/hero.svg" alt="groundwork — 레포가 일하는 방식을 한 번에 정합니다. Claude Code와 Codex용 플러그인." width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2F6B5A"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-D97757">
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-1F1E1B">
  <img alt="Version 0.3.1" src="https://img.shields.io/badge/version-0.3.1-6E6C66">
</p>

<p align="center"><b>한 번 세팅하고 그다음엔 만들 것만 말하세요.</b></p>

<p align="center">
  <a href="#설치">설치</a> &ensp;·&ensp;
  <a href="#첫-기능-만들기">첫 기능 만들기</a> &ensp;·&ensp;
  <a href="#이렇게-말하면-됩니다">이렇게 말하면 됩니다</a> &ensp;·&ensp;
  <a href="README.md">English</a> &ensp;·&ensp;
  <a href="README.zh-CN.md">简体中文</a>
</p>

<br>

**groundwork**는 레포에서 AI 코딩 에이전트가 일하는 방식을 한 번에 잡아 주는 Claude Code·Codex 플러그인입니다. 이슈 관리, 워크플로우, 브랜치·배포 전략, 아키텍처, 코드 리뷰, 화면 검사까지 처음 한 번만 정해 두면 그다음부터는 "이 기능 만들어 줘"라고 말하기만 하면 됩니다. 이슈 생성부터 구현, 테스트, 리뷰, 수정까지 선택한 방식대로 알아서 흘러가고 사람이 결정해야 하는 지점에서만 멈춥니다.

외울 명령어는 없습니다. 모든 스킬은 어떤 언어로든 평소 말하듯 실행할 수 있습니다.

## 설치

Claude Code:

```
/plugin marketplace add enebin/groundwork
/plugin install groundwork@groundwork
```

세팅할 레포에서 이렇게 말하면 됩니다.

```text
이 레포에 groundwork 세팅해 줘.
```

온보딩 과정에서 여덟 가지를 물어보고 항목마다 추천안을 함께 보여 준 뒤 고른 내용을 `GROUNDWORK.md`에 저장합니다. 나머지 스킬은 전부 이 파일을 읽고 움직입니다.

Claude Code에서는 하루 최대 한 번 GitHub에서 새 버전을 확인해 새 릴리스가 나왔을 때 알려 줍니다. 업데이트할 때는 `claude plugin update groundwork@groundwork`를 실행한 뒤 Claude Code를 재시작하면 됩니다.

선택 사항: [skeptic-review](https://github.com/enebin/skeptic-review)를 함께 설치하면 리뷰어가 잡은 내용을 사용자에게 보여 주기 전에 실제로 맞는 지적인지 한 번 더 걸러 줍니다. 설치하지 않으면 리뷰 결과에 `SkepticReview: OFF`로 표시됩니다.

## 첫 기능 만들기

```text
로그인 화면 추가해 줘.
```

요청은 이 한 문장이 전부입니다. 기본 설정이라면 groundwork가 이어서 이렇게 진행합니다.

1. 요청을 이슈로 만들고 전용 worktree에 브랜치를 엽니다.
2. 기능을 구현하면서 테스트도 함께 작성합니다.
3. 빌드와 테스트를 실행한 뒤 선택한 리뷰어들을 동시에 돌립니다.
4. 리뷰에서 확인된 문제를 고치고 중대한 지적이 남지 않을 때까지 반복합니다.
5. 화면 검사를 켜 두었다면 바뀐 화면도 점검합니다.
6. 작업 내용을 정리해 보여 주고 커밋할지 묻습니다.

아직 커밋이 없거나 빌드·테스트 명령이 확인되지 않은 레포에서는, 기본 구조를 세팅하는 단계로 시작하는 짧은 계획을 먼저 보여 주고 승인을 기다립니다.

결과가 마음에 들면 이렇게 말합니다.

```text
푸시하고 PR 올려 줘.
```

groundwork가 rebase하고 다시 검증하고 push한 뒤 PR을 엽니다. 자동 머지를 켜 두었다면 CI 통과를 기다렸다가 머지하고 브랜치 정리까지 합니다.

PR 하나로 끝나지 않는 큰 작업은 먼저 여러 단계로 나눕니다. 계획을 승인하면 각 단계를 위와 같은 방식으로 진행합니다.

### 사람이 결정하는 지점

아래는 groundwork가 혼자 정하지 않습니다.

- **계획 승인:** 큰 작업을 여러 단계로 나눴을 때 먼저 계획을 확인받습니다.
- **설계 문서 승인:** `design-first` 워크플로우에서는 구현에 들어가기 전에 설계 문서를 승인받습니다.
- **push와 PR 생성:** 직접 요청할 때까지 기다립니다.
- **머지:** 자동 머지를 켜 두지 않았다면 알아서 머지하지 않습니다.
- **릴리스:** 요청할 때만 시작하며 정기 릴리스 준비도 배포 전에 최종 승인을 받습니다.

## 이렇게 말하면 됩니다

예시일 뿐이고 같은 뜻이면 어떻게 말해도 됩니다.

| 이렇게 말하면 | 실행되는 스킬 |
|---|---|
| "다크 모드 추가해 줘." / "설정 화면에서 앱 죽는 거 고쳐 줘." | `step`: 이슈 → 구현 → 테스트 → 리뷰 → 수정 |
| "이거 크니까 이슈로 쪼개 줘." | `plan`, 이어서 단계마다 `step` |
| "푸시하고 PR 올려 줘." | `takeoff`, 자동 머지가 켜져 있으면 `autoland` |
| "PR 머지됐어. 정리해 줘." | `landing` |
| "내가 바꾼 코드 리뷰해 줘." | `review` |
| "신규 사용자가 가입까지 잘 가는지 봐 줘." | `ux-journey` (실제 앱에서 실행) |
| "앱에서 설정 화면 확인해 줘." | `ui-qa` |
| "1.2.0 릴리스해 줘." | `release` |
| "매주 금요일마다 릴리스 준비해 줘." | `release-prep` |
| "이번 주 정리해 줘." | `weekly-summary` |
| "오늘은 여기까지. 다음에 이어서 할 수 있게 남겨 줘." | `handoff` |

정확하게 부르고 싶을 때는 `/groundwork:step`처럼 스킬 이름을 직접 입력해도 됩니다.

## 한 번만 세팅하기

질문을 시작하기 전에 전체 단계와 추천 구성을 한눈에 먼저 보여 줍니다.

<p align="center">
  <img src="assets/overview.svg" alt="onboarding이 8개 질문을 차례로 거치며 질문마다 추천 답을 보여 줍니다. 답은 GROUNDWORK.md 초안에 모이고 승인한 뒤에만 저장됩니다." width="100%">
</p>

각 선택지는 **번들** 단위입니다. 서로 맞물려 돌아가는 규칙과 스킬을 묶어 둔 세트로, 장단점과 토큰 비용이 함께 나옵니다.

<p align="center">
  <img src="assets/choices.svg" alt="onboarding 8단계 중 3단계: 워크플로우 번들을 장단점과 토큰 비용으로 비교하고 추천 번들을 맨 앞에 둡니다." width="100%">
</p>

| 단계 | 항목 | 선택지 | 새 프로젝트 기본값 |
|---|---|---|---|
| 1 | 언어 | 대화 언어 / 산출물 언어 | 사용자 언어 / 영어 (토큰 절약) |
| 2 | 이슈 트래커 | local files, GitHub Projects, Linear, Jira | local files |
| 3 | 워크플로우 | step-loop, design-first, tdd-loop, quick, review-only; 이슈별 worktree | step-loop, 이슈별 worktree |
| 4 | 배포 전략 | develop + release, main only; 머지 방식 | develop + release |
| 5 | 아키텍처 | unidirectional, mvvm, layered-service, layered-web, none | 기술 스택에 따라 추천 |
| 6 | 리뷰 | app, sdk, service, product, light | 프로젝트 성격에 따라 추천 |
| 7 | 화면 검사 | UX(코드·앱)와 QA: 매 PR, 릴리스 전, 수동 | UX: 매 PR, 코드 기반. QA: 수동 |
| 8 | 추가 규칙 | 자유 입력 | 없음 |

막 `git init` 한 새 레포에서 특히 효과적입니다. 사이드 프로젝트, 해커톤 프로토타입, 내일 아침 제출인 과제처럼 첫 커밋 전에 깔아 두면 `최종_v2_진짜최종.py`부터 생기는 대신 규칙과 리뷰, QA가 잡힌 상태로 시작합니다. 이미 운영 중인 레포에서도 같은 8단계를 거치되 기존 코드와 설정을 읽어 그에 맞는 추천안을 골라 줍니다.

`GROUNDWORK.md`와 온보딩이 만들어 준 문서는 레포에 커밋해 두세요. 팀원은 플러그인만 깔면 같은 규칙으로 작업합니다. 나중에 설정을 바꾸고 싶으면 말로 바꾸면 되고 플러그인 업데이트 후 새 기능을 붙이려면 "groundwork 업데이트해 줘"라고 하면 됩니다.

<p align="center">
  <img src="assets/how-it-works.svg" alt="onboarding이 GROUNDWORK.md, AGENTS.md, ARCHITECTURE.md를 쓰고 모든 groundwork 스킬과 리뷰어 에이전트가 이를 따릅니다." width="100%">
</p>

## 요청 뒤에서 도는 것

- **테스트는 구현의 기본 단계**입니다. 켜고 끄는 옵션이 아닙니다. 온보딩이 레포의 빌드·테스트 명령을 찾아 [구현 규칙](plugins/groundwork/reference/implementation.md)을 `AGENTS.md`에 적어 둡니다.
- **리뷰어**는 아키텍처, 코드 품질, 보안, 문구, 개발자 경험을 변경이 생길 때마다 동시에 점검합니다. 확인된 지적은 깨끗한 컨텍스트에서 시작하는 `fixer` 에이전트가 고치기 때문에, 대화에는 짧은 요약만 남습니다.
- **화면 검사**는 사용자 페르소나가 작업을 끝낼 수 있는지를 코드 또는 실제 앱으로 확인하고 화면이 요구사항에 맞는지 봅니다. [화면 검사](plugins/groundwork/catalog/screen-checks.md)와 [UX 검사 비교](plugins/groundwork/reference/ux-checks.md)를 참고하세요. [벤치마크](bench/ux/flow-reviewer/README.md)에서 코드 기반 UX 리뷰는 심어 둔 결함 39개 중 36개를 찾았고 비용은 앱 기반 리뷰의 약 10분의 1이었습니다.
- **작업 강도**는 `eco`, `normal`(기본), `sport` 프리셋 하나로 검증 깊이, 리뷰 반복 횟수, 화면 검사 범위를 함께 조절합니다. "이번 건 sport 모드로 해 줘"처럼 요청할 때 한 번만 바꿔서 실행할 수도 있습니다.

리뷰가 사람의 판단을 대신하지는 않습니다. 실제 앱으로 하는 검사는 시간이 오래 걸리고 토큰을 많이 쓸 수 있습니다.

## 부가기능

요청하기 전에는 아무것도 돌지 않습니다. "groundwork 부가기능 보여 줘"라고 하면 목록을 볼 수 있습니다.

| 부가기능 | 하는 일 |
|---|---|
| `slack-report` | 작업 내용과 테스트 결과를 Slack에 보냅니다 |
| `handoff` | 끝낸 일, 남은 일, 다음 시작점을 저장합니다 |
| `weekly-summary` | 한 주의 커밋·PR·이슈를 요약합니다 |
| `release-notes` | 커밋 범위를 사용자용 릴리스 노트로 정리합니다 |
| `ux-journey` | 처음 온 사용자가 실제 앱에서 전체 여정을 끝까지 해 보고 막힌 곳을 알려 줍니다 |
| `release-prep` | 정해진 주기로 릴리스를 준비하고 검증한 뒤 최종 승인을 받습니다 |

Slack 인증 정보는 Git 밖의 `~/.config/slack-report/`에 보관합니다. 자세한 내용은 [Slack 연결 안내](plugins/groundwork/skills/slack-report/references/setup.md)를 참고하세요. 자동 보고를 켜면 두 클라이언트에 저장소용 턴 종료 훅을 설치합니다.

<details>
<summary><b>전체 스킬</b></summary>

| 스킬 | 설명 |
|---|---|
| `onboarding` | `GROUNDWORK.md` 초기 설정 및 변경 |
| `update` | 플러그인 업데이트 후 마이그레이션을 적용하고 새 기능을 골라 붙이기 |
| `addons` | 부가기능 목록을 보고 설정이나 일회성 사용으로 이어가기 |
| `plan` | 큰 작업을 상위 이슈 하나와 세부 단계 이슈들로 쪼개기 |
| `step` | 단계 하나 실행: 구현 후 확인된 🔴/🟠 이슈가 남지 않을 때까지 검증 → 리뷰 → 수정 반복 |
| `takeoff` | 끝난 단계를 rebase하고 push한 뒤 PR 열기 |
| `landing`, `rejoin` | 머지 후 정리, 또는 브랜치를 worktree 밖으로 옮기기 |
| `release`, `autoland` | 릴리스 생성, CI 통과 시 머지 |
| `review-and-fix`, `commit-push` | quick 워크플로우 |
| `review` | 선택한 리뷰어들을 병렬로 돌려 결과 취합 |
| `ux-review` | 지정한 사용자 페르소나 기준으로 코드 또는 실제 앱에서 사용성 리뷰 |
| `ui-qa` | 실제 앱을 띄워 자동 테스트가 놓치는 UI 항목 점검 |
| `slack-report`, `handoff`, `weekly-summary`, `release-notes`, `release-prep`, `ux-journey` | 부가기능; 위 설명 참고 |

</details>

## GROUNDWORK.md

상세 규약은 [`plugins/groundwork/reference/config.md`](plugins/groundwork/reference/config.md)에 있습니다. 설정 키는 추가만 되고 이름이 바뀌거나 삭제되지 않습니다. 구조가 바뀌어야 할 때는 스키마 버전을 올리고 온보딩이 기존 파일을 마이그레이션합니다.

## 라이선스

MIT
