# MarkItDown 集成到 DocuFlow 项目 - 修正版方案

## 修订说明

本方案基于原方案进行以下关键修正：

1. **环境集成方式修正**：从跨环境调用改为直接集成到 DocuFlow venv
2. **前端集成增强**：添加 MarkItDown 特有参数设计
3. **输出处理标准化**：定义明确的处理流程
4. **API 接口完善**：详细的接口参数设计

---

## 1. 项目分析

### 1.1 DocuFlow 现有架构

- **核心功能**：多格式文档转换、图片过滤、增强过滤
- **技术栈**：Python + Flask + Pandoc
- **文件结构**：
  ```
  DocuFlow/
  ├── converter/
  │   └── document_converter.py    # 核心转换类
  ├── main_web.py                  # Web服务
  ├── templates/
  │   └── index.html               # 前端界面
  ├── requirements.txt             # 项目依赖
  └── config/                      # 配置目录
  ```

### 1.2 MarkItDown 功能矩阵

| 功能 | MarkItDown 支持 | DocuFlow 当前 | 集成优先级 |
|------|----------------|--------------|-----------|
| PowerPoint (PPTX) | ✅ | ❌ | **P0** |
| 图片 OCR | ✅ 高级 | ⚠️ 基础 | **P0** |
| Word (DOCX) | ✅ | ✅ | P1 |
| Excel (XLSX/XLS) | ✅ | ✅ | P1 |
| PDF | ✅ | ✅ | P1 |
| EML 邮件 | ✅ | ❌ | P2 |
| 图片描述 (LLM) | ✅ | ❌ | P2 |
| 音频转录 | ✅ | ❌ | P3 |
| YouTube 视频 | ✅ | ❌ | P3 |
| EPubs | ✅ | ❌ | P2 |

### 1.3 集成目标

1. **功能增强**：填补 PPTX、图片 OCR 等能力空白
2. **LLM 友好**：输出更适合 AI 处理的 Markdown 格式
3. **用户体验**：统一的 Web 界面，支持引擎选择
4. **向后兼容**：不破坏现有转换功能

---

## 2. 环境集成方案

### 2.1 环境策略

**最终方案**：将 markitdown 直接集成到 DocuFlow venv

```
原方案（不推荐）：
  ~/markitdown-env (独立环境)
  ~/文档转换/venv (DocuFlow 环境)
  → 需要跨环境调用，复杂且难以维护

修正方案（推荐）：
  ~/文档转换/venv (统一环境)
  → 直接导入 markitdown 库，简单可靠
```

### 2.2 依赖安装

```bash
# 进入 DocuFlow 虚拟环境
cd ~/trae/文档转换
source venv/bin/activate

# 安装 markitdown 及相关依赖
pip install 'markitdown[all]'

# 可选：安装特定格式支持（减少依赖体积）
pip install 'markitdown[pdf,docx,pptx,xlsx,image]'
```

### 2.3 依赖兼容性检查

```python
# 创建 converter/markitdown_requirements.py
"""
MarkItDown 依赖兼容性检查
"""

MARKITDOWN_CORE = "markitdown>=0.11.0"
MARKITDOWN_FORMATS = {
    "pdf": ["pypdf"],
    "docx": ["python-docx"],
    "pptx": ["python-pptx"],
    "xlsx": ["openpyxl", "pandas"],
    "image": ["pillow", "pytesseract"],
    "audio": ["openai-whisper"],
    "youtube": ["yt-dlp"],
}

def check_markitdown_available():
    """检查 markitdown 是否可用"""
    try:
        from markitdown import MarkItDown
        return True
    except ImportError:
        return False

def get_supported_formats():
    """获取 MarkItDown 支持的格式列表"""
    from markitdown import MarkItDown
    markitdown = MarkItDown()
    # MarkItDown 自动检测支持的文件格式
    return markitdown.supported_formats
```

---

## 3. 核心模块设计

### 3.1 MarkItDown 转换器模块

