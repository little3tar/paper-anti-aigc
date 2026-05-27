---
name: docx-translator
description: >-
  用于将 Word 文档(.docx)内容翻译为中文。用户要求翻译 Word 文档、翻译 docx 文件、
  将英文论文翻译为中文、docx 中译、Word 文件翻译成中文、translate docx to Chinese、
  Word document translation 时使用。也适用于需要保留原文档格式的学术论文、技术报告、工程文档翻译场景。
---

# DOCX 文档翻译工作流

将英文（或其他语言）.docx 文件翻译为中文，生成翻译后的 .docx，保留原文格式与语境风格。

## Red Flags（停止并检查）

| AI的想法 | 正确做法 |
|---|---|
| "用 glob 模糊搜索 .docx 文件" | 目录中可能有多个 .docx，模糊匹配可能选错文件导致段落索引偏差。始终操作确定文件名的副本 |
| "复用之前的段落索引列表" | 不同 .docx 段落结构不同（空段落数量差异），每次翻译前必须重新导出段落列表 |
| "翻译文本里的引号用 ASCII 直引号就行" | 中文翻译文本中的引号必须用弯引号 `""`，ASCII `"` 会破坏 JSON 字符串和 Python 语法 |
| "print 中文到终端看看结果" | Windows Git Bash 用 GBK 编码，print 中文会触发 UnicodeEncodeError。始终写入 UTF-8 文件再读取 |
| "Write 工具写个含中文的 Python 脚本" | Windows Python 用系统编码（GBK）读取源码，中文变乱码破坏语法。中文数据用 base64 编码存储 |

## 核心挑战：Windows 环境下的编码陷阱

Windows Git Bash 终端使用 GBK 编码，中文文本在多个工具链之间传递时会乱码：
- **Write 工具**写含中文的 Python 源码 → Python 解析器用系统编码读取 → 语法错误
- **Python print 中文**到终端 → `UnicodeEncodeError: 'gbk' codec can't encode character`
- **中文路径**在 Bash → Python → 文件系统间传递可能被破坏

**总原则：中文文本只在 Python 运行时内存中存在；所有持久化到文件的中文必须经由 base64 编码。**

## 工作流程（按顺序执行）

**执行前先确定当前环境的 Python 调用方式**（参见文末"依赖说明"），以下示例统一用 `uv run --with python-docx python` 作为占位符，实际执行时替换为适合当前环境的命令。

### Step 1：准备 ASCII 文件名副本

```bash
cp "原文件.docx" input.docx
```

Bash 可以正确处理中文文件名，此步安全。后续所有操作使用 `input.docx`。

**重要**：不要用 `glob` 或 `os.walk` 模糊搜索 .docx 文件。目录中可能有多个 .docx 文件，模糊匹配可能选错文件导致段落索引偏差。始终操作确定文件名的副本。

### Step 2：导出段落列表

运行 `scripts/export_paragraphs.py`，将目标文档的段落索引和内容导出为 UTF-8 文本文件。

```bash
uv run --with python-docx python scripts/export_paragraphs.py input.docx paragraphs.txt
```

**输出文件 `paragraphs.txt`** 中每一行格式为：`[索引] [样式名] 文本内容`

段落索引是后续创建翻译映射的关键依据。不同 .docx 文件的段落结构不同（空段落数量差异），**绝不能假设索引，必须每次重新导出**。

### Step 3：翻译内容

阅读 `paragraphs.txt`，逐段翻译需要翻译的段落。翻译原则：

- **正文**（摘要、引言、方法、结果、讨论、结论）：完整翻译为中文，保持学术/专业语境
- **图表标题**：翻译为中文
- **参考文献条目**：保留原文（英文）不变
- **作者名、机构名**：机构名可翻译，作者名保留原文
- **专业术语**：使用领域标准译名，首次出现可附英文缩写（如 DCD（动态切割盘））
- **引号使用**：中文文本中使用弯引号 `"` (U+201C) 和 `"` (U+201D)，不要使用 ASCII 直引号 `"`

### Step 4：Base64 编码翻译文本

在 Bash 中用 `python -c` 将翻译文本 base64 编码后写入纯 ASCII 的 JSON 文件。

**原因**：Write 工具写的含中文 Python 源码会被 Python 用系统编码误读导致乱码；而 bash 中的 `python -c` 内联代码直接在内存中处理中文，只要不经过文件写入就不会出问题。

格式如下（在 bash 中执行）：

```bash
uv run --with python-docx python -c "
import json, base64
t = {
    '0': '翻译后的标题文本',
    '5': '翻译后的摘要文本',
    # ... 更多翻译
}
encoded = {k: base64.b64encode(v.encode('utf-8')).decode('ascii') for k, v in t.items()}
with open('translations_b64.json', 'w', encoding='utf-8') as f:
    json.dump(encoded, f, ensure_ascii=True)
print(f'Saved {len(encoded)} translations')
"
```

**关键细节**：
- 字典 key 是段落索引（字符串格式，与 `export_paragraphs.py` 输出一致）
- 翻译文本中的引号必须使用弯引号 `""`，如果误用 ASCII `"` 会破坏 Python 字符串语法
- `ensure_ascii=True` 确保 JSON 中只有 ASCII 字符
- 可以分多次执行（每次追加一部分翻译），也可以一次性写完

### Step 5：应用翻译到 docx

运行 `scripts/apply_translations.py`：

```bash
uv run --with python-docx python scripts/apply_translations.py input.docx translations_b64.json output.docx
```

