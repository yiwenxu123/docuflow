#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocuFlow Web 版本 - 文档转换器
使用 Flask 提供 Web 界面，避免 tkinter 依赖问题
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import tempfile
import shutil
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from converter.document_converter import DocumentConverter
from exceptions import ConversionError, ValidationError
from utils import get_supported_formats, is_supported_file

app = Flask(__name__)
app.secret_key = 'docuflow_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# 全局变量
config = Config()
converter = DocumentConverter(config)
upload_folder = tempfile.mkdtemp(prefix='docuflow_uploads_')
os.makedirs(upload_folder, exist_ok=True)

@app.route('/')
def index():
    """主页"""
    supported_formats = get_supported_formats()
    # 将扩展名格式化为更友好的分类
    formatted_formats = {
        'Word文档': [ext for ext in supported_formats if ext in ['.docx', '.doc']],
        'PDF文档': [ext for ext in supported_formats if ext == '.pdf'],
        'Markdown': [ext for ext in supported_formats if ext == '.md'],
        'HTML': [ext for ext in supported_formats if ext in ['.html', '.htm']],
        '电子书': [ext for ext in supported_formats if ext == '.epub']
    }
    stats = converter.get_stats()
    return render_template('index.html', 
                         supported_formats=formatted_formats,
                         stats=stats,
                         output_formats=config.SUPPORTED_OUTPUT_FORMATS)

@app.route('/upload', methods=['POST'])
def upload_files():
    """上传文件"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'success': False, 'error': '没有选择有效文件'})
        
        uploaded_files = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                if is_supported_file(filename):
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    
                    # 检查文件大小
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    if file_size > config.MAX_FILE_SIZE_MB:
                        os.remove(file_path)
                        continue
                    
                    uploaded_files.append({
                        'name': filename,
                        'path': file_path,
                        'size': f"{file_size:.1f}MB"
                    })
        
        return jsonify({
            'success': True, 
            'files': uploaded_files,
            'message': f'成功上传 {len(uploaded_files)} 个文件'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/convert', methods=['POST'])
def convert_files():
    """转换文件"""
    try:
        data = request.get_json()
        file_paths = data.get('files', [])
        output_format = data.get('output_format', '.md')
        keep_original_name = data.get('keep_original_name', True)
        use_async = data.get('use_async', False)
        max_workers = data.get('max_workers', 4)
        
        if not file_paths:
            return jsonify({'success': False, 'error': '没有要转换的文件'})
        
        # 创建输出目录
        output_dir = tempfile.mkdtemp(prefix='docuflow_output_')
        
        results = []
        
        if use_async:
            # 异步转换
            conversion_results = converter.async_batch_convert(
                file_paths, output_format, output_dir,
                keep_original_name=keep_original_name,
                max_workers=max_workers
            )
            
            for file_path, result in conversion_results.items():
                results.append({
                    'file': os.path.basename(file_path),
                    'success': result['status'] == 'success',
                    'output_file': result.get('output_file', ''),
                    'error': result.get('error', '')
                })
        else:
            # 同步转换
            for file_path in file_paths:
                try:
                    result = converter.convert_file(
                        file_path, output_format, output_dir, keep_original_name
                    )
                    results.append({
                        'file': os.path.basename(file_path),
                        'success': result['success'],
                        'output_file': result.get('output_file', ''),
                        'error': result.get('error', '')
                    })
                except Exception as e:
                    results.append({
                        'file': os.path.basename(file_path),
                        'success': False,
                        'output_file': '',
                        'error': str(e)
                    })
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': total_count,
                'success': success_count,
                'failed': total_count - success_count,
                'success_rate': (success_count / total_count * 100) if total_count > 0 else 0
            },
            'output_dir': output_dir
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<path:file_path>')
def download_file(file_path):
    """下载转换后的文件"""
    try:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'error': '文件不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def get_stats():
    """获取统计信息"""
    try:
        stats = converter.get_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/cleanup', methods=['POST'])
def cleanup_temp_files():
    """清理临时文件"""
    try:
        cleaned_count = converter.cleanup_temp_files()
        
        # 清理上传文件夹
        if os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
            os.makedirs(upload_folder, exist_ok=True)
        
        return jsonify({
            'success': True, 
            'message': f'清理了 {cleaned_count} 个临时文件'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    """重置统计信息"""
    try:
        converter.reset_stats()
        return jsonify({'success': True, 'message': '统计信息已重置'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': '文件太大，请选择小于100MB的文件'}), 413

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'未处理的异常: {e}')
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

def cleanup_on_exit():
    """程序退出时清理资源"""
    try:
        converter.cleanup_temp_files()
        if os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
    except:
        pass

if __name__ == '__main__':
    import atexit
    atexit.register(cleanup_on_exit)
    
    print("\n" + "="*50)
    print("🚀 DocuFlow Web 版本启动中...")
    print("📁 支持的格式:", list(get_supported_formats().keys()))
    print("🌐 访问地址: http://localhost:8080")
    print("="*50 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=8080)