创建文件：`converter/markitdown_converter.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarkItDown 转换器模块
提供 MarkItDown 特有的转换能力
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

from exceptions import ConversionError

logger = logging.getLogger(__name__)


@dataclass
class MarkItDownOptions:
    """MarkItDown 转换选项"""
    enable_ocr: bool = False              # 启用图片 OCR
    llm_description: bool = False         # 使用 LLM 生成图片描述
    llm_client: Optional[str] = None      # LLM 客户端类型 (openai/azure)
    llm_model: Optional[str] = None        # LLM 模型名称
    language: str = "zh-CN"               # OCR 语言
    extract_images: bool = False           # 提取图片到本地
    image_output_dir: Optional[str] = None # 图片输出目录


class MarkItDownConverter:
    """MarkItDown 转换器类"""

    # MarkItDown 专门优化的格式（优先使用 MarkItDown）
    MARKITDOWN_NATIVE_FORMATS = {
        '.pptx': 'PowerPoint 演示文稿',
        '.ppt': 'PowerPoint 演示文稿',
        '.eml': '电子邮件',
        '.msg': 'Outlook 邮件',
        '.mp3': '音频文件',
        '.wav': '音频文件',
        '.m4a': '音频文件',
        '.epub': '电子书',
        '.odt': 'OpenDocument 文档',
        '.rtf': '富文本格式',
    }

    # MarkItDown 表现更好的格式（可选使用）
    MARKITDOWN_BETTER_FORMATS = {
        '.pdf': 'PDF 文档（优化版）',
        '.docx': 'Word 文档（优化版）',
        '.xlsx': 'Excel 表格（优化版）',
        '.png': 'PNG 图片',
        '.jpg': 'JPEG 图片',
        '.jpeg': 'JPEG 图片',
        '.gif': 'GIF 图片',
        '.webp': 'WebP 图片',
    }

    def __init__(self, options: Optional[MarkItDownOptions] = None):
        """
        初始化 MarkItDown 转换器

        Args:
            options: MarkItDown 选项，如果为 None 则使用默认选项
        """
        self.options = options or MarkItDownOptions()
        self._markitdown = None
        self._check_availability()

    def _check_availability(self) -> None:
        """检查 MarkItDown 是否可用"""
        try:
            from markitdown import MarkItDown
            self._markitdown = MarkItDown()
            logger.info("MarkItDown 初始化成功")
        except ImportError as e:
            logger.error(f"MarkItDown 未安装: {e}")
            raise ConversionError(
                "MarkItDown 未安装，请运行: pip install 'markitdown[all]'",
                error_code="MARKITDOWN_NOT_INSTALLED"
            )

    def is_markitdown_format(self, file_path: Union[str, Path]) -> bool:
        """
        检查文件是否适合使用 MarkItDown 转换

        Args:
            file_path: 文件路径

        Returns:
            bool: 是否适合使用 MarkItDown
        """
        ext = Path(file_path).suffix.lower()
        return ext in (self.MARKITDOWN_NATIVE_FORMATS | self.MARKITDOWN_BETTER_FORMATS)

    def get_format_description(self, file_path: Union[str, Path]) -> str:
        """
        获取文件格式的描述

        Args:
            file_path: 文件路径

        Returns:
            str: 格式描述
        """
        ext = Path(file_path).suffix.lower()
        return self.MARKITDOWN_NATIVE_FORMATS.get(
            ext, self.MARKITDOWN_BETTER_FORMATS.get(ext, '未知格式')
        )

    def convert(
        self,
        input_path: Union[str, Path],
        output_format: str = "markdown",
        options: Optional[MarkItDownOptions] = None
    ) -> str:
        """
        使用 MarkItDown 转换文件

        Args:
            input_path: 输入文件路径
            output_format: 输出格式（默认 markdown）
            options: 转换选项

        Returns:
            str: 转换后的内容

        Raises:
            ConversionError: 转换失败时抛出
        """
        options = options or self.options
        input_path = str(input_path)

        if not os.path.exists(input_path):
            raise ConversionError(
                f"文件不存在: {input_path}",
                error_code="FILE_NOT_FOUND"
            )

        try:
            logger.info(f"使用 MarkItDown 转换: {input_path}")

            # 构建 MarkItDown 实例
            from markitdown import MarkItDown

            # 配置 LLM 客户端（如果需要）
            if options.llm_description and options.llm_client:
                markitdown = MarkItDown(
                    llm_client=options.llm_client,
                    llm_model=options.llm_model
                )
            else:
                markitdown = MarkItDown()

            # 执行转换
            result = markitdown.convert(input_path)

            # 获取转换结果
            content = result.text_content

            logger.info(f"MarkItDown 转换成功，长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"MarkItDown 转换失败: {e}")
            raise ConversionError(
                f"MarkItDown 转换失败: {str(e)}",
                error_code="MARKITDOWN_CONVERSION_FAILED",
                details={"input_file": input_path, "error": str(e)}
            )

    def convert_to_file(
        self,
        input_path: Union[str, Path],
        output_path: Union[str, Path],
        options: Optional[MarkItDownOptions] = None
    ) -> str:
        """
        转换文件并保存到指定路径

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            options: 转换选项

        Returns:
            str: 输出文件路径

        Raises:
            ConversionError: 转换失败时抛出
        """
        content = self.convert(input_path, options=options)

        # 应用输出处理
        content = self._post_process(content)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"已保存到: {output_path}")
        return output_path

    def _post_process(self, content: str) -> str:
        """
        后处理 MarkItDown 输出

        Args:
            content: 原始转换内容

        Returns:
            str: 处理后的内容
        """
        # 基础清理
        content = content.strip()

        # 移除过多的空行
        import re
        content = re.sub(r'\n{3,}', '\n\n', content)

        return content

    def get_supported_formats() -> list:
        """获取 MarkItDown 支持的所有格式"""
        all_formats = list(MarkItDown.MARKITDOWN_NATIVE_FORMATS.keys())
        all_formats.extend(list(MarkItDown.MARKITDOWN_BETTER_FORMATS.keys()))
        return sorted(set(all_formats))

    @staticmethod
    def is_available() -> bool:
        """检查 MarkItDown 是否可用"""
        try:
            from markitdown import MarkItDown
            return True
        except ImportError:
            return False
```

