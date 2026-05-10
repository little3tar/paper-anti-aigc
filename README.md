<div align="center">

# 📝 Paper Anti-AIGC

**自用论文润色工具 — Skills & Scripts**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-≥3.7-green.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/little3tar/paper-anti-aigc/pulls)

</div>

---

写论文过程中积攒的 Skills 和辅助脚本，配合 AI 编码工具（OpenCode / Claude Code / Cursor 等）使用。目前主要覆盖工程类中文论文正文润色、模板化表达清理、通用中文标点检查，以及 LaTeX/Markdown 格式自检。

> ⚠️ **声明**：本项目仅供学术写作润色与风格优化参考，请遵守所在机构的学术诚信规范。

## 📦 已收录 Skills

| Skill | 说明 | 适用场景 | 环境要求 |
| ----- | ---- | -------- | -------- |
| [engineering-paper-humanizer](./engineering-paper-humanizer/) | 重写工程类中文学术文本，减少机械化和聊天式表达，检查通用中文标点（支持 LaTeX/Markdown/纯文本正文） | 工程类中文学术文本 | Python ≥3.7, Git |
| [academic-format-cleaner](./academic-format-cleaner/) | 检查学术文档格式层问题，如 LaTeX 引用位置、百分号、命令断行和列表格式 | LaTeX/Markdown/纯文本格式自检 | Python ≥3.7 |

## 🚀 快速开始

### 环境要求

- Python ≥ 3.7（无需额外依赖，仅使用标准库）
- **Git（可选）**：分支备份首选 Git；若非 Git 仓库会自动尝试 `git init` 初始化；Git 不可用时自动回退到文件复制备份
- 支持 SKILL.md 的 AI 编码工具

### 安装

将 Skill 目录复制到你的 AI 编码工具对应的 skills 路径：

```bash
# OpenCode
cp -r engineering-paper-humanizer/ your-project/.opencode/skills/
cp -r academic-format-cleaner/ your-project/.opencode/skills/

# Claude Code
cp -r engineering-paper-humanizer/ your-project/.claude/skills/
cp -r academic-format-cleaner/ your-project/.claude/skills/

# Cursor / 其他
cp -r engineering-paper-humanizer/ your-project/.agents/skills/
cp -r academic-format-cleaner/ your-project/.agents/skills/
```

### 辅助脚本

```bash
# 中文正文 AI 腔和通用标点检查（支持多格式正文）
python engineering-paper-humanizer/scripts/check_text.py your-paper.tex
python engineering-paper-humanizer/scripts/check_text.py your-doc.md --format markdown
python engineering-paper-humanizer/scripts/check_text.py your-text.txt --format plain

# LaTeX/Markdown/plain 格式检查
python academic-format-cleaner/scripts/check_format.py your-paper.tex
python academic-format-cleaner/scripts/check_format.py your-doc.md --format markdown

# 从 text_rules.json 生成人类可读敏感词速查表
python engineering-paper-humanizer/scripts/generate_dict.py

# 智能备份（首选 Git 分支，无 Git 时自动初始化，失败则回退到文件复制）
python engineering-paper-humanizer/scripts/git_snapshot.py your-paper.tex

# 其他：--list / --rollback / --diff <file> / --cleanup
python engineering-paper-humanizer/scripts/git_snapshot.py --list
```

## 📁 目录结构

```text
engineering-paper-humanizer/
├── SKILL.md                           # 核心指令
├── LICENSE                            # MIT 许可证
├── assets/
│   └── main-tex-context-template.md   # 背景知识模板
├── references/
│   ├── rewrite-guide.md               # 正文改写规则 + 工程语气指南
│   ├── punctuation-guide.md           # 中文引号和破折号专项规则
│   ├── optional-checks.md             # 质量评分标准（可选）
│   └── main-tex-context.md            # main.tex 背景知识（按项目填写）
└── scripts/
    ├── check_text.py                  # 中文正文和通用标点检查
    ├── text_rules.json                # 文本规则数据源
    ├── generate_dict.py               # 从 text_rules.json 生成敏感词速查表
    └── git_snapshot.py                # Git 分支备份（备份/回滚/清理）

academic-format-cleaner/
├── SKILL.md                           # 格式检查 skill 指令
├── LICENSE                            # MIT 许可证
├── references/
│   └── format-guide.md                # 格式检查边界说明
└── scripts/
    ├── check_format.py                # 格式检查脚本
    ├── format_rules.json              # 格式规则数据源
    └── generate_format_dict.py        # 从 format_rules.json 生成格式规则速查表
```

## 🤝 欢迎贡献

欢迎提交新的 Skill 或改进现有工具！可以是：

- 针对其他学科或语言的降 AIGC Skill
- 有助于 AI 生成论文的辅助工具（排版、查重预检、参考文献整理等）
- Bug 修复或文档完善

## 📚 参考来源

engineering-paper-humanizer 在以下项目基础上针对中文工程论文场景做了适配：

- **[Humanizer-zh](https://github.com/op7418/Humanizer-zh)** — Humanizer 汉化版，24 种 AI 写作模式识别。MIT License。
- **[blader/humanizer](https://github.com/blader/humanizer)** — 英文原版，Wikipedia “Signs of AI writing” 指南。
- **[hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)** — 核心规则与质量评分灵感来源。

## 📄 许可证

[MIT License](LICENSE)
