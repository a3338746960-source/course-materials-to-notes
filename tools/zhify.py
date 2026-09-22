#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 本文件为脱敏版：本地绝对路径与课程名已替换为占位符（课程A / 课程B），使用前请改成你自己的。
"""把 课程A / 课程B 两门课的笔记全中文化（正文 + 文件名 + 链接）。
用法：python3 zh.py          # 空跑，只报告
      python3 zh.py --apply  # 落盘
"""
import os, re, sys

VAULT = os.environ.get('ZH_VAULT', os.getcwd())
COURSES = ['课程A', '课程B']
APPLY = '--apply' in sys.argv

# ---------------------------------------------------------------- 文件重命名
RENAME = {
    'Course Hub': '课程主页',
    'Week 02 Review': '第 02 周复习',
    'Week 03 Review': '第 03 周复习',
    'L01 - 导论：会计研究范式与实证研究方法': '第 01 讲 - 导论：会计研究范式与实证研究方法',
    'L02 - 中国股票市场有效性与事件研究法': '第 02 讲 - 中国股票市场有效性与事件研究法',
    'L02 - 条件概率、全概率公式与贝努利概型': '第 02 讲 - 条件概率、全概率公式与贝努利概型',
    'L03 - 随机变量与离散型分布律': '第 03 讲 - 随机变量与离散型分布律',
    'Random Variable': '随机变量',
    'Probability Mass Function': '分布律',
    'Bernoulli and Binomial Distribution': '贝努利分布与二项分布',
    'Total Probability Formula': '全概率公式',
    'Bayes Theorem': '贝叶斯公式',
    'Independence and Mutual Exclusivity': '独立性与互斥',
    'Event Study': '事件研究法',
    'Efficient Market Hypothesis': '有效市场假说',
    'Endogeneity': '内生性',
    'Difference-in-Differences': '双重差分',
    'Post-Earnings Announcement Drift': '盈余后漂移',
    'Libby Box': 'Libby Box 框架',
}
# 改名后在两门课中会重名 ⇒ 必须写路径限定的基名
NEED_PATH = {'课程主页', '第 02 周复习', '第 03 周复习'}

# ---------------------------------------------------------------- 保护段
PROT = re.compile(r'!\[\[[^\]]*\]\]|\[\[[^\]]*\]\]|`[^`\n]*`|\$\$[^$]*\$\$|\$[^$\n]*\$|https?://\S+')
WIKI = re.compile(r'\[\[([^\]\|#]+)(#[^\]\|]*)?(\|[^\]]*)?\]\]')