### 3.2 集成到 DocumentConverter

修改 `converter/document_converter.py`：

```python
# 在 DocumentConverter 类中添加以下方法

def __init__(self, config_obj=None):
    # ... 现有初始化代码 ...

    # 初始化 MarkItDown 转换器（延迟加载）
    self._markitdown_converter = None

    # 转换引擎选择
    self.use_markitdown_by_default = False

@property
def markitdown_converter(self):
    """延迟加载 MarkItDown转换器"""
    if self._markitdown_converter is None:
        if MarkItDownConverter.is_available():
            self._markitdown_converter = MarkItDownConverter()
        else:
            logger.warning("MarkItDown 未安装，部分功能不可用")
    return self._markitdown_converter

def _should_use_markitdown(self, file_path: str, use_markitdown: bool = False) -> bool:
    """
    判断是否应使用 MarkItDown 转换

    Args:
        file_path: 文件路径
        use_markitdown: 用户显式指定的偏好

    Returns:
        bool: 是否使用 MarkItDown
    """
    # 如果用户显式指定，优先使用
    if use_markitdown:
        return MarkItDownConverter.is_available()

    # 检查文件格式
    ext = Path(file_path).suffix.lower()

    # MarkItDown 原生支持的格式，优先使用
    if ext in MarkItDownConverter.MARKITDOWN_NATIVE_FORMATS:
        return MarkItDownConverter.is_available()

    # 用户偏好设置
    if self.use_markitdown_by_default:
        return MarkItDownConverter.is_available()

    return False

def convert_with_markitdown(
    self,
    file_path: str,
    output_format: str = "md",
    options: Optional[MarkItDownOptions] = None
) -> str:
    """
    使用 MarkItDown 转换文件

    Args:
        file_path: 输入文件路径
        output_format: 输出格式（默认 md）
        options: MarkItDown 选项

    Returns:
        str: 输出文件路径

    Raises:
        ConversionError: 转换失败时抛出
    """
    if not self.markitdown_converter:
        raise ConversionError(
            "MarkItDown 不可用",
            error_code="MARKITDOWN_UNAVAILABLE"
        )

    # 确定输出路径
    input_path = Path(file_path)
    output_path = input_path.with_suffix(f".{output_format}")

    # 执行转换
    self.markitdown_converter.convert_to_file(
        input_path=str(input_path),
        output_path=str(output_path),
        options=options
    )

    # 应用 DocuFlow 的增强过滤（可选）
    if self.clean_content:
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = self._clean_content(
            content,
            content_type='markdown',
            filter_images=self.filter_images,
            clean_content=True
        )
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return str(output_path)
```

