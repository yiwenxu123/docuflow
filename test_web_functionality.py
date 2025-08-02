#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web版本转换功能测试脚本
模拟Web界面的文件上传和转换过程
"""

import requests
import os
import json
import time

def test_web_conversion():
    """测试Web版本的文件转换功能"""
    base_url = "http://localhost:5003"
    test_file = "/Users/yiwenxu123/Documents/tare/文档转换/test_web_conversion.md"
    
    print("🧪 开始测试Web版本转换功能...")
    print(f"📁 测试文件: {test_file}")
    print(f"🌐 服务器地址: {base_url}")
    print("-" * 50)
    
    try:
        # 1. 测试服务器连接
        print("1️⃣ 测试服务器连接...")
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print(f"❌ 服务器连接失败: {response.status_code}")
            return False
        
        # 2. 测试文件上传
        print("\n2️⃣ 测试文件上传...")
        if not os.path.exists(test_file):
            print(f"❌ 测试文件不存在: {test_file}")
            return False
            
        with open(test_file, 'rb') as f:
            files = {'files': (os.path.basename(test_file), f, 'text/markdown')}
            upload_response = requests.post(f"{base_url}/upload", files=files, timeout=10)
            
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            if upload_data.get('success'):
                print("✅ 文件上传成功")
                print(f"📄 上传文件数: {len(upload_data.get('files', []))}")
                uploaded_files = upload_data.get('files', [])
                if uploaded_files:
                    print(f"📝 文件信息: {uploaded_files[0]['name']} ({uploaded_files[0]['size']})")
            else:
                print(f"❌ 文件上传失败: {upload_data.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ 上传请求失败: {upload_response.status_code}")
            return False
        
        # 3. 测试文件转换 (MD -> HTML)
        print("\n3️⃣ 测试文件转换 (Markdown -> HTML)...")
        conversion_data = {
            'files': [uploaded_files[0]['path']],
            'output_format': 'html',
            'output_dir': '/Users/yiwenxu123/Documents/tare/文档转换/web_test_output',
            'keep_original_name': True,
            'async_conversion': False
        }
        
        convert_response = requests.post(
            f"{base_url}/convert", 
            json=conversion_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if convert_response.status_code == 200:
            convert_data = convert_response.json()
            if convert_data.get('success'):
                print("✅ 文件转换成功")
                results = convert_data.get('results', [])
                summary = convert_data.get('summary', {})
                print(f"📊 转换统计: {summary.get('success')}/{summary.get('total')} 成功")
                print(f"📈 成功率: {summary.get('success_rate', 0):.1f}%")
                
                # 检查转换结果
                for result in results:
                    if result['success']:
                        output_file = result['output_file']
                        if os.path.exists(output_file):
                            file_size = os.path.getsize(output_file)
                            print(f"✅ 输出文件: {os.path.basename(output_file)} ({file_size} bytes)")
                        else:
                            print(f"❌ 输出文件不存在: {output_file}")
                    else:
                        print(f"❌ 转换失败: {result.get('error', '未知错误')}")
            else:
                print(f"❌ 文件转换失败: {convert_data.get('error', '未知错误')}")
                return False
        else:
            print(f"❌ 转换请求失败: {convert_response.status_code}")
            print(f"响应内容: {convert_response.text}")
            return False
        
        # 4. 测试文件转换 (MD -> DOCX)
        print("\n4️⃣ 测试文件转换 (Markdown -> DOCX)...")
        conversion_data['output_format'] = 'docx'
        
        convert_response2 = requests.post(
            f"{base_url}/convert", 
            json=conversion_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if convert_response2.status_code == 200:
            convert_data2 = convert_response2.json()
            if convert_data2.get('success'):
                print("✅ DOCX转换成功")
                summary2 = convert_data2.get('summary', {})
                print(f"📊 转换统计: {summary2.get('success')}/{summary2.get('total')} 成功")
                print(f"📈 成功率: {summary2.get('success_rate', 0):.1f}%")
            else:
                print(f"❌ DOCX转换失败: {convert_data2.get('error', '未知错误')}")
        else:
            print(f"❌ DOCX转换请求失败: {convert_response2.status_code}")
        
        print("\n" + "="*50)
        print("🎉 Web版本转换功能测试完成!")
        print("✅ 所有核心功能正常工作")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Web服务器，请确保服务器正在运行")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时，服务器响应过慢")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_web_conversion()
    exit(0 if success else 1)