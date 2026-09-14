#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
relang —— 课程笔记批量改写引擎
================================

把 Obsidian 课程笔记从「英文结构标签 + 直贴英文原句」改写成
「中文结构标签 + 中文主述 + 英文原句降级为引用附注」。

引擎与数据分离：本脚本只负责"怎么改"，"改什么"放在外置 JSON 规则文件里。
这样同一份脚本可以复用到任意课程，不必每次都改代码。

用法
----
    python relang.py --rules <rules.json> --root <笔记根目录> [--dry] [--stats]

    --rules   规则文件路径（见 lang_rules.example.json）
    --root    要处理的目录，递归处理其中所有 .md
    --dry     试运行：只报告会改多少处，不写文件
    --stats   统计每个文件的"阅读路径中文占比"，不做任何改写

规则文件格式
------------
    {
      "exact": {
        "<相对 root 的文件路径>": [ ["原文", "改写"], ... ]
      },
      "global": [ ["原文", "改写"], ... ]
    }

执行顺序：**先 exact、再 global**。
原因：global 往往是宽泛的标签替换（如 `**Definition**：` → `**定义**：`），
若先跑 global，可能把 exact 里作为定位锚点的原串提前破坏掉，导致 exact 失配。

设计原则
--------
  1. 每处替换报告命中数，未命中单独列出 —— "改了什么"必须可审计，不能静默漏改。
  2. 支持 --dry 试运行，确认 0 未命中后再落地。
  3. 幂等：重复运行结果不变（替换掉的原串第二次已不存在）。
  4. 落地前请自行备份：cp -r <笔记目录> <备份目录>