### 3.3 输出处理标准化

创建 `converter/output_processor.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
转换输出处理器
统一处理不同转换引擎的输出
"""

import re
from typing import Optional
from dataclasses import dataclass


@dataclass
class OutputProcessorOptions:
    """输出处理选项"""
    remove_excess_whitespace: bool = True
    normalize_headings: bool = True
    fix_broken_words: bool = True
    remove_page_markers: bool = True
    standardize_tables: bool = True
    filter_images: bool = False
    target_audience: str = "llm"  # "llm" | "human" | "archive"


class OutputProcessor:
    """转换输出处理器"""

    # MarkItDown 特有的标记（需要清理）
    MARKITDOWN_MARKERS = [
        r'\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)',  # 图片嵌套链接
        r':::\{[^}]*\}',                         # MarkItDown 元数据
        r'<!--.*?-->',                           # HTML 注释
    ]

    # PDF 常见的问题字符
    PDF_FIXES = {
        'PDFnMarkdow': 'PDF转Markdown',
        'Markdow': 'Markdown',
        'docume t': 'document',
        'seco d': 'second',
    }

    def __init__(self, options: Optional[OutputProcessorOptions] = None):
        self.options = options or OutputProcessorOptions()

    def process(self, content: str, source_engine: str = "auto") -> str:
        """
        处理转换输出

        Args:
            content: 原始转换内容
            source_engine: 来源引擎 ("pandoc" | "markitdown" | "auto")

        Returns:
            str: 处理后的内容
        """
        # 应用通用清理
        content = self._apply_general_cleanup(content)

        # 根据来源引擎应用特定处理
        if source_engine in ("markitdown", "auto"):
            content = self._process_markitdown_output(content)

        if source_engine in ("pandoc", "auto"):
            content = self._process_pandoc_output(content)

        # 应用格式标准化
        content = self._standardize_format(content)

        return content

    def _apply_general_cleanup(self, content: str) -> str:
        """通用清理"""
        if not self.options.remove_excess_whitespace:
            return content

        # 移除过多的空行
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 清理行首行尾空白
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(lines)

        # 移除页码标记
        if self.options.remove_page_markers:
            content = re.sub(r'^第\s*\d+\s*页\s*$', '', content, flags=re.MULTILINE)
            content = re.sub(r'^\d+\s*$', '', content)  # 纯数字行

        return content

    def _process_markitdown_output(self, content: str) -> str:
        """处理 MarkItDown 特有输出"""
        # 清理 MarkItDown 特有标记
        for pattern in self.MARKITDOWN_MARKERS:
            content = re.sub(pattern, '', content)

        # 修复 MarkItDown 可能产生的格式问题
        content = re.sub(r'\[([^\]]+)\]\(\)\s*', r'\1 ', content)  # 空链接

        return content

    def _process_pandoc_output(self, content: str) -> str:
        """处理 Pandoc 特有输出"""
        # 清理 HTML 标签（保留 Markdown 格式）
        # ... 现有清理逻辑 ...

        return content

    def _standardize_format(self, content: str) -> str:
        """格式标准化"""
        if not self.options.normalize_headings:
            return content

        # 确保标题格式一致
        content = re.sub(r'^#+\s+', lambda m: m.group(0), content, flags=re.MULTILINE)

        # 标准化链接格式
        content = re.sub(r'\[([^\]]+)\]\s*\(\s*\)', r'**\1**', content)

        return content

    def process_for_llm(self, content: str) -> str:
        """
        为 LLM 处理优化输出

        Args:
            content: 原始内容

        Returns:
            str: LLM 优化后的内容
        """
        options = OutputProcessorOptions(
            remove_excess_whitespace=True,
            normalize_headings=True,
            fix_broken_words=True,
            remove_page_markers=True,
            standardize_tables=True,
            filter_images=False,
            target_audience="llm"
        )
        self.options = options

        return self.process(content, source_engine="auto")
```

