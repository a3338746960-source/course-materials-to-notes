# 课程材料 → Obsidian 复习笔记

**把一学期几十份课件、一本电子课本、几十小时的课堂录音，压成一棵两天就能过一遍的复习树。**

![license](https://img.shields.io/badge/license-MIT-blue.svg)
![language](https://img.shields.io/badge/%E6%96%87%E6%A1%A3-%E4%B8%AD%E6%96%87-brightgreen.svg)
![python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![obsidian](https://img.shields.io/badge/Obsidian-vault-7C3AED.svg)

一个用于 AI 编程助手（WorkBuddy / Claude Code 等）的 **Skill**：把散落在文件夹里的课程原始材料整合成结构化的 Obsidian 知识库，服务于**考试复习**与**课后快速回顾**，而不是建造复杂的"第二大脑"。

---

## 它解决什么问题

学期结束时，你手上通常是这样一堆东西：

```
课件/      几十份 PPT / PDF，每份 40–80 页
课本/      一本几百页的电子书
录音纪要/  几十小时的课堂转写，还有整理版和逐字稿两套
syllabus   一份 PDF 或 docx
```

想复习的时候，你得**重新翻一遍所有材料**——这正是最浪费时间的地方。

这个 Skill 做的事，是把这些材料**压缩、融合、分级**成四层结构，每一层对应一个复习时长：

| 复习时长 | 看哪一层 |
|---|---|
| 2 分钟 | **Course Hub** —— 这门课到底考什么、权重多少 |
| 10 分钟 | **Weekly Review** —— 本周讲了什么、什么必须会 |
| 20–30 分钟 | **Lecture Note** —— 每节课的完整脉络 |
| 深挖一个知识点 | **Concept Note** —— 概念的定义、图示、出现于哪几讲 |
| 想看原图 | **原始 PPT/PDF** —— 按页码直接嵌入 |

**目标压缩率 40–60%** —— 保留原课程信息里最有学习价值的部分，剩下的丢掉。

---

## 核心特性

**🔍 证据分级，不编造**
严格区分 `计划中` / `课件已到位` / `已讲授` / `老师强调` / `与考核相关` 五种状态。没有课堂录音就绝不写"老师强调了"；课件存在 ≠ 老师讲过。**这是本 Skill 与"让 AI 总结一下 PPT"最本质的区别。**

**📄 书面材料 > 课堂录音**
录音转写必然有噪音（教材作者名被听成同音中文、deadweight loss 记成 "dead loss"、权重数字说错）。凡录音与 syllabus / 课件冲突，一律以书面为准。而且——**"整理版纪要和逐字稿两处一致"不能提高可信度，两者同源，会一起错。**

**🀄 阅读路径全中文**
小节标题、表格列头、字段标签、状态值全部中文化；术语本体保留英文；PPT 英文原句**降级为引用附注**而非删除。阅读路径中文占比可达 82–97%，同时不丢考试卷面用语。

**🔗 同名文件链接消歧**
7 门课就有 7 个 `Course Hub.md`，Obsidian 的 `[[Course Hub]]` 会歧义。本 Skill 规定路径限定写法，并附带一条规律：**每新增一个同名文件，都会让原先靠唯一性侥幸成立的旧链接失效** —— 所以每次新增后必须复跑歧义审计。

**🛠 真的能跑的工具链**
老式 `.ppt`（二进制 OLE 格式）在 macOS 上没有可用的命令行转换器（LibreOffice 通常未装、WPS 沙盒版无法命令行调用）。本仓库自带一个**递归下降的 OLE 解析器**，直接读 `PowerPoint Document` 流提取文本。

---

## 工作流

```
原始材料                    Skill 的处理                    产出
─────────────────────────────────────────────────────────────────────
syllabus ──┐
课件 PPT  ──┤  ① 提取文本（extract.py）        ┌─ Course Hub.md
录音纪要  ──┼─ ② 判定证据等级                   ├─ Lectures/LXX - Topic.md
课本      ──┤  ③ 压缩到 40–60%                 ├─ Concepts/Concept Name.md
转写原文  ──┘  ④ 中文化改写（relang.py）        ├─ Weekly Reviews/Week XX.md
               ⑤ 链接消歧与审计                 └─ 考试与截止日期总览.md
```

增量推进：每次拿到新材料，只更新受影响的那几页，**不重写整个库**。

---

## 安装

本仓库就是一份 Skill。把它放到你的助手的 skills 目录即可。

**WorkBuddy / Claude Code（用户级）：**

```bash
git clone https://github.com/<你的账号>/course-materials-to-notes.git
cp -r course-materials-to-notes ~/.workbuddy/skills/obsidian-course-vault
# 或 Claude Code：
# cp -r course-materials-to-notes ~/.claude/skills/obsidian-course-vault
```

**项目级**（只对某个项目生效）：放进 `<项目>/.workbuddy/skills/obsidian-course-vault/`。

安装后，直接对助手说类似这样的话就会触发：

> 帮我把 `课件/` 里的材料整理成 Obsidian 笔记
> 这门课的录音纪要我放进去了，更新一下
> 这些笔记英文太多了，看着费劲

**依赖：**

```bash
pip install pdfplumber python-docx olefile    # 必装
pip install python-pptx                        # 可选，仅在需要读 .pptx 时
```

---

## 快速开始（手动使用）

即使不装成 Skill，工具也可以单独用。

```bash
# 1) 提取材料文本
python tools/extract.py "微观经济学/课件/Ch01.ppt" /tmp/ch01.txt
python tools/extract.py "微观经济学/课件/第1讲.pdf" /tmp/l01.txt

# 2) 按模板写笔记（templates/ 下有四个骨架）
cp "templates/Lecture Note.md" "University/微观经济学/Lectures/L01 - 主题.md"

# 3) 把笔记里的英文标签与英文定义句中文化
cp tools/lang_rules.example.json /tmp/lang_rules.json
#    编辑 lang_rules.json：把 exact 段替换为你本课程的实际改写对
python tools/relang.py --rules /tmp/lang_rules.json --root University --dry   # 先试运行
python tools/relang.py --rules /tmp/lang_rules.json --root University         # 确认后落地

# 4) 自检阅读路径中文占比
python tools/relang.py --root University --stats
```

---

## 目录结构

```
.
├── SKILL.md                      ← 完整方法论（14 节，本仓库的核心）
├── README.md
├── LICENSE
├── templates/                    ← 四类笔记的骨架，直接复制使用
│   ├── Course Hub.md
│   ├── Lecture Note.md
│   ├── Concept Note.md
│   └── Week XX Review.md
├── tools/
│   ├── extract.py                ← 材料文本提取（PDF / docx / .ppt / .pptx）
│   ├── relang.py                 ← 批量改写引擎（引擎与规则分离）
│   └── lang_rules.example.json   ← 规则示例，内置 66 条通用标签映射
└── examples/
    └── 改写前后对比.md            ← 语言规范的效果演示
```

### 建议的 Vault 布局

```
<Vault 根目录>/                    ← 含 .obsidian，是所有材料的共同上级
├── 微观经济学/
│   ├── 课件/
│   ├── 课堂录音纪要/
│   └── 课本/
├── 宏观经济学/
│   └── ...
└── University/                    ← 笔记单独一支，与原始材料并列
    ├── 微观经济学/
    │   ├── Course Hub.md
    │   ├── Lectures/L01 - 主题.md
    │   ├── Concepts/概念名.md
    │   └── Weekly Reviews/Week 01 Review.md
    └── 考试与截止日期总览.md
```

**关键点：Vault 根必须是所有原始材料的共同上级目录** —— 否则 `![[第1讲.pdf#page=18]]` 解析不到文件，嵌图会变成灰字。

---

## 工具说明

### `tools/extract.py`

| 格式 | 实现 | 输出特点 |
|---|---|---|
| PDF | `pdfplumber` | 逐页输出，标注每页 `images=N`（便于判断是否扫描件） |
| .docx | `python-docx` | 保留 Heading 层级与表格（syllabus 的考核表常是表格） |
| **.ppt** | **自写 OLE 解析器** | 递归下降遍历记录树，提取 `TextCharsAtom` / `TextBytesAtom` |
| .pptx | `python-pptx`（可选） | 按 slide 分组输出 |

### `tools/relang.py`

通用批量改写引擎。**引擎与数据分离**——同一份脚本可复用到任意课程，只需换规则 JSON。

```bash
python tools/relang.py --rules <rules.json> --root <笔记目录> [--dry] [--stats]
```

设计要点：

- `exact`（精确对）+ `global`（全局规则）两段，**先精确、再全局**，否则精确对的锚点会被全局替换提前破坏
- 每处替换**报告命中数**，未命中单独列出 —— 改了什么必须可审计，不能静默漏改
- `--dry` 试运行，确认 0 异常未命中后再落地
- **幂等**，重复运行结果不变
- `--stats` 统计阅读路径中文占比

---

## 设计原则

| 原则 | 含义 |
|---|---|
| **准确性 > 学习价值 > 清晰度 > 完整性 > 笔记数量** | 优先级顺序，冲突时前者胜 |
| **压缩到 40–60%** | 不是目标，是手段——用"未来复习时这条值不值得再看到"来筛 |
| **只有存在讲授证据才建讲义** | 否则一片 `课件已到位` 的空壳反而污染 Graph |
| **不为每个术语建概念页** | 须满足六条门槛之一（跨讲出现 / 核心框架 / 与考核相关 …） |
| **不做无效链接** | 未建立的笔记不写 `[[ ]]`，避免 Graph 里一堆未解析节点 |
| **不删文件** | 合并/废弃的文件移入 `.workbuddy/_archive/`（dot 目录 Obsidian 不索引，但可还原） |
| **破坏性操作先问** | 新增与增量维护可自动执行；删除、大规模移动、重构必须先确认 |

---

## 踩过的坑（本仓库最值钱的部分）

这些都是在真实使用中踩出来的，已全部写入 `SKILL.md`：

| 坑 | 现象 | 处理 |
|---|---|---|
| **.ppt 解析返回 0 字符** | 遍历器遇容器记录按 `rec_len` 整块跳过，而文字块藏在容器**内部** | 判据 `(rec_ver_inst & 0x000F) == 0x000F` 即容器，**必须递归** |
| **.ppt 页码不可靠** | 逐页分组数量在不同 deck 差异极大（0/1/8 不等） | 正文可靠，**不要依赖 SLIDE 编号定位页码** |
| **课件页码 ≠ PPT 页码** | 部分课件 PDF 含封面页 → PDF 第 N 页 = 原 PPT 第 N−1 页 | 嵌入填 PDF 页码，图注**同时标出两者**，引用前先核对 |
| **"假纪要"** | 名为"课堂录音纪要"的文件夹里其实是课件的重复副本 | 用 `md5` 校验；一致则说明该课**没有真实纪要**，只能标 `课件已到位` |
| **文件名 ≠ 章节号** | 文件名 `1.2` 里装的其实是 `§1.1` | **以内容章节标记为准**，不要按文件名推测 |
| **同名链接事后引爆** | 新增一个同名文件，让旧笔记里靠唯一性成立的链接当场变歧义 | 每次新增同名文件后**全库复跑歧义审计** |
| **"某讲已讲授" ≠ "该章讲完了"** | 第一次课通常是导论，只覆盖第一章的一小部分 | 讲义与主页**双处声明覆盖边界**；未讲的课件页**不嵌入** |
| **纪要里混入 AI 注释** | 整理版纪要含 `【AI 注释】`、`待查证盲区` 等小节 | 那是**生成方推断，不是课程材料**，一律不得采信 |
| **录音串音** | 课堂录音尾部混入完全无关的内容（如时政解说） | 剔除并在笔记中标注；提醒使用者检查录音设备 |
| **结构调整导致路径失效** | 挪动材料目录后，笔记里写死的 `` `课件/课程/` `` 全指向不存在的目录 | 结构变动后**复跑路径审计** |

---

## 适用范围与边界

**适合：**

- 商科 / 经济 / 社科类课程，以 PPT + syllabus + 录音转写为主要材料
- 目标是考试复习与课后回顾，而不是完备的知识管理
- 一学期 7–8 门课，维护成本必须足够低

**不适合：**

- 需要逐字保留全部信息的场景（本方法论**主动丢弃 40–60%**）
- 材料是扫描件（本工具链不含 OCR，需要先自行 OCR）
- 需要跨课程知识关联（本方法论**明确禁止**跨课程 Concept Link）

**版权提醒：** 本仓库只包含方法论、脚本与模板。**请不要把你从老师和出版社获得的课件、电子课本、课堂录音推送到公开仓库。**

---

## License

[MIT](LICENSE)

---

## 致谢

方法论沉淀自一个真实学期的使用过程：8 门课、几十份课件、4 门课的课堂录音，以及在过程中踩到的每一个坑。