# ---------------------------------------------------------------- 术语替换规则
RULES = [
    # ---- 通用：讲次代号 / 链接名 / 教学大纲 ----
    (r'(?:教学大纲|syllabus)\s*/\s*course outline', '教学大纲'),
    (r'Assessment', '考核'),
    (r'\bTimeline\b', '课程进度表'),
    (r'Lecture\s*0(\d)\s*[—-]+\s*', r'第 0\1 讲 —— '),
    (r'\s*\((Course A|Course B)\)', ''),
    # ---- 中英并列的表格单元（避免出现「事件日 事件日」） ----
    (r'事件日\s+Event date', '事件日'),
    (r'事件窗口\s+Event window', '事件窗口期'),
    (r'估计窗口\s+Estimation window', '估计窗口'),
    (r'earnings announcement month', '盈余公告月'),
    (r'\bData\b', '数据'),
    (r'\bMethod\b', '方法'),
    (r'Lecture Note', '讲次笔记'),
    (r'Concept Note', '概念笔记'),
    (r'Weekly Reviews?', '周复习'),
    (r'Week\s*0*(\d{1,2})\s*Review', r'第 0\1 周复习'),
    (r'Week\s*0*(\d{1,2})', r'第 \1 周'),
    (r'L0(\d)', r'第 0\1 讲'),
    (r'Course Hub', '课程主页'),
    (r'syllabus,', '教学大纲 '),
    (r'syllabus', '教学大纲'),
    (r'\s*vs\.?\s*', '与'),
    # ---- 课程A ----
    (r'Bernoulli Trials', '贝努利试验'),
    (r'（Random Variable）', ''),
    (r'Random Variable', '随机变量'),
    (r'Bernoulli and Binomial Distribution', '贝努利分布与二项分布'),
    (r'Binomial Distribution', '二项分布'),
    (r'Bernoulli', '贝努利'),
    (r'伯努利', '贝努利'),
    (r'（Probability Mass Function）', ''),
    (r'Probability Mass Function', '分布律'),
    (r'\bPMF\b', '分布律'),
    (r"Bayes'\s*Theorem", '贝叶斯公式'),
    (r'Bayes\s*Theorem', '贝叶斯公式'),
    (r'Total Probability Formula', '全概率公式'),
    (r'Independence and Mutual Exclusivity', '独立性与互斥'),
    (r'Mutual Exclusivity', '互斥'),
    (r'\bIndependence\b', '独立性'),
    (r'Complete Event Group\s*/\s*完备事件组', '完备事件组'),
    (r'Complete Event Group', '完备事件组'),
    (r'Prior & Posterior Probability', '先验概率与后验概率'),
    (r'Multiplication Rule', '乘法公式'),
    (r'（Discrete）', ''),
    (r'\bDiscrete\b', '离散型'),
    (r'\bVenn\b', '维恩'),
    (r'\btrial\b', '试验'),
    # ---- 课程B ----
    (r'Unexpected Income Change', '未预期盈余'),
    (r'Unexpected Earnings', '未预期盈余'),
    (r'unexpected income change', '未预期盈余'),
    (r'income numbers', '盈余数字'),
    (r'income change', '盈余变动'),
    (r'net income', '净利润'),
    (r'\bEPS\b', '每股收益'),
    (r'Abnormal Performance Index', '异常业绩指数'),
    (r'\bAPI\b', '异常业绩指数'),
    (r'Cumulative abnormal returns', '累积异常收益'),
    (r'\bCAAR\b', '平均累积异常收益'),
    (r'\bAAR\b', '平均异常收益'),
    (r'\bCARs?\b', '累积异常收益'),
    (r'\bARs\b', '异常收益率'),
    (r'(?<![A-Za-z])AR(?![A-Za-z_])', '异常收益'),
    (r'Event window', '事件窗口期'),
    (r'Estimation window', '估计窗口'),
    (r'\bEvent date\b', '事件日'),
    (r'[Ee]vent [Ss]tudy', '事件研究法'),
    (r'Fama-French Three Factor Model', 'Fama 三因子模型'),
    (r'Fama 三因子模型（Fama-French Three Factor Model）', 'Fama 三因子模型'),
    (r'Market-adjusted Model', '市场调整模型'),
    (r'Market Model', '市场模型'),
    (r'good news', '好消息'),
    (r'bad news', '坏消息'),
    (r'Winsoriz\w+', '缩尾'),
    (r'\bTreat\b', '处理组'),
    (r'\bPost\b', '政策后'),
    (r'\bDID\b', '双重差分'),
    (r'\bEMH\b', '有效市场假说'),
    (r'\bPEAD\b', '盈余后漂移'),
    (r'\bSemi-strong\b', '半强势'),
    (r'\bWeak\b', '弱势'),
    (r'\bStrong\b', '强势'),
    (r'\bConceptual\b', '概念层'),
    (r'\bOperational\b', '操作层'),
    (r'\bControl\b', '控制层'),
    (r'\bIndependent\b', '自变量'),
    (r'\bDependent\b', '因变量'),
    (r'p-hacking', 'p 值操纵'),
    (r'\bHARKing\b', '先定结论再补假设'),
    (r'Source discrepancy', '来源冲突'),
    (r'MD&A', '管理层讨论与分析'),
    (r'\bOLS\b', '最小二乘'),
    (r'工具变量法（IV）', '工具变量法'),
    (r'\bIV\b', '工具变量法'),
    (r'断点回归（RDD）', '断点回归'),
    (r'\bRDD\b', '断点回归'),
    (r'AI Agent', 'AI 智能体'),
    (r'\bAgent\b', '智能体'),
    (r'\bIdea\b', '选题'),
    (r'Basic introduction of empirical research', ''),
    (r'Efficiency of Chinese Stock Market', ''),
    (r'IPO research in China', ''),
    (r'Information disclosure of listed companies in China', ''),
    (r'Corporate governance and Investor Protection', ''),
    (r'Information Intermediary', ''),
    (r'Course B', ''),
    (r'\b[Cc]ritique\b', '评论'),
    (r'Libby Box（Libby Box 框架）', 'Libby Box 框架'),
    (r'（Libby Box）', ''),
    (r'Cheeting Sheet', '速查纸'),
    (r'Cheating Sheet', '速查纸'),
    (r'（Event Study）', ''),
    (r'Introduces', '引入'),
    (r'\bUpdates\b', '更新'),
    (r'在 Vault 内', '在本库内'),
    # ---- 末尾清理：空格 ----
    (r'(?<=[\u4e00-\u9fff*])\s(?=[\u4e00-\u9fff，。；：、（）])', ''),
    (r'(?<=）)\s(?=[\u4e00-\u9fff])', ''),
    (r' {2,}\|', ' |'),
]

