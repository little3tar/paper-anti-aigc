# Trigger Eval Grader

评估 skill 触发准确率。对照 `trigger-evals.json` 中的预期，判断每次查询实际触发的 skill 是否正确。

## 输入

- **expectations**: `trigger-evals.json` 路径（含 `skill_name`、`query`、`should_trigger`、`expected_reason`）
- **results**: 每次查询的实际触发结果（`actual_skill`、`triggered`、`latency_ms`）

## 评估流程

### Step 1：读取预期

解析 `trigger-evals.json`，建立 `(query, skill_name, should_trigger)` 三元组。

### Step 2：逐条判断

对每条用例：

| 预期 | 实际 | 判定 |
|---|---|---|
| `should_trigger=true` | 匹配的 skill 正确 | PASS |
| `should_trigger=true` | 未触发或触发错误 skill | FAIL（漏触发） |
| `should_trigger=false` | 未触发目标 skill | PASS |
| `should_trigger=false` | 触发了目标 skill | FAIL（误触发） |

### Step 3：按 skill 汇总

计算每个 skill 的：
- 触发准确率（正例 PASS / 正例总数）
- 误触发率（反例 FAIL / 反例总数）
- 综合 F1

### Step 4：标记异常

- 同 skill 内多个正例 FAIL → description 触发词不足
- 同 skill 内多个反例 FAIL → description 过于宽泛
- 特定 query 反复 FAIL → 边界用例需调整

## 输出格式

```json
{
  "summary": {
    "total": 56,
    "passed": 50,
    "failed": 6,
    "accuracy": 0.893
  },
  "by_skill": [
    {
      "skill_name": "thesis-writing-workflow",
      "positive_total": 5,
      "positive_pass": 5,
      "negative_total": 3,
      "negative_pass": 3,
      "trigger_accuracy": 1.0,
      "false_trigger_rate": 0.0
    }
  ],
  "failures": [
    {
      "skill_name": "docx-translator",
      "query": "请将这个 .docx 文件中的英文翻译为中文。",
      "expected": "trigger",
      "actual": "none",
      "reason": "查询未命中任何 skill description 关键词"
    }
  ],
  "anomalies": [
    {
      "skill_name": "engineering-paper-humanizer",
      "pattern": "3 条正例 FAIL，均为短查询（<15 字）",
      "suggestion": "description 需补充短查询触发词"
    }
  ]
}
```
