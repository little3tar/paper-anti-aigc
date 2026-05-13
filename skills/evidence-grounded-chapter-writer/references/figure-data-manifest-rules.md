# 图表数据溯源规则

`figure-data-manifest.md` 持久记录每张图的数据来源、生成脚本和输出格式，用于后续可复现性核查。它比 ledger 的 `figures-tables` 分区更细一层。

## 文件位置

`.thesis-workflow/figure-data-manifest.md`

## 与 ledger figures-tables 的分工

| | `figures-tables`（ledger） | `figure-data-manifest.md` |
|---|---|---|
| 问题 | 需要什么图 | 图怎么生成 |
| 粒度 | 图表级 | 数据文件 + 脚本级 |
| 主要列 | 占位符名、所需内容、目标章节、状态 | 数据文件路径、真实/mock、来源、生成脚本、输出格式 |
| 更新阶段 | 规划、写作 | 写作、审计 |

## 列定义

| Figure ID | 占位符名 | 数据文件 | 真实/mock | 来源说明 | 生成脚本 | 输出格式 | 状态 |
|---|---|---|---|---|---|---|---|
| Fig 3-1 | 流量-压力曲线 | data/ch3/flow.csv | real | 实验台采集 | scripts/ch3/fig01.py | PNG, SVG | draft |

- **Figure ID**：按章编号，如 `Fig 3-1`
- **数据文件**：源数据文件路径（相对于论文项目根目录）
- **真实/mock**：`real`（真实数据）、`mock`（占位数据，文件名应含 `mock_` 或 `synthetic_` 前缀）
- **来源说明**：数据出处——实验采集、仿真导出、用户提供、开放数据集等
- **生成脚本**：从数据文件生成最终图表的脚本路径
- **输出格式**：目标输出格式列表
- **状态**：`draft`、`data-ready`、`generated`、`confirmed`

## 生命周期

大纲阶段建表框架（从 `figures-tables` 同步图表清单）→ 写作阶段逐图填充数据文件和脚本 → 审计阶段交叉校验数据来源与正文一致。

## 动作规则

图表插入点仍需在正文中使用 `[此处插入图片：...]` 占位符，尾部图表清单只汇总不替代。`figure-data-manifest.md` 不替代正文插入点。