# 文献标题：属专名，先遮蔽再还原，避免内部英文被译
MASKS = [
    'An empirical evaluation of accounting income numbers',
    'Ball and Brown (1968): A retrospective',
    'Journal of Accounting Research',
    'The Accounting Review',
]

# frontmatter 值替换（按行首键名分别处理）
FM_VALUE = [
    (r'^课程A \(Course A\)$', '课程A'),
    (r'^课程B \(Course B\)$', '课程B'),
    (r'^(.*?)\s*\((Course A|Course B)\)$', r'\1'),
    (r'^Autumn 2026$', '2026 秋'),
    (r'^none$', '无'),
    (r'^concept$', '概念'),
    (r'^lecture$', '讲义'),
    (r'^weekly-review$', '周复习'),
    (r'^L0(\d)$', r'第 0\1 讲'),
    (r'^第 0(\d) 讲$', r'第 0\1 讲'),
]
ALIAS_DROP = {
    'PMF', 'random variable', 'Bayes公式', 'Binomial Distribution', 'Bernoulli Distribution',
    'Event Study Method', 'Libby Box Framework', 'DID', 'EMH', 'PEAD', 'BB1968',
    'Post-Earnings Announcement Drift',
}
# 逐条精确替换（H1、frontmatter 整行、固定长句）
EXACT = {
    '# 课程A (Course A)': '# 课程A',
    '# 课程B (Course B)': '# 课程B',
    '# Random Variable（随机变量）': '# 随机变量',
    '# Probability Mass Function（分布律，PMF）': '# 分布律',
    '# Bernoulli and Binomial Distribution（0-1 分布与二项分布）': '# 贝努利分布与二项分布',
    '# Total Probability Formula（全概率公式）': '# 全概率公式',
    "# Bayes' Theorem（贝叶斯公式）": '# 贝叶斯公式',
    '# Independence and Mutual Exclusivity（独立性与互斥）': '# 独立性与互斥',
    '# Event Study（事件研究法）': '# 事件研究法',
    '# Efficient Market Hypothesis（有效市场假说，EMH）': '# 有效市场假说',
    '# Endogeneity（内生性）': '# 内生性',
    '# Difference-in-Differences（双重差分，DID）': '# 双重差分',
    '# Post-Earnings Announcement Drift（PEAD，盈余后漂移）': '# 盈余后漂移',
    '# Libby Box（Libby Box 框架）': '# Libby Box 框架',
    '# Ball and Brown (1968)（BB1968）': '# Ball and Brown（1968）',
    '# Lecture 01 — ': '# 第 01 讲 —— ',
    '# Lecture 02 — ': '# 第 02 讲 —— ',
    '# Lecture 03 — ': '# 第 03 讲 —— ',
    '# Week 02 Review（课程A）': '# 第 02 周复习（课程A）',
    '# Week 03 Review（课程A）': '# 第 03 周复习（课程A）',
    '# Week 02 Review（课程B）': '# 第 02 周复习（课程B）',
    '# Week 03 Review（课程B）': '# 第 03 周复习（课程B）',
    '> 复习入口：2 分钟看本页 → 10 分钟看 Weekly Review → 20–30 分钟看 Lecture Note → 深挖看 Concept Note → 原图看 PPT/PDF。':
        '> 复习入口：2 分钟看本页 → 10 分钟看周复习 → 20–30 分钟看讲次笔记 → 深挖看概念笔记 → 原图看课件。',
    '### 完备事件组（Complete Event Group / 完备事件组）': '### 完备事件组',
    '### 独立性与互斥（Independence vs. Mutual Exclusivity）': '### 独立性与互斥',
    '### 先验概率与后验概率（Prior & Posterior Probability）': '### 先验概率与后验概率',
    '### 1. 乘法公式（Multiplication Rule）': '### 1. 乘法公式',
    '### 2. 全概率公式（Total Probability Formula）——已知原因，求结果': '### 2. 全概率公式——已知原因，求结果',
    "### 3. 贝叶斯公式（Bayes' Theorem）——已知结果，倒推原因": '### 3. 贝叶斯公式——已知结果，倒推原因',
    '### 4. n 重贝努利概型与二项分布（Bernoulli Trials & Binomial Distribution）': '### 4. n 重贝努利概型与二项分布',
    '### ⑤ 伯努利概型与二项分布': '### ⑤ 贝努利概型与二项分布',
    '### 随机变量（Random Variable）': '### 随机变量',
    '### Libby Box 框架（Libby Box）': '### Libby Box 框架',
    '### 内生性（Endogeneity）': '### 内生性',
    '### 双重差分（Difference-in-Differences, DID）': '### 双重差分',
    '### 有效市场假说（Efficient Market Hypothesis, EMH）': '### 有效市场假说',
    '### 会计盈余的信息含量（Information Content）': '### 会计盈余的信息含量',
    '### 未预期盈余（Unexpected Earnings / Unexpected Income Change）': '### 未预期盈余',
    '### 事件研究法（Event Study）': '### 事件研究法',
    '### 数据获取的新范式（AI Agent 抓年报）': '### 数据获取的新范式（AI 智能体抓年报）',
    '### 2. DID 模型与净效应推导': '### 2. 双重差分模型与净效应推导',
    '### 3. 实验研究 → DID 的类比（为什么随机很重要）': '### 3. 实验研究 → 双重差分的类比（为什么随机很重要）',
    '### 6. 全学期论文报告安排（10 篇 → 周次）': '### 6. 全学期论文报告安排（10 篇 → 周次）',
    'aliases: [贝叶斯公式, Bayes公式]': 'aliases: [贝叶斯公式]',
    'aliases: [0-1分布, 两点分布, 二项分布, Binomial Distribution, Bernoulli Distribution]':
        'aliases: [0-1分布, 两点分布, 二项分布]',
    'aliases: [分布律, PMF, Probability Mass Function]': 'aliases: [分布律]',
    'aliases: [随机变量, random variable]': 'aliases: [随机变量]',
    'aliases: [BB1968, Ball and Brown（1968）, 实证会计开山之作]': 'aliases: [Ball and Brown（1968）, 实证会计开山之作]',
    'aliases: [DID, 双重差分]': 'aliases: [双重差分]',
    'aliases: [EMH, 有效市场假说]': 'aliases: [有效市场假说]',
    'aliases: [事件研究法, Event Study Method]': 'aliases: [事件研究法]',
    'aliases: [Libby Box 框架, Libby Box Framework]': 'aliases: [Libby Box 框架]',
    'aliases: [PEAD, 盈余后漂移, 盈余公告后漂移, Post-Earnings Announcement Drift]':
        'aliases: [盈余后漂移, 盈余公告后漂移]',
}


