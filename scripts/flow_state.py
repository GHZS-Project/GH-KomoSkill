#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_state.py — 小项目开发全流程的「阶段状态机 + 门禁校验」。

用途：把 SKILL.md 里那套 S0→S6 的流程变成可记录、可校验、可跨会话恢复的状态。

状态文件：<项目目录>/.workbuddy/flow.json

用法
----
  python flow_state.py <项目目录>                        # 看当前状态
  python flow_state.py <项目目录> --init [--name 名称]    # 初始化
  python flow_state.py <项目目录> --set S3               # 推进到某阶段
  python flow_state.py <项目目录> --ok S1 交付产物        # 勾选某要素（也接受序号）
  python flow_state.py <项目目录> --unok S1 交付产物      # 取消勾选
  python flow_state.py <项目目录> --list S1              # 列出该阶段待办项
  python flow_state.py <项目目录> --gate S2              # 校验某阶段门禁
  python flow_state.py <项目目录> --note "说明"           # 追加一条历史记录
  python flow_state.py <项目目录> --json                 # 机器可读输出

退出码
------
  0 = 正常 / 门禁通过
  2 = 门禁未通过（有未勾选项）
  3 = 尚未初始化
  4 = 参数错误
"""

import argparse
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ---------------------------------------------------------------- 阶段定义

STAGES = [
    ("S0", "进场判断", []),
    ("S1", "需求接收与要素补全", [
        "场景用途", "交付产物", "核心功能", "约束偏好",
        "需求确认单已确认", "六字段Prompt已产出",
    ]),
    ("S2", "项目启动确认", [
        "项目类型", "项目目标", "预计技术栈", "建议调用能力",
        "是否包含前端", "默认项目目录", "主要交付内容", "预计验证方式",
        "建议能力已过存在性验证",
        "用户已确认",
    ]),
    ("S3", "执行计划生成与确认", [
        "步骤数不超过5",
        "每步四属性齐全",
        "用户已确认",
    ]),
    ("S4", "分步执行与过程管控", [
        "阶段小结已输出",
        "大输出已落盘(对话只留指针)",
    ]),
    ("S5", "验收与交付", [
        "交付验收单五项齐全",
        "已做自我反证",
        "用户已验收",
    ]),
    ("S6", "归档与收尾", [
        "已询问GitHub与本地归档",
        "五项汇报已输出",
    ]),
]

STAGE_ORDER = [s[0] for s in STAGES]
STAGE_NAME = {s[0]: s[1] for s in STAGES}
STAGE_ITEMS = {s[0]: list(s[2]) for s in STAGES}

# 每个阶段的「通过后去向」提示
NEXT_HINT = {
    "S0": "判完类型/分级/步数 → 进 S1 补全需求要素",
    "S1": "出需求确认单 + 六字段 Prompt，等用户确认 → 进 S2",
    "S2": "出 8 项启动确认清单（本阶段禁止落盘）→ 进 S3",
    "S3": "出 ≤5 步执行计划（四属性）并落 PLAN.md → 进 S4",
    "S4": "逐步执行；异常给 3 个方案；每阶段出小结 → 进 S5",
    "S5": "出交付验收单 + 自我反证 → 进 S6",
    "S6": "问 GitHub/归档 → 出五项汇报 → 结束",
}

STATE_REL = Path(".workbuddy") / "flow.json"


# ---------------------------------------------------------------- 读写状态

def state_path(root: Path) -> Path:
    return root / STATE_REL


def load(root: Path):
    p = state_path(root)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print("[!!] 状态文件损坏: %s (%s)" % (p, e), file=sys.stderr)
        return None


def save(root: Path, st) -> None:
    p = state_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def new_state(root: Path, name=None):
    return {
        "project": name or root.name,
        "dir": str(root),
        "stage": "S0",
        "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checklist": {s: {i: False for i in STAGE_ITEMS[s]} for s in STAGE_ORDER},
        "history": [{"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "note": "初始化流程状态"}],
    }


def resolve_item(stage: str, raw: str):
    """把 '序号' 或 '要素名' 解析成真实要素名。"""
    items = STAGE_ITEMS.get(stage, [])
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(items):
            return items[idx]
        return None
    if raw in items:
        return raw
    # 宽松匹配：包含关系
    hits = [i for i in items if raw and (raw in i or i in raw)]
    return hits[0] if len(hits) == 1 else None


# ---------------------------------------------------------------- 展示

def stage_line(stage: str, st):
    items = STAGE_ITEMS.get(stage, [])
    if not items:
        return "  %s  %s  （无勾选项，按需 --note 记录）" % (stage, STAGE_NAME[stage])
    done = sum(1 for i in items if st["checklist"][stage].get(i))
    bar = "●" * done + "○" * (len(items) - done)
    return "  %s  %-16s %s  %d/%d" % (stage, STAGE_NAME[stage], bar, done, len(items))


def cmd_status(root: Path, st, as_json=False):
    if as_json:
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return 0
    cur = st["stage"]
    print("项目：%s" % st["project"])
    print("目录：%s" % st["dir"])
    print("当前阶段：%s %s" % (cur, STAGE_NAME.get(cur, "")))
    print("-" * 56)
    for s in STAGE_ORDER:
        mark = "▶" if s == cur else " "
        print("%s%s" % (mark, stage_line(s, st)[1:]))

    # 当前阶段未完成项
    todo = [i for i in STAGE_ITEMS.get(cur, []) if not st["checklist"][cur].get(i)]
    print("-" * 56)
    if todo:
        print("当前阶段待办（%d 项）：" % len(todo))
        for n, i in enumerate(todo, 1):
            print("  %d) %s" % (n, i))
        print("勾选：--ok %s <序号或名称>" % cur)
    else:
        print("当前阶段门禁已全部通过 ✅")
    print("下一步：%s" % NEXT_HINT.get(cur, "—"))
    if st["history"]:
        print("-" * 56)
        print("最近记录：")
        for h in st["history"][-3:]:
            print("  %s  %s" % (h["ts"], h.get("note", "")))
    return 0


def cmd_gate(root: Path, st, stage: str):
    if stage not in STAGE_ITEMS:
        print("[!!] 未知阶段：%s（可用：%s）" % (stage, " ".join(STAGE_ORDER)), file=sys.stderr)
        return 4
    items = STAGE_ITEMS[stage]
    if not items:
        print("[OK] %s %s：无勾选项，视为通过（可按需 --note 留痕）" % (stage, STAGE_NAME[stage]))
        return 0
    missing = [i for i in items if not st["checklist"][stage].get(i)]
    if missing:
        print("[!!] %s %s 门禁未通过，缺 %d 项：" % (stage, STAGE_NAME[stage], len(missing)))
        for i in missing:
            print("     - %s" % i)
        print("补齐后重跑：--ok %s <序号或名称>" % stage)
        return 2
    print("[OK] %s %s 门禁通过（%d/%d）" % (stage, STAGE_NAME[stage], len(items), len(items)))
    return 0


def cmd_list(root: Path, st, stage: str):
    if stage not in STAGE_ITEMS:
        print("[!!] 未知阶段：%s" % stage, file=sys.stderr)
        return 4
    items = STAGE_ITEMS[stage]
    print("%s %s（%d 项）" % (stage, STAGE_NAME[stage], len(items)))
    for n, i in enumerate(items, 1):
        ok = "x" if st["checklist"][stage].get(i) else " "
        print("  [%s] %d) %s" % (ok, n, i))
    return 0


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser(add_help=True, description="小项目开发全流程阶段状态机")
    ap.add_argument("dir", help="项目目录")
    ap.add_argument("--init", action="store_true", help="初始化状态文件")
    ap.add_argument("--name", default=None, help="项目名（配合 --init）")
    ap.add_argument("--set", dest="set_stage", default=None, help="推进到某阶段，如 S3")
    ap.add_argument("--ok", nargs=2, metavar=("阶段", "要素"), default=None, help="勾选某要素")
    ap.add_argument("--unok", nargs=2, metavar=("阶段", "要素"), default=None, help="取消勾选")
    ap.add_argument("--list", dest="list_stage", default=None, help="列出某阶段待办项")
    ap.add_argument("--gate", dest="gate_stage", default=None, help="校验某阶段门禁")
    ap.add_argument("--note", default=None, help="追加一条历史记录")
    ap.add_argument("--json", action="store_true", help="机器可读输出")
    args = ap.parse_args()

    root = Path(args.dir).expanduser().resolve()
    if not root.exists():
        print("[!!] 目录不存在：%s" % root, file=sys.stderr)
        return 4

    # --init
    if args.init:
        p = state_path(root)
        if p.exists():
            print("[OK] 已存在状态文件，未覆盖：%s" % p)
            return 0
        st = new_state(root, args.name)
        save(root, st)
        print("[OK] 已初始化：%s" % p)
        print("    当前阶段 S0；用 --ok S1 <要素> 开始勾选。")
        return 0

    st = load(root)
    if st is None:
        print("[!!] 尚未初始化：%s" % state_path(root), file=sys.stderr)
        print("     先跑：python flow_state.py \"%s\" --init" % root, file=sys.stderr)
        return 3

    # 阶段推进
    if args.set_stage:
        s = args.set_stage.upper()
        if s not in STAGE_ORDER:
            print("[!!] 未知阶段：%s（可用：%s）" % (s, " ".join(STAGE_ORDER)), file=sys.stderr)
            return 4
        old = st["stage"]
        # 前进前校验【途经的所有阶段】的门禁（仅提示，不阻断——用户可能确实要跳）
        warn = None
        i_old, i_new = STAGE_ORDER.index(old), STAGE_ORDER.index(s)
        if i_new > i_old:
            blocked = []
            for k in range(i_old, i_new):
                stage_k = STAGE_ORDER[k]
                miss = [i for i in STAGE_ITEMS.get(stage_k, [])
                        if not st["checklist"][stage_k].get(i)]
                if miss:
                    blocked.append("%s 缺 %s" % (stage_k, "、".join(miss)))
            if blocked:
                warn = "；".join(blocked)
        st["stage"] = s
        st["history"].append({
            "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "推进 %s → %s" % (old, s) + ("（⚠ %s）" % warn if warn else ""),
        })
        save(root, st)
        print("[OK] 阶段：%s → %s（%s）" % (old, s, STAGE_NAME[s]))
        if warn:
            print("[!!] 注意：%s" % warn)
        return 0

    # 勾选 / 取消
    for flag, val in (("--ok", args.ok), ("--unok", args.unok)):
        if val:
            stage, raw = val[0].upper(), val[1]
            if stage not in STAGE_ITEMS:
                print("[!!] 未知阶段：%s" % stage, file=sys.stderr)
                return 4
            item = resolve_item(stage, raw)
            if not item:
                print("[!!] %s 下找不到要素「%s」" % (stage, raw), file=sys.stderr)
                print("     可用：%s" % "、".join(STAGE_ITEMS[stage]), file=sys.stderr)
                return 4
            on = flag == "--ok"
            st["checklist"][stage][item] = on
            st["history"].append({
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "note": "%s %s.%s" % ("完成" if on else "取消", stage, item),
            })
            save(root, st)
            print("[%s] %s · %s" % ("x" if on else " ", stage, item))
            missing = [i for i in STAGE_ITEMS[stage] if not st["checklist"][stage].get(i)]
            if not missing:
                print("[OK] %s 门禁已全部通过 ✅ — 可以 --set <下一阶段>" % stage)
            else:
                print("     还剩 %d 项：%s" % (len(missing), "、".join(missing)))
            return 0

    if args.list_stage:
        return cmd_list(root, st, args.list_stage.upper())

    if args.gate_stage:
        return cmd_gate(root, st, args.gate_stage.upper())

    if args.note:
        st["history"].append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "note": args.note})
        save(root, st)
        print("[OK] 已记录：%s" % args.note)
        return 0

    return cmd_status(root, st, args.json)


if __name__ == "__main__":
    sys.exit(main())
