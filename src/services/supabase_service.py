from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
from src.config.database import get_supabase_client

class SupabaseService:
    def __init__(self):
        self.client = get_supabase_client()
    
    def get_companies(self) -> List[Dict[str, Any]]:
        """
        从companies表获取所有要分析的公司列表
        
        Returns:
            List[Dict]: 公司信息列表
        """
        try:
            response = self.client.table('companies').select('*').execute()
            return response.data
        except Exception as e:
            print(f"获取公司列表失败: {e}")
            return []
    
    def get_recent_news_ids(self, company_names: List[str], hours: int = 24) -> List[str]:
        """
        获取最近指定小时内与指定公司相关的新闻ID
        
        Args:
            company_names: 公司名称列表
            hours: 时间范围（小时）
            
        Returns:
            List[str]: 新闻ID列表
        """
        try:
            # 计算时间范围
            time_threshold = datetime.now() - timedelta(hours=hours)
            time_str = time_threshold.isoformat()
            
            # 查询news_items表
            # 假设companies字段是数组类型，published_at是时间戳字段
            response = (
                self.client.table('news_items')
                .select('id, companies, published_at, title')
                .gte('published_at', time_str)
                .execute()
            )
            
            # 筛选包含指定公司的新闻
            relevant_news_ids = []
            for news_item in response.data:
                if news_item.get('companies'):
                    # 检查新闻是否包含任何一个指定的公司
                    news_companies = news_item['companies']
                    if any(company in news_companies for company in company_names):
                        relevant_news_ids.append(news_item['id'])
            
            return relevant_news_ids
            
        except Exception as e:
            print(f"获取最近新闻ID失败: {e}")
            return []
    
    def get_company_news_ids(self, company_name: str, hours: int = 24) -> List[str]:
        """
        获取单个公司最近指定小时内的新闻ID
        
        Args:
            company_name: 公司名称
            hours: 时间范围（小时）
            
        Returns:
            List[str]: 新闻ID列表
        """
        print(f"    🔍 查询 {company_name} 最近 {hours} 小时的新闻...")
        
        try:
            # 计算时间范围
            time_threshold = datetime.now() - timedelta(hours=hours)
            time_str = time_threshold.isoformat()
            print(f"    📅 时间阈值: {time_str}")
            
            # 查询news_items表
            print(f"    📊 执行Supabase查询...")
            response = (
                self.client.table('news_items')
                .select('id, companies, published_at, title')
                .gte('published_at', time_str)
                .execute()
            )
            
            print(f"    ✅ 查询返回 {len(response.data)} 条记录")
            
            # 筛选包含指定公司的新闻
            relevant_news_ids = []
            relevant_news_info = []
            
            for news_item in response.data:
                if news_item.get('companies'):
                    # 检查新闻是否包含指定的公司
                    news_companies = news_item['companies']
                    if company_name in news_companies or any(company_name in str(company) for company in news_companies):
                        relevant_news_ids.append(news_item['id'])
                        relevant_news_info.append({
                            'id': news_item['id'],
                            'title': news_item.get('title', '无标题')[:50],
                            'published_at': news_item.get('published_at', '未知时间'),
                            'companies': news_companies
                        })
            
            print(f"    🎯 筛选出 {len(relevant_news_ids)} 条 {company_name} 相关新闻")
            
            # 显示相关新闻的详细信息
            if relevant_news_info:
                print(f"    📰 相关新闻列表:")
                for i, info in enumerate(relevant_news_info[:5], 1):  # 最多显示5条
                    print(f"       {i}. {info['title']}... ({info['published_at'][:19]})")
                if len(relevant_news_info) > 5:
                    print(f"       ... 还有 {len(relevant_news_info) - 5} 条新闻")
            
            return relevant_news_ids
            
        except Exception as e:
            print(f"    ❌ 查询失败: {e}")
            return []
    
    def update_company_summary(self, company_id: str, summary_data: Dict[str, Any]) -> bool:
        """
        更新公司的24小时摘要数据
        
        Args:
            company_id: 公司ID
            summary_data: 摘要数据字典
            
        Returns:
            bool: 更新是否成功
        """
        try:
            print(f"    🔄 更新公司 {company_id} 的摘要数据...")
            
            # 检查是否需要设置为NULL（当analysis为None且news_count为0时）
            analysis = summary_data.get('analysis')
            news_count = summary_data.get('news_count', 0)
            
            if analysis is None and news_count == 0:
                # 无新闻内容，将summary_24hrs设置为NULL
                print(f"    📭 无新闻内容，将summary_24hrs设置为NULL")
                response = self.client.table('companies').update({
                    'summary_24hrs': None
                }).eq('id', company_id).execute()
            else:
                # 有内容，正常保存JSON
                # 添加更新时间戳
                summary_data['updated_at'] = datetime.now().isoformat()
                
                # 转换为JSON字符串
                summary_json = json.dumps(summary_data, ensure_ascii=False)
                
                response = self.client.table('companies').update({
                    'summary_24hrs': summary_json
                }).eq('id', company_id).execute()
            
            print(f"    ✅ 摘要数据更新成功")
            return True
            
        except Exception as e:
            print(f"    ❌ 更新摘要数据失败: {e}")
            return False
    
    def get_company_by_name(self, company_name: str) -> Dict[str, Any]:
        """
        根据公司名称获取公司信息
        
        Args:
            company_name: 公司名称
            
        Returns:
            Dict: 公司信息，不存在则返回空字典
        """
        try:
            response = self.client.table('companies').select('*').eq('name', company_name).execute()
            if response.data:
                return response.data[0]
            return {}
        except Exception as e:
            print(f"查询公司信息失败: {e}")
            return {}
    
    def get_company_article_counts(self, company_id: str) -> Dict[str, int]:
        """
        获取公司的文章计数信息
        
        Args:
            company_id: 公司ID
            
        Returns:
            Dict: 包含current_article_count_24hrs和last_article_count_24hrs的字典
        """
        try:
            response = self.client.table('companies').select('current_article_count_24hrs, last_article_count_24hrs').eq('id', company_id).execute()
            if response.data:
                data = response.data[0]
                return {
                    'current_article_count_24hrs': data.get('current_article_count_24hrs', 0),
                    'last_article_count_24hrs': data.get('last_article_count_24hrs', 0)
                }
            return {'current_article_count_24hrs': 0, 'last_article_count_24hrs': 0}
        except Exception as e:
            print(f"获取公司文章计数失败: {e}")
            return {'current_article_count_24hrs': 0, 'last_article_count_24hrs': 0}
    
    def should_analyze_company(self, company_id: str) -> tuple[bool, int]:
        """
        检查是否应该分析该公司（基于文章计数是否有变化）
        
        Args:
            company_id: 公司ID
            
        Returns:
            tuple: (是否需要分析, 当前文章数量)
        """
        try:
            counts = self.get_company_article_counts(company_id)
            current_count = counts['current_article_count_24hrs']
            last_count = counts['last_article_count_24hrs']
            
            should_analyze = current_count != last_count
            print(f"    📊 文章计数检查: 当前={current_count}, 上次={last_count}, 需要分析={should_analyze}")
            
            return should_analyze, current_count
        except Exception as e:
            print(f"检查是否需要分析时出错: {e}")
            return True, 0  # 出错时默认进行分析
    
    def update_last_article_count(self, company_id: str, new_count: int) -> bool:
        """
        更新公司的last_article_count_24hrs
        
        Args:
            company_id: 公司ID
            new_count: 新的文章计数
            
        Returns:
            bool: 更新是否成功
        """
        try:
            print(f"    🔄 更新公司 {company_id} 的last_article_count_24hrs为 {new_count}...")
            
            response = self.client.table('companies').update({
                'last_article_count_24hrs': new_count
            }).eq('id', company_id).execute()
            
            print(f"    ✅ last_article_count_24hrs更新成功")
            return True
            
        except Exception as e:
            print(f"    ❌ 更新last_article_count_24hrs失败: {e}")
            return False