def fix_link(m, course, stats):
    target, anchor, alias = m.group(1), m.group(2) or '', m.group(3) or ''
    base = target.split('/')[-1]
    path_limited = '/' in target
    if not path_limited:
        # 裸链接：目标属于本课 → 直接改名；若改名后两课重名 → 补路径限定
        if base in RENAME:
            new = RENAME[base]
            if new in NEED_PATH:
                folder = 'Weekly Reviews' if '周复习' in new else ''
                prefix = f'{course}/{folder}/' if folder else f'{course}/'
                stats.append(('link->path限定', f'{target} -> {prefix}{new}'))
                target = f'{prefix}{new}'
            else:
                stats.append(('link改名', f'{target} -> {new}'))
                target = new
    else:
        parts = target.split('/')
        # 只处理本课路径；其他课程的同名文件不动
        if parts[0] == course:
            if parts[-1] in RENAME:
                old = parts[-1]
                parts[-1] = RENAME[old]
                stats.append(('link路径改', f'{target} -> {"/".join(parts)}'))
                target = '/'.join(parts)
    if alias:
        a = alias[1:]
        if a in RENAME:
            a = RENAME[a]
        else:
            for pat, rep in RULES:
                a = re.sub(pat, rep, a)
        alias = '|' + a
    return f'[[{target}{anchor}{alias}]]'


