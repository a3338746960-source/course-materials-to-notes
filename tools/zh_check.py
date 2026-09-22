#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""zhify.py 之后的收尾核查（每次单课全中文化改写后必跑）。

# 本文件为脱敏版：本地绝对路径与课程名已替换为占位符（课程A / 课程B），使用前请改成你自己的。
用法：
    PY=python3
    $PY zh_check.py <vault 根> 课程A 课程B \
        --backup .workbuddy/_archive/2026-09-22-zh-backup

（--backup 的相对路径按 Vault 根解析；课程名只取位置参数。）

做四件事（缺一都会留下隐患）：
  1. 清理 frontmatter 的 aliases（正文规则碰不到它）
  2. 与备份对账「行数 / 嵌图数 / 公式数 / 链接数」——四项必须完全相同
     （若某文件在收尾修正步骤里被**有意**补写内容，如补一行记号对照，会出现 +N 行 / +N 公式；
      差异必须能逐个指名解释，否则就是规则改坏了东西）
  3. 扫描重复译名（双重替换产物，如「盈余后漂移盈余后漂移」）
  4. 全库链接审计：未解析 / 歧义 / 路径不存在
"""
import os, re, sys, glob, collections

VAULT = sys.argv[1] if len(sys.argv) > 1 else '.'
BACKUP = None
if '--backup' in sys.argv:
    i = sys.argv.index('--backup')
    BACKUP = sys.argv[i + 1]
    del sys.argv[i:i + 2]
# 课程名 = 第 3 个位置参数起（--backup 及其值已在上面摘除，不再被误当成课程）
COURSES = [a for a in sys.argv[2:] if not a.startswith('--')]
if BACKUP and not os.path.isabs(BACKUP):
    # 相对路径按 Vault 根解析（脚本可能在别处运行）
    BACKUP = os.path.normpath(os.path.join(VAULT, BACKUP))

PURE_LATIN = re.compile(r"^[A-Za-z][A-Za-z0-9 \-\.&'’,/]*$")
ALIAS_DROP = {'PMF', 'DID', 'EMH', 'PEAD', 'BB1968', 'IV', 'OLS', 'RDD', 'syllabus'}


def files_of(course):
    return sorted(glob.glob(os.path.join(VAULT, 'University', course, '**', '*.md'), recursive=True))


def stats(text):
    return (len(text.split('\n')),
            len(re.findall(r'!\[\[', text)),
            len(re.findall(r'\$[^$\n]+\$', text)),
            len(re.findall(r'(?<!!)\[\[', text)))


def check_aliases(paths):
    changed = 0
    for p in paths:
        t = open(p, encoding='utf-8').read()

        def fix(m):
            nonlocal changed
            items = [x.strip() for x in m.group(1).split(',') if x.strip()]
            keep = [x for x in items if x not in ALIAS_DROP and not PURE_LATIN.match(x)]
            if keep != items:
                changed += 1
                print(f"   aliases 清理 {os.path.relpath(p, VAULT)}: {items} -> {keep}")
            return 'aliases: [' + ', '.join(keep) + ']'

        new = re.sub(r'^aliases: \[(.*)\]$', fix, t, flags=re.M)
        if new != t:
            open(p, 'w', encoding='utf-8').write(new)
    print(f"  ⇒ 清理 {changed} 处")


def check_integrity(course):
    old, new = {}, {}
    for p in glob.glob(os.path.join(BACKUP, course, '**', '*.md'), recursive=True):
        old[os.path.relpath(p, os.path.join(BACKUP, course))] = stats(open(p, encoding='utf-8').read())
    for p in files_of(course):
        new[os.path.relpath(p, os.path.join(VAULT, 'University', course))] = stats(open(p, encoding='utf-8').read())
    a = collections.Counter(old.values())
    b = collections.Counter(new.values())
    ok = (a == b)
    print(f"  逐文件 (行,嵌图,公式,链接) 多重集一致：{'✅ 是' if ok else '❌ 否'}")
    if not ok:
        print("     仅备份有:", dict(a - b))
        print("     仅新库有:", dict(b - a))
    ta = [sum(v[i] for v in old.values()) for i in range(4)]
    tb = [sum(v[i] for v in new.values()) for i in range(4)]
    print(f"  合计 行 {ta[0]}→{tb[0]} / 嵌图 {ta[1]}→{tb[1]} / 公式 {ta[2]}→{tb[2]} / 链接 {ta[3]}→{tb[3]}")


def check_dup(paths):
    pats = [re.compile(r'([\u4e00-\u9fff]{3,8})[\u4e00-\u9fff]\1'),
            re.compile(r'([\u4e00-\u9fff]{2,7})\1')]
    n = 0
    for p in paths:
        for i, line in enumerate(open(p, encoding='utf-8'), 1):
            s = re.sub(r'\$[^$\n]*\$|`[^`\n]*`|\[\[[^\]]*\]\]', '', line)
            for pt in pats:
                m = pt.search(s)
                if m and m.group(0) not in ('什么什么', '极差极差', '非常非常'):
                    print(f"   {os.path.relpath(p, VAULT)}:{i} 疑似重复译名「{m.group(0)}」")
                    n += 1
                    break
    print(f"  ⇒ 疑似 {n} 处（人工确认，中文口语里的叠词是正常的）")


def check_links():
    files = [os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.join(VAULT, 'University'))
             for f in fn if f.endswith('.md')]
    base = collections.defaultdict(list)
    for p in files:
        base[os.path.basename(p)].append(p)
    dups = {k: v for k, v in base.items() if len(v) > 1}
    total = 0
    unres, ambig, pathbad = [], [], []
    for p in files:
        raw = open(p, encoding='utf-8').read()
        txt = re.sub(r'!\[\[[^\]]*\]\]', '', raw)
        for m in re.finditer(r'\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]*)?\]\]', txt):
            t = m.group(1).strip()
            total += 1
            cand = t + '.md'
            if any(q.endswith('/' + cand) for q in files):
                continue
            if '/' in t:
                pathbad.append((p, t))
                continue
            (ambig if os.path.basename(cand) in dups else unres).append((p, t))
    print(f"  笔记 {len(files)} | 链接 {total} | 未解析 {len(unres)} | 歧义 {len(ambig)} | 路径失效 {len(pathbad)}")
    for x in unres[:10]:
        print("    UNRES", x)
    for x in ambig[:10]:
        print("    AMBIG", x)
    for x in pathbad[:10]:
        print("    PATHBAD", x)
    print("  重名组:", {k: len(v) for k, v in sorted(dups.items())})


if __name__ == '__main__':
    paths = [p for c in COURSES for p in files_of(c)]
    print("① aliases 清理")
    check_aliases(paths)
    if BACKUP:
        print("② 内容完整性对账")
        for c in COURSES:
            print(f"  [{c}]")
            check_integrity(c)
    print("③ 重复译名扫描")
    check_dup(paths)
    print("④ 全库链接审计")
    check_links()
