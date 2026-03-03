<div align="center">

# 📝 Paper Anti-AIGC

**自用 AI 论文写作工具集 — Skills & Scripts**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3](https://img.shields.io/badge/Python-≥3.7-green.svg)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/little3tar/paper-anti-aigc/pulls)

</div>

---

写论文过程中积攒的 Skills 和辅助脚本，配合 AI 编码工具（OpenCode / Claude Code / Cursor 等）使用。目前主要覆盖 AIGC 痕迹消除，后续可能加入其他有助于 AI 生成论文的工具。

> ⚠️ **声明**：本项目仅供学术写作润色与风格优化参考，请遵守所在机构的学术诚信规范。

## 📦 已收录 Skills

| Skill | 说明 | 适用场景 | 环境要求 |
| ----- | ---- | -------- | -------- |
| [engineering-paper-humanizer](./engineering-paper-humanizer/) | 重写工程类中文 LaTeX 论文，从十二个维度消除 AIGC 痕迹 | 工程类中文 LaTeX 论文 | Python ≥3.7, Git |

## 🚀 快速开始

### 环境要求

- Python ≥ 3.7（脚本纯标准库，无额外依赖）
- Git（分支备份/回滚需要；非 Git 环境自动跳过）
- 支持 SKILL.md 的 AI 编码工具

### 安装

将 Skill 目录复制到你的 AI 编码工具对应的 skills 路径：

```bash
# OpenCode
cp -r engineering-paper-humanizer/ your-project/.opencode/skills/

# Claude Code
cp -r engineering-paper-humanizer/ your-project/.claude/skills/

# Cursor / 其他
cp -r engineering-paper-humanizer/ your-project/.agents/skills/
```

### 辅助脚本

```bash
# LaTeX 格式 + AIGC 残留检查
python3 engineering-paper-humanizer/scripts/check_latex.py your-paper.tex

# Git 分支备份（修改前自动创建，最多保留 5 个）
python3 engineering-paper-humanizer/scripts/git_snapshot.py your-paper.tex

# 其他：--list / --rollback / --diff <file> / --cleanup
python3 engineering-paper-humanizer/scripts/git_snapshot.py --list
```

## 📁 目录结构

```text
engineering-paper-humanizer/
├── SKILL.md                           # 核心指令
├── LICENSE.txt                        # MIT 许可证
├── assets/
│   └── main-tex-context-template.md   # 背景知识模板
├── references/
│   ├── humanizer-rules.md             # 十二维度规则 + 替换字典 + LaTeX 保护红线
│   └── main-tex-context.md            # main.tex 背景知识（按项目填写）
└── scripts/
    ├── check_latex.py                 # LaTeX 格式 + AIGC 残留自动检查
    └── git_snapshot.py                # Git 分支备份（备份/回滚/清理）
```

## 🤝 欢迎贡献

欢迎提交新的 Skill 或改进现有工具！可以是：

- 针对其他学科或语言的降 AIGC Skill
- 有助于 AI 生成论文的辅助工具（排版、查重预检、参考文献整理等）
- Bug 修复或文档完善

## 📚 参考来源

engineering-paper-humanizer 在以下项目基础上针对工程类 LaTeX 论文场景做了适配：

- **[Humanizer-zh](https://github.com/op7418/Humanizer-zh)** — Humanizer 汉化版，24 种 AI 写作模式识别。MIT License。
- **[blader/humanizer](https://github.com/blader/humanizer)** — 英文原版，Wikipedia "Signs of AI writing" 指南。
- **[hardikpandya/stop-slop](https://github.com/hardikpandya/stop-slop)** — 核心规则与质量评分灵感来源。

## 📄 许可证

[MIT License](LICENSE)
