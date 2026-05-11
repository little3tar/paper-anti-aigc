---
name: engineering-paper-humanizer
description: >-
  用于中文工程类论文正文润色与去 AI 味。用户提到论文润色、中文工程论文改写、减少机器感、
  humanize thesis prose、academic Chinese polishing、模板化套话、中文引号或破折号问题时使用。
  适用于 LaTeX、Markdown、plain text 中的正文内容；不处理 citation placement、BibTeX/LaTeX
  命令或 Markdown 格式问题，这些交给 academic-format-cleaner。
---

# Engineering Paper Humanizer

本 skill 负责中文工程论文的正文表达和通用中文标点，不承担 LaTeX、Markdown 或 txt 的格式检查职责。它可以读取 `.tex`、`.md`、`.txt`，但目标是正文内容，而不是命令、引用位置、标题层级或代码块格式。

运行脚本需要 Python 3.7 或更高版本；Git 仅在需要查看差异时使用。

## 在 Thesis Workflow 中的位置

本 skill 应位于 `reference-integrity-auditor` 之后、`academic-format-cleaner` 之前。

推荐顺序：

1. `thesis-outline-planner`：规划总大纲和文献池。
2. `evidence-grounded-chapter-writer`：撰写带证据标记的章节初稿。
3. `reference-integrity-auditor`：检查无来源结论、source marker 和待补证据。
4. `engineering-paper-humanizer`：在证据可靠后润色正文，降低 AI 腔。
5. `academic-format-cleaner`：最后处理引用位置、LaTeX/Markdown 格式和命令保护。

若草稿仍存在 P0/P1 证据问题，先退回证据审计或章节写作，不要直接润色成更像定论的文字。

## 处理范围

处理这些问题：

1. **AI 腔与模板化表达**：如“具有重要意义”“应运而生”“值得注意的是”“综上所述”“广阔应用前景”等空泛套话。
2. **中文工程论文语气**：用具体工况、参数、约束、代价和工程取舍替代空泛升华。
3. **通用中文标点**：ASCII 直双引号、中英文引号混用、半边引号、破折号和异常 dash。
4. **中文化规则**：清理无主语动作句、权威感套话、引导式开场、口号式尾部否定、碎片化标题和堆叠句。
5. **文本级自检**：运行 `scripts/check_text.py` 定位正文表达问题。

不处理这些问题：

- `\cite{}` 位置、LaTeX 百分号转义、命令参数断行。
- Markdown frontmatter、代码块围栏、标题层级等格式问题。
- 图表、公式、代码环境内部内容。
- 公式变量、参数字母、单位、数值、编号、推导步骤和计算结果。
- 缺来源结论、伪造文献、P0/P1 审计问题。

这些交给 `academic-format-cleaner` 或 `reference-integrity-auditor`。

## 核心原则

1. **保留原意**：术语、物理量、结论方向和已有数据不随意替换。
2. **不编造数据**：没有来源的数字、实验条件和性能提升不能补写。
3. **不编造文献**：无真实文献依据时，删除模糊归因，改为客观陈述或放入证据缺口。
4. **工程表达优先**：用限制、代价、参数和工况说话，而不是用宏大叙事升华。
5. **标点服务语义**：引号只用于真实引用、特指术语、语义距离；破折号默认改成逗号、分号、句号或自然连接词。
6. **公式数据保护**：润色时只改公式前后的说明文字，不改 LaTeX 数学环境、参数符号、单位、数值和计算结论。
7. **证据边界保护**：润色前先检查正文是否含 `[待补来源: ...]`、`needs-source`、P0/P1 或其他缺来源内容。此类内容应移出正文，放入证据缺口或项目台账；润色只处理已有来源、用户材料、已确认设计假设或可复现推导支撑的正文。

## 工作流程

### 1. 读取上下文

先判断文本类型和用户目标。若用户只要求格式修复，转用 `academic-format-cleaner`。若用户要求润色、降 AI 味或修复中文标点，继续本流程。

如果用户要求直接修改论文主文件，修改前先备份主文件，并在输出中说明备份位置；复制备份默认放在论文项目根目录的 `.thesis-workflow/backups/`。修改完成后，即使已经写回主文件，也要把本轮润色结果另存或同步到 `.thesis-workflow/04-humanized.md`。若只在对话中返回改写文本且没有进入论文项目工作流，则不需要创建备份或产物文件。

单独运行本 skill 时，若当前目录、用户指定目录或已识别的论文项目根目录中存在 `.thesis-workflow/`，或用户明确处于论文 workflow 项目中，结束时必须更新 `.thesis-workflow/04-humanized.md` 和必要的 `project-ledger.md`；不要因为用户没有再次说“生成文件”而跳过更新。若 P0/P1 仍未解决，不生成可提交润色稿，只把可润色段落、禁止润色段落和证据缺口写入阶段产物。

如用户提供了项目级上下文文件，例如论文主文件地图、术语表、已确认参数表或 project ledger，先读取这些项目文件以保持术语、章节关系和参数一致。项目特定事实不要写入本 skill 目录；需要建立上下文时，可参考 `assets/main-tex-context-template.md` 在论文项目根目录的 `.thesis-workflow/main-tex-context.md` 创建项目本地文件。

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

- 中文正文外层用中文双引号，嵌套用中文单引号。
- 书名、论文名、标准名、法规名优先用书名号。
- 代码、命令、变量、路径、文件名用反引号或等宽命令，不用中文引号。
- 英文整句引用不要强行改成中文引号；LaTeX 中优先用 TeX 式引号或 `\enquote{}`。
- 单纯强调不要加引号。

破折号：

- 中文正文默认不用 `——`、`—`、`–`、`--`、`---`。
- 解释关系改为“即”“也就是说”或拆句。
- 补充插入改为逗号或括号。
- 强转折改为分号或句号。
- 数字范围、页码范围、数学负号、复合术语、代码片段除外。

### 5. 二次 AI 痕迹审计

完成初稿后，做一次短审：

1. 问自己：这段哪里还明显像 AI 生成？
2. 列出剩余痕迹：节奏过整齐、术语堆叠、连接词过强、结尾太漂亮、参数不够实。
3. 再改一遍，直到文本读起来像工程师写出的论文段落，而不是模型拼出的总结。

### 6. 输出

返回改写后的文本，并附简短说明。若用户给的是文件并要求直接修改文件，先备份、再修改文件，修改后运行 `check_text.py` 复查，并把本轮润色结果另存或同步到 `.thesis-workflow/04-humanized.md`。若用户要求生成独立润色稿但未指定目录，默认写入 `.thesis-workflow/04-humanized.md`；直接修改原文时仍写回同一个主文件或用户指定文件，同时保留该阶段产物，不主动拆成多个文件。

## 参考文件

| 文件 | 用途 |
| --- | --- |
| `scripts/check_text.py` | 通用中文文本检查 |
| `scripts/text_rules.json` | 文本规则数据 |
| `scripts/generate_dict.py` | 生成文本规则速查表 |
| `references/rewrite-guide.md` | 中文工程论文改写规则 |
| `references/punctuation-guide.md` | 引号和破折号专项规则 |
| `references/optional-checks.md` | 可选质量评判 |
| `assets/main-tex-context-template.md` | 项目级 `main.tex` 地图模板；只作为创建项目本地上下文的参考 |