def convert(text, course, stats):
    # 1) 链接
    text = WIKI.sub(lambda m: fix_link(m, course, stats), text)
    # 2) 逐行：frontmatter 值、tags、正文
    out, in_fm, fm_done = [], False, False
    for i, line in enumerate(text.split('\n')):
        if i == 0 and line.strip() == '---':
            in_fm, fm_done = True, False
            out.append(line)
            continue
        if in_fm and line.strip() == '---':
            in_fm, fm_done = False, True
            out.append(line)
            continue
        if in_fm:
            m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$', line)
            if m:
                key, val = m.group(1), m.group(2)
                for pat, rep in FM_VALUE:
                    nv = re.sub(pat, rep, val)
                    if nv != val:
                        stats.append(('frontmatter', f'{key}: {val} -> {nv}'))
                        val = nv
                out.append(f'{key}: {val}')
                continue
            if re.match(r'^\s*-\s+\S+$', line):
                v = line.split('-', 1)[1].strip()
                if v in ('concept', 'lecture', 'weekly-review'):
                    nv = {'concept': '概念', 'lecture': '讲义', 'weekly-review': '周复习'}[v]
                    stats.append(('tag', f'{v} -> {nv}'))
                    out.append(line.replace(v, nv))
                    continue
            out.append(line)
            continue
        # 3) 正文：整行精确替换 → 术语规则（保护段跳过）
        s = EXACT.get(line, line)
        if s != line:
            stats.append(('整行', f'{line[:40]} -> {s[:40]}'))
        pos, buf = 0, []
        for pm in PROT.finditer(s):
            seg = s[pos:pm.start()]
            buf.append(apply_rules(seg, stats))
            buf.append(pm.group(0))
            pos = pm.end()
        buf.append(apply_rules(s[pos:], stats))
        out.append(''.join(buf))
    return '\n'.join(out)


def _fixb(pat):
    """把 \\b 换成只在 ASCII 字母数字处生效的边界（中文相邻处 \\b 会失效）。"""
    out, i = [], 0
    while True:
        j = pat.find('\\b', i)
        if j < 0:
            out.append(pat[i:])
            break
        out.append(pat[i:j])
        prev = pat[max(0, j - 2):j]
        if j == 0 or prev.endswith('|') or prev.endswith('('):
            out.append('(?<![0-9A-Za-z])')
        else:
            out.append('(?![0-9A-Za-z])')
        i = j + 2
    return ''.join(out)


