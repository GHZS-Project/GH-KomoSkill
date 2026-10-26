#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""install.py — 把 GH-KomoSkill 装到目标 agent 的 skills 目录。

用法
----
  python scripts/install.py                        # 自动探测已存在的 skills 根目录
  python scripts/install.py --target workbuddy     # 装到 ~/.workbuddy/skills/
  python scripts/install.py --target codex         # 装到 ~/.codex/skills/
  python scripts/install.py --dest D:/my/skills    # 装到自定义目录
  python scripts/install.py --dry-run              # 只看会做什么，不落盘
  python scripts/install.py --force                # 覆盖已存在的同名技能

安装结果
--------
  <skills_root>/gh-komoskills/   ← 一个自包含技能目录（SKILL.md + references + scripts + templates）

退出码
------
  0 = 成功（或已是最新）
  1 = 失败
  2 = 参数错误
"""

import argparse
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SKILL_NAME = "gh-komoskills"
REPO_ROOT = Path(__file__).resolve().parent.parent

TARGETS = {
    "workbuddy": Path.home() / ".workbuddy" / "skills",
    "codex": Path.home() / ".codex" / "skills",
    "claude": Path.home() / ".claude" / "skills",
}

# 不进安装包的目录 / 文件
SKIP_DIRS = {".git", "__pycache__", ".github", "node_modules", ".venv", ".idea", ".vscode"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}


def log(msg=""):
    print(msg)


def detect_targets():
    """返回已存在的 skills 根目录（按 TARGETS 顺序）。"""
    found = []
    for name, root in TARGETS.items():
        if root.is_dir():
            found.append((name, root))
    return found


def iter_payload():
    """遍历仓库根下应安装的文件（相对路径）。"""
    for p in sorted(REPO_ROOT.rglob("*")):
        if p.is_dir():
            continue
        rel = p.relative_to(REPO_ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if rel.name in SKIP_FILES:
            continue
        if rel.suffix == ".pyc":
            continue
        yield rel


def main():
    ap = argparse.ArgumentParser(
        description="把 GH-KomoSkill 装到目标 agent 的 skills 目录",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--target", choices=sorted(TARGETS), help="目标运行时")
    ap.add_argument("--dest", help="自定义 skills 根目录（与 --target 二选一）")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的同名技能")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划，不写文件")
    args = ap.parse_args()

    if args.target and args.dest:
        log("[!!] --target 与 --dest 只能选一个")
        return 2

    # 决定 skills 根
    if args.dest:
        skills_root = Path(args.dest).expanduser().resolve()
        label = "custom"
    elif args.target:
        skills_root = TARGETS[args.target].expanduser().resolve()
        label = args.target
    else:
        found = detect_targets()
        if not found:
            log("[!!] 没探测到任何已知 skills 目录。请用 --target 或 --dest 指定。")
            log("     已知位置：")
            for n, r in TARGETS.items():
                log("       %-10s %s" % (n, r))
            return 2
        if len(found) > 1:
            log("[!!] 探测到多个 skills 目录，请用 --target 指定其一：")
            for n, r in found:
                log("       --target %-10s %s" % (n, r))
            return 2
        label, skills_root = found[0]

    dest = skills_root / SKILL_NAME
    payload = list(iter_payload())

    log("源目录  : %s" % REPO_ROOT)
    log("目标运行时: %s" % label)
    log("目标目录: %s" % dest)
    log("待装文件: %d 个" % len(payload))

    if args.dry_run:
        log("")
        log("[dry-run] 将写入以下文件：")
        for rel in payload:
            log("  + %s" % rel)
        log("")
        log("[dry-run] 未做任何改动。")
        return 0

    if dest.exists():
        if not args.force:
            log("")
            log("[OK] 已存在：%s" % dest)
            log("     如需覆盖，加 --force")
            return 0
        log("")
        log("[..] 覆盖已有安装：%s" % dest)
        shutil.rmtree(dest)

    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    for rel in payload:
        src = REPO_ROOT / rel
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1

    log("")
    log("[OK] 已安装 %d 个文件 → %s" % (n, dest))
    log("")
    log("验证：")
    log("  python \"%s\"          # 自检" % (dest / "scripts" / "doctor.py"))
    log("")
    log("然后在对话里说：")
    log("  做个工具，走我的流程")
    log("")
    log("正确表现：它只问一句「这个工具解决什么问题？什么场景下用？」")
    return 0


if __name__ == "__main__":
    sys.exit(main())
