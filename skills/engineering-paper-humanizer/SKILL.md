---
name: engineering-paper-humanizer
description: >-
  用于中文工程类论文正文润色与去 AI 味。用户提到论文润色、中文工程论文改写、减少机器感、
  humanize thesis prose、academic Chinese polishing、模板化套话、中文引号或破折号问题时使用。
  适用于 LaTeX、Markdown、plain text 中的正文内容；不处理 citation placement、BibTeX/LaTeX
  命令或 Markdown 格式问题，这些交给 academic-format-cleaner。
---

# Engineering Paper Humanizer

## Red Flags（停止并检查）

| AI的想法 | 正确做法 |
|---|---|
| "这段写得太平淡，加点升华" | 工程论文用参数、约束和代价说话，不加宏大叙事 |
| "破折号改成逗号太麻烦，保留" | 中文正文破折号必须处理，不得保留 `——` |
| "status.json 里 P0 还在，先润色" | P0/P1 未清零时拒绝润色，退回到审计 |
| "这个结论的证据我帮它补上" | 不补写来源、数据、实验条件，缺证据移入缺口清单 |
| "润色就是压缩文字" | 保留数据口径、方法条件、指标含义和结论边界，不删必要信息 |
| "marker 里的题名太长，缩写一下" | `[文献题名]` 方括号内的题名是 bibliography 解析依据，不得修改、缩写、翻译或删除 |

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

启动润色前，检查 `.thesis-workflow/status.json`：若 `p0_count` 或 `p1_count` > 0，或 `next_allowed` 不为 `"humanizer"`，拒绝继续并提示先运行 `reference-integrity-auditor` 并将 P0/P1 清零。若 `next_allowed` 为 `"fix-evidence"` 说明审计已发现问题但尚未修复，拒绝继续。若文件不存在，说明审计阶段未运行，拒绝继续并提示先运行审计。Validation mode 下可忽略此门控。

## 处理范围

处理这些问题：

1. **AI 腔与模板化表达**：如“具有重要意义”“应运而生”“值得注意的是”“综上所述”“广阔应用前景”等空泛套话。
2. **中文工程论文语气**：用具体工况、参数、约束、代价和工程取舍替代空泛升华。
3. **通用中文标点**：ASCII 直双引号、中英文引号混用、半边引号、破折号和异常 dash。
4. **中文化规则**：清理无主语动作句、权威感套话、引导式开场、口号式尾部否定、碎片化标题和堆叠句。
5. **文本级自检**：运行 `scripts/check_text.py` 定位正文表达问题。

不处理：LaTeX 命令、Markdown 格式结构、公式/代码环境内部内容、变量/数值/单位、缺来源结论——这些交给 format-cleaner 或 auditor。**source marker 方括号及题名文字绝对不动**，只改 marker 前后的连接词。

## 核心原则

1. **工程表达优先**：用限制、代价、参数和工况说话，而不是用宏大叙事升华。
2. **标点服务语义**：引号只用于真实引用、特指术语、语义距离；破折号默认改成逗号、分号、句号或自然连接词。
3. **公式数据保护**：只改公式前后的说明文字，不改 LaTeX 数学环境、参数符号、单位、数值和计算结论。
4. **证据边界保护**：含 `[待补来源: ...]`、`needs-source`、P0/P1 的内容移出正文，放入证据缺口或台账。润色只处理已有来源支撑的正文。
5. **Source marker 保护**：`[文献题名]`、`[Mxx]`、`[参考文献]` 等方括号标记不动方括号、不动题名文字——不缩写、不翻译、不删减。只改 marker 前后的连接词和句式。

## 工作流程

### 1. 读取上下文

先判断文本类型和用户目标。若用户只要求格式修复，转用 `academic-format-cleaner`。若用户要求润色、降 AI 味或修复中文标点，继续本流程。

**强制读取审计报告**：启动时必须读取 `.thesis-workflow/03-reference-audit.md`（如存在），获取其中的两个手交清单：

- `可润色段落`：这些段落可以正常改写润色。
- `禁止润色成定论的段落`：这些段落含 P0/P1、缺数据或 unsupported claims，**只做标点和连接词修正，不改变技术表述的确定性**。不得将这些段落中的”可能””初步””待验证”等降级表述改为肯定语气。

如果 `03-reference-audit.md` 不存在但 `status.json` 存在且 P0/P1 已清零，可继续但需在输出中注明”审计报告缺失，润色边界由 humanizer 自行判断”。

如果用户要求直接修改论文主文件，修改前先通过 `scripts/git_snapshot.py <主文件>` 创建备份。修改完成后将本轮润色操作记录（变更清单，非全文副本）写入 `.thesis-workflow/04-humanized.md`，最终润色后文本写入 `main.md` / `main.txt`。

文件产出规则遵循 workflow §输出与文件安全。本阶段产物为 `.thesis-workflow/04-humanized.md`（润色操作记录，非全文副本）。

如用户提供了项目级上下文文件（`ledger/` 目录），先读取 `ledger/facts.md` 和 `ledger/decisions.md`。

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

返回改写后的文本，并附简短说明。若用户给的是文件并要求直接修改文件，先备份、再修改文件，修改后运行 `check_text.py` 复查，并把本轮润色变更清单写入 `.thesis-workflow/04-humanized.md`（非全文副本），最终润色后文本写入 `main.md` / `main.txt`。

## 参考文件

| 文件 | 用途 |
| --- | --- |
| `scripts/check_text.py` | 通用中文文本检查 |
| `scripts/text_rules.json` | 文本规则数据 |
| `scripts/generate_dict.py` | 生成文本规则速查表 |
| `references/rewrite-guide.md` | 中文工程论文改写规则 |
| `references/punctuation-guide.md` | 引号和破折号专项规则 |
| `references/optional-checks.md` | 可选质量评判 |
| `assets/main-tex-context-template.md` | 论文主文件结构地图模板；只作为创建项目本地上下文的参考 |
