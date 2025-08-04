from typing import List, Dict, Any
from src.services.supabase_service import SupabaseService
from src.services.gemini_service import GeminiService
from src.services.pinecone_service import PineconeService

class NewsAnalyzer:
    def __init__(self, debug=False):
        self.debug = debug
        self.supabase_service = SupabaseService()
        self.gemini_service = GeminiService()
        self.pinecone_service = PineconeService()
    
    def _debug_print(self, message, data=None):
        """调试输出函数"""
        if self.debug:
            print(f"🔍 DEBUG: {message}", flush=True)
            if data is not None:
                if isinstance(data, (list, dict)):
                    import json
                    print(f"    数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                else:
                    print(f"    数据: {str(data)}")
            print("    " + "-" * 50, flush=True)
    
    def analyze_all_companies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        分析所有公司的最新新闻
        
        Args:
            hours: 分析时间范围（小时）
            
        Returns:
            List[Dict]: 所有公司的分析结果
        """
        print("正在获取公司列表...")
        companies = self.supabase_service.get_companies()
        
        if not companies:
            print("未找到任何公司数据")
            return []
        
        print(f"找到 {len(companies)} 家公司，检查文章计数变化...")
        
        results = []
        analyzed_count = 0
        skipped_count = 0
        
        for company in companies:
            company_id = company.get('id', '')
            company_name = company.get('name', '未知公司')
            
            print(f"\n🔍 检查公司: {company_name}")
            
            # 检查是否需要分析该公司
            should_analyze, current_article_count = self.supabase_service.should_analyze_company(company_id)
            
            if should_analyze:
                print(f"✅ {company_name} 文章数量有变化，开始分析...")
                analysis_result = self.analyze_single_company_with_count_update(
                    company_name, company_id, current_article_count, hours
                )
                if analysis_result:
                    results.append(analysis_result)
                    analyzed_count += 1
            else:
                print(f"⏭️  {company_name} 文章数量无变化，跳过分析")
                skipped_count += 1
        
        print(f"\n📊 分析总结: 分析了 {analyzed_count} 家公司，跳过 {skipped_count} 家公司")
        return results
    
    def analyze_single_company_with_count_update(self, company_name: str, company_id: str, current_article_count: int, hours: int = 24) -> Dict[str, Any]:
        """
        分析单个公司的最新新闻，并在完成后更新文章计数
        
        Args:
            company_name: 公司名称
            company_id: 公司ID
            current_article_count: 当前文章数量
            hours: 分析时间范围（小时）
            
        Returns:
            Dict: 分析结果
        """
        # 如果当前文章数量为0，直接返回null内容，不需要分析
        if current_article_count == 0:
            print(f"📭 {company_name} 当前24小时内无文章，设置内容为null")
            
            # 更新last_article_count为0
            update_success = self.supabase_service.update_last_article_count(company_id, 0)
            if update_success:
                print(f"✅ {company_name} 文章计数更新为0")
            else:
                print(f"⚠️  {company_name} 文章计数更新失败")
            
            # 返回content为null的结果
            return {
                'company': company_name,
                'news_count': 0,
                'analysis': None,  # content设置为null
                'sources': [],
                'time_range_hours': hours,
                'status': 'no_news',
                'message': '当前24小时内无文章'
            }
        
        # 执行分析
        analysis_result = self.analyze_single_company(company_name, hours)
        
        # 如果分析成功，更新last_article_count
        if analysis_result and analysis_result.get('status') in ['success', 'no_news', 'no_vector_data']:
            print(f"\n🔄 分析完成，更新 {company_name} 的文章计数...")
            update_success = self.supabase_service.update_last_article_count(company_id, current_article_count)
            if update_success:
                print(f"✅ {company_name} 文章计数更新成功")
            else:
                print(f"⚠️  {company_name} 文章计数更新失败")
        
        return analysis_result
    
    def analyze_single_company(self, company_name: str, hours: int = 24) -> Dict[str, Any]:
        """
        分析单个公司的最新新闻
        
        Args:
            company_name: 公司名称
            hours: 分析时间范围（小时）
            
        Returns:
            Dict: 分析结果
        """
        try:
            print(f"\n📈 开始分析公司: {company_name}", flush=True)
            print("=" * 60, flush=True)
            
            # 步骤1: 从Supabase获取相关新闻ID
            print(f"📊 步骤1: 获取 {company_name} 最近 {hours} 小时的新闻ID...", flush=True)
            news_ids = self.supabase_service.get_company_news_ids(company_name, hours)
            
            self._debug_print(f"从Supabase获取的新闻ID", news_ids)
            
            if not news_ids:
                print(f"⚠️  {company_name} 未找到相关新闻")
                return {
                    'company': company_name,
                    'news_count': 0,
                    'analysis': None,  # 返回null而非文本
                    'sources': [],
                    'time_range_hours': hours,
                    'status': 'no_news'
                }
            
            print(f"✅ 找到 {len(news_ids)} 条相关新闻")
            
            # 步骤2: 生成查询语句和向量
            print(f"\n🧠 步骤2: 生成语义搜索查询...")
            query_text = self.gemini_service.generate_company_query(company_name)
            print(f"📝 查询语句: {query_text}")
            
            self._debug_print("生成的查询文本", query_text)
            
            query_vector = self.gemini_service.generate_embedding(query_text)
            if not query_vector:
                print(f"❌ 生成查询向量失败")
                return None
            
            print(f"✅ 生成向量成功，维度: {len(query_vector)}")
            self._debug_print("查询向量样本 (前10个值)", query_vector[:10])
            
            # 步骤3: 使用语义搜索结合metadata过滤在Pinecone中搜索
            print(f"\n🔍 步骤3: 使用语义搜索在向量数据库中搜索相关内容...")
            news_data = self.pinecone_service.search_with_semantic_and_metadata(
                query_vector=query_vector,
                news_ids=news_ids,
                company_name=company_name,
                hours=hours,
                top_k=50
            )
            
            self._debug_print("Pinecone返回的匹配结果", [
                {
                    'id': item.get('id'),
                    'score': item.get('score'),
                    'metadata_keys': list(item.get('metadata', {}).keys())
                } for item in news_data
            ])
            
            if not news_data:
                print(f"⚠️  向量数据库中未找到 {company_name} 的相关内容")
                return {
                    'company': company_name,
                    'news_count': len(news_ids),  # 实际找到了新闻ID
                    'analysis': None,  # 但没有向量内容，返回null
                    'sources': [],
                    'time_range_hours': hours,
                    'status': 'no_vector_data',
                    'message': f"找到{len(news_ids)}条新闻记录，但向量数据库中无对应内容"
                }
            
            print(f"✅ 从向量数据库获取到 {len(news_data)} 条新闻内容")
            
            # 步骤4: 显示具体的新闻内容
            print(f"\n📰 步骤4: 检索到的新闻内容预览...")
            for i, news in enumerate(news_data[:3], 1):  # 只显示前3条
                metadata = news.get('metadata', {})
                title = metadata.get('article_title', metadata.get('title', '无标题'))[:50]
                score = news.get('score', 0)
                print(f"   {i}. {title}... (相似度: {score:.3f})")
            
            if len(news_data) > 3:
                print(f"   ... 还有 {len(news_data) - 3} 条新闻")
            
            # 步骤5: 使用Gemini分析新闻内容
            print(f"\n🤖 步骤5: 使用Gemini分析新闻内容...")
            
            # 显示发送给AI的内容样本
            sample_content = self.gemini_service._format_news_for_analysis(news_data[:2])
            self._debug_print("发送给Gemini分析的内容样本（前2条新闻）", sample_content)
            
            analysis_result = self.gemini_service.analyze_news(company_name, news_data)
            
            print(f"✅ 分析完成，生成报告长度: {len(analysis_result)} 字符")
            self._debug_print("Gemini分析结果完整内容", analysis_result)
            
            # 步骤6: 提取引用信息
            print(f"\n📚 步骤6: 整理引用信息...")
            sources = self._extract_sources(news_data)
            print(f"✅ 整理了 {len(sources)} 个新闻来源")
            
            print("\n🎉 分析完成！")
            print("=" * 60)
            
            # 统一返回格式
            return {
                'company': company_name,
                'news_count': len(news_ids),  # 使用从Supabase获取的新闻ID数量
                'analysis': analysis_result,  # 可能是dict（JSON格式）或str（文本格式）
                'sources': sources,
                'time_range_hours': hours,
                'status': analysis_result.get('status', 'success') if isinstance(analysis_result, dict) else 'success'
            }
            
        except Exception as e:
            print(f"  分析 {company_name} 时出现错误: {e}")
            import traceback
            traceback.print_exc()
            return {
                'company': company_name,
                'news_count': 0,
                'analysis': None,
                'sources': [],
                'time_range_hours': hours,
                'status': 'error',
                'error': str(e)
            }
    
    def _extract_sources(self, news_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        从新闻数据中提取引用信息
        
        Args:
            news_data: 新闻数据列表
            
        Returns:
            List[Dict]: 引用信息列表
        """
        sources = []
        seen_urls = set()  # 用于去重的URL集合
        
        for news in news_data:
            metadata = news.get('metadata', {})
            url = metadata.get('article_url', metadata.get('url', ''))
            
            # 跳过已经见过的URL或空URL
            if url in seen_urls or not url:
                continue
                
            source_info = {
                'news_id': metadata.get('news_id', news.get('id', '')),
                'title': metadata.get('article_title', metadata.get('title', '无标题')),
                'source': metadata.get('source', '未知来源'),
                'published_at': metadata.get('article_published_time', metadata.get('published_at', '未知时间')),
                'url': url,
                'score': round(news.get('score', 0), 3)
            }
            sources.append(source_info)
            seen_urls.add(url)  # 标记该URL已处理
        
        # 按相似度分数排序
        sources.sort(key=lambda x: x['score'], reverse=True)
        return sources