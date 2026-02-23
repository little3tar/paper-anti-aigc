# CLI 使用场景与建议 Prompt

## 场景一：全局或局部 LaTeX 文档洗稿去 AI 化

**建议 Prompt**：

```text
请使用 engineering-paper-humanizer 技能审查并优化当前目录下的 main.tex 的第 3 节。
重点：
1) 削减过度书面化的 AI 腔调和堆砌的段首连接词
2) 大幅提升文本的"突发性(Burstiness)"，制造长短句顿挫
3) 严格遵循数据完整性红线，严禁捏造未出现的数据
4) 保证文献引用标签 \cite 及所有 LaTeX/ctexart 排版命令绝对不被破坏
处理完毕后直接覆盖更新原文件。
```

## 场景二：外部 AI 文本降特征后无缝缝合（缝合怪模式）

**建议 Prompt**：

```text
我有一段关于[非线性死区补偿算法]的新文本内容。
请先使用 engineering-paper-humanizer 将其洗稿，注入"人味"和具体参数（注意严格遵循数据完整性红线），
消除平稳的 AI 句式（突发性最大化）。
然后检索 main.tex，找到 3.3.2 节（单缸位置伺服控制律设计）最合理的锚点位置进行植入。
确保新植入段与前后文（特别是方程 eq:control_law 附近）逻辑不断层，语气风格浑然一体。
```

## 场景三：段落快速查杀与对抗改写验证

**建议 Prompt**：

```text
请使用 engineering-paper-humanizer 帮我评估并当场改写下面这段话的 AI 特征
（特别是"困惑度"和"突发性"缺陷）。
指出它为什么像 AI 写的，然后在不捏造事实数据的前提下，
给出 2 个具有强烈人类工程师顿挫感（长短句交错）的改写版本：

[粘贴你的段落]
```

## 场景四：自动化格式检查

**直接在终端运行**：

```bash
# 全文检查并输出人类可读报告
python3 .opencode/skills/engineering-paper-humanizer/scripts/check_latex.py main.tex

# 只看第 2 章的 error
python3 .opencode/skills/engineering-paper-humanizer/scripts/check_latex.py main.tex --section 2 --severity error

# 输出 JSON 供 agent 自动处理
python3 .opencode/skills/engineering-paper-humanizer/scripts/check_latex.py main.tex --json
```

**在 agent 对话中使用**：

```text
请先运行 check_latex.py 检查 main.tex 第 3 节，然后根据输出的诊断结果逐条修复所有 error 级别问题。
修复完毕后再次运行脚本确认清零。
```
