---
name: gh-komoskills
description: >-
  A portable, clone-and-go workflow skill: it turns a one-line casual request into a staged,
  gated, evidence-backed delivery. Use it when the user says 做个工具 / 写个脚本 / 做个小项目 /
  开发个网页 / 做个小程序 / 搞个工具, or 按流程来 / 走 SOP / 按我的流程启动 / 帮我控一下流程,
  or any fuzzy 我想做个 XX / 帮我整个 XX. It runs six gated stages (intake -> kickoff -> plan ->
  stepwise build -> acceptance -> archive), never asks the user to write a full prompt, asks one
  question at a time, refuses to claim "done" without a re-read artifact, and keeps project state
  in .workbuddy/flow.json so a new session can resume with one command.
  Trigger words: GH-KomoSkill, gh-komoskills, 走我的流程, 按流程来, 做个工具, 做个小项目, 继续, 整理下状态.
---

# GH-KomoSkill — 可复刻的 AI 协作工作法

一个**元技能（meta-skill）**：它不替你写代码，它管**怎么把一件事做完并可交付**。

装上它，agent 的行为会从「你说一句它干一段」变成「先问清 → 先出单子 → 先过门禁 → 干完自己反证 → 给你五项汇报」。

---

## 一、它解决什么

默认的 agent 有三个通病，本技能逐条对症：

| 通病 | 具体表现 | 本技能的对策 |
|---|---|---|
| **要求你写长 Prompt** | 「请详细描述你的需求、背景、预期…」 | 你只说「做个工具」就够启动；它**一次只问一个**关键问题补齐 4 要素 |
| **假装已完成** | 「已修复 ✅」但文件根本没改 | 说完成必须给绝对路径 / 回读内容 / 命令输出；**改完回读**再宣称 |
| **换会话就失忆** | 新会话又从头问一遍 | 状态存在 `.workbuddy/flow.json`；说「继续」先跑简报把上下文捞回来 |

---

## 二、三条铁律（不可违背）

| # | 铁律 | 含义 |
|---|---|---|
| 1 | **永远不要让用户写完整 Prompt** | 缺什么它问什么；用户说一个词就能启动 |
| 2 | **一次只问一个关键问题** | 补信息时逐项一问；到了要点头的关口才用一个合并确认问题 |
| 3 | **阶段不通过，不进下一阶段** | 每阶段有门禁清单，靠 `flow_state.py --gate` 校验，退出码非 0 不许往下走 |

---

## 三、六阶段（S0 → S6）

```
S0 进场判断      判类型（新建/续作/修补/调研）· 判风险 · 判步数      不打扰你
      ↓
S1 需求补全      4 要素缺哪问哪（一次一问）→ 出「需求确认单」       你回「确认」
      ↓
S2 启动确认      8 项清单（类型/目标/栈/能力/目录/交付/验证…）      ⛔ 禁止建文件、装依赖
      ↓
S3 执行计划      ≤5 大步，每步四属性（做什么/动什么/怎么验/风险）   你回「确认」
      ↓
S4 分步执行      逐步做 + 每步给产物路径 + 阶段小结 + 大输出落盘
      ↓
S5 验收交付      交付验收单 + **自我反证**（构造能证伪自己的检查）   你回「通过」
      ↓
S6 归档收尾      问是否推远端 → 写留档 → 出「五项汇报」（全部实测）
```

完整 SOP、四张单子模板、门禁清单 → `references/six-stage-flow.md`

---

## 四、极简指令表（说一个词就行）

| 你说 | 它做什么 |
|---|---|
| `确认` / `对` / `ok` / `好` | 通过当前节点，进下一阶段 |
| `继续` / `下一步` | 先跑简报召回上下文，再往下做 |
| `停` / `等等` | 立即终止，保留已完成部分，报停在哪一步 |
| `改：XXX` | 只改 XXX，其它不动，改完回读确认 |
| `重设：XXX` | 重置核心需求，回 S1 重出需求确认单 |
| `整理下状态` | 给进度 + 产物位置 + 下一步 |
| `跳过` | 跳过当前阶段（**仅低风险**；中高风险必须再问一次） |

