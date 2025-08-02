from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.config.database import get_pinecone_client

class PineconeService:
    def __init__(self):
        self.index = get_pinecone_client()
    
    def search_by_vector(self, 
                        query_vector: List[float], 
                        top_k: int = 10,
                        filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        使用向量在Pinecone中搜索相似内容
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            response = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_metadata
            )
            
            return response.get('matches', [])
            
        except Exception as e:
            print(f"Pinecone向量搜索失败: {e}")
            return []
    
    def search_by_ids(self, news_ids: List[str]) -> List[Dict[str, Any]]:
        """
        根据新闻ID列表在Pinecone中搜索相关向量
        
        Args:
            news_ids: 新闻ID列表
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        if not news_ids:
            print("    ⚠️  新闻ID列表为空，跳过Pinecone查询")
            return []
        
        try:
            print(f"    🔍 在Pinecone中搜索 {len(news_ids)} 个新闻ID...")
            print(f"    📋 新闻ID列表: {news_ids[:3]}{'...' if len(news_ids) > 3 else ''}")
            
            # 使用元数据过滤查询指定ID的向量
            filter_condition = {
                "news_id": {"$in": news_ids}
            }
            
            print(f"    🔧 过滤条件: {filter_condition}")
            print(f"    🔄 执行向量查询...")
            
            response = self.index.query(
                vector=[0.0] * 768,  # 占位符向量，实际不用于相似性计算
                top_k=len(news_ids) * 2,  # 确保能够获取所有相关结果
                include_metadata=True,
                filter=filter_condition
            )
            
            matches = response.get('matches', [])
            print(f"    ✅ 查询完成，找到 {len(matches)} 个匹配的向量")
            
            if matches:
                print(f"    📄 匹配结果预览:")
                for i, match in enumerate(matches[:3], 1):
                    metadata = match.get('metadata', {})
                    title = metadata.get('title', '无标题')[:40]
                    news_id = metadata.get('news_id', '无ID')
                    print(f"       {i}. {title}... (ID: {news_id})")
                if len(matches) > 3:
                    print(f"       ... 还有 {len(matches) - 3} 个结果")
            else:
                print(f"    ⚠️  未找到匹配的向量数据")
                print(f"    💡 可能原因: Pinecone中的news_id与Supabase中的id不匹配")
            
            return matches
            
        except Exception as e:
            print(f"    ❌ 根据ID搜索向量失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_with_semantic_and_metadata(self,
                                         query_vector: List[float],
                                         news_ids: List[str],
                                         company_name: str,
                                         hours: int = 24,
                                         top_k: int = 20) -> List[Dict[str, Any]]:
        """
        使用语义搜索结合metadata过滤进行查询
        
        Args:
            query_vector: 查询向量
            news_ids: 从Supabase获取的相关新闻ID列表
            company_name: 公司名称
            hours: 时间范围（小时）
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            print(f"    🔍 执行语义搜索 + metadata过滤...")
            print(f"    📊 查询向量维度: {len(query_vector)}")
            print(f"    🎯 目标公司: {company_name}")
            print(f"    📋 相关新闻ID: {len(news_ids)} 个")
            print(f"    🔄 返回结果数量: {top_k}")
            
            # 构建过滤条件：只使用新闻ID过滤，不使用时间过滤
            filter_condition = {
                "news_id": {"$in": news_ids}  # 只限制在相关新闻ID内
            }
            
            print(f"    🔧 过滤条件: 仅限制在 {len(news_ids)} 个相关新闻ID内")
            print(f"    🔄 执行语义相似性搜索...")
            
            response = self.index.query(
                vector=query_vector,  # 使用真实的查询向量
                top_k=top_k,
                include_metadata=True,
                filter=filter_condition
            )
            
            matches = response.get('matches', [])
            print(f"    ✅ 搜索完成，找到 {len(matches)} 个匹配结果")
            
            if matches:
                print(f"    📈 相似度分数范围: {matches[0].get('score', 0):.3f} - {matches[-1].get('score', 0):.3f}")
                print(f"    📄 匹配结果预览:")
                for i, match in enumerate(matches[:3], 1):
                    metadata = match.get('metadata', {})
                    title = metadata.get('article_title', '无标题')[:40]
                    score = match.get('score', 0)
                    news_id = metadata.get('news_id', '无ID')
                    print(f"       {i}. {title}... (分数: {score:.3f}, ID: {news_id})")
                if len(matches) > 3:
                    print(f"       ... 还有 {len(matches) - 3} 个结果")
            else:
                print(f"    ⚠️  未找到匹配的向量数据")
                print(f"    💡 可能原因: metadata字段不匹配或时间戳格式问题")
            
            return matches
            
        except Exception as e:
            print(f"    ❌ 语义搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_company_news(self, 
                           query_vector: List[float],
                           company_name: str,
                           hours: int = 24,
                           top_k: int = 20) -> List[Dict[str, Any]]:
        """
        搜索特定公司最近时间范围内的相关新闻
        
        Args:
            query_vector: 查询向量
            company_name: 公司名称
            hours: 时间范围（小时）
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果列表
        """
        try:
            print(f"    🔍 在Pinecone中搜索 {company_name} 相关新闻...")
            print(f"    📊 查询向量维度: {len(query_vector)}")
            print(f"    🎯 返回结果数量: {top_k}")
            
            # 计算时间阈值
            time_threshold = datetime.now() - timedelta(hours=hours)
            time_timestamp = int(time_threshold.timestamp())
            print(f"    📅 时间过滤: >= {time_threshold.isoformat()} (时间戳: {time_timestamp})")
            
            # 构建过滤条件
            filter_condition = {
                "$and": [
                    {"company": {"$eq": company_name}},
                    {"published_at": {"$gte": time_timestamp}}
                ]
            }
            
            print(f"    🔧 过滤条件: {filter_condition}")
            
            print(f"    🔄 执行向量相似性搜索...")
            response = self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
                filter=filter_condition
            )
            
            matches = response.get('matches', [])
            print(f"    ✅ 搜索完成，找到 {len(matches)} 个匹配结果")
            
            if matches:
                print(f"    📈 相似度分数范围: {matches[0].get('score', 0):.3f} - {matches[-1].get('score', 0):.3f}")
                print(f"    📄 匹配结果预览:")
                for i, match in enumerate(matches[:3], 1):
                    metadata = match.get('metadata', {})
                    title = metadata.get('title', '无标题')[:40]
                    score = match.get('score', 0)
                    print(f"       {i}. {title}... (分数: {score:.3f})")
                if len(matches) > 3:
                    print(f"       ... 还有 {len(matches) - 3} 个结果")
            
            return matches
            
        except Exception as e:
            print(f"    ❌ 搜索公司新闻失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_vector_by_id(self, vector_id: str) -> Dict[str, Any]:
        """
        根据向量ID获取单个向量数据
        
        Args:
            vector_id: 向量ID
            
        Returns:
            Dict: 向量数据
        """
        try:
            response = self.index.fetch(ids=[vector_id])
            vectors = response.get('vectors', {})
            
            if vector_id in vectors:
                return vectors[vector_id]
            else:
                return {}
                
        except Exception as e:
            print(f"获取向量数据失败: {e}")
            return {}