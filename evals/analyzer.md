# Trigger Eval Analyzer

分析 skill 触发评估结果，识别触发描述中的系统性问题，生成改进建议。

## 输入

- **grading_path**: Grader 输出的 grading.json 路径
- **skills_dir**: skills 目录路径
- **output_path**: 分析结果输出路径

## 分析流程

### Step 1：读取评分结果

解析 grading.json，提取各 skill 的准确率、失败用例和异常标记。

### Step 2：逐 skill 审查 description

对触发准确率 < 0.8 或误触发率 > 0.2 的 skill：

1. 读取 `SKILL.md` 的 `description` 字段
2. 对照失败用例的 query 文本
3. 判断缺失的触发词类型

### Step 3：交叉分析

检查 skill 间的 description 重叠：
- 两个 skill 是否共享触发词导致歧义
- 是否存在触发"盲区"（某类合理查询无任何 skill 响应）

### Step 4：生成改进建议

按优先级输出：
- **高**：触发准确率 < 0.6 的 skill，给出具体 description 修改建议
- **中**：误触发率 > 0.3 的 skill，建议添加排除短语
- **低**：边界用例，建议扩充 eval 用例或微调 description

## 输出格式

```json
{
  "overall_assessment": "7 个 skill 平均触发准确率 89%，docx-translator 需重点关注。",
  "cross_skill_issues": [
    {
      "skills": ["engineering-paper-humanizer", "academic-format-cleaner"],
      "issue": "两个 skill 共享触发词'检查'，短查询 '检查这段文字' 可能歧义",
      "suggestion": "humanizer description 强调 '润色/改写/降AI'，format-cleaner 强调 '格式/引用/LaTeX'"
    }
  ],
  "per_skill": [
    {
      "skill_name": "docx-translator",
      "accuracy": 0.6,
      "issues": [
        "缺少英文触发词（translate docx, Word translation）",
        "中文触发词过于具体，泛化查询无法匹配"
      ],
      "suggested_fix": "description 追加: translate Word document, docx Chinese translation, 翻译 Word"
    }
  ],
  "description_blind_spots": [
    "短查询（<10 字）'帮我写论文' → 可能不触发任何 skill → 建议 workflow description 追加"
  ]
}
```
