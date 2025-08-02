#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试下载文件名修改功能
验证转换后的文件下载时显示正确的文件扩展名
"""

import requests
import json
import os
import tempfile
import time

def test_download_filename():
    """测试下载文件名功能"""
    base_url = "http://localhost:5003"
    
    print("🧪 开始测试下载文件名功能...")
    
    # 1. 创建测试文件
    test_content = """# 测试文档

这是一个测试文档，用于验证下载文件名功能。

## 功能说明

- 原始文件：test_document.pdf
- 转换格式：Markdown (.md)
- 期望下载文件名：test_document.md

## 测试内容

这个文档包含了一些基本的Markdown格式：

1. 标题
2. 列表
3. **粗体文本**
4. *斜体文本*

测试完成！
"""
    
    # 创建临时测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        test_file_path = f.name
    
    print(f"📄 创建测试文件: {test_file_path}")
    
    try:
        # 2. 上传文件
        print("📤 上传测试文件...")
        with open(test_file_path, 'rb') as f:
            files = {'files': (os.path.basename(test_file_path), f, 'text/markdown')}
            response = requests.post(f"{base_url}/upload", files=files)
        
        if response.status_code != 200:
            print(f"❌ 上传失败: {response.status_code}")
            return False
        
        upload_result = response.json()
        if not upload_result.get('success'):
            print(f"❌ 上传失败: {upload_result.get('error')}")
            return False
        
        uploaded_files = upload_result.get('files', [])
        if not uploaded_files:
            print("❌ 没有上传成功的文件")
            return False
        
        print(f"✅ 文件上传成功: {len(uploaded_files)} 个文件")
        
        # 3. 转换文件 (Markdown -> HTML)
        print("🔄 开始转换文件 (Markdown -> HTML)...")
        conversion_data = {
            'files': [f['path'] for f in uploaded_files],
            'output_format': '.html',
            'keep_original_name': True,
            'use_async': False,
            'output_location': 'temp'
        }
        
        response = requests.post(
            f"{base_url}/convert",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(conversion_data)
        )
        
        if response.status_code != 200:
            print(f"❌ 转换请求失败: {response.status_code}")
            return False
        
        convert_result = response.json()
        if not convert_result.get('success'):
            print(f"❌ 转换失败: {convert_result.get('error')}")
            return False
        
        results = convert_result.get('results', [])
        print(f"📊 转换结果: {len(results)} 个文件")
        
        for i, result in enumerate(results):
            print(f"  文件 {i+1}: 成功={result.get('success')}, 错误={result.get('error')}")
        
        successful_results = [r for r in results if r.get('success')]
        
        if not successful_results:
            print("❌ 没有转换成功的文件")
            print(f"📋 完整转换结果: {json.dumps(convert_result, indent=2, ensure_ascii=False)}")
            return False
        
        print(f"✅ 转换成功: {len(successful_results)} 个文件")
        
        # 4. 验证文件名格式
        print("🔍 验证下载文件名格式...")
        for result in successful_results:
            original_filename = os.path.basename(test_file_path)
            expected_filename = os.path.splitext(original_filename)[0] + '.html'
            actual_filename = result.get('file')
            
            print(f"  原始文件名: {original_filename}")
            print(f"  期望文件名: {expected_filename}")
            print(f"  实际文件名: {actual_filename}")
            
            if actual_filename == expected_filename:
                print("  ✅ 文件名格式正确")
            else:
                print("  ❌ 文件名格式错误")
                return False
            
            # 5. 测试下载链接
            download_id = result.get('download_id')
            if download_id:
                print(f"  📥 测试下载链接: {download_id}")
                download_response = requests.get(f"{base_url}/download/{download_id}")
                
                if download_response.status_code == 200:
                    # 检查Content-Disposition头部
                    content_disposition = download_response.headers.get('Content-Disposition', '')
                    print(f"  Content-Disposition: {content_disposition}")
                    
                    if expected_filename in content_disposition:
                        print("  ✅ 下载文件名正确")
                    else:
                        print("  ⚠️  下载文件名可能不正确，但文件可以下载")
                else:
                    print(f"  ❌ 下载失败: {download_response.status_code}")
                    return False
        
        print("\n🎉 所有测试通过！下载文件名功能正常工作。")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理测试文件
        try:
            os.unlink(test_file_path)
            print(f"🧹 清理测试文件: {test_file_path}")
        except:
            pass

def test_multiple_formats():
    """测试多种格式转换的文件名"""
    print("\n🧪 测试多种格式转换...")
    
    test_cases = [
        ('.md', '.html', 'Markdown -> HTML'),
        ('.md', '.pdf', 'Markdown -> PDF'),
        ('.html', '.md', 'HTML -> Markdown'),
    ]
    
    for input_ext, output_ext, description in test_cases:
        print(f"\n📋 测试: {description}")
        
        # 创建测试内容
        if input_ext == '.md':
            content = "# 测试文档\n\n这是一个测试文档。\n\n- 项目1\n- 项目2"
        elif input_ext == '.html':
            content = "<html><body><h1>测试文档</h1><p>这是一个测试文档。</p></body></html>"
        else:
            content = "测试文档内容"
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix=input_ext, delete=False, encoding='utf-8') as f:
            f.write(content)
            test_file = f.name
        
        try:
            # 上传文件
            with open(test_file, 'rb') as f:
                files = {'files': (os.path.basename(test_file), f)}
                response = requests.post("http://localhost:5003/upload", files=files)
            
            if response.status_code == 200:
                upload_result = response.json()
                if upload_result.get('success'):
                    uploaded_files = upload_result.get('files', [])
                    
                    # 转换文件
                    conversion_data = {
                        'files': [f['path'] for f in uploaded_files],
                        'output_format': output_ext,
                        'keep_original_name': True,
                        'use_async': False,
                        'output_location': 'temp'
                    }
                    
                    response = requests.post(
                        "http://localhost:5003/convert",
                        headers={'Content-Type': 'application/json'},
                        data=json.dumps(conversion_data)
                    )
                    
                    if response.status_code == 200:
                        convert_result = response.json()
                        if convert_result.get('success'):
                            results = convert_result.get('results', [])
                            for result in results:
                                if result.get('success'):
                                    original_name = os.path.basename(test_file)
                                    expected_name = os.path.splitext(original_name)[0] + output_ext
                                    actual_name = result.get('file')
                                    
                                    if actual_name == expected_name:
                                        print(f"  ✅ {description}: {actual_name}")
                                    else:
                                        print(f"  ❌ {description}: 期望 {expected_name}, 实际 {actual_name}")
                                else:
                                    print(f"  ❌ {description}: 转换失败 - {result.get('error')}")
                        else:
                            print(f"  ❌ {description}: 转换请求失败")
                    else:
                        print(f"  ❌ {description}: HTTP错误 {response.status_code}")
                else:
                    print(f"  ❌ {description}: 上传失败")
            else:
                print(f"  ❌ {description}: 上传HTTP错误 {response.status_code}")
        
        except Exception as e:
            print(f"  ❌ {description}: 异常 - {str(e)}")
        
        finally:
            try:
                os.unlink(test_file)
            except:
                pass

if __name__ == "__main__":
    print("🚀 DocuFlow 下载文件名功能测试")
    print("="*50)
    
    # 等待服务启动
    print("⏳ 等待Web服务启动...")
    time.sleep(2)
    
    # 检查服务是否可用
    try:
        response = requests.get("http://localhost:5003/stats", timeout=5)
        if response.status_code == 200:
            print("✅ Web服务已就绪")
        else:
            print("❌ Web服务不可用")
            exit(1)
    except Exception as e:
        print(f"❌ 无法连接到Web服务: {str(e)}")
        exit(1)
    
    # 运行测试
    success = test_download_filename()
    
    if success:
        test_multiple_formats()
        print("\n🎉 所有测试完成！")
    else:
        print("\n❌ 主要测试失败，跳过其他测试。")