---

## 4. API 接口设计

### 4.1 修改现有接口

修改 `main_web.py` 中的 `/convert` 接口：

```python
@app.route('/convert', methods=['POST'])
def convert_files():
    """转换文件"""
    try:
        data = request.get_json()
        file_paths = data.get('file_paths', data.get('files', []))
        output_format = data.get('output_format', 'md')

        # ===== 新增参数 =====
        use_markitdown = data.get('use_markitdown', False)  # 是否使用 MarkItDown
        enable_ocr = data.get('enable_ocr', False)          # 启用 OCR
        llm_description = data.get('llm_description', False) # 使用 LLM 描述图片
        output_dir = data.get('output_dir', None)

        if not file_paths:
            return jsonify({
                'success': False,
                'error': '没有指定要转换的文件'
            })

        converted_files = []
        errors = []

        for file_path in file_paths:
            try:
                # 根据参数选择转换引擎
                if use_markitdown and converter._should_use_markitdown(file_path, use_markitdown=True):
                    # 使用 MarkItDown 转换
                    markitdown_options = MarkItDownOptions(
                        enable_ocr=enable_ocr,
                        llm_description=llm_description
                    )
                    result_path = converter.convert_with_markitdown(
                        file_path,
                        output_format=output_format,
                        options=markitdown_options
                    )
                else:
                    # 使用原有 Pandoc 转换
                    result_path = converter.convert_file(
                        file_path,
                        output_format=output_format,
                        output_dir=output_dir
                    )

                converted_files.append({
                    'original': file_path,
                    'converted': result_path,
                    'engine': 'markitdown' if use_markitdown else 'pandoc'
                })

            except Exception as e:
                errors.append({
                    'file': file_path,
                    'error': str(e)
                })

        return jsonify({
            'success': True,
            'converted': converted_files,
            'errors': errors,
            'summary': f"成功转换 {len(converted_files)} 个文件，{len(errors)} 个失败"
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
```

### 4.2 新增接口

```python
@app.route('/markitdown/status', methods=['GET'])
def markitdown_status():
    """获取 MarkItDown 状态"""
    available = MarkItDownConverter.is_available()
    formats = []

    if available:
        formats = list(
            MarkItDownConverter.MARKITDOWN_NATIVE_FORMATS.keys()
        ) + list(
            MarkItDownConverter.MARKITDOWN_BETTER_FORMATS.keys()
        )

    return jsonify({
        'available': available,
        'supported_formats': formats,
        'message': 'MarkItDown 可用' if available else 'MarkItDown 未安装'
    })


@app.route('/markitdown/formats', methods=['GET'])
def markitdown_formats():
    """获取 MarkItDown 支持的格式详情"""
    if not MarkItDownConverter.is_available():
        return jsonify({
            'success': False,
            'error': 'MarkItDown 未安装'
        })

    native_formats = [
        {'ext': ext, 'name': name, 'type': 'native'}
        for ext, name in MarkItDownConverter.MARKITDOWN_NATIVE_FORMATS.items()
    ]

    better_formats = [
        {'ext': ext, 'name': name, 'type': 'better'}
        for ext, name in MarkItDownConverter.MARKITDOWN_BETTER_FORMATS.items()
    ]

    return jsonify({
        'success': True,
        'native_formats': native_formats,  # MarkItDown 原生支持
        'better_formats': better_formats    # MarkItDown 表现更好的格式
    })
```

---

## 5. 前端界面设计

### 5.1 添加 MarkItDown 选项

在 `templates/index.html` 中添加 MarkItDown 相关 UI：

