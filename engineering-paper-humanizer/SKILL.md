---
name: engineering-paper-humanizer
description: 深度重写工程类中文学术文本（LaTeX），按十二大维度消除 AIGC 痕迹，注入人类工程师行文风格与真实个性。当用户提及洗稿、去AI、humanize、降AIGC、防检测、人味、AI浓度，或要求对中文工程类 LaTeX 文档（.tex）进行去 AI 化改写时，必须使用此 Skill。也适用于用户提交一段工程文本要求消除 AIGC 检测特征（困惑度、突发性），或需要将 AI 生成内容植入现有 main.tex 并保持风格一致的场景。
compatibility:
  python: ">=3.7"
  git: optional
---

# Engineering Paper Humanizer

深度重写工程类学术文本，彻底消除 AI 生成痕迹。在保留原意、专业术语、文献引用和 LaTeX 命令完整的前提下，使其呈现出人类工程师真实、严谨且带有"工程粗糙感"和长短句顿挫的行文风格。

## Core Principle

1. **保留原意** — 术语替换会导致学术语义偏移，引用丢失直接影响查重通过率。专业术语、`\cite{}`、LaTeX 命令保持原样不动
2. **彻底去 AI 味** — 按十二大维度逐条扫描降解（详见 `references/humanizer-rules.md` Part 1）
3. **注入人味** — 工程妥协语态、定量参数碾压、长短句顿挫极化
4. **禁止捏造数据** — 编造数字是学术不端硬伤，一旦被查无法辩护。只用原文已有数据或可追溯推导

## Step-by-Step Process

### Phase 0：安全备份（Git 分支备份）

在对任何 .tex 文件进行修改之前，先执行 Git 分支备份：

```bash
python3 <SKILL_DIR>/scripts/git_snapshot.py <TARGET_FILE>
```

非 Git 环境自动跳过，不影响后续流程。

### Phase 0.5：背景知识一致性预检

读取 `references/main-tex-context.md` 前，快速扫描 `main.tex` 章节结构与核心参数，与背景文件交叉比对。若发现章节结构不一致、核心参数缺失/过时、或新增章节未记录等显著偏差，警告用户并建议按模板（`assets/main-tex-context-template.md`）重置更新。用户拒绝则使用现有版本继续。

### Phase 1：扫描解构

读入用户草稿，按十二大维度（`references/humanizer-rules.md` Part 1）逐段定位 AIGC 痕迹，同时查阅降重字典（Part 2）标记敏感词组。

### Phase 2：重构注入

结合宿主文档背景事实（`references/main-tex-context.md`），按十二大维度执行重写。重写时严格遵守：

- **数据完整性红线**（见下方表格）
- **LaTeX 保护红线**（`references/humanizer-rules.md` Part 3）

### Phase 3：格式修复

运行自动检查脚本，根据输出的精确行号逐条修复：

```bash
python3 <SKILL_DIR>/scripts/check_latex.py <TARGET_FILE>
```

修复完毕后再次运行脚本确认 error 清零。

### Phase 4：静默输出

只输出重写后的 LaTeX 代码块，不附加任何主观解释、不输出过程分析。

**改写示例**（展示期望的风格转换方向）：

输入：
```latex
本系统采用了先进的模糊PID控制算法，该算法能够有效地提升系统的响应速度和稳定性。
实验结果表明，与传统PID相比，该方法在多个性能指标上均表现出显著的优越性。
```

输出：
```latex
控制器选用模糊PID方案。相比经典PID，超调量从$12.3\%$压至$4.7\%$，
调节时间由$3.8\,\mathrm{s}$缩短到$1.2\,\mathrm{s}$——代价是模糊规则表
需要离线整定约40条，现场调参耗时两个工作日。
```

### Phase 4.5：质量自检（可选）

若用户要求评估 AI 浓度，按五维评分标准（`references/humanizer-rules.md` Part 4）执行评估。常规洗稿流程跳过此步。

### Phase 5：背景知识同步

完成所有修改后，询问用户是否需要同步更新 `references/main-tex-context.md`。若用户确认：

1. 读取最新 `main.tex` 全文
2. 按模板格式（`assets/main-tex-context-template.md`）提取信息
3. 覆盖写入 `main-tex-context.md`

## Data Integrity Red Line

| 优先级  | 数据来源 | 规则                                          |
| ------- | -------- | --------------------------------------------- |
| P1 首选 | 原位数据 | 直接复用宿主文档或用户提供信息中的真实数据    |
| P2 次选 | 推导论证 | 基于已有参数做物理/数学推算，必须展现推导链条 |
| P3 末选 | 外部检索 | 极少数情况，必须标注信息源（"根据 XX 手册"）  |
| ⛔ 禁止  | 凭空捏造 | 编造数据属学术不端，不得臆造文档中未提及的数字或结论 |

## Reference Files

| 文件 | 内容 |
| ---- | ---- |
| `references/humanizer-rules.md` | 十二大维度 + 降重字典 + LaTeX 红线 + 质量评分（合集） |
| `references/main-tex-context.md` | 宿主文档 main.tex 章节锚点与工程事实 |
| `assets/main-tex-context-template.md` | 背景知识模板格式（Phase 0.5/5 用） |
| `scripts/check_latex.py` | LaTeX 格式自动检查脚本 |
| `scripts/git_snapshot.py` | Git 分支备份脚本 |