RULES = [(re.compile(_fixb(p)), r) for p, r in RULES]
KEEP_PAREN = re.compile(r'@|lianxh|^t\s*=\s*0$|^[XYZ]$|^BB\s*2019$|Ball & Brown|Robert Libby|^PR$')


def _delparen(m):
    return m.group(0) if KEEP_PAREN.search(m.group(1)) else ''


def apply_rules(seg, stats):
    if not seg.strip():
        return seg
    saved = []
    for k, t in enumerate(MASKS):
        if t in seg:
            seg = seg.replace(t, f'\x00{k}\x00')
            saved.append(k)
    seg = re.sub(r'(?<=[\u4e00-\u9fff\u2018\u2019\u201c\u201d\u3008-\u303f\uff00-\uffefA-Za-z\)\*"\'])'
                 r'（([A-Za-z][^（）]{0,60}?)）', _delparen, seg)
    # BB1968：首次出现写全名，其后用「该研究」
    if 'BB1968' in seg:
        n = seg.count('BB1968')
        seg = seg.replace('BB1968', 'Ball and Brown（1968）', 1)
        if n > 1:
            seg = seg.replace('BB1968', '该研究')
        stats.append(('BB1968', f'{n} 处'))
    for pat, rep in RULES:
        new = pat.sub(rep, seg)
        if new != seg:
            stats.append((pat.pattern, f'{len(pat.findall(seg))} 处'))
            seg = new
    for k in saved:
        seg = seg.replace(f'\x00{k}\x00', MASKS[k])
    return seg


def main():
    stats, plan = [], []
    files = []
    for c in COURSES:
        for dp, dn, fn in os.walk(os.path.join(VAULT, 'University', c)):
            for f in sorted(fn):
                if f.endswith('.md'):
                    files.append(os.path.join(dp, f))
    for p in files:
        course = os.path.relpath(p, os.path.join(VAULT, 'University')).split('/')[0]
        txt = open(p, encoding='utf-8').read()
        new = convert(txt, course, stats)
        base = os.path.basename(p)
        newbase = RENAME.get(base[:-3], base[:-3]) + '.md'
        newp = os.path.join(os.path.dirname(p), newbase)
        plan.append((p, newp, txt, new))
    # 报告
    from collections import Counter
    cnt = Counter(k for k, _ in stats)
    print(f"文件 {len(plan)} 篇；改动规则命中：")
    for k, v in cnt.most_common():
        print(f"   {v:>4}  {k[:70]}")
    print("\n=== 重命名 ===")
    for p, np_, _, _ in plan:
        if p != np_:
            print(f"   {os.path.relpath(p, VAULT)}  ->  {os.path.basename(np_)}")
    # 残留拉丁字母（正文，排除保护段与允许清单）
    ALLOW = re.compile(r'Ball and Brown|Fama|Libby|CSMAR|Stata|Python|CRSP|IBM|EPS|IPO|AI|MD5|T\+1|'
                       r'DeepSeek|PPT|Word|PDF|docx|pdf|ppt|lianxh|cufe|Ball|WorkBuddy|'
                       r'B\(n,p\)|SAS|SPSS|Excel|A4|Agent|Internet|\bL0\d\b')
    print("\n=== 正文残留拉丁字母（需人工确认） ===")
    for p, np_, _, new in plan:
        lines = new.split('\n')
        fm = 0
        if lines[0].strip() == '---':
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    fm = i; break
        for i, l in enumerate(lines[fm + 1:], fm + 2):
            s = PROT.sub(lambda m: '', l)
            s = ALLOW.sub('', s)
            if len(re.findall(r'[A-Za-z]', s)) >= 2:
                print(f"   {os.path.relpath(p, VAULT)}:{i}  {s.strip()[:140]}")
    if not APPLY:
        print("\n（空跑模式，未落盘）")
        return
    for p, np_, txt, new in plan:
        if new != txt:
            open(p, 'w', encoding='utf-8').write(new)
        if p != np_:
            os.rename(p, np_)
    # 删除空的 Weekly Reviews 残留
    print("\n已落盘。")


main()