```html
<!-- 添加到转换选项区域 -->

<div class="converter-options" id="converterOptions">
    <h3>转换引擎选择</h3>

    <div class="engine-selector">
        <label class="radio-option">
            <input type="radio" name="converter_engine" value="auto" checked>
            <span class="radio-label">
                <strong>自动选择</strong>
                <small>根据文件格式自动选择最佳引擎</small>
            </span>
        </label>

        <label class="radio-option">
            <input type="radio" name="converter_engine" value="pandoc">
            <span class="radio-label">
                <strong>Pandoc 引擎</strong>
                <small>稳定可靠，适合基础转换</small>
            </span>
        </label>

        <label class="radio-option" id="markitdownOption">
            <input type="radio" name="converter_engine" value="markitdown">
            <span class="radio-label">
                <strong>MarkItDown 引擎</strong>
                <small>支持更多格式，LLM 友好</small>
            </span>
        </label>
    </div>

    <!-- MarkItDown 特有选项（仅在选择 MarkItDown 时显示） -->
    <div class="markitdown-options" id="markitdownOptions" style="display: none;">
        <h4>MarkItDown 高级选项</h4>

        <label class="checkbox-option">
            <input type="checkbox" id="enableOcr">
            <span>启用图片 OCR</span>
            <small>从图片中提取文字</small>
        </label>

        <label class="checkbox-option">
<input type="checkbox" id="llmDescription">
            <span>使用 LLM 描述图片</span>
            <small>生成图片内容描述（需要配置 LLM API）</small>
        </label>

        <div class="llm-config" id="llmConfig" style="display: none;">
            <select id="llmClient">
                <option value="">选择 LLM 客户端</option>
                <option value="openai">OpenAI</option>
                <option value="azure">Azure OpenAI</option>
            </select>
            <input type="text" id="llmModel" placeholder="模型名称（如 gpt-4o）">
        </div>
    </div>
</div>

<script>
// 引擎选择切换
document.querySelectorAll('input[name="converter_engine"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const markitdownOptions = document.getElementById('markitdownOptions');
        if (this.value === 'markitdown') {
            markitdownOptions.style.display = 'block';
        } else {
            markitdownOptions.style.display = 'none';
        }
    });
});

// LLM 选项切换
document.getElementById('llmDescription')?.addEventListener('change', function() {
    const llmConfig = document.getElementById('llmConfig');
    llmConfig.style.display = this.checked ? 'flex' : 'none';
});

// 修改转换请求
async function convertFiles() {
    const formData = {
        file_paths: selectedFiles.map(f => f.path),
        output_format: document.getElementById('outputFormat').value,
        // 新增参数
        use_markitdown: document.querySelector('input[name="converter_engine"]:checked').value === 'markitdown',
        enable_ocr: document.getElementById('enableOcr')?.checked || false,
        llm_description: document.getElementById('llmDescription')?.checked || false
    };

    const response = await fetch('/convert', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(formData)
    });

    return await response.json();
}
</script>
```

### 5.2 更新格式支持列表

```javascript
// 在前端添加 MarkItDown 特有格式
const markitdownFormats = {
    native: {
        '.pptx': 'PowerPoint 演示文稿',
        '.ppt': 'PowerPoint 演示文稿',
        '.eml': '电子邮件',
        '.epub': '电子书'
    },
    better: {
        '.pdf': 'PDF 文档（优化）',
        '.docx': 'Word 文档（优化）',
        '.xlsx': 'Excel 表格（优化）'
    }
};

// 更新 UI 显示
function updateFormatList() {
    const formatList = document.getElementById('supportedFormats');

    // 原有格式
    let html = '<h4>基础支持</h4>';
    html += '<ul class="format-list">';
    html += '<li><strong>PDF</strong> - PDF 文档</li>';
    html += '<li><strong>Word</strong> - DOCX 文档</li>';
    html += '<li><strong>Excel</strong> - XLSX/XLS 表格</li>';
    html += '<li><strong>HTML</strong> - 网页文件</li>';
    html += '</ul>';

    // MarkItDown 增强
    html += '<h4>MarkItDown 增强</h4>';
    html += '<ul class="format-list highlight">';
    html += '<li><strong>PowerPoint</strong> - PPTX/PPT 演示文稿 ⭐NEW</li>';
    html += '<li><strong>Email</strong> - EML 邮件文件 ⭐NEW</li>';
    html += '<li><strong>Ebook</strong> - EPUB 电子书 ⭐NEW</li>';
    html += '<li><strong>图片 OCR</strong> - 从图片提取文字 ⭐NEW</li>';
    html += '</ul>';

    formatList.innerHTML = html;
}
```

