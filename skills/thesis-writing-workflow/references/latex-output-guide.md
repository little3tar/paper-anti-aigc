# LaTeX 输出指南

本文件指导从已定稿的 Markdown 或纯文本草稿生成 LaTeX 项目。在 `academic-format-cleaner` 完成格式清理后使用。

## 模板检测

检查用户是否在 `latex-templates/` 或项目根目录提供了 LaTeX 模板文件（`.cls`、`.sty`、主 `.tex` 示例）。

**有模板时**：
1. 解析模板的 `\documentclass` 和导言区。
2. 识别模板定义的章节命令（如 `\chapter`、`\section`）和特殊环境（如 `\begin{abstract}`）。
3. 按模板命令生成对应的章节 `.tex` 文件。

**无模板时**：
- 中文论文：默认使用 `ctexart` 文档类。
- 英文论文：默认使用 `article` 文档类。
- 也可以让用户提供学校模板。

## 输出结构

```
thesis-latex/
├── main.tex              # 主文件
├── chapters/             # 章节内容 (.tex)
│   ├── 00-abstract.tex
│   ├── 01-introduction.tex
│   ├── 02-literature-review.tex
│   ├── 03-methodology.tex
│   ├── 04-results-analysis.tex
│   ├── 05-discussion.tex
│   └── 06-conclusion.tex
├── figures/              # 图片文件
├── references.bib        # BibTeX 参考文献
└── latex-templates/      # 原始模板（只读）
```

## main.tex 模板

```latex
\documentclass[zihao=-4]{ctexart}

\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{hyperref}
\usepackage[backend=biber,style=gb7714-2015]{biblatex}
\addbibresource{references.bib}

\title{论文题目}
\author{作者}

\begin{document}

\maketitle
\input{chapters/00-abstract}
\tableofcontents

\input{chapters/01-introduction}
\input{chapters/02-literature-review}
\input{chapters/03-methodology}
\input{chapters/04-results-analysis}
\input{chapters/05-discussion}
\input{chapters/06-conclusion}

\printbibliography

\end{document}
```

## Markdown → LaTeX 转换规则

| Markdown | LaTeX |
|---|---|
| `# 章节标题` | `\chapter{章节标题}` |
| `## 节标题` | `\section{节标题}` |
| `### 小节标题` | `\subsection{小节标题}` |
| `**加粗**` | `\textbf{加粗}` |
| `*斜体*` | `\textit{斜体}` |
| `[参考文献]` | `\cite{key}` 或 `\supercite{key}` |
| `` `代码` `` | `\texttt{代码}` |
| `- 列表项` | `\begin{itemize}\item 列表项\end{itemize}` |
| `1. 编号项` | `\begin{enumerate}\item 编号项\end{enumerate}` |
| `> 引用` | `\begin{quote}引用\end{quote}` |
| `![图注](path)` | `\includegraphics{path}` |
| `$$...$$` | `\begin{equation}...\end{equation}` |

## 特殊字符转义

LaTeX 中需转义的字符：`#` `$` `%` `&` `_` `{` `}` `~` `^` `\`

中文论文使用 XeLaTeX 编译，支持中文 UTF-8 直接输入。

## 编译流程

```bash
xelatex main.tex
biber main
xelatex main.tex
xelatex main.tex
```

或使用 latexmk 一键编译：
```bash
latexmk -xelatex main.tex
```

## references.bib 生成

从 Zotero 导出或从 source marker 清单导出 BibTeX 条目。格式：

```bibtex
@article{key2024,
    author  = {作者},
    title   = {论文标题},
    journal = {期刊名},
    year    = {2024},
    volume  = {10},
    pages   = {1-10},
}

@standard{gb50009-2012,
    title   = {建筑结构荷载规范},
    number  = {GB 50009-2012},
    year    = {2012},
    publisher = {中国建筑工业出版社},
}
```

## 与现有流程的衔接

1. 完成所有阶段的 `.thesis-workflow/` 产物。
2. `academic-format-cleaner` 通过后，启动 LaTeX 输出。
3. 将 `.md` 或纯文本章节转为 `.tex` 文件。
4. 生成 `main.tex` 和 `references.bib`。
5. 编译验证，报告编译结果和可能的问题。
