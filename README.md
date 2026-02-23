<div align="center">

# 📝 Paper Anti-AIGC

**通过 Skills 自动化降低论文 AI 特征**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-3.x-green.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/little3tar/paper-anti-aigc/pulls)

</div>

---

## 🎯 项目简介

随着 AI 写作工具的普及，学术论文中的 AIGC（AI Generated Content）特征越来越容易被检测工具识别。本仓库收集并持续维护一系列 **Skills** 和辅助工具，帮助研究者将 AI 辅助生成的学术文本进行深度改写，消除 AIGC 痕迹，使其更贴近人类真实写作风格。

> ⚠️ **声明**：本项目仅供学术写作润色与风格优化参考，请遵守所在机构的学术诚信规范。

## ✨ 特性

- 🔧 **模块化 Skill 架构** — 每个 Skill 独立成目录，即插即用
- 🛡️ **LaTeX 安全保护** — 严格保护数学公式、引用格式、命令完整性
- 📊 **多维度降解** — 从语态、结构、词频、突发性等多维度消除 AI 痕迹
- 🐍 **零依赖脚本** — 辅助工具基于纯 Python 3 标准库，开箱即用
- 🔄 **安全回滚** — 内置 Git 快照机制，修改前自动备份

## 📦 已收录 Skills

| Skill | 说明 | 适用场景 |
| ----- | ---- | -------- |
| [engineering-paper-humanizer](./engineering-paper-humanizer/) | 深度重写工程类中文学术文本（LaTeX），消除 AIGC 痕迹，注入人类工程师行文风格 | 工程类中文 LaTeX 论文 |
| *更多 Skill 持续添加中…* | | |

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/little3tar/paper-anti-aigc.git
cd paper-anti-aigc
```

### 2. 选择并安装 Skill

以 `engineering-paper-humanizer` 为例，将 Skill 目录复制到你的 AI 编码工具对应的 skills 路径：

```bash
# OpenCode
cp -r engineering-paper-humanizer/ your-project/.opencode/skills/

# Claude Code
cp -r engineering-paper-humanizer/ your-project/.claude/skills/

# Cursor / 其他支持 SKILL.md 的工具
cp -r engineering-paper-humanizer/ your-project/.agents/skills/
```

### 3. 使用辅助脚本

```bash
# LaTeX 格式检查
python3 engineering-paper-humanizer/scripts/check_latex.py your-paper.tex

# Git 安全快照（修改前备份）
python3 engineering-paper-humanizer/scripts/git_snapshot.py your-paper.tex
```

## 📁 项目结构

```text
paper-anti-aigc/
├── README.md                          # 本文件
├── LICENSE                            # MIT 许可证
└── engineering-paper-humanizer/       # Skill：工程论文人性化改写
    ├── SKILL.md                       # 核心指令定义
    ├── README.md                      # Skill 详细说明
    ├── references/                    # 参考规则文档
    │   ├── aigc-kill-dimensions.md    # 七大维度详细规则
    │   ├── aigc-word-replacements.md  # 降重替换字典
    │   ├── latex-protection-rules.md  # LaTeX 保护红线
    │   └── main-tex-context.md        # main.tex 背景知识
    ├── examples/                      # 使用示例
    │   └── cli-workflows.md           # CLI 使用场景
    └── scripts/                       # 辅助脚本
        ├── check_latex.py             # LaTeX 格式自动检查
        └── git_snapshot.py            # Git 安全快照
```

## 🤝 贡献指南

欢迎贡献新的 Skill 或改进现有工具！建议的贡献方向：

- 🆕 **新增 Skill** — 针对不同学科（医学、法学、社科等）或不同语言的论文降 AIGC Skill
- 🔨 **新增工具** — 开发更多辅助检测/改写脚本
- 📖 **完善文档** — 补充使用案例、最佳实践
- 🐛 **修复问题** — 报告或修复已知 Bug

### 新增 Skill 规范

每个 Skill 应作为独立目录存放在仓库根目录下，推荐包含以下文件：

```text
your-new-skill/
├── SKILL.md          # [必需] 核心指令定义
├── README.md         # [必需] Skill 说明文档
├── references/       # [推荐] 参考规则文档
├── examples/         # [推荐] 使用示例
└── scripts/          # [可选] ��助脚本
```

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

<div align="center">

**如果这个项目对你有帮助，请点个 ⭐ Star 支持一下！**

</div>