> 有歧义时默认按「**继续当前项目**」理解，不会莫名其妙重走 S1。

---

## 五、两条纪律（这是它和普通 prompt 模板的分水岭）

### 证据纪律（防幻想）

- 结论分三态：`事实`（有工具输出/文件为证）/ `推断`（有依据的猜）/ `待核验`（必须查）。**禁止把推断写成事实。**
- 关键数字、文件内容、版本号、端口 —— 一律**重新读一次**，不许「我记得」。
- 改完文件**必须回读**再报完成；不看就报完成 = 幻想。
- 交付前至少做一个**能证伪自己**的检查（跑命令 / 比 md5 / 看渲染）。找不到反证方式 → 验收标准不够硬，回 S3 重写。
- 判「线上是不是最新版」比 **md5 / tree sha**，不能只看 HTTP 200。

### 上下文纪律（防失忆）

- 单一事实来源：长期约定只写 `PROJECT.md`，日志只写「今天干了什么」。**两处都写 = 迟早打架。**
- 四级压缩：L0 原文落盘（对话只留路径）→ L1 摘要（≤15 行）→ L2 指针进档案卡。
- **压缩红线**：数字 / 路径 / 命令 / 报错原文 / 决策理由**一条都不许压**。
- 记「为什么」不只记「改了什么」—— 下次的自己最需要的是决策理由。

细节 → `references/evidence-discipline.md`、`references/context-memory.md`

---

## 六、脚本（把流程变成可校验的状态）

```bash
# 1) 初始化项目状态（在项目目录下）
python scripts/flow_state.py <项目目录> --init --name 项目名

# 2) 看进度 / 推阶段 / 勾要素 / 校验门禁
python scripts/flow_state.py <项目目录>
python scripts/flow_state.py <项目目录> --set S3
python scripts/flow_state.py <项目目录> --ok S1 交付产物
python scripts/flow_state.py <项目目录> --gate S2      # 退出码 0 通过 / 2 未过 / 3 未初始化

# 3) 防失忆：交接简报（≤22 行）
python scripts/project_brief.py <项目目录>
python scripts/project_brief.py --init <项目目录>
python scripts/project_brief.py --check <项目目录>

# 4) 安装 / 自检
python scripts/install.py --target workbuddy     # 或 codex / --dest <自定义 skills 目录>
python scripts/doctor.py
```

`install.py` 会把本技能装到目标 agent 的 skills 目录；`doctor.py` 报告装在哪、缺什么。

---

## 七、和「路由层」的关系

本技能是**流程层**（管走到第几步）。它不关心该用哪个具体工具。

- 需要「该用哪个能力」时 → 交给你的路由技能（如果装了 `komo-skill` 之类）或直接用目标 agent 的原生能力。
- **推荐能力必须先验证存在**，不存在就说「用内联能力替代」，**不许声称已调用**。

通用路由规则 → `references/capability-routing.md`

---

## 八、安全红线

1. 只操作当前项目目录与已授权目录。
2. 不读改 `.env` / 密钥 / 敏感配置，除非明确授权。
3. 删除前二次确认；破坏性操作前先备份。
4. 爬取/扫描只在用户指定目标上执行，不扩范围。
5. **绝不默认自动推远端**：大版本更新/上线先问；提交信息用 Conventional Commits。
6. 报告类默认只生成本地 Markdown，不自动推送外部平台。

---

## 九、安装后的最小验证

装完说这句，能正确复现就是装好了：

```
做个工具，走我的流程
```

正确表现：它**不会**问「请详细描述需求」，而是只问一句
「这个工具解决什么问题？什么场景下用？」—— 看到这句，说明 S1 在生效。

---

## 十、变更日志

见 `CHANGELOG.md`。本技能更新时追加带日期的条目，不写入密钥或项目敏感数据。
