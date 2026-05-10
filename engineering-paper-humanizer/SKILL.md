---
name: engineering-paper-humanizer
description: 深度润色中文工程类学术文本，清理 AI 腔、模板化套话、机械连接词、通用积极结论、中文标点暴露、引号混用、破折号滥用和工程论文中的空泛表达。适用于 LaTeX、Markdown、纯文本中的正文内容；当用户提到论文润色、中文工程论文改写、减少机器感、增加人味、清除对话痕迹、修复中文引号/破折号问题时必须使用。不要处理 LaTeX/Markdown 专属格式问题，格式检查交给 academic-format-cleaner。
---

# Engineering Paper Humanizer

本 skill 只负责中文工程论文的正文表达和通用中文标点，不再承担 LaTeX/Markdown/txt 的格式检查职责。它可以读取 `.tex`、`.md`、`.txt`，但目标是正文内容，而不是命令、引用位置、标题层级或代码块格式。

运行脚本需要 Python 3.7 或更高版本；Git 仅在需要查看差异时使用。

## Position In Thesis Workflow

在完整论文写作流程中，本 skill 应位于 `reference-integrity-auditor` 之后、`academic-format-cleaner` 之前。

推荐顺序：

1. `thesis-outline-planner`：规划总大纲和文献池。
2. `evidence-grounded-chapter-writer`：撰写带证据标记的章节初稿。
3. `reference-integrity-auditor`：检查无来源结论、引用关键词和待补证据。
4. `engineering-paper-humanizer`：在证据可靠后润色正文，降低 AI 腔。
5. `academic-format-cleaner`：最后处理引用位置、LaTeX/Markdown 格式和命令保护。

若草稿仍存在 P0/P1 证据问题，先退回证据审查或章节写作，不要直接润色。

## Scope

处理这些问题：

1. **AI 腔与模板化表达**：如“具有重要意义”“应运而生”“值得注意的是”“综上所述”“广阔应用前景”。
2. **中文工程论文语气**：用具体工况、参数、约束、代价和工程妥协替代空泛升华。
3. **通用中文标点**：ASCII 直双引号、中英文引号混用、半边引号、破折号和异常 dash。
4. **新版 humanizer 中文化规则**：无主语动作句、权威感套话、引导式开场、口号式尾部否定、中文化后缀堆叠、碎片化标题。
5. **文本级自检**：运行 `scripts/check_text.py` 定位正文问题。

不处理这些问题：

- `\cite{}` 位置、LaTeX 百分号转义、命令参数断行。
- Markdown frontmatter、代码块围栏、标题层级等格式问题。
- 图表、公式、代码环境内部内容。
- 公式变量、参数字母、单位、数值、编号、推导步骤和计算结果。

这些交给 `academic-format-cleaner`。

## Core Principles

1. **保留原意**：术语、物理量、结论方向和已有数据不随意替换。
2. **禁止捏造数据**：没有来源的数字、实验条件和性能提升不能编造。
3. **禁止编造文献**：无真实文献依据时，删除模糊归因，改为客观陈述。
4. **工程表达优先**：用限制、代价、参数和工况说话，而不是用宏大叙事升华。
5. **标点服务语义**：引号只用于真实引用、特指术语、语义距离；破折号默认改成逗号、分号、句号或自然连接词。
6. **公式数据保护**：润色时只改公式前后的说明文字，不改 LaTeX 数学环境、参数符号、单位、数值和计算结论。

## Workflow

### 1. 读取上下文

先判断文本类型和用户目标。若用户只要求格式修复，转用 `academic-format-cleaner`。若用户要求润色、降 AI 味或修复中文标点，继续本流程。

### 2. 运行文本检查

```bash
python <SKILL_DIR>/scripts/check_text.py <TARGET_FILE>
python <SKILL_DIR>/scripts/check_text.py <TARGET_FILE> --format markdown
python <SKILL_DIR>/scripts/check_text.py <TARGET_FILE> --format plain
```

统一使用 `check_text.py` 作为正文检查入口。

### 3. 按规则改写

按 `references/rewrite-guide.md` 和 `references/punctuation-guide.md` 逐段处理：

- 删除章节预告、教程式开场、对话残留。
- 将“显著提升”“关键作用”等空泛判断换成具体指标；无指标时降级为克制表述。
- 把“本质上”“核心在于”“真正的问题是”等伪洞察开头改为直接技术陈述。
- 对“完成了/实现了/进行了”这类无主语动作句补出主体或工况。
- 对“无需猜测”“无额外配置”等口号式尾巴改成完整机制说明。

### 4. 标点专项处理

引号：

- 中文正文外层用 `“...”`，嵌套用 `‘...’`。
- 书名、论文名、标准名、法规名优先用 `《...》`。
- 代码、命令、变量、路径、文件名用反引号或等宽命令，不用中文引号。
- 英文整句引用不要强行改成中文引号；LaTeX 中优先用 TeX 式引号或 `\enquote{}`。
- 单纯强调不要加引号。

破折号：

- 中文正文默认不用 `——`、`—`、`–`、`--`、`---`。
- 解释关系改“即”“也就是说”或拆句。
- 补充插入改逗号或括号。
- 强转折改分号或句号。
- 数字范围、页码范围、数学负号、复合术语、代码片段除外。

### 5. 二次反 AI 审计

完成初稿后，做一次短审：

1. 问自己：这段哪里还明显像 AI 生成？
2. 列出剩余痕迹：节奏过整齐、术语堆叠、连接词过强、结尾太漂亮、参数不够实。
3. 再改一遍，直到文本读起来像工程师写出的论文段落，而不是模型拼出的总结。

### 6. 输出

返回改写后的文本，并附简短说明。若用户给的是文件并要求直接修改文件，修改文件后再运行 `check_text.py` 复查。

## Reference Files

| 文件 | 用途 |
| --- | --- |
| `scripts/check_text.py` | 通用中文文本检查 |
| `scripts/text_rules.json` | 文本规则数据 |
| `scripts/generate_dict.py` | 生成文本规则速查表 |
| `references/rewrite-guide.md` | 中文工程论文改写规则 |
| `references/punctuation-guide.md` | 引号和破折号专项规则 |
| `references/optional-checks.md` | 可选质量评分 |