"""

import argparse
import json
import os
import re
import sys

PPT_PREFIX = "> PPT 原文："


def load_rules(path):
    """
    读规则文件。允许以下写法，都是等价的：
        ["原文", "改写"]
        {"old": "原文", "new": "改写"}
    以 "_" 开头的键、以及含 "_" 标记的字典，一律视为注释并跳过
    （JSON 不支持注释，用这种方式让人能在规则文件里写说明）。
    """
    with open(path, encoding="utf-8") as f:
        rules = json.load(f)

    def norm(pairs):
        out = []
        for p in pairs:
            if isinstance(p, dict):
                if "_" in p and "old" not in p:
                    continue  # 注释行
                if "old" not in p:
                    continue
                out.append((p["old"], p["new"]))
            elif isinstance(p, list) and len(p) == 2:
                out.append((p[0], p[1]))
        return out

    exact_raw = rules.get("exact", {}) or {}
    exact = {k.rstrip("/"): norm(v)
             for k, v in exact_raw.items() if not k.startswith("_")}
    glob = norm(rules.get("global", []) or [])
    return exact, glob


def iter_md(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if name.endswith(".md"):
                yield os.path.join(dirpath, name)


def apply_exact(text, pairs):
    """精确改写。返回 (新文本, [(old, 命中数), ...])"""
    report = []
    for old, new in pairs:
        n = text.count(old)
        report.append((old, n))
        if n:
            text = text.replace(old, new)
    return text, report


def apply_global(text, pairs):
    report = []
    for old, new in pairs:
        n = text.count(old)
        report.append((old, n))
        if n:
            text = text.replace(old, new)
    return text, report


def rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def cmd_rewrite(root, rules_path, dry):
    exact, glob = load_rules(rules_path)
    files = sorted(iter_md(root))
    if not files:
        print(f"!! {root} 下没有 .md 文件", file=sys.stderr)
        return 1

    total_hits = 0
    missed_exact = []
    changed_files = []
    per_file = []

    for path in files:
        text = open(path, encoding="utf-8").read()
        original = text
        r = rel(root, path)
        hits = 0

        if r in exact:
            text, rep = apply_exact(text, exact[r])
            for old, n in rep:
                if n == 0:
                    missed_exact.append((r, old[:70]))
                hits += n

        text, rep = apply_global(text, glob)
        for old, n in rep:
            if n == 0:
                missed_exact.append(("(global) " + r, old[:70]))
            hits += n

        if text != original:
            changed_files.append(r)
            if not dry:
                open(path, "w", encoding="utf-8").write(text)
        total_hits += hits
        per_file.append((r, hits))

    mode = "【试运行 --dry，未写盘】" if dry else "【已写盘】"
    print(f"{mode} 规则：{rules_path}")
    print(f"扫描 {len(files)} 个 md，改动 {len(changed_files)} 个文件，共 {total_hits} 处替换\n")

    print("按文件命中：")
    for r, h in per_file:
        if h:
            print(f"  {h:>5}  {r}")

    if missed_exact:
        print(f"\n⚠️ 未命中 {len(missed_exact)} 条（规则里的原串在笔记中找不到）：")
        for r, old in missed_exact:
            print(f"  {r}\n      → {old}...")
        print("\n未命中通常有两类原因，都不一定是错误：")
        print("  a) 该规则对这类文件本就不适用（例如标签规则只作用于讲义，不作用于概念页）。")
        print("  b) exact 已先行改写了同一处，global 第二次自然找不到 —— 这是设计预期。")
        print("若某条 exact 在你的目标文件里未命中，才说明规则或笔记已被改动过，请核对。")
    else:
        print("\n所有规则均至少命中一次。")

    if not changed_files:
        print("\n没有文件需要改动 —— 规则可能已全部应用过（幂等）。")
    elif dry:
        print("\n确认无误后去掉 --dry 再跑一次即可落地。")
    return 0


# --------------------------------------------------------------------------
# 阅读路径中文占比统计
# --------------------------------------------------------------------------
def cmd_stats(root):
    """
    阅读路径 = 排除引用块（>）、图片嵌入（![[]]）、表格行（|）、分隔线、代码块。
    这些位置保留英文是"证据"，不属于阅读路径。
    """
    files = sorted(iter_md(root))
    if not files:
        print(f"!! {root} 下没有 .md 文件", file=sys.stderr)
        return 1

    print("阅读路径中文占比（排除引用块 / 嵌图 / 表格行 / 代码块）")
    print(f"{'文件':<56}{'正文中文占比':>12}{'全文中文数':>12}")
    print("-" * 82)

    low = []
    for path in files:
        lines = open(path, encoding="utf-8").read().split("\n")
        body = [l for l in lines if not l.lstrip().startswith((">", "![[", "|", "---", "```"))]
        allt = "\n".join(lines)
        bt = "\n".join(body)
        zh_all = len(re.findall(r"[\u4e00-\u9fff]", allt))
        z = len(re.findall(r"[\u4e00-\u9fff]", bt))
        e = len(re.findall(r"[A-Za-z]+", bt))
        pct = z / (z + e) * 100 if (z + e) else 0.0
        r = rel(root, path)
        flag = "  ← 偏低" if pct < 85 else ""
        if pct < 85:
            low.append(r)
        print(f"{r:<56}{pct:>11.1f}%{zh_all:>12}{flag}")

    print("-" * 82)
    if low:
        print(f"\n⚠️ {len(low)} 个文件低于 85%，说明仍有英文落在正文里：")
        for r in low:
            print(f"  {r}")
    else:
        print("\n全部文件均 ≥ 85%。")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="课程笔记批量改写引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--rules", help="规则 JSON 路径")
    ap.add_argument("--root", required=True, help="要处理的笔记目录（递归）")
    ap.add_argument("--dry", action="store_true", help="试运行，不写盘")
    ap.add_argument("--stats", action="store_true", help="只统计阅读路径中文占比")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.root))
    if not os.path.isdir(root):
        print(f"!! 目录不存在：{root}", file=sys.stderr)
        return 1

    if args.stats:
        return cmd_stats(root)

    if not args.rules:
        print("!! 需要 --rules（或用 --stats 只做统计）", file=sys.stderr)
        print("   参考 tools/lang_rules.example.json", file=sys.stderr)
        return 1
    if not os.path.isfile(args.rules):
        print(f"!! 规则文件不存在：{args.rules}", file=sys.stderr)
        return 1

    return cmd_rewrite(root, args.rules, args.dry)


if __name__ == "__main__":
    sys.exit(main())
