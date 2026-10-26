#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_brief.py — 项目交接简报（防"失忆"）

新会话 / 换任务 / 上下文跑偏时，第一条命令就跑它：
把项目档案卡 + 最近记忆日志 + 方案 + 变更流水拼成 ≤20 行的简报，
让接手的自己（或下一个会话）不用重新问一遍"这个项目到哪了"。

用法:
    python project_brief.py                # 简报当前目录
    python project_brief.py <项目目录>
    python project_brief.py --init [目录]  # 生成 PROJECT.md 档案卡骨架
    python project_brief.py --check [目录] # 只检查留档完整性

留档约定（SOP 第 5 段）:
    <项目>/.workbuddy/memory/PROJECT.md      项目档案卡（单一事实来源）
    <项目>/.workbuddy/memory/YYYY-MM-DD.md   每日工作日志（追加，不覆盖）
    <项目>/PLAN.md                           当前方案（做什么/影响面/验收）
    <项目>/CHANGELOG.md                      变更流水
"""

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

MAX_LINES = 22
LOG_TAIL = 6
RECENT_LOGS = 2

PROJECT_TEMPLATE = """# PROJECT.md — 项目档案卡

> 单一事实来源。重大变化才改这里；日常进展写进 `YYYY-MM-DD.md` 日志。

- **项目名**：{name}
- **一句话目标**：
- **项目类型**：
- **技术栈**：
- **根目录**：{root}
- **当前阶段**：
- **当前版本**：
- **本地服务 / 端口**：
- **远端仓库 / 分支**：
- **上线地址**：

## 关键约定（不许违反）

- 

## 未决项 / 待办

- [ ] 

## 下一步

- 

## 已知坑（踩过的）

- 
"""


def mem_dir(root: Path) -> Path:
    return root / ".workbuddy" / "memory"


def read_head(path: Path, limit=12):
    if not path.exists():
        return None
    lines = [l.rstrip() for l in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    return lines[:limit]


def read_tail(path: Path, limit=LOG_TAIL):
    if not path.exists():
        return None
    lines = [l.rstrip() for l in path.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()]
    return lines[-limit:]


def find_logs(root: Path):
    d = mem_dir(root)
    if not d.exists():
        return []
    logs = sorted((p for p in d.glob("*.md") if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", p.name)),
                  reverse=True)
    return logs[:RECENT_LOGS]


def field(card_lines, label):
    if not card_lines:
        return None
    for l in card_lines:
        m = re.match(r"^-\s*\*\*" + re.escape(label) + r"\*\*[:：]\s*(.*)$", l.strip())
        if m:
            return m.group(1).strip() or None
    return None


def section(card_lines, title):
    """取 `## title` 段落到下一个 `##` 之间的非空行。"""
    if not card_lines:
        return []
    out, on = [], False
    for l in card_lines:
        if l.startswith("## "):
            on = title in l
            continue
        if on and l.strip():
            out.append(l.rstrip())
    return out


def check_archive(root: Path):
    items = [
        ("PROJECT.md 档案卡", mem_dir(root) / "PROJECT.md"),
        ("当日日志", mem_dir(root) / f"{dt.date.today().isoformat()}.md"),
        ("PLAN.md 方案", root / "PLAN.md"),
        ("CHANGELOG.md 变更流水", root / "CHANGELOG.md"),
    ]
    return [(name, p.exists(), p) for name, p in items]


def first_item(lines):
    """取段落里第一条有实际内容的条目；空占位（如 `- [ ]`）不算。"""
    for l in lines:
        t = re.sub(r"^[-*\s]*(\[[ xX]\])?\s*", "", l).strip()
        if t:
            return t[:60]
    return None


def do_init(root: Path):
    d = mem_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    card = d / "PROJECT.md"
    if card.exists():
        print(f"⚠️  已存在，未覆盖：{card}")
        return 1
    card.write_text(PROJECT_TEMPLATE.format(name=root.name, root=str(root)), encoding="utf-8")
    print(f"✅ 已生成档案卡：{card}")
    print("   请把「一句话目标 / 当前阶段 / 关键约定 / 下一步」补上——这几项是防失忆的核心。")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir", nargs="?", default=".")
    ap.add_argument("--init", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    root = Path(args.dir).expanduser().resolve()

    if args.init:
        return do_init(root)

    status = check_archive(root)
    if args.check:
        print(f"留档完整性检查：{root}")
        for name, ok, p in status:
            print(f"  {'[OK]' if ok else '[缺]'} {name}  ->  {p}")
        return 0 if all(ok for _, ok, _ in status) else 2

    card_path = mem_dir(root) / "PROJECT.md"
    if not card_path.exists():
        print(f"⚠️  没有档案卡：{card_path}")
        print(f"   先跑：python {Path(__file__).name} --init \"{root}\"")
        return 2

    card = read_head(card_path, 40)
    out = []
    out.append(f"📌 项目：{field(card, '项目名') or root.name}")
    for label in ("一句话目标", "项目类型", "技术栈", "当前阶段", "当前版本",
                  "本地服务 / 端口", "远端仓库 / 分支", "上线地址"):
        v = field(card, label)
        if v:
            out.append(f"   {label}：{v}")

    for label, icon in (("未决项", "⚠️ 未决项："), ("下一步", "➡️ 下一步："),
                        ("关键约定", "🔒 关键约定："), ("已知坑", "🕳 已知坑：")):
        v = first_item(section(card, label))
        if v:
            out.append(icon + v)

    logs = find_logs(root)
    if logs:
        for lg in logs:
            tail = read_tail(lg, LOG_TAIL) or []
            out.append(f"--- 日志 {lg.stem}（末 {len(tail)} 行）---")
            out.extend("   " + t[:100] for t in tail)
    else:
        out.append("--- 无记忆日志 ---")

    plan = root / "PLAN.md"
    if plan.exists():
        tail = read_tail(plan, 4) or []
        out.append(f"--- PLAN.md（末 {len(tail)} 行）---")
        out.extend("   " + t[:100] for t in tail)

    missing = [n for n, ok, _ in status if not ok]
    if missing:
        out.append("📂 留档缺失：" + "、".join(missing))

    if len(out) > MAX_LINES:
        keep = out[:MAX_LINES - 1]
        keep.append(f"...（已截断 {len(out) - MAX_LINES + 1} 行，完整内容看档案卡与日志）")
        out = keep

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
