# CLI 使用场景与 Prompt 模板

本文件收录 engineering-paper-humanizer 的典型使用场景，包括建议 Prompt 和脚本命令。

## 场景一：全局/局部洗稿去 AI 化

```text
请使用 engineering-paper-humanizer 技能审查并优化当前目录下的 main.tex 的第 3 节。
重点：
1) 削减过度书面化的 AI 腔调和堆砌的段首连接词
2) 大幅提升文本的"突发性(Burstiness)"，制造长短句顿挫
3) 严格遵循数据完整性红线，严禁捏造未出现的数据
4) 保证文献引用标签 \cite 及所有 LaTeX/ctexart 排版命令绝对不被破坏
处理完毕后直接覆盖更新原文件。
```

## 场景二：外部 AI 文本缝合植入

```text
我有一段关于[非线性死区补偿算法]的新文本内容。
请先使用 engineering-paper-humanizer 将其洗稿，注入"人味"和具体参数（注意严格遵循数据完整性红线），
消除平稳的 AI 句式（突发性最大化）。
然后检索 main.tex，找到 3.3.2 节（单缸位置伺服控制律设计）最合理的锚点位置进行植入。
确保新植入段与前后文（特别是方程 eq:control_law 附近）逻辑不断层，语气风格浑然一体。
```

## 场景三：段落查杀与对抗改写

```text
请使用 engineering-paper-humanizer 帮我评估并当场改写下面这段话的 AI 特征
（特别是"困惑度"和"突发性"缺陷）。
指出它为什么像 AI 写的，然后在不捏造事实数据的前提下，
给出 2 个具有强烈人类工程师顿挫感（长短句交错）的改写版本：

[粘贴你的段落]
```

## 场景四：自动化格式检查

终端直接运行：

```bash
# 全文检查
python3 <SKILL_DIR>/scripts/check_latex.py <TARGET_FILE>

# 只看第 2 章的 error
python3 <SKILL_DIR>/scripts/check_latex.py <TARGET_FILE> --section 2 --severity error

# JSON 输出供 agent 处理
python3 <SKILL_DIR>/scripts/check_latex.py <TARGET_FILE> --json
```

在 agent 对话中使用：

```text
请先运行 check_latex.py 检查 main.tex 第 3 节，然后根据输出的诊断结果逐条修复所有 error 级别问题。
修复完毕后再次运行脚本确认清零。
```

## 场景五：分支备份与回滚

脚本会自动创建独立的备份分支（`backup/humanizer/<时间戳>`），不污染主分支提交历史。

```bash
# 修改前创建分支备份（agent 自动执行，也可手动）
python3 <SKILL_DIR>/scripts/git_snapshot.py <TARGET_FILE>

# 查看所有备份分支
python3 <SKILL_DIR>/scripts/git_snapshot.py --list

# 从最近备份恢复文件
python3 <SKILL_DIR>/scripts/git_snapshot.py --rollback

# 从指定备份分支恢复
python3 <SKILL_DIR>/scripts/git_snapshot.py --rollback backup/humanizer/20260224-120000

# 对比当前文件与最近备份的差异
python3 <SKILL_DIR>/scripts/git_snapshot.py --diff <TARGET_FILE>

# 清理旧备份分支（交互确认）
python3 <SKILL_DIR>/scripts/git_snapshot.py --cleanup

# 跳过确认直接清理
python3 <SKILL_DIR>/scripts/git_snapshot.py --cleanup --yes
```
