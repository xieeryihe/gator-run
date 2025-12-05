#!/usr/bin/env python
"""
测试保留源码功能的脚本
演示如何在分析时同时保存源码和结果
"""

import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 70)
    print("WTG 可视化 - 保留源码演示")
    print("=" * 70)
    print()
    print("此脚本将分析 APV 并保留解压的源代码")
    print("输出结构：")
    print("  output/apv/source/  - APK 解压源码")
    print("  output/apv/results/ - 分析结果")
    print()
    
    # 修改 viz-demo.json 使其保留解压目录
    import subprocess
    
    cmd = [
        "python", "runGator.py", 
        "-j", "viz-demo.json", 
        "-p", "apv"
    ]
    
    # 注意：需要在 runGator.py 中添加 --keep-decoded-apk-dir 支持
    # 或者修改配置文件
    
    print("[1/2] 运行 Gator 分析...")
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode != 0:
        print("分析失败")
        return
    
    print()
    print("[2/2] 检查输出...")
    
    output_base = os.path.join(script_dir, "..", "output", "apv")
    source_dir = os.path.join(output_base, "source")
    results_dir = os.path.join(output_base, "results")
    
    if os.path.exists(source_dir):
        print(f"✓ 源码目录: {source_dir}")
        print(f"  - 包含文件: {len(os.listdir(source_dir))} 项")
    else:
        print(f"✗ 源码目录不存在（使用临时目录）")
    
    if os.path.exists(results_dir):
        print(f"✓ 结果目录: {results_dir}")
        for f in os.listdir(results_dir):
            print(f"  - {f}")
    
    print()
    print("=" * 70)
    print("完成！查看结果：")
    html_file = os.path.join(results_dir, "apv_wtg_viewer.html")
    if os.path.exists(html_file):
        print(f"  {html_file}")

if __name__ == "__main__":
    main()
