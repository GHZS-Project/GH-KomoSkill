#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""doctor.py — GH-KomoSkill 安装自检。

检查内容
--------
  1. Python 版本
  2. 技能是否已装到某个 skills 根目录
  3. SKILL.md 的 frontmatter（name / description）
  4. references / templates 文件齐不齐
  5. scripts 能不能跑（真实执行 --help）
  6. 中文字符编码是否正常

用法
----
  python scripts/doctor.py
  python scripts/doctor.py --root ~/.workbuddy/skills

退出码
------
  0 = 全部通过
  1 = 有 FAIL
  2 = 只有 WARN
"""

import argparse
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

SKILL_NAME = "gh-komoskills"
HERE = Path(__file__).resolve().parent.parent

EXPECT_REFS = [
    "six-stage-flow.md",
    "prompt-normalize.md",
    "evidence-discipline.md",
    "context-memory.md",
    "capability-routing.md",
    "safety-boundaries.md",
]
EXPECT_SCRIPTS = ["flow_state.py", "project_brief.py", "install.py", "doctor.py"]
EXPECT_TEMPLATES = ["PROJECT.md", "PLAN.md", "AGENTS.md"]

RESULTS = []


def add(level, name, detail=""):
    RESULTS.append((level, name, detail))


def check_python():
    v = sys.version_info
    ok = (v.major, v.minor) >= (3, 8)
    add("OK" if ok else "FAIL", "Python 版本", "%d.%d.%d" % (v.major, v.minor, v.micro))


def find_install(root_hint=None):
    if root_hint:
        cand = Path(root_hint).expanduser().resolve() / SKILL_NAME
        return cand if cand.is_dir() else None
    candidates = [
        Path.home() / ".workbuddy" / "skills" / SKILL_NAME,
        Path.home() / ".codex" / "skills" / SKILL_NAME,
        Path.home() / ".claude" / "skills" / SKILL_NAME,
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def check_frontmatter(base):
    f = base / "SKILL.md"
    if not f.exists():
        add("FAIL", "SKILL.md", "不存在")
        return
    text = f.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        add("FAIL", "SKILL.md frontmatter", "文件未以 --- 开头")
        return
    end = text.find("\n---", 3)
    if end == -1:
        add("FAIL", "SKILL.md frontmatter", "缺少结束的 ---")
        return
    fm = text[3:end]
    has_name = any(l.strip().startswith("name:") for l in fm.splitlines())
    has_desc = "description:" in fm
    if has_name and has_desc:
        add("OK", "SKILL.md frontmatter", "name + description 齐全")
    else:
        add("FAIL", "SKILL.md frontmatter",
            "缺 %s" % "、".join(x for x, y in (("name", has_name), ("description", has_desc)) if not y))


def check_files(base, sub, expect, label):
    d = base / sub
    if not d.is_dir():
        add("FAIL", label, "目录不存在：%s" % sub)
        return
    missing = [x for x in expect if not (d / x).exists()]
    if missing:
        add("WARN", label, "缺 %d 个：%s" % (len(missing), "、".join(missing)))
    else:
        add("OK", label, "%d 个文件齐全" % len(expect))


def check_script_runs(base, name):
    f = base / "scripts" / name
    if not f.exists():
        add("FAIL", "脚本 %s" % name, "不存在")
        return
    try:
        r = subprocess.run(
            [sys.executable, str(f), "--help"],
            capture_output=True, text=True, timeout=25,
        )
        if r.returncode == 0:
            add("OK", "脚本 %s" % name, "可执行")
        else:
            add("FAIL", "脚本 %s" % name, "退出码 %d" % r.returncode)
    except subprocess.TimeoutExpired:
        add("FAIL", "脚本 %s" % name, "执行超时")
    except Exception as e:  # noqa: BLE001
        add("FAIL", "脚本 %s" % name, str(e)[:60])


def check_encoding(base):
    """确认 README/SKILL 里的中文没被写坏。"""
    probe = "流程"
    bad = []
    for name in ("SKILL.md", "README.md"):
        f = base / name
        if not f.exists():
            continue
        try:
            f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            bad.append(name)
    if bad:
        add("FAIL", "UTF-8 编码", "无法按 UTF-8 读取：%s" % "、".join(bad))
    else:
        add("OK", "UTF-8 编码", "可正常读取（探针字符「%s」）" % probe)


def main():
    ap = argparse.ArgumentParser(description="GH-KomoSkill 安装自检")
    ap.add_argument("--root", help="skills 根目录（默认自动探测）")
    args = ap.parse_args()

    print("GH-KomoSkill · doctor")
    print("=" * 52)
    print("源码目录：%s" % HERE)

    check_python()

    installed = find_install(args.root)
    if installed:
        add("OK", "安装位置", str(installed))
        base = installed
    else:
        add("WARN", "安装位置", "未在已知 skills 目录找到（只检查源码目录）")
        base = HERE

    print("检查目录：%s" % base)
    print("-" * 52)

    check_frontmatter(base)
    check_files(base, "references", EXPECT_REFS, "references")
    check_files(base, "templates", EXPECT_TEMPLATES, "templates")
    check_files(base, "scripts", EXPECT_SCRIPTS, "scripts")
    for s in ("flow_state.py", "project_brief.py"):
        check_script_runs(base, s)
    check_encoding(base)

    print("-" * 52)
    for level, name, detail in RESULTS:
        print("  [%-4s] %-22s %s" % (level, name, detail))

    n_ok = sum(1 for r in RESULTS if r[0] == "OK")
    n_warn = sum(1 for r in RESULTS if r[0] == "WARN")
    n_fail = sum(1 for r in RESULTS if r[0] == "FAIL")
    print("-" * 52)
    print("合计：OK %d / WARN %d / FAIL %d" % (n_ok, n_warn, n_fail))
    print("")

    if n_fail:
        print("结论：❌ 有失败项，先修再使用。")
        return 1
    if n_warn:
        print("结论：⚠️ 可用，但有告警项。")
        return 2
    print("结论：✅ 全部通过。装好了。")
    print("下一步：在对话里说「做个工具，走我的流程」验证 S1 是否生效。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