脚本执行以下操作：
1. 读取 base64 JSON，解码为中文 UTF-8 文本
2. 遍历文档段落，对匹配索引的段落执行 `para.clear()` + `para.add_run(translated_text)`
3. 保存为新 docx 文件

**`para.clear()` + `add_run()` 方法会保留段落样式**（标题、正文、列表等），但会丢失字符级格式（如粗体、斜体）。对于以样式驱动的学术文档，这通常不影响最终效果。

### Step 6：验证输出

读取输出文件的段落内容，抽样检查翻译质量和索引匹配：

```bash
uv run --with python-docx python -c "
from docx import Document
doc = Document('output.docx')
with open('verify.txt', 'w', encoding='utf-8') as f:
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            f.write(f'[P{i}] {para.text[:200]}\n')
"
```

**不要直接在终端 print 中文**。这会触发 `UnicodeEncodeError`。始终写入 UTF-8 文件再读取验证。

### Step 7：清理

```bash
rm -f input.docx paragraphs.txt translations_b64.json verify.txt
```

保留最终输出文件 `output.docx`。

## 表格处理

`apply_translations.py` 仅处理段落文本。如需翻译表格内容，在 Step 5 之后用额外的 `python -c` 内联脚本处理：

```bash
uv run --with python-docx python -c "
from docx import Document
doc = Document('output.docx')
# Walk table cells: table.rows -> row.cells -> cell.paragraphs -> run.text
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    if run.text == 'English Header':
                        run.text = '中文表头'
doc.save('output.docx')
"
```

合并单元格的表头可能需要遍历 `cell.paragraphs` 并匹配完整文本而非单个 run。

## 故障排查：常见错误与解决方案

以下是本次工作流实战中实际遇到过的错误，按出现频率排序。

### `UnicodeEncodeError: 'gbk' codec can't encode character`

**原因**：Python print 中文到 Git Bash 终端，终端用 GBK 编码无法显示某些 Unicode 字符。

**解决**：永远不要 print 中文到终端。将所有输出写入 UTF-8 文件（`with open(..., 'w', encoding='utf-8')`），再用 Read 工具读取验证。

### `SyntaxError: invalid syntax` 在 Python 源码包含中文时

**原因**：Write 工具写的 .py 文件含中文字符串，Python 解释器在 Windows 上默认用系统编码（GBK）读取源码，导致中文被误读为乱码，进而破坏 Python 语法结构（如字符串未闭合）。

**解决**：Python 脚本源码保持纯 ASCII。中文数据通过 base64 编码存储在 JSON 中，由脚本运行时解码。参见 Step 4 的 base64 方案。

### `JSONDecodeError: Expecting ',' delimiter`

**原因**：翻译文本中包含 ASCII 直引号 `"`，与 JSON 字符串分隔符冲突，导致 JSON 解析失败。例如 `"被称为"岩石疲劳"的"` 中的 `"岩石疲劳"` 会提前结束 JSON 字符串。

**排查**：找到报错位置的字符（`error.pos`），检查是否为中文文本内的 ASCII 引号。

**解决**：中文文本中的引号必须使用 Unicode 弯引号 `"`（“）和 `"`（”），而非 ASCII `"`（`"`）。在 `python -c` 内联代码中直接输入弯引号即可。

### `PermissionError` 在读取中文路径文件时

**原因**：中文路径在 Bash → Python 的传递过程中被终端编码破坏，Python 收到的路径字符串已是乱码，无法找到文件。

**解决**：不要将中文路径硬编码在 Python 源码中。使用 `os.listdir()` 在运行时动态获取文件列表，或提前用 `cp "中文名.docx" ascii_name.docx` 复制为 ASCII 文件名。

### 翻译结果中英文混排 / 翻译到了错误的段落

**原因**：段落索引不匹配。可能原因：(a) 翻译映射使用了另一个文档的索引（如用 Erarslan 论文的索引去翻译另一篇论文）；(b) 导出段落列表后文档被修改。

**解决**：**每次翻译前必须对目标文件重新运行 Step 2 导出段落列表。** 不要复用旧的段落列表。不要用 glob 模糊匹配文件。始终操作确定文件名的副本（Step 1 的 `input.docx`）。

### `para.text` 赋值无效

**原因**：`python-docx` 中 `paragraph.text` 是只读属性，直接赋值不会报错但也不会生效。

**解决**：使用 `para.clear()` 清除所有 run，然后 `para.add_run(new_text)` 添加翻译文本。此方法保留段落样式。

## 依赖说明

本工作流依赖 `python-docx`。根据当前环境选择安装方式：

### 方案 1：uv（推荐，如果已安装）

```bash
uv run --with python-docx python script.py
```

### 方案 2：工作区虚拟环境（未安装 uv 时）

```bash
python -m venv .venv
.venv\Scripts\python -m pip install python-docx    # Windows
# 或
.venv/bin/python -m pip install python-docx         # macOS / Linux
.venv\Scripts\python script.py
```

### 判断用哪个

先检测 `uv` 是否可用：

```bash
which uv 2>/dev/null && echo "uv available" || echo "no uv"
```

- 有 `uv` → 方案 1（隔离执行，不污染全局环境）
- 无 `uv` → 方案 2（虚拟环境）

## 参考文件

| 文件 | 用途 |
| --- | --- |
| `scripts/export_paragraphs.py` | 导出 docx 段落索引和内容为 UTF-8 文本 |
| `scripts/apply_translations.py` | 读取 base64 翻译映射并应用到 docx 段落 |
