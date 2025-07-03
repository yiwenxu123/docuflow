<h1>DocuFlow HTML转换测试</h1>
<h2>功能介绍</h2>
<p>这是一个用于测试DocuFlow HTML输入格式支持的示例文档。</p>
<h2>主要特性</h2>
<ul>
<li><strong>多格式支持</strong>：支持PDF、Word、Excel、PowerPoint、Markdown、HTML等格式</li>
<li><strong>批量转换</strong>：可以同时处理多个文件</li>
<li><strong>智能输出</strong>：默认输出到源文件所在目录</li>
<li><strong>现代界面</strong>：基于PySide6的现代化GUI</li>
</ul>
<h2>代码示例</h2>

<p>以下是一个简单的Python代码示例：</p>
<pre><code>def convert_document(input_file, output_format):
&quot;&quot;&quot;转换文档格式&quot;&quot;&quot;
converter = DocumentConverter()
return converter.convert_file(input_file, output_format)</code></pre>

<h2>支持的转换</h2>
<p>HTML文档可以转换为以下格式：</p>
<ol>
<li>Markdown (.md)</li>
<li>纯文本 (.txt)</li>
<li>PDF文档 (.pdf)</li>
<li>Word文档 (.docx)</li>
</ol>
<h2>注意事项</h2>
<p>转换过程中会保持原有的文档结构和格式，但某些CSS样式可能无法完全保留。</p>
<p><em>测试文档 - DocuFlow v2.0.0</em></p>