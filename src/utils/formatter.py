from typing import List, Dict, Any
from datetime import datetime

class OutputFormatter:
    def __init__(self):
        pass
    
    def format_analysis_results(self, results: List[Dict[str, Any]]) -> str:
        """
        格式化所有公司的分析结果
        
        Args:
            results: 所有公司的分析结果列表
            
        Returns:
            str: 格式化后的输出内容
        """
        if not results:
            return "未找到任何分析结果。"
        
        output_lines = []
        
        # 添加标题和时间戳
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_lines.append("=" * 80)
        output_lines.append("🔥 FOMO新闻摘要分析报告")
        output_lines.append(f"📅 生成时间: {current_time}")
        output_lines.append(f"📊 分析公司数量: {len(results)}")
        output_lines.append("=" * 80)
        output_lines.append("")
        
        # 添加每个公司的分析结果
        for i, result in enumerate(results, 1):
            company_section = self.format_single_company_result(result, i)
            output_lines.append(company_section)
            output_lines.append("")
        
        # 添加总结
        summary_section = self._generate_summary(results)
        output_lines.append(summary_section)
        
        return "\n".join(output_lines)
    
    def format_single_company_result(self, result: Dict[str, Any], index: int = None) -> str:
        """
        格式化单个公司的分析结果
        
        Args:
            result: 公司分析结果
            index: 公司序号
            
        Returns:
            str: 格式化后的公司分析内容
        """
        lines = []
        
        # 公司标题
        company_name = result.get('company', '未知公司')
        news_count = result.get('news_count', 0)
        time_range = result.get('time_range_hours', 24)
        
        if index:
            lines.append(f"📈 {index}. {company_name}")
        else:
            lines.append(f"📈 {company_name}")
        
        lines.append("-" * 60)
        lines.append(f"🔍 分析时间范围: 最近 {time_range} 小时")
        lines.append(f"📰 相关新闻数量: {news_count} 条")
        lines.append("")
        
        # 分析内容
        analysis = result.get('analysis', '无分析内容')
        
        # 处理analysis为null的情况
        if analysis is None:
            status = result.get('status', 'unknown')
            if status == 'no_news':
                lines.append("💡 分析结果: 未找到相关新闻")
            elif status == 'no_vector_data':
                lines.append("💡 分析结果: 向量数据库中无对应内容")
                if 'message' in result:
                    lines.append(f"   说明: {result['message']}")
            else:
                lines.append("💡 分析结果: 无数据")
            lines.append("")
        # 检查是否是JSON格式的分析结果
        elif isinstance(analysis, dict) and 'facts' in analysis and 'opinions' in analysis:
            lines.append("💡 分析总结:")
            lines.append("")
            
            # 格式化事实部分
            lines.append("📊 事实:")
            for fact in analysis.get('facts', []):
                lines.append(f"  ▪ {fact.get('topic', '')}:")
                for detail in fact.get('details', []):
                    content = detail.get('content', '')
                    citation = detail.get('citation', {})
                    news_id = citation.get('news_id', '')
                    quote = citation.get('quote', '')[:50] + '...' if len(citation.get('quote', '')) > 50 else citation.get('quote', '')
                    lines.append(f"    - {content}")
                    lines.append(f"      (引用: 新闻{news_id} - \"{quote}\")")
                lines.append("")
            
            # 格式化观点部分
            lines.append("💭 观点:")
            for opinion in analysis.get('opinions', []):
                lines.append(f"  ▪ {opinion.get('topic', '')}:")
                for detail in opinion.get('details', []):
                    content = detail.get('content', '')
                    citation = detail.get('citation', {})
                    news_id = citation.get('news_id', '')
                    quote = citation.get('quote', '')[:50] + '...' if len(citation.get('quote', '')) > 50 else citation.get('quote', '')
                    lines.append(f"    - {content}")
                    lines.append(f"      (引用: 新闻{news_id} - \"{quote}\")")
                lines.append("")
        else:
            # 兼容旧格式（纯文本）
            lines.append("💡 分析总结:")
            if isinstance(analysis, str):
                lines.append(analysis)
            else:
                lines.append(str(analysis))
            lines.append("")
        
        # 引用来源
        sources = result.get('sources', [])
        if sources:
            lines.append("📚 新闻来源:")
            for j, source in enumerate(sources[:5], 1):  # 最多显示5个来源
                source_line = self._format_source(source, j)
                lines.append(source_line)
        else:
            lines.append("📚 新闻来源: 暂无")
        
        # 错误信息（如果有）
        if 'error' in result:
            lines.append("")
            lines.append(f"⚠️ 错误信息: {result['error']}")
        
        return "\n".join(lines)
    
    def _format_source(self, source: Dict[str, str], index: int) -> str:
        """
        格式化单个新闻来源
        
        Args:
            source: 来源信息
            index: 来源序号
            
        Returns:
            str: 格式化后的来源信息
        """
        title = source.get('title', '无标题')
        source_name = source.get('source', '未知来源')
        published_at = source.get('published_at', '未知时间')
        score = source.get('score', 0)
        url = source.get('url', '')
        
        # 格式化时间
        try:
            if published_at != '未知时间':
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%m-%d %H:%M")
            else:
                formatted_time = published_at
        except:
            formatted_time = published_at
        
        source_line = f"   {index}. 📄 {title}"
        source_line += f"\n      🏢 {source_name} | ⏰ {formatted_time} | 🎯 相似度: {score}"
        
        if url:
            source_line += f"\n      🔗 {url}"
        
        return source_line
    
    def _generate_summary(self, results: List[Dict[str, Any]]) -> str:
        """
        生成总体分析摘要
        
        Args:
            results: 所有分析结果
            
        Returns:
            str: 总体摘要
        """
        lines = []
        lines.append("=" * 80)
        lines.append("📋 总体分析摘要")
        lines.append("=" * 80)
        
        total_companies = len(results)
        total_news = sum(result.get('news_count', 0) for result in results)
        companies_with_news = len([r for r in results if r.get('news_count', 0) > 0])
        companies_without_news = total_companies - companies_with_news
        
        lines.append(f"🏢 总分析公司数: {total_companies}")
        lines.append(f"📰 总新闻条数: {total_news}")
        lines.append(f"✅ 有新闻的公司: {companies_with_news}")
        lines.append(f"❌ 无新闻的公司: {companies_without_news}")
        
        if total_news > 0:
            avg_news_per_company = total_news / companies_with_news if companies_with_news > 0 else 0
            lines.append(f"📊 平均每家公司新闻数: {avg_news_per_company:.1f}")
        
        # 最热门的公司（新闻数量最多）
        if results:
            hottest_company = max(results, key=lambda x: x.get('news_count', 0))
            if hottest_company.get('news_count', 0) > 0:
                lines.append("")
                lines.append(f"🔥 最热门公司: {hottest_company['company']} ({hottest_company['news_count']} 条新闻)")
        
        lines.append("")
        lines.append("📝 注: 本报告基于最新24小时内的新闻数据生成")
        lines.append("⚡ 由 FOMO新闻摘要系统 自动生成")
        
        return "\n".join(lines)
    
    def save_to_file(self, content: str, filename: str = None) -> str:
        """
        将分析结果保存到文件
        
        Args:
            content: 要保存的内容
            filename: 文件名（可选）
            
        Returns:
            str: 保存的文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fomo_analysis_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return filename
        except Exception as e:
            print(f"保存文件失败: {e}")
            return ""