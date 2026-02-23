# engineering-paper-humanizer

深度重写工程类中文学术文本（LaTeX），消除 AIGC 痕迹，注入人类工程师行文风格。

## 功能

- 针对中文 AI 写作七大高频特征（宏大叙事、机械结构、连接词泛滥、低突发性等）进行定向降解
- 注入工程妥协语态、定量参数、长短句顿挫，提升 Burstiness 与 Perplexity
- 严格保护 LaTeX 命令、数学环境、`\cite{}` 引用格式
- 内置数据完整性红线，严禁捏造

## 安装

将整个 `engineering-paper-humanizer/` 目录放入以下任一位置：

- `.opencode/skills/engineering-paper-humanizer/`
- `.claude/skills/engineering-paper-humanizer/`
- `.agents/skills/engineering-paper-humanizer/`

## 文件结构

```text
engineering-paper-humanizer/
├── SKILL.md                              # 核心指令
├── references/
│   ├── aigc-kill-dimensions.md           # 七大维度详细规则
│   ├── aigc-word-replacements.md         # 降重替换字典
│   ├── latex-protection-rules.md         # LaTeX 保护红线
│   └── main-tex-context.md              # main.tex 背景知识
├── examples/
│   └── cli-workflows.md                  # CLI 使用场景
├── scripts/
│   ├── check_latex.py                    # LaTeX 格式自动检查
│   └── git_snapshot.py                   # Git 安全快照（修改前备份/回滚）
└── README.md
```

## 格式检查脚本

无需额外依赖（纯 Python 3 标准库），直接运行：

```bash
python3 scripts/check_latex.py main.tex
python3 scripts/check_latex.py main.tex --section 3 --severity error
python3 scripts/check_latex.py main.tex --json
```

检测内容包括：`\cite{}` 位置错误、裸百分号、花括号内换行、英文引号、AIGC 敏感词、段首连接词泛滥、段落突发性过低。

`check_latex.py` 的规则全部集中在文件顶部的 `RULES` 列表和 `CONNECTIVES` 列表中，新增规则只需要往列表里追加字典，不用改任何其他代码。

## 安全快照脚本

在修改 .tex 文件前自动创建 Git 备份快照，支持一键回滚。无需额外依赖（纯 Python 3 标准库），需要 Git 环境：

```bash
# 修改前创建快照
python3 scripts/git_snapshot.py main.tex

# 查看所有备份快照
python3 scripts/git_snapshot.py --list

# 回滚到最近的快照
python3 scripts/git_snapshot.py --rollback

# 对比当前文件与最近快照的差异
python3 scripts/git_snapshot.py --diff main.tex
```

非 Git 环境下脚本会自动跳过，不影响任何功能。

## 使用方式

详见 `examples/cli-workflows.md`。

## License

MIT
