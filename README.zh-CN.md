<p align="center">
  <img src="assets/hero.svg" alt="groundwork — 一次性定好仓库的工作方式。适用于 Claude Code 和 Codex 的插件。" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-2F6B5A"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-D97757">
  <img alt="Codex plugin" src="https://img.shields.io/badge/Codex-plugin-1F1E1B">
  <img alt="Version 0.3.1" src="https://img.shields.io/badge/version-0.3.1-6E6C66">
</p>

<p align="center"><b>设置一次，之后只需说出要做什么。</b></p>

<p align="center">
  <a href="#安装">安装</a> &ensp;·&ensp;
  <a href="#做第一个功能">做第一个功能</a> &ensp;·&ensp;
  <a href="#这样说就行">这样说就行</a> &ensp;·&ensp;
  <a href="README.md">English</a> &ensp;·&ensp;
  <a href="README.ko.md">한국어</a>
</p>

<br>

**groundwork** 是一个 Claude Code 和 Codex 插件，用来一次性设定 AI 编程智能体在仓库中的工作方式：问题跟踪、工作流、分支与发布策略、架构、代码审查和界面检查。设置好之后，你只需直接说"帮我做这个功能"，智能体就会按照你选定的方式创建 issue、实现功能、编写并运行测试、审查代码并修复问题。它只会在需要人来决定的地方停下来。

不需要记任何命令。所有技能都可以直接用日常语言调用，用什么语言说都行。

## 安装

Claude Code：

```
/plugin marketplace add enebin/groundwork
/plugin install groundwork@groundwork
```

然后在要设置的仓库里说：

```text
帮这个仓库设置 groundwork。
```

onboarding 会问八个问题，每个问题都给出推荐答案，并把你的选择保存到 `GROUNDWORK.md`。其他所有技能都会读取这个文件。

在 Claude Code 中，groundwork 每天最多检查一次 GitHub 上的新版本，每个新版本只提醒一次。更新时运行 `claude plugin update groundwork@groundwork`，然后重启 Claude Code。

