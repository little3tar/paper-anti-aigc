# LaTeX 绝对保护红线

## 禁止全局替换

禁止使用 replaceAll 修改 LaTeX 命令。缺失反斜杠时（如 `includegraphics`），只在当前单词前补全 `\`。

## 排版环境绝对保护

绝不修改、删除或翻译任何以 `\` 开头的命令和环境。特别注意：

- `ctexart` 中文字体设置命令（`\zihao`、`\songti`、`\setCJKmainfont` 等）
- `\begin{}`/`\end{}` 环境声明
- `\label{}`、`\ref{}`、`\includegraphics{}` 等交叉引用命令

## 数学体系免疫

`equation`、`align` 等数学公式环境块内部的字母推导、等式演算 **绝对禁止修改**。

## 禁止内部换行

- 严禁将 `\cite{...}` 或连同前后符号拆分到多行
- 严禁在 `\label{...}` 或 `\includegraphics{...}` 的花括号内部换行
- 百分号必须输出为 `\%`

## 引用格式规则

- `\cite{...}` 紧贴被引文字
- 禁止在 `\cite{}` 前加空格
- 引用标记必须在句号、逗号的 **内侧**

```latex
% ❌ 错误
控制任务。 \cite{xxx}

% ✅ 正确
控制任务\cite{xxx}。
```
