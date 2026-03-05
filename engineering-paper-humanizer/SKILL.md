---
name: engineering-paper-humanizer
description: 深度重写工程类中文学术文本（LaTeX/Markdown/纯文本），按核心维度消除 AIGC 痕迹，注入人类工程师行文风格与真实个性。当用户提及洗稿、去AI、humanize、降AIGC、防检测、人味、AI浓度，或要求对中文工程类文档进行去 AI 化改写时，必须使用此 Skill。支持 LaTeX (.tex)、Markdown (.md) 和纯文本格式。
compatibility:
  python: ">=3.7"
  git: optional
---

# Engineering Paper Humanizer

深度重写工程类学术文本，彻底消除 AI 生成痕迹。在保留原意、专业术语、文献引用和 LaTeX 命令完整的前提下，使其呈现出人类工程师真实、严谨且带有"工程粗糙感"和长短句顿挫的行文风格。不仅要"干净"（无 AI 痕迹），更要"鲜活"（有真实人味）。

## Core Principle

1. **保留原意** — 术语替换会导致学术语义偏移，引用丢失直接影响查重通过率。专业术语、`\cite{}`、LaTeX 命令保持原样不动。
2. **彻底去 AI 味** — 按核心维度逐条扫描降解（详见 `references/rewrite-guide.md`）。
3. **注入人味与灵魂** — 避免无菌、没有声音的机器感写作。引入工程妥协语态、定量参数碾压、长短句顿挫极化。
4. **禁止捏造数据** — 编造数字是学术不端硬伤，一旦被查无法辩护。只用原文已有数据或可追溯推导。

## Step-by-Step Process

### Phase 1：准备阶段（Git 备份 + 背景知识预检）

1. **安全备份**：在对任何文件进行修改前，执行 Git 分支备份（非 Git 环境自动跳过）：
   ```bash
   python <SKILL_DIR>/scripts/git_snapshot.py <TARGET_FILE>
   ```
2. **背景预检**：快速扫描 `main.tex` 章节结构与核心参数，与 `references/main-tex-context.md` 交叉比对。若发现显著偏差，警告用户并建议按模板更新。用户拒绝则使用现有版本继续。

### Phase 2：扫描解构

读入用户草稿，按 `references/rewrite-guide.md` 逐段定位 AIGC 痕迹：

- 五大核心规则分类逐条扫描
- 个性与灵魂指南识别"缺乏灵魂的写作迹象"
- 运行 `check_aigc.py` 标记敏感词组和格式问题

### Phase 3：重构注入（重写 + 格式修复 + 自检）

1. **执行重写**：结合宿主文档背景事实，按核心维度执行重写。严格遵守**数据完整性红线**（见下方表格）和 **LaTeX 绝对保护红线**（见 `references/rewrite-guide.md` Part 3）。
2. **格式修复**：运行自动检查脚本，根据输出的精确行号逐条修复：

   ```bash
   # LaTeX 文件（默认）
   python <SKILL_DIR>/scripts/check_aigc.py <TARGET_FILE>

   # Markdown 文件
   python <SKILL_DIR>/scripts/check_aigc.py <TARGET_FILE> --format markdown

   # 纯文本文件
   python <SKILL_DIR>/scripts/check_aigc.py <TARGET_FILE> --format plain
   ```

   修复完毕后再次运行脚本确认 error 清零。

3. **自检**：`check_aigc.py` 输出即为自检结果。此外，对照以下脚本无法覆盖的结构性问题速查表：
   - ✓ 连续 3 句以上长度相近？→ 打断其中一句，制造长短句顿挛
   - ✓ 段落以简洁单行“金句”结尾？→ 改为技术细节或直接删除
   - ✓ 任何地方有三项顺序并列？→ 改为两项或四项，打破三段式模板
   - ✓ 有比喻/类比后紧跟解释？→ 删除解释，信任读者能理解
   - ✓ 全段只有陈述没有数字？→ 补充定量参数（百分比、单位值）
   - ✓ 段落读起来像产品新闻稿或维基百科？→ 注入工程妥协感和真实困境

### Phase 4：输出交付

只输出重写后的代码块（LaTeX/Markdown/纯文本），不附加任何主观解释、不输出过程分析。

**改写示例与解析**（展示期望的风格转换方向）：

**输入（AI 味道，干净但无灵魂）：**

```latex
本系统采用了先进的模糊PID控制算法，该算法作为提升系统性能的关键，能够有效地提升系统的响应速度和稳定性。
此外，实验结果表明，与传统PID相比，该方法在多个性能指标上均表现出显著的优越性，不仅降低了超调，还减少了时间。
```

**输出（人性化，鲜活且硬核）：**

```latex
控制器选用模糊PID方案。相比经典PID，超调量从$12.3\%$压至$4.7\%$，
调节时间由$3.8\,\mathrm{s}$缩短到$1.2\,\mathrm{s}$——代价是模糊规则表
需要离线整定约40条，现场调参耗时两个工作日。
```

**所做更改标注：**

- 删除了"作为...的关键"（系动词回避/夸大意义）
- 删除了"此外"（AI 高频词）
- 删除了"不仅...还..."（否定式排比）
- 删除了"先进的"、"有效地"、"显著的优越性"（宣传性语言/空泛表达）
- **注入灵魂**：加入了具体参数（$12.3\%$、$3.8\,\mathrm{s}$）替代模糊主张，并补充了"现场调参耗时两个工作日"的工程妥协感（承认复杂性与真实困境）。

### Phase 5：后续维护（可选）

1. **质量评分**：若用户要求评估 AI 浓度，按 **references/optional-checks.md** 中的质量评分标准（五维评分）执行评估。
2. **背景知识同步**：完成所有修改后，询问用户是否需要同步更新 `references/main-tex-context.md`。若确认，则读取最新 `main.tex` 全文并按模板覆盖写入。

## Data Integrity Red Line

| 优先级  | 数据来源 | 规则                                                    |
| ------- | -------- | ------------------------------------------------------- |
| P1 首选 | 原位数据 | 直接复用宿主文档或用户提供信息中的真实数据              |
| P2 次选 | 推导论证 | 基于已有参数做物理/数学推算，必须展现推导链条与计算过程 |
| P3 末选 | 外部检索 | 极少数情况，必须标注信息源（"根据 XX 手册"）            |
| ⛔ 禁止 | 凭空捏造 | 编造数据属学术不端，不得臆造文档中未提及的数字或结论    |

## Reference Files

| 文件                                  | 内容                                         |
| ------------------------------------- | -------------------------------------------- |
| `references/rewrite-guide.md`         | 五大核心规则 + 灵魂注入指南 + LaTeX 保护红线 |
| `references/optional-checks.md`       | 质量评分标准（可选）                         |
| `references/main-tex-context.md`      | 宿主文档 main.tex 章节锚点与工程事实         |
| `assets/main-tex-context-template.md` | 背景知识模板格式（Phase 1/5 用）             |
| `scripts/check_aigc.py`               | AIGC 检测脚本（支持 LaTeX/Markdown/纯文本）  |
| `scripts/git_snapshot.py`             | Git 分支备份脚本                             |
| `scripts/rules.json`                  | 敏感词规则数据源（唯一权威源）               |
| `scripts/generate_dict.py`            | 从 rules.json 生成人类可读敏感词速查表       |
