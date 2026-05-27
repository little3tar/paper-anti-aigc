# Skill 触发评估

`trigger-evals.json` 包含七个 skill 的触发提示（正例）和近误提示（反例），用于修订 `SKILL.md` frontmatter 中的 description。正面案例应清晰激活指定 skill；负面案例是应路由到其他位置的相邻请求。

## 文件

| 文件 | 用途 |
|---|---|
| `trigger-evals.json` | 评估用例（56 条，每 skill 5 正例 + 3 反例） |
| `run_eval.py` | 评估运行器（手动交互 / JSON 输出 / 汇总查看） |
| `grader.md` | 触发评分代理定义（判断 PASS/FAIL + 异常检测） |
| `analyzer.md` | 结果分析代理定义（交叉分析 + 改进建议） |
| `benchmark.json` | 基准测试结果（运行时生成） |

## 使用

```bash
# 手动交互评估（逐条输入触发的 skill）
python evals/run_eval.py

# 只评估单个 skill
python evals/run_eval.py --skill docx-translator

# 查看已有 benchmark 汇总
python evals/run_eval.py --summary-only

# 输出 eval 用例列表供外部工具使用
python evals/run_eval.py --json
```
