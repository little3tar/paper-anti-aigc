<div align="center">

# 📝 Paper Anti-AIGC

**通过 Skills 自动化降低论文 AI 特征**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-≥3.7-green.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/little3tar/paper-anti-aigc/pulls)

</div>

---

## 🎯 项目简介

随着 AI 写作工具的普及，学术论文中的 AIGC（AI Generated Content）特征越来越容易被检测工具识别。本仓库收集并持续维护一系列 **Skills** 和辅助工具，帮助研究者将 AI 辅助生成的学术文本进行深度改写，消除 AIGC 痕迹，使其更贴近人类真实写作风格。

> ⚠️ **声明**：本项目仅供学术写作润色与风格优化参考，请遵守所在机构的学术诚信规范。

## ✨ 特性

- 🔧 **模块化 Skill 架构** — 每个 Skill 独立成目录，即插即用
- 🛡️ **LaTeX 安全保护** — 严格保护数学公式、引用格式、命令完整性
- 📊 **十二维度降解** — 从语态、结构、词频、突发性等十二大维度消除 AI 痕迹
- 🐍 **零依赖脚本** — 辅助工具基于纯 Python 3 标准库（≥3.7），开箱即用
- 🔄 **安全回滚** — 内置 Git 分支备份机制，精确恢复被备份文件，不污染主分支提交历史
- 🌐 **跨平台兼容** — 支持 Windows / macOS / Linux，适配 OpenCode、Claude Code、Cursor 等主流 AI 编码工具

## 📦 已收录 Skills

| Skill | 说明 | 适用场景 | 环境要求 |
| ----- | ---- | -------- | -------- |
| [engineering-paper-humanizer](./engineering-paper-humanizer/) | 深度重写工程类中文学术文本（LaTeX），按十二大维度消除 AIGC 痕迹，注入人类工程师行文风格 | 工程类中文 LaTeX 论文 | Python ≥3.7, Git |
| *更多 Skill 持续添加中…* | | | |

## 🚀 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
| ---- | ---- | ---- |
| Python | ≥3.7 | 脚本使用纯标准库，无需安装额外依赖 |
| Git | 任意版本 | 分支备份/回滚功能需要；非 Git 环境自动跳过 |
| AI 编码工具 | — | OpenCode / Claude Code / Cursor 等支持 SKILL.md 的工具 |

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

# Git 分支备份（修改前自动创建备份分支）
python3 engineering-paper-humanizer/scripts/git_snapshot.py your-paper.tex

# 查看所有备份分支
python3 engineering-paper-humanizer/scripts/git_snapshot.py --list

# 从最近备份恢复文件
python3 engineering-paper-humanizer/scripts/git_snapshot.py --rollback

# 对比当前文件与最近备份的差异
python3 engineering-paper-humanizer/scripts/git_snapshot.py --diff your-paper.tex

# 清理所有备份分支
python3 engineering-paper-humanizer/scripts/git_snapshot.py --cleanup
```

## 📁 项目结构

```text
paper-anti-aigc/
├── README.md                          # 本文件
├── LICENSE                            # MIT 许可证
└── engineering-paper-humanizer/       # Skill：工程论文人性化改写
    ├── SKILL.md                       # 核心指令定义
    ├── assets/                        # 资源文件（模板等）
    │   └── main-tex-context-template.md # 背景知识模板格式
    ├── references/                    # 参考规则与使用指南
    │   ├── aigc-kill-dimensions.md    # 十二大维度详细规则
    │   ├── aigc-word-replacements.md  # 降重替换字典
    │   ├── latex-protection-rules.md  # LaTeX 保护红线
    │   ├── main-tex-context.md        # main.tex 背景知识
    │   └── cli-workflows.md           # CLI 使用场景与 Prompt 模板
    └── scripts/                       # 辅助脚本
        ├── check_latex.py             # LaTeX 格式自动检查
        └── git_snapshot.py            # Git 分支备份（备份/回滚/清理）
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
skill-name/                    # 文件夹名：小写 + 连字符
├── SKILL.md                   # 【必需】核心指令文件
│   ├── YAML frontmatter       # 【必需】元数据
│   │   ├── name:              # 技能名称（与目录名一致）
│   │   ├── description:       # 触发描述（最重要）
│   │   ├── license:           # 许可证
│   │   ├── requirements:      # 【推荐】环境需求（python/git/os）
│   │   ├── allowed-tools:     # 【推荐】允许使用的工具白名单
│   │   └── metadata:          # 【可选】触发词、来源、语言等
│   └── Markdown body          # 【必需】使用指南
├── scripts/                   # 【可选】可执行脚本
├── references/                # 【可选】参考文档
└── assets/                    # 【可选】资源文件
```

## 📚 参考来源

本项目的工程论文 Humanizer 能力整合了以下开源项目的核心规则：

- **[Humanizer-zh](https://github.com/op7418/Humanizer-zh)** — Humanizer 的汉化版本，Claude Code Skills，24 种通用 AI 写作模式识别与修复。MIT License。
- **[blader/humanizer](https://github.com/blader/humanizer)** — 英文原版，Wikipedia "Signs of AI writing" 指南的技能实现。
- **[hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)** — 实用工具部分（核心规则、快速检查清单、质量评分）灵感来源。

> 声明：engineering-paper-humanizer 在 Humanizer-zh 基础上针对工程类 LaTeX 论文场景进行了深度适配，保留了原项目的 MIT 许可证。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源许可证。

---

<div align="center">

**如果这个项目对你有帮助，请点个 ⭐ Star 支持一下！**

</div>
