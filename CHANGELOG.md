# CHANGELOG — GH-KomoSkill

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。
版本号语义：`MAJOR` 流程断层 / `MINOR` 新增能力 / `PATCH` 措辞与修错。

---

## v1.0.0 — 2026-10-26

首个可复刻版本。把此前散落在专家包里的工作法，提炼成一个**与运行环境无关**的独立技能。

### 新增

- `SKILL.md` —— 技能入口。三条铁律（不要求写完整 Prompt / 一次只问一个 / 门禁不过不前进）+ 六阶段主干 + 极简指令表。
- `references/six-stage-flow.md` —— S0→S6 每阶段的输入/动作/输出/门禁，含四张单子模板（需求确认单 / 启动确认清单 / 执行计划表 / 交付验收单）与阶段跳过规则。
- `references/prompt-normalize.md` —— 六字段结构化 Prompt、优化四招（形容词→指标 / 补隐含约束 / 合并提问 / 标不确定项）、反例库、两个口语→结构化的完整实例。
- `references/evidence-discipline.md` —— 三态标注（事实/推断/待核验）、五条硬动作、六个领域的专属验收口径、五项汇报格式、触发即停的红旗清单。
- `references/context-memory.md` —— 留档三件套职责划分、四级压缩与压缩红线、防失忆 5 条、跨会话恢复三步、项目隔离。
- `references/capability-routing.md` —— 与具体产品无关的路由三原则、「目录名 ≠ 技能 id」的验证要点、能力分类决策树、降级三选一。
- `references/safety-boundaries.md` —— 文件系统 / 凭据 / 破坏性操作分级 / 网络爬取 / Git 远端 / 报告外部平台 / 金融交易 七类红线，及冲突时的优先级。
- `scripts/install.py` —— 一键装到 workbuddy / codex / claude / 自定义目录，支持 `--dry-run` 与 `--force`，自动探测多个 skills 根并拒绝擅自选择。
- `scripts/doctor.py` —— 七项自检（Python 版本 / 安装位置 / frontmatter / references / templates / scripts 实跑 / UTF-8 编码），退出码区分 FAIL 与 WARN。
- `scripts/flow_state.py` —— 阶段状态机与门禁校验（退出码 0/2/3/4），状态存 `<项目>/.workbuddy/flow.json`。
- `scripts/project_brief.py` —— 防失忆交接简报（≤22 行）。
- `templates/PROJECT.md` / `PLAN.md` / `AGENTS.md` —— 三份可直接套用的档案模板。
- `examples/01-一句话到交付.md` —— 从「做个本地记账小网页」（6 个字）到五项汇报的完整对话复盘，含关键环节的作用说明与「没有这套流程时」的反向对照。

### 设计决定

- **门禁写进代码而非提示词** —— 劝告无效，退出码有效。`--gate` 返回 2 就是没过。
- **只依赖 Python 标准库** —— 无 pip install，Windows / macOS / Linux 直接跑。
- **不捆绑具体厂商能力** —— 路由规则与产品解耦，装到任何 agent 都成立。
- **保留 `待核验` 作为独立字段** —— 六字段模板实际是七行，因为「不确定」必须显式存在，否则会被偷偷当成事实写进方案。

### 来源

内核来自作者自用的工作法（`komo-skill` 路由层 + `small-project-guide` 流程层，v2.0.1）。
本版做的主要工作是**通用化**：去掉个人路径绑定、把「preflight 预检」抽象成环境无关的「能力存在性验证」、把四张单子与门禁从正文抽到独立文件以便复用。
