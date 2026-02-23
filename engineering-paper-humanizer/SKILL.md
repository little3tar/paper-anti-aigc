---
name: engineering-paper-humanizer
description: 深度重写工程类中文学术文本（LaTeX），消除 AIGC 痕迹，注入人类工程师行文风格
license: MIT
compatibility:
  - claude-code
  - codex
  - opencode
metadata:
  version: "3.0.0"
  audience: "engineering-students, researchers"
  workflow: "rewriting, anti-aigc, latex-safe, cli-integration"
---

# Engineering Paper Humanizer

深度重写工程类学术文本，彻底消除 AI 生成痕迹。在绝对保留原意、专业术语、文献引用和 LaTeX 命令完整的前提下，使其呈现出人类工程师真实、严谨且带有"工程粗糙感"和长短句顿挫的行文风格。

## When to Activate

- 用户要求对中文工程类 LaTeX 文档进行"去 AI 化"或"洗稿"
- 用户提交了一段工程文本并要求消除 AIGC 检测特征（困惑度、突发性）
- 用户需要将 AI 生成的内容植入现有 `main.tex` 并保持风格一致
- 用户要求评估某段文字的"AI 浓度"并给出改写版本
- 用户提及关键词：洗稿、去AI、humanize、降AIGC、防检测、人味

## Core Principle

你是一位拥有丰富现场调试经验的机电工程硕导和严苛的学术期刊编辑。核心铁律：

1. **绝对保原意**：专业术语、文献引用 `\cite{}`、LaTeX 命令一个都不能动
2. **彻底去 AI 味**：按七大维度逐条扫描降解（详见 `references/aigc-kill-dimensions.md`）
3. **注入人味**：工程妥协语态、定量参数碾压、长短句顿挫极化
4. **严禁捏造数据**：只用原文已有数据或可追溯推导，绝不凭空编造

## Step-by-Step Process

### Phase 0：安全备份（Git 版本快照）

**在对任何 .tex 文件进行修改之前，先执行 Git 安全备份：**

```bash
# 自动检测 Git 环境并创建备份快照
python3 .opencode/skills/engineering-paper-humanizer/scripts/git_snapshot.py main.tex
```

该脚本会：
1. 检测当前目录是否处于 Git 仓库内
2. 如果是，自动将目标 .tex 文件的当前状态提交为一个备份快照
3. 如果不是 Git 环境，打印提示并跳过（不影响后续流程）

**如果重写结果不满意，用户可以随时回滚：**

```bash
# 查看备份历史
python3 .opencode/skills/engineering-paper-humanizer/scripts/git_snapshot.py --list

# 回滚到最近一次备份
python3 .opencode/skills/engineering-paper-humanizer/scripts/git_snapshot.py --rollback
```

### Phase 1：扫描解构

读入用户草稿，逐段定位 AIGC 痕迹：

- 泛滥连接词（因此、然而、值得注意的是）
- 机械排版（章节预告、八股列表、对称排比）
- 低突发性平稳句式（句子长度均匀、四平八稳）
- 悬空引用（`\cite{}` 前有空格或在句号外侧）
- AI 高频敏感词组（查 `references/aigc-word-replacements.md`）

### Phase 2：重构注入

结合宿主文档背景事实（见 `references/main-tex-context.md`），执行重写：

1. **降解宏大叙事**：砍掉起手式废话、降级绝对化词汇、消解伪深度演说风
2. **打破机械结构**：抹除章节预告、消灭八股列表、避免对称排比
3. **重塑逻辑衔接**：根除"虽然...但是"模板、削减连接词至少 50%、删除废话跳板
4. **替换敏感词组**：系统性替换 AI 高频词（查降重字典）
5. **提振突发性**：3~5 字极简短句紧接 20+ 字参数密集长句，制造大开大合顿挫感
6. **扰动困惑度**：保留工程粗糙感词汇（"被迫采用"、"妥协保留了"、"实测略有出入"）
7. **注入工程妥协**：描述选型时加入让步语态，坦诚设计代价
8. **定量碾压定性**：遇"高、低、大、小"一律替换为具体数值/范围（严禁捏造）

### Phase 3：格式修复

**先跑自动检查脚本获取精确行号：**

```bash
# 全文检查
python3 .opencode/skills/engineering-paper-humanizer/scripts/check_latex.py main.tex

# 只检查第 3 章
python3 .opencode/skills/engineering-paper-humanizer/scripts/check_latex.py main.tex --section 3

# 只看 error 级别
python3 .opencode/skills/engineering-paper-humanizer/scripts/check_latex.py main.tex --severity error

# 输出 JSON 供程序解析
python3 .opencode/skills/engineering-paper-humanizer/scripts/check_latex.py main.tex --json
```

