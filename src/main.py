#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOMO新闻摘要系统主入口

该系统从Supabase获取公司列表，分析最近24小时的相关新闻，
使用Pinecone向量数据库检索相关内容，并通过Gemini生成分析报告。
"""

import sys
import os
import io
import argparse
from datetime import datetime

# 设置标准输出编码为UTF-8（Windows兼容）并启用无缓冲输出
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)
else:
    # 非Windows系统也启用行缓冲
    sys.stdout.reconfigure(line_buffering=True)

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.analyzer import NewsAnalyzer
from src.utils.formatter import OutputFormatter

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='FOMO新闻摘要分析系统')
    parser.add_argument('--hours', type=int, default=24, 
                       help='分析时间范围（小时），默认24小时')
    parser.add_argument('--company', type=str, 
                       help='分析特定公司（可选），不指定则分析所有公司')
    parser.add_argument('--output', type=str, 
                       help='输出文件名（可选），不指定则输出到控制台')
    parser.add_argument('--verbose', action='store_true', 
                       help='显示详细处理过程')
    parser.add_argument('--debug', action='store_true', 
                       help='显示调试信息（包括中间数据）')
    parser.add_argument('--json', type=str, 
                       help='保存JSON格式的分析结果到指定文件')
    parser.add_argument('--save-db', action='store_true', 
                       help='将分析结果保存到Supabase数据库')
    
    args = parser.parse_args()
    
    # 初始化组件
    analyzer = NewsAnalyzer(debug=args.debug)
    formatter = OutputFormatter()
    
    try:
        print("启动FOMO新闻摘要分析系统...")
        print(f"分析时间范围: 最近 {args.hours} 小时")
        
        if args.company:
            # 分析单个公司
            print(f"🎯 目标公司: {args.company}")
            
            # 获取公司信息
            from src.services.supabase_service import SupabaseService
            supabase_service = SupabaseService()
            company_info = supabase_service.get_company_by_name(args.company)
            
            if not company_info:
                print(f"❌ 未找到公司 {args.company} 的数据库记录")
                return 1
            
            company_id = company_info.get('id')
            
            # 检查是否需要分析
            should_analyze, current_article_count = supabase_service.should_analyze_company(company_id)
            
            if should_analyze:
                print(f"✅ {args.company} 文章数量有变化，开始分析...")
                result = analyzer.analyze_single_company_with_count_update(
                    args.company, company_id, current_article_count, args.hours
                )
                if result:
                    results = [result]
                else:
                    print(f"❌ 分析公司 {args.company} 失败")
                    return 1
            else:
                print(f"⏭️  {args.company} 文章数量无变化，跳过分析")
                results = []
        else:
            # 分析所有公司
            print("🌐 目标: 所有公司")
            results = analyzer.analyze_all_companies(args.hours)
        
        if not results:
            print("❌ 未获取到任何分析结果")
            return 1
        
        # 格式化输出
        print("\n📝 正在格式化输出结果...")
        formatted_output = formatter.format_analysis_results(results)
        
        # JSON输出处理
        if args.json:
            import json
            try:
                with open(args.json, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                print(f"✅ JSON分析结果已保存到文件: {args.json}")
            except Exception as e:
                print(f"❌ 保存JSON文件失败: {e}")
        
        # 数据库保存处理
        if args.save_db:
            from src.services.supabase_service import SupabaseService
            supabase_service = SupabaseService()
            
            for result in results:
                if result.get('status') == 'success':
                    company_name = result.get('company', '')
                    company_info = supabase_service.get_company_by_name(company_name)
                    if company_info:
                        company_id = company_info.get('id')
                        success = supabase_service.update_company_summary(company_id, result)
                        if success:
                            print(f"✅ {company_name} 分析结果已保存到数据库")
                        else:
                            print(f"❌ {company_name} 保存数据库失败")
                    else:
                        print(f"⚠️ 未找到公司 {company_name} 的数据库记录")
        
        # 输出结果
        if args.output:
            # 保存到文件
            saved_file = formatter.save_to_file(formatted_output, args.output)
            if saved_file:
                print(f"✅ 分析结果已保存到文件: {saved_file}")
            else:
                print("❌ 保存文件失败，将输出到控制台")
                print("\n" + formatted_output)
        else:
            # 输出到控制台
            print("\n" + formatted_output)
        
        print(f"\n🎉 分析完成！共分析了 {len(results)} 家公司")
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断程序执行")
        return 1
    except Exception as e:
        print(f"\n💥 系统执行出现错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def test_connections():
    """测试所有数据库连接"""
    print("🔧 测试数据库连接...")
    
    try:
        from src.config.database import get_supabase_client, get_pinecone_client, get_gemini_client
        
        # 测试Supabase连接
        print("  📊 测试Supabase连接...")
        supabase = get_supabase_client()
        print("  ✅ Supabase连接成功")
        
        # 测试Pinecone连接
        print("  🔍 测试Pinecone连接...")
        pinecone_index = get_pinecone_client()
        stats = pinecone_index.describe_index_stats()
        print(f"  ✅ Pinecone连接成功，索引维度: {stats.get('dimension', 'N/A')}")
        
        # 测试Gemini连接
        print("  🧠 测试Gemini连接...")
        gemini = get_gemini_client()
        print("  ✅ Gemini连接成功")
        
        print("🎉 所有数据库连接测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def show_usage_examples():
    """显示使用示例"""
    examples = """
🔥 FOMO新闻摘要系统使用示例:

1. 分析所有公司最近24小时的新闻：
   python src/main.py

2. 分析所有公司最近12小时的新闻：
   python src/main.py --hours 12

3. 分析特定公司（如"苹果"）的新闻：
   python src/main.py --company "苹果"

4. 将结果保存到文件：
   python src/main.py --output "analysis_report.txt"

5. 显示详细处理过程：
   python src/main.py --verbose

6. 测试数据库连接：
   python src/main.py --test

组合使用：
   python src/main.py --company "英伟达" --hours 6 --output "nvidia_6h.txt" --verbose
    """
    print(examples)

if __name__ == "__main__":
    # 检查特殊命令
    if len(sys.argv) > 1:
        if '--test' in sys.argv:
            success = test_connections()
            sys.exit(0 if success else 1)
        elif '--help-examples' in sys.argv:
            show_usage_examples()
            sys.exit(0)
    
    # 执行主程序
    exit_code = main()
    sys.exit(exit_code)