#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions自动化运行脚本
用于在GitHub Actions环境中运行FOMO新闻分析
"""

import sys
import os
import argparse
import json
from datetime import datetime
import subprocess

# 添加当前项目目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def ensure_output_directory():
    """确保输出目录存在"""
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def run_analysis(hours=24, company=None, save_to_db=False):
    """运行新闻分析"""
    output_dir = ensure_output_directory()
    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M')
    
    # 构建命令 - 移除JSON输出，只保留控制台输出
    cmd = [
        sys.executable,
        os.path.join(project_root, 'src', 'main.py'),
        '--hours', str(hours),
        '--verbose'
    ]
    
    # 添加可选参数
    if company:
        cmd.extend(['--company', company])
    
    if save_to_db:
        cmd.append('--save-db')
    
    print(f"🚀 开始运行FOMO新闻分析...")
    print(f"📅 时间范围: {hours}小时")
    print(f"🏢 目标公司: {company if company else '所有公司'}")
    print(f"💾 保存到数据库: {'是' if save_to_db else '否'}")
    print("-" * 50)
    
    try:
        # 运行分析
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        # 输出运行日志
        print("📝 运行日志:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ 错误信息:")
            print(result.stderr)
        
        # 不再生成文件摘要，所有信息都在控制台输出中
        
        if result.returncode == 0:
            print("\n✅ 分析完成!")
            return True
        else:
            print(f"\n❌ 分析失败，退出码: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n💥 运行出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_summary(output_dir, timestamp, hours, company):
    """生成分析摘要"""
    summary_file = os.path.join(output_dir, 'summary.txt')
    json_file = os.path.join(output_dir, f'news-analysis-{timestamp}.json')
    
    try:
        # 读取分析结果
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # 生成摘要
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"FOMO新闻分析摘要 (基于文章计数变化)\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"分析范围: {hours}小时\n")
                f.write(f"目标公司: {company if company else '所有公司'}\n")
                f.write(f"分析结果: 共{len(results)}家公司\n")
                f.write("-" * 40 + "\n\n")
                
                # 统计各种状态
                analyzed_count = 0
                skipped_count = 0
                success_count = 0
                
                # 列出各公司分析状态
                for result in results:
                    company_name = result.get('company', 'Unknown')
                    status = result.get('status', 'Unknown')
                    
                    if status == 'success':
                        analyzed_count += 1
                        success_count += 1
                        analysis = result.get('analysis', {})
                        if isinstance(analysis, dict):
                            facts_count = len(analysis.get('facts', []))
                            opinions_count = len(analysis.get('opinions', []))
                            f.write(f"✅ {company_name}: {facts_count}个事实, {opinions_count}个观点\n")
                        else:
                            f.write(f"✅ {company_name}: 分析完成\n")
                    elif status in ['no_news', 'no_vector_data']:
                        analyzed_count += 1
                        f.write(f"⚠️ {company_name}: {status}\n")
                    elif status == 'skipped':
                        skipped_count += 1
                        f.write(f"⏭️ {company_name}: 文章数量无变化，跳过分析\n")
                    else:
                        analyzed_count += 1
                        error = result.get('error', 'Unknown error')
                        f.write(f"❌ {company_name}: {error}\n")
                
                # 添加统计信息
                f.write(f"\n{'-' * 40}\n")
                f.write(f"📊 统计信息:\n")
                f.write(f"   - 已分析: {analyzed_count}家公司\n")
                f.write(f"   - 成功分析: {success_count}家公司\n")
                f.write(f"   - 跳过分析: {skipped_count}家公司\n")
                f.write(f"   - 总计: {len(results) + skipped_count}家公司\n")
                
                print(f"\n📄 摘要已保存到: {summary_file}")
        else:
            print(f"⚠️ 未找到分析结果文件: {json_file}")
            
    except Exception as e:
        print(f"⚠️ 生成摘要时出错: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GitHub Actions FOMO新闻分析运行脚本')
    parser.add_argument('--hours', type=int, default=24,
                       help='分析时间范围（小时），默认24')
    parser.add_argument('--company', type=str, default='',
                       help='公司名称（可选），默认分析所有公司')
    parser.add_argument('--save-db', type=str, default='false',
                       help='是否保存到数据库（true/false），默认false')
    
    args = parser.parse_args()
    
    # 转换save-db参数
    save_to_db = args.save_db.lower() == 'true'
    
    # 运行分析
    success = run_analysis(
        hours=args.hours,
        company=args.company if args.company else None,
        save_to_db=save_to_db
    )
    
    # 设置退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()