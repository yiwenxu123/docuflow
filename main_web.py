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
from utils.file_utils import get_supported_formats, is_supported_file

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
                         output_formats=config.files.supported_output_formats)

@app.route('/upload', methods=['POST'])
def upload_files():
    """上传文件"""
    try:
        print(f"[DEBUG] 收到上传请求")
        if 'files' not in request.files:
            print(f"[DEBUG] 请求中没有files字段")
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        files = request.files.getlist('files')
        print(f"[DEBUG] 获取到 {len(files)} 个文件")
        if not files or all(f.filename == '' for f in files):
            print(f"[DEBUG] 没有有效文件")
            return jsonify({'success': False, 'error': '没有选择有效文件'})
        
        os.makedirs(upload_folder, exist_ok=True)
        
        uploaded_files = []
        for i, file in enumerate(files):
            print(f"[DEBUG] 处理文件 {i+1}: {file.filename}")
            if file and file.filename:
                # 保留原始文件名，只对路径进行安全处理
                original_filename = file.filename
                if is_supported_file(original_filename):
                    print(f"[DEBUG] 文件格式支持")
                    file_path = os.path.join(upload_folder, original_filename)
                    print(f"[DEBUG] 保存路径: {file_path}")
                    file.save(file_path)
                    print(f"[DEBUG] 文件已保存")
                    
                    # 检查文件大小
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                    print(f"[DEBUG] 文件大小: {file_size:.1f}MB")
                    if file_size > (config.conversion.max_file_size / (1024 * 1024)):  # 转换为MB
                        print(f"[DEBUG] 文件过大，删除")
                        os.remove(file_path)
                        continue
                    
                    uploaded_files.append({
                        'name': original_filename,  # 显示原始文件名
                        'path': file_path,
                        'size': f"{file_size:.1f}MB"
                    })
                    print(f"[DEBUG] 文件添加到上传列表")
                else:
                    print(f"[DEBUG] 文件格式不支持: {original_filename}")
        
        print(f"[DEBUG] 最终上传文件数: {len(uploaded_files)}")
        return jsonify({
            'success': True, 
            'files': uploaded_files,
            'message': f'成功上传 {len(uploaded_files)} 个文件'
        })
    
    except Exception as e:
        print(f"[ERROR] 上传异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/upload_folder', methods=['POST'])
def upload_folder_handler():
    """处理文件夹上传"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        files = request.files.getlist('files')
        if not files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        uploaded_files = []
        for file in files:
            if file and file.filename:
                # 处理文件夹结构，保持相对路径
                relative_path = file.filename
                if not relative_path:
                    continue

                # 安全地处理路径，防止路径遍历攻击
                safe_relative_path = os.path.normpath(relative_path)
                if safe_relative_path.startswith(('..', '/')):
                    continue

                filename = os.path.basename(safe_relative_path)
                if not is_supported_file(file.filename):
                    continue

                # 创建子目录结构，处理中文路径
                dir_path = os.path.dirname(safe_relative_path)
                if dir_path:
                    # 对中文目录名进行安全处理
                    safe_dir_parts = []
                    for part in dir_path.split(os.sep):
                        if part:
                            # 保留中文字符，但移除特殊字符
                            safe_part = re.sub(r'[<>:"/\\|?*]', '_', part)
                            safe_dir_parts.append(safe_part)
                    safe_dir_path = os.sep.join(safe_dir_parts)
                    full_dir = os.path.join(upload_folder, safe_dir_path)
                else:
                    full_dir = upload_folder
                
                os.makedirs(full_dir, exist_ok=True)
                
                # 对文件名也进行安全处理，保留中文字符
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
                file_path = os.path.join(full_dir, safe_filename)
                file.save(file_path)
                
                print(f"[DEBUG] 文件夹上传 - 原始路径: {relative_path}")
                print(f"[DEBUG] 文件夹上传 - 保存路径: {file_path}")
                print(f"[DEBUG] 文件夹上传 - 文件存在: {os.path.exists(file_path)}")

                # 检查文件大小
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                if file_size > (config.conversion.max_file_size / (1024 * 1024)):  # 转换为MB
                    os.remove(file_path)
                    continue
                
                uploaded_files.append({
                    'name': safe_filename,  # 使用安全处理后的文件名
                    'path': file_path,
                    'relative_path': relative_path,
                    'original_name': filename,  # 保留原始文件名用于显示
                    'size': f"{file_size:.1f}MB"
                })
        
        if not uploaded_files:
            return jsonify({'success': False, 'error': '文件夹中没有支持的文件格式'})
        
        return jsonify({
            'success': True,
            'files': uploaded_files,
            'message': f'成功上传文件夹中的 {len(uploaded_files)} 个文件'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/convert', methods=['POST'])
def convert_files():
    """转换文件"""
    try:
        data = request.get_json()
        # 支持两种参数名：files 和 file_paths
        file_paths = data.get('file_paths', data.get('files', []))
        output_format = data.get('output_format', '.md')
        keep_original_name = data.get('keep_original_name', True)
        use_async = data.get('use_async', False)
        max_workers = data.get('max_workers', 4)
        output_location = data.get('output_location', 'temp')  # 'temp' 或 'source'
        
        if not file_paths:
            return jsonify({'success': False, 'error': '没有要转换的文件'})
        
        # 根据用户选择确定输出目录
        if output_location == 'source':
            # 当选择源文件目录时，由于上传的文件在临时目录中，
            # 我们创建一个专门的输出目录供用户下载
            output_dir = tempfile.mkdtemp(prefix='docuflow_source_output_')
            print(f"[INFO] 用户选择源文件目录模式，创建输出目录: {output_dir}")
        else:
            # 创建临时输出目录
            output_dir = tempfile.mkdtemp(prefix='docuflow_temp_output_')
            print(f"[INFO] 用户选择临时目录模式，创建输出目录: {output_dir}")
        
        results = []
        
        if use_async:
            # 异步转换
            conversion_results = converter.async_batch_convert(
                file_paths, output_format, output_dir,
                keep_original_name=keep_original_name,
                max_workers=max_workers
            )
            
            for file_path, result in conversion_results.items():
                if result['status'] == 'success' and result.get('output_file'):
                    # 生成唯一的下载ID
                    import uuid
                    download_id = str(uuid.uuid4())
                    file_download_map[download_id] = {
                        'file_path': result['output_file'],
                        'timestamp': time.time()
                    }
                    
                    results.append({
                        'file': os.path.basename(file_path),
                        'success': True,
                        'output_file': result['output_file'],
                        'download_id': download_id,
                        'error': ''
                    })
                else:
                    results.append({
                        'file': os.path.basename(file_path),
                        'success': False,
                        'output_file': '',
                        'download_id': '',
                        'error': result.get('error', '')
                    })
        else:
            # 同步转换
            for file_path in file_paths:
                try:
                    # convert_file返回的是输出文件路径，不是字典
                    output_file_path = converter.convert_file(
                        file_path, output_format, output_dir, keep_original_name
                    )
                    
                    # 确保返回完整的文件路径信息
                    if output_file_path and os.path.exists(output_file_path):
                        # 生成唯一的下载ID
                        import uuid
                        download_id = str(uuid.uuid4())
                        file_download_map[download_id] = {
                            'file_path': output_file_path,
                            'timestamp': time.time()
                        }
                        
                        results.append({
                            'file': os.path.basename(file_path),
                            'success': True,
                            'output_file': output_file_path,
                            'download_id': download_id,
                            'error': ''
                        })
                        print(f"[SUCCESS] 转换成功: {file_path} -> {output_file_path} (下载ID: {download_id})")
                    else:
                        results.append({
                            'file': os.path.basename(file_path),
                            'success': False,
                            'output_file': '',
                            'error': '转换失败：输出文件未生成'
                        })
                        print(f"[ERROR] 转换失败: {file_path} - 输出文件未生成")
                except Exception as e:
                    print(f"[ERROR] 转换失败 {file_path}: {str(e)}")
                    import traceback
                    traceback.print_exc()
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

# 存储文件路径映射，用于安全下载（包含时间戳）
file_download_map = {}
import time

def cleanup_expired_downloads():
    """清理过期的下载链接（超过1小时）"""
    current_time = time.time()
    expired_ids = []
    
    for file_id, data in file_download_map.items():
        if isinstance(data, dict) and current_time - data.get('timestamp', 0) > 3600:  # 1小时
            expired_ids.append(file_id)
        elif isinstance(data, str):  # 兼容旧格式
            expired_ids.append(file_id)
    
    for file_id in expired_ids:
        del file_download_map[file_id]
    
    return len(expired_ids)

@app.route('/download/<file_id>')
def download_file(file_id):
    """下载转换后的文件"""
    try:
        # 定期清理过期下载链接
        cleanup_expired_downloads()
        
        # 从映射中获取真实文件路径
        if file_id not in file_download_map:
            return jsonify({'error': '文件不存在或已过期'}), 404
            
        download_data = file_download_map[file_id]
        
        # 兼容新旧格式
        if isinstance(download_data, dict):
            file_path = download_data['file_path']
        else:
            file_path = download_data  # 旧格式兼容
        
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            # 清理无效的映射
            del file_download_map[file_id]
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
        
        # 清理下载映射中的无效文件和过期链接
        expired_count = cleanup_expired_downloads()
        
        invalid_ids = []
        for file_id, download_data in file_download_map.items():
            if isinstance(download_data, dict):
                file_path = download_data['file_path']
            else:
                file_path = download_data  # 旧格式兼容
                
            if not os.path.exists(file_path):
                invalid_ids.append(file_id)
        
        for file_id in invalid_ids:
            del file_download_map[file_id]
        
        total_cleaned = cleaned_count + len(invalid_ids) + expired_count
        
        return jsonify({
            'success': True, 
            'message': f'清理了 {total_cleaned} 个临时文件和下载链接'
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
    
    # 从环境变量获取端口，默认为5003
    port = int(os.environ.get('PORT', 5003))
    
    print("\n" + "="*50)
    print("🚀 DocuFlow Web 版本启动中...")
    print("📁 支持的格式:", list(get_supported_formats().keys()))
    print(f"🌐 访问地址: http://localhost:{port}")
    print("="*50 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=port)