---

## 6. 实施计划

### Phase 1: 环境准备（30分钟）

| 任务 | 预计时间 | 状态 |
|------|---------|------|
| 在 DocuFlow venv 安装 markitdown | 10分钟 | ⬜ |
| 测试 markitdown 基本功能 | 10分钟 | ⬜ |
| 验证依赖兼容性 | 10分钟 | ⬜ |

```bash
cd ~/trae/文档转换
source venv/bin/activate
pip install 'markitdown[pdf,docx,pptx,xlsx,image]'
python -c "from markitdown import MarkItDown; print('OK')"
```

### Phase 2: 核心模块开发（2小时）

| 任务 | 预计时间 | 状态 |
|------|---------|------|
| 创建 markitdown_converter.py | 30分钟 | ⬜ |
| 创建 output_processor.py | 30分钟 | ⬜ |
| 集成到 DocumentConverter | 30分钟 | ⬜ |
| 添加引擎选择逻辑 | 30分钟 | ⬜ |

### Phase 3: Web 接口和前端（1.5小时）

| 任务 | 预计时间 | 状态 |
|------|---------|------|
| 修改 /convert 接口 | 20分钟 | ⬜ |
| 添加 MarkItDown 状态接口 | 10分钟 | ⬜ |
| 更新前端 UI | 40分钟 | ⬜ |
| 添加格式列表更新 | 20分钟 | ⬜ |

### Phase 4: 测试验证（1小时）

| 任务 | 预计时间 | 状态 |
|------|---------|------|
| PPTX 转换测试 | 15分钟 | ⬜ |
| 图片 OCR 测试 | 15分钟 | ⬜ |
| 性能对比测试 | 15分钟 | ⬜ |
| 回归测试 | 15分钟 | ⬜ |

### Phase 5: 文档和部署（30分钟）

| 任务 | 预计时间 | 状态 |
|------|---------|------|
| 更新 README | 10分钟 | ⬜ |
| 更新 requirements.txt | 5分钟 | ⬜ |
| 部署测试 | 15分钟 | ⬜ |

---

## 7. 风险评估和缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 依赖冲突 | 低 | 中 | 使用可选依赖，分步安装测试 |
| 输出格式不一致 | 中 | 高 | 统一使用 OutputProcessor 处理 |
| MarkItDown 转换失败 | 中 | 低 | 实现回退到 Pandoc 引擎 |
| LLM API 费用 | 低 | 中 | 默认关闭，需用户显式启用 |

---

## 8. 验收标准

### 功能验收

- [ ] 可以成功转换 PPTX 文件
- [ ] 可以启用图片 OCR 功能
- [ ] 可以选择不同的转换引擎
- [ ] 输出格式与现有功能一致

### 性能验收

- [ ] MarkItDown 转换速度不比 Pandoc 慢
- [ ] UI 响应时间 < 1秒
- [ ] 大文件（>50MB）转换不超时

### 兼容性验收

- [ ] 现有 Pandoc 转换功能不受影响
- [ ] 所有支持的格式仍可正常转换
- [ ] Web 界面所有功能正常

---

## 9. 后续优化方向

1. **智能引擎选择**：根据文件内容自动选择最佳引擎
2. **批量转换优化**：对多个文件并行使用不同引擎
3. **缓存机制**：对相同文件使用缓存，避免重复转换
4. **LLM 增强**：集成更多 LLM 能力，如自动摘要、问答

---

## 附录

### A. MarkItDown 常用命令

```bash
# CLI 用法
markitdown input.pptx > output.md
markitdown --enable-ocr input.pdf > output.md
markitdown --llm-description input.pdf --llm-client openai --llm-model gpt-4o > output.md

# Python API 用法
from markitdown import MarkItDown
markitdown = MarkItDown()
result = markitdown.convert("input.pdf")
print(result.text_content)
```

### B. 相关资源

- MarkItDown GitHub: https://github.com/microsoft/markitdown
- MarkItDown 文档: https://microsoft.github.io/markitdown/
- 安装指南: `pip install 'markitdown[all]'`

---

*文档版本: 1.1*
*最后更新: 2026-04-08*
