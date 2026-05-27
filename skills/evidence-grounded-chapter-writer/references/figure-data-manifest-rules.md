# 图表数据溯源规则

`figure-data-manifest.md` 持久记录每张图的数据来源、生成脚本和输出格式，用于后续可复现性核查。它与 `ledger/` 台账分工不同：台账记录设计参数和决策，manifest 追踪图表从数据到成品的完整生成链。

## 文件位置

`.thesis-workflow/figure-data-manifest.md`

## 列定义

| Figure ID | 占位符名 | 数据文件 | 真实/mock | 来源说明 | 生成脚本 | 输出格式 | 状态 |
|---|---|---|---|---|---|---|---|
| Fig 3-1 | 流量-压力曲线 | data/ch3/flow.csv | real | 实验台采集 | scripts/ch3/fig01.py | PNG, SVG | draft |

- **Figure ID**：按章编号，如 `Fig 3-1`
- **占位符名**：正文中使用的占位符描述文本，如 `[此处插入图片：流量-压力曲线]` 中去掉前缀的"流量-压力曲线"，与 Figure ID 一一对应
- **数据文件**：源数据文件路径（相对于论文项目根目录）
- **真实/mock**：`real`（真实数据）、`mock`（占位数据，文件名应含 `mock_` 或 `synthetic_` 前缀）
- **来源说明**：数据出处——实验采集、仿真导出、用户提供、开放数据集等
- **生成脚本**：从数据文件生成最终图表的脚本路径
- **输出格式**：目标输出格式列表
- **状态**：`draft`、`data-ready`、`generated`、`confirmed`

## 生命周期

大纲阶段建表框架（从大纲的图表计划同步图表清单，此时仅填充 Figure ID 和占位符名列）→ 写作阶段逐图填充数据文件、来源说明和生成脚本 → 审计阶段交叉校验数据来源与正文一致。

## 动作规则

图表插入点仍需在正文中使用 `[此处插入图片：...]` 占位符，尾部图表清单只汇总不替代。`figure-data-manifest.md` 不替代正文插入点。

## 生成图存放规则

AI 根据 Mermaid 代码块、matplotlib 脚本、Graphviz DOT 文件或提示词模板渲染产生的图片文件，统一存放在 `.thesis-workflow/generated-figures/`。该目录与 `evidence/` 分工明确：

| 目录 | 放什么 | 性质 |
|---|---|---|
| `evidence/user-figures/` | 用户提供的原始照片、截图、渲染图 | 用户原始输入，只读 |
| `evidence/user-videos/` | 用户提供的原始视频 | 用户原始输入，只读 |
| `.thesis-workflow/generated-figures/` | AI 生成的图（Mermaid/matplotlib/DOT/提示词渲染） | 可重新生成，不混入用户材料 |

**命名格式**：`Fig X-Y 描述.png`（与 manifest 中 Figure ID 对应，如 `Fig 3-1 流量-压力曲线.png`）。

此规则全流程适用——无论图片在 outline-planner、chapter-writer 还是修改回环中产生，均存入同一目录。manifest 中"生成脚本"列记录生成该图的代码/提示词来源，"数据文件"列可为空（纯代码生成图无外部数据文件）。

Mermaid/matplotlib/DOT 图表代码块在格式转换阶段（format-cleaner）的保护规则见 format-cleaner 参考文件 `format-guide.md` §图表代码块保护。
