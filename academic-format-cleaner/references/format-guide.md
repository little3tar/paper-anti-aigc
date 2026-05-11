# 学术文档格式检查指南

本文件记录 `academic-format-cleaner` 的格式检查边界。正文润色、AI 腔清理和中文标点语义改写不放在这里。

## LaTeX

- `\cite{}` 紧贴被引文字，不在前面留空格。
- `\cite{}` 放在中文句号、逗号内侧：`结论\cite{key}。`
- `\label{}`、`\ref{}`、`\includegraphics{}`、`\cite{}` 的花括号不要跨行。
- 百分号写为 `\%`，除非确实是 LaTeX 注释。
- 数学环境、代码环境、绘图环境内只检查命令完整性，不做正文风格判断。

## Markdown

- fenced code block 和 YAML frontmatter 受保护，不做正文润色。
- 若需要清理标题层级、列表风格或代码块围栏，应在格式 skill 内完成。
- 正文中的 AI 腔和中文标点交给 `engineering-paper-humanizer`。

## Plain Text

纯文本只检查与格式相关的占位引用、年份式虚构归因等轻量问题。一般正文表达问题仍由 `engineering-paper-humanizer` 处理。