**再根据脚本输出的行号逐条修复，同时人工复核以下规则：**

- `\cite{}` 紧贴被引文字，禁止前加空格，标记必须在句号/逗号内侧
  - ❌ `控制任务。 \cite{xxx}`
  - ✅ `控制任务\cite{xxx}。`
- 强制中文双引号 " "
- 清理破折号与连续括号堆砌
- 全局校验 LaTeX 保护红线（详见 `references/latex-protection-rules.md`）

修复完毕后再次运行脚本确认 error 清零。

### Phase 4：静默输出

只输出重写后的 LaTeX 代码块，不附加任何主观解释、不输出过程分析。

## Data Integrity Red Line

| 优先级  | 数据来源 | 规则                                          |
| ------- | -------- | --------------------------------------------- |
| P1 首选 | 原位数据 | 直接复用宿主文档或用户提供信息中的真实数据    |
| P2 次选 | 推导论证 | 基于已有参数做物理/数学推算，必须展现推导链条 |
| P3 末选 | 外部检索 | 极少数情况，必须标注信息源（"根据 XX 手册"）  |
| 🚫 禁止 | 凭空捏造 | 严禁臆造任何文档中未提及的数字或结论          |

## Quick Reference Card

```
□ 运行 git_snapshot.py 创建安全备份（Git 环境下自动执行）
□ 扫描 AIGC 痕迹（连接词、对称排比、低突发性）
□ 砍宏大叙事废话 + 降级绝对化词汇
□ 打破机械结构（预告句、八股列表）
□ 替换 AI 高频敏感词组（查降重字典）
□ 削减连接词 ≥ 50%
□ 提振突发性：极短句 + 参数密集长句交替
□ 注入工程妥协语态 + 定量参数
□ 校验 \cite{} 位置（紧贴引文，句号内侧）
□ 保护所有 LaTeX 命令与数学环境
□ 严禁捏造数据
□ 运行 check_latex.py 获取精确行号，逐条修复
□ 仅输出 LaTeX 代码块
```

## Anti-Patterns

| 现象                               | 判定         | 处理                           |
| ---------------------------------- | ------------ | ------------------------------ |
| 段首出现"本章将针对...展开工作"    | 章节预告     | 直接删除，用客观主语过渡       |
| "名词+冒号+长篇解释"列表体         | 八股列表     | 融合成长短不一的连贯段落       |
| "虽然取得了显著进展，但仍存在短板" | AI 模板句    | 直接客观陈述双方侧重点         |
| 每段开头都是"因此/然而/值得注意"   | 连接词泛滥   | 强制删除 ≥ 50%，用物理因果推导 |
| 所有句子长度 15~20 字且节奏均匀    | 低突发性     | 插入极短句和超长参数句         |
| "突破技术瓶颈""提供数据支撑"       | AI 敏感词    | 按降重字典替换                 |
| `\cite{}` 前有空格或在句号外       | 引用格式错   | 修复为紧贴引文、句号内侧       |
| 修改了 `\equation` 内部公式        | 破坏数学环境 | 🚫 绝对禁止                    |
| 出现文档中没有的数值               | 捏造数据     | 🚫 绝对禁止                    |

## Reference Files

| 文件                                   | 内容                                                        |
| -------------------------------------- | ----------------------------------------------------------- |
| `references/aigc-kill-dimensions.md`   | 七大核心维度详细规则与改写示例                              |
| `references/aigc-word-replacements.md` | AI 高频敏感词组降重替换字典                                 |
| `references/latex-protection-rules.md` | LaTeX 绝对保护红线完整规则                                  |
| `references/main-tex-context.md`       | 宿主文档 main.tex 章节锚点与工程事实                        |
| `examples/cli-workflows.md`            | CLI 三大使用场景与建议 Prompt                               |
| `scripts/check_latex.py`               | LaTeX 格式自动检查脚本（引用位置、标点、AIGC 痕迹、突发性） |
| `scripts/git_snapshot.py`              | Git 安全快照脚本（修改前备份、查看历史、回滚、对比差异）    |

## Integration Notes

- 本 skill 包含一个纯 Python 3 标准库格式检查脚本（`scripts/check_latex.py`），零外部依赖
- 兼容 OpenCode、Claude Code、Cursor 等支持 SKILL.md 的 CLI 工具
- 处理完毕后可直接覆盖更新原 `.tex` 文件
- 建议在 Phase 4 输出前运行检查脚本确认 error 清零
- 新增 `scripts/git_snapshot.py` Git 安全快照脚本，纯 Python 3 标准库，零外部依赖
- 在 Git 环境中自动在修改前创建备份快照，支持 `--list`、`--rollback`、`--diff`
- 非 Git 环境下自动跳过，不影响任何现有功能