可选：安装 [skeptic-review](https://github.com/enebin/skeptic-review)，在审查结果交给你之前再核实一遍。未安装时，审查结果会显示 `SkepticReview: OFF`。

## 做第一个功能

```text
加一个登录页面。
```

这一句话就是全部请求。在默认设置下，groundwork 接下来会：

1. 为这个请求创建 issue，并在独立的 worktree 中新建分支。
2. 实现功能，同时编写测试。
3. 运行构建和测试，再并行运行你选择的审查器。
4. 修复经确认的问题，反复进行，直到没有严重问题为止。
5. 如果启用了界面检查，接着检查改动过的界面。
6. 汇报完成的内容，并询问是否提交。

如果仓库还没有任何提交，或者构建和测试命令尚未确认，groundwork 会先提出一个以搭建基础结构为第一步的简短计划，等你批准后再继续。

满意之后再说：

```text
推送并创建 PR。
```

groundwork 会 rebase、再次验证、推送并创建 PR。如果开启了自动合并，它还会等 CI 通过后合并，并清理分支。

一个 PR 装不下的大任务会先拆成多个步骤。你批准计划后，每个步骤都按上面的方式进行。

### 由你决定的地方

以下事项 groundwork 不会自己决定：

- **批准计划**：大任务拆分为多个步骤时，先由你确认计划。
- **批准设计文档**：采用 `design-first` 工作流时，实现前先由你批准设计文档。
- **推送和创建 PR**：始终等你明确提出后才执行。
- **合并**：除非开启了自动合并，否则不会擅自合并。
- **发布**：仅在你提出时启动；定期发布准备也会在发布前等你最终确认。

## 这样说就行

以下只是示例，意思相同的任何说法都可以。

| 你说 | 运行的技能 |
|---|---|
| "加上深色模式。" / "修复设置页面的崩溃。" | `step`：issue → 实现 → 测试 → 审查 → 修复 |
| "这个太大了，拆成几个 issue。" | `plan`，然后每个部分运行 `step` |
| "推送并创建 PR。" | `takeoff`，开启自动合并时再运行 `autoland` |
| "PR 已经合并了，清理一下。" | `landing` |
| "审查一下我的改动。" | `review` |
| "看看新用户能不能顺利完成注册。" | `ux-journey`（在运行中的应用里执行） |
| "在应用里检查一下设置页面。" | `ui-qa` |
| "发布 1.2.0 版本。" | `release` |
| "每周五准备一次发布。" | `release-prep` |
| "总结一下这周。" | `weekly-summary` |
| "今天先到这里，留个记录方便下次继续。" | `handoff` |

想精确调用时，也可以直接输入技能名，例如 `/groundwork:step`。

## 只需设置一次

在问第一个问题之前，onboarding 会先一览展示所有步骤和推荐配置：

<p align="center">
  <img src="assets/overview.svg" alt="onboarding 依次完成 8 个问题，并为每个问题推荐一个答案。答案汇总到 GROUNDWORK.md 草稿中，只有在你批准后才会保存。" width="100%">
</p>

每个选项都是一个**方案包**：一组相互配合的规则和技能，并附有优缺点和 token 成本。

<p align="center">
  <img src="assets/choices.svg" alt="onboarding 第 3 步（共 8 步）：按优缺点和 token 成本比较工作流方案，推荐方案排在最前。" width="100%">
</p>

| 步骤 | 类别 | 选项 | 新项目默认值 |
|---|---|---|---|
| 1 | 语言 | 对话语言 / 产出物语言 | 你的语言 / 英语（节省 token） |
| 2 | 问题跟踪 | local files、GitHub Projects、Linear、Jira | local files |
| 3 | 工作流 | step-loop、design-first、tdd-loop、quick、review-only；每个 issue 一个 worktree | step-loop，每个 issue 一个 worktree |
| 4 | 发布策略 | develop + release、main only；合并方式 | develop + release |
| 5 | 架构 | unidirectional、mvvm、layered-service、layered-web、none | 根据技术栈推荐 |
| 6 | 审查 | app、sdk、service、product、light | 根据项目类型推荐 |
| 7 | 界面检查 | UX（基于代码或应用）和 QA：每个 PR、发布前或手动 | UX：每个 PR，基于代码。QA：手动 |
| 8 | 自定义规则 | 自由填写 | 无 |

它尤其适合刚 `git init` 的新仓库，比如业余项目、黑客松原型或明天早上要交的作业。在第一次提交前装好，就能从一开始把规则、审查和 QA 配齐。在已有的仓库中，它会问同样的问题，并根据现有代码给出推荐。

请把 `GROUNDWORK.md` 和 onboarding 生成的文档提交到仓库。队友只需安装插件，就能按同样的规则工作。之后想改某个选择，直接说就行；插件更新后想加入新功能，说"更新 groundwork"即可。

<p align="center">
  <img src="assets/how-it-works.svg" alt="onboarding 写入 GROUNDWORK.md、AGENTS.md 和 ARCHITECTURE.md；所有 groundwork 技能和审查智能体都遵循这些文件。" width="100%">
</p>

## 请求背后运行的内容

- **测试是实现的一部分**，不是可选项。onboarding 会找到仓库的构建和测试命令，并把[实现规则](plugins/groundwork/reference/implementation.md)写入 `AGENTS.md`。
- **审查器**会针对每次改动，并行检查架构、代码质量、安全、文案和开发者体验。确认的问题交给在全新上下文中启动的 `fixer` 智能体修复，因此你的对话里只会留下简短的摘要。
- **界面检查**会通过代码或运行中的应用，确认每个用户角色能否完成任务，并检查界面是否符合需求。详见[界面检查](plugins/groundwork/catalog/screen-checks.md)和 [UX 检查对比](plugins/groundwork/reference/ux-checks.md)。在一次[基准测试](bench/ux/flow-reviewer/README.md)中，基于代码的 UX 审查找出了 39 个预埋缺陷中的 36 个，成本约为基于应用审查的十分之一。
- **工作强度**由一个预设控制：`eco`、`normal`（默认）或 `sport`，同时调整验证深度、审查轮数和界面检查范围。说"这次用 sport 模式"即可只对单次请求生效。

审查不能代替你自己的判断。在运行中的应用上做检查可能耗时较长，并消耗较多 token。

## 可选附加功能

在你提出之前，这些功能都不会运行。说"给我看看 groundwork 的附加功能"即可浏览。

| 附加功能 | 作用 |
|---|---|
| `slack-report` | 把工作变更和测试结果发送到 Slack |
| `handoff` | 保存已完成的工作、剩余的工作和下次的起点 |
| `weekly-summary` | 汇总一周的提交、PR 和 issue |
| `release-notes` | 把一段提交范围整理成面向用户的发布说明 |
| `ux-journey` | 让首次使用的用户在运行中的应用上走完整个流程，并报告卡住的地方 |
| `release-prep` | 按固定周期准备并验证发布，然后请求最终批准 |

Slack 凭据保存在 Git 之外的 `~/.config/slack-report/` 中，详见 [Slack 设置说明](plugins/groundwork/skills/slack-report/references/setup.md)。开启自动报告后，会为两个客户端安装仓库级的 Stop 钩子。

<details>
<summary><b>全部技能</b></summary>

| 技能 | 说明 |
|---|---|
| `onboarding` | 初始化或修改 `GROUNDWORK.md` |
| `update` | 插件更新后应用迁移，并从发布说明中挑选新功能 |
| `addons` | 浏览附加功能，继续设置或单次使用 |
| `plan` | 把大任务拆成一个父 issue 和多个步骤 issue |
| `step` | 运行一个步骤：实现后反复进行验证 → 审查 → 修复，直到没有确认的 🔴/🟠 问题 |
| `takeoff` | 对完成的步骤执行 rebase、推送并创建 PR |
| `landing`、`rejoin` | 合并后清理，或把分支移出 worktree |
| `release`、`autoland` | 创建发布，CI 通过后合并 |
| `review-and-fix`、`commit-push` | quick 工作流 |
| `review` | 并行运行选定的审查器并汇总结果 |
| `ux-review` | 以选定的用户角色视角，基于代码或应用进行可用性审查 |
| `ui-qa` | 启动应用，检查自动化测试覆盖不到的界面行为 |
| `slack-report`、`handoff`、`weekly-summary`、`release-notes`、`release-prep`、`ux-journey` | 附加功能；见上文 |

</details>

## GROUNDWORK.md

完整规范见 [`plugins/groundwork/reference/config.md`](plugins/groundwork/reference/config.md)。配置键只会新增，不会重命名或删除。结构需要变化时，会提升 schema 版本，并由 onboarding 迁移你的文件。

## 许可证

MIT
