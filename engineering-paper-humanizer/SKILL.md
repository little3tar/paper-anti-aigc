---
name: engineering-paper-humanizer
description: 深度重写工程类中文学术文本（LaTeX），消除 AIGC 痕迹，注入人类工程师行文风格
license: MIT
compatibility:
  - claude-code
  - codex
  - opencode
metadata:
  version: "3.1.0"
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

在对任何 .tex 文件进行修改之前，先执行 Git 安全备份：

```bash
python3 .opencode/skills/engineering-paper-humanizer/scripts/git_snapshot.py main.tex
```

非 Git 环境自动跳过，不影响后续流程。回滚与历史查看详见 `examples/cli-workflows.md` 场景五。

### Phase 1：扫描解构

读入用户草稿，按七大维度（详见 `references/aigc-kill-dimensions.md`）逐段定位 AIGC 痕迹，同时查阅 `references/aigc-word-replacements.md` 标记敏感词组。

### Phase 2：重构注入

结合宿主文档背景事实（见 `references/main-tex-context.md`），按七大维度执行重写。重写时严格遵守：

- **数据完整性红线**（见下方表格）
- **LaTeX 保护红线**（详见 `references/latex-protection-rules.md`）

### Phase 3：格式修复

运行自动检查脚本，根据输出的精确行号逐条修复：

```bash
python3 .opencode/skills/engineering-paper-humanizer/scripts/check_latex.py main.tex
```

修复完毕后再次运行脚本确认 error 清零。脚本用法详见 `examples/cli-workflows.md` 场景四。

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
□ 按七大维度扫描 + 重写（references/aigc-kill-dimensions.md）
□ 替换 AI 高频敏感词组（references/aigc-word-replacements.md）
□ 严格遵守 LaTeX 保护红线（references/latex-protection-rules.md）
□ 严禁捏造数据（Data Integrity Red Line）
□ 运行 check_latex.py 逐条修复，确认 error 清零
□ 仅输出 LaTeX 代码块
```

## Reference Files

| 文件                                   | 内容                                                        |
| -------------------------------------- | ----------------------------------------------------------- |
| `references/aigc-kill-dimensions.md`   | 七大核心维度详细规则、改写示例与 Anti-Patterns 速查表       |
| `references/aigc-word-replacements.md` | AI 高频敏感词组降重替换字典                                 |
| `references/latex-protection-rules.md` | LaTeX 绝对保护红线完整规则                                  |
| `references/main-tex-context.md`       | 宿主文档 main.tex 章节锚点与工程事实                        |
| `examples/cli-workflows.md`            | CLI 使用场景与建议 Prompt                                   |
| `scripts/check_latex.py`               | LaTeX 格式自动检查脚本（引用位置、标点、AIGC 痕迹、突发性） |
| `scripts/git_snapshot.py`              | Git 安全快照脚本（修改前备份、查看历史、回滚、对比差异）    |

## Integration Notes

- 两个脚本均为纯 Python 3 标准库，零外部依赖
- 兼容 OpenCode、Claude Code、Cursor 等支持 SKILL.md 的 CLI 工具
- 处理完毕后可直接覆盖更新原 `.tex` 文件
- 非 Git 环境下 git_snapshot.py 自动跳过，不影响任何现有功能
