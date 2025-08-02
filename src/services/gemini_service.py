from typing import List, Dict, Any, Optional
import json
import re
import time
from google.genai import types
from src.config.database import get_gemini_client

class GeminiService:
    def __init__(self):
        self.client = get_gemini_client()
        self.embedding_model = "gemini-embedding-001"
        self.generation_model = "gemini-2.0-flash-lite"
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        使用Gemini embedding模型生成文本向量
        
        Args:
            text: 要转换为向量的文本
            
        Returns:
            List[float]: 文本向量
        """
        try:
            print(f"    🧠 使用模型 {self.embedding_model} 生成向量...")
            print(f"    📝 输入文本: {text}")
            
            result = self.client.models.embed_content(
                model=self.embedding_model,
                contents=[text],
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
            
            # 获取第一个embedding
            embedding = result.embeddings[0].values
            print(f"    ✅ 向量生成成功，维度: {len(embedding)}")
            print(f"    📊 向量样本: {embedding[:5]}...")
            
            return embedding
        except Exception as e:
            print(f"    ❌ 生成向量失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def generate_company_query(self, company_name: str) -> str:
        """
        为公司生成向量搜索查询语句
        
        Args:
            company_name: 公司名称
            
        Returns:
            str: 查询语句
        """
        return f"{company_name}公司的最新新闻、财报、股价和市场动态"
    
    def analyze_news(self, company_name: str, news_data: List[Dict[str, Any]], max_retries: int = 3) -> Dict[str, Any]:
        """
        使用Gemini分析公司相关新闻并生成总结
        
        Args:
            company_name: 公司名称
            news_data: 从向量数据库检索到的新闻数据
            max_retries: 最大重试次数
            
        Returns:
            Dict: 包含分析结果的字典，格式为 {facts: [...], opinions: [...], status: ...}
        """
        if not news_data:
            return {
                "status": "no_data",
                "facts": [],
                "opinions": [],
                "message": f"未找到{company_name}相关的最新新闻。"
            }
        
        print(f"    🤖 使用 {self.generation_model} 分析 {len(news_data)} 条新闻...")
        
        # 构建分析提示词
        news_content = self._format_news_for_analysis(news_data)
        
        prompt = f"""
请分析以下关于{company_name}公司的最新新闻内容，重点提取具体发生的事件。

核心要求：
1. Topic应该是明确的新闻事件，让读者立即明白发生了什么（而非宽泛的主题归类）
2. Aspect应该关注事件的具体细节和信息点
3. Content要包含具体的人物、时间、地点、金额、产品等关键信息
4. Citations必须包含充足的上下文，能够支撑Summary中提到的所有关键信息

{news_content}

请以JSON格式输出分析结果，格式如下：

{{
  "facts": [
    {{
      "topic": "简洁描述具体发生的事件（如：{company_name}与X公司达成Y合作、{company_name}推出Z产品等）",
      "summaries": [
        {{
          "aspect": "事件核心信息",
          "content": "详细描述事件的关键要素：谁做了什么、何时何地、涉及多少金额、有什么具体计划等",
          "citations": [
            {{
              "news_id": "实际的新闻ID",
              "content": "包含这些具体信息的完整原文段落，确保读者能看到原始信息来源"
            }}
          ]
        }},
        {{
          "aspect": "相关细节或影响",
          "content": "事件的其他重要细节、背景信息或预期影响",
          "citations": [
            {{
              "news_id": "实际的新闻ID",
              "content": "支撑这些信息的原文段落"
            }}
          ]
        }}
      ]
    }}
  ],
  "opinions": [
    {{
      "topic": "针对{company_name}具体事件的评价或预测",
      "summaries": [
        {{
          "aspect": "市场或专家观点",
          "content": "具体的人物或机构对事件的看法、预测的影响、给出的评价等",
          "citations": [
            {{
              "news_id": "实际的新闻ID",
              "content": "包含这些观点的完整原文段落"
            }}
          ]
        }}
      ]
    }}
  ]
}}

提示：
- Topic应该一句话说清楚发生了什么具体事件
- 优先提取包含具体信息的内容（人名、公司名、产品名、金额、时间等）
- 保持客观，基于新闻内容提取，不要过度解释
- Citations要完整，让读者能验证Summary中的信息

关键要求：
1. 必须输出有效的JSON格式
2. Topic聚焦具体事件而非宽泛主题
3. Content包含具体可验证的信息
4. Citations提供充分的原文支撑
5. 只输出JSON，不要有其他文字
        """
        
        print(f"    📝 分析提示词长度: {len(prompt)} 字符")
        print(f"    📊 新闻内容长度: {len(news_content)} 字符")
        
        # 重试逻辑
        for attempt in range(max_retries):
            try:
                print(f"    🔄 正在请求Gemini生成分析... (尝试 {attempt + 1}/{max_retries})")
                
                # 生成分析
                response = self.client.models.generate_content(
                    model=self.generation_model,
                    contents=[prompt]
                )
                
                if not response or not response.text:
                    raise Exception("API返回空响应")
                
                analysis_text = response.text
                print(f"    ✅ 获得响应，长度: {len(analysis_text)} 字符")
                
                # 尝试解析JSON
                result = self._try_parse_json(analysis_text)
                if result and self._validate_json_structure(result):
                    print(f"    ✅ 分析成功，JSON格式正确")
                    result['status'] = 'success'
                    return result
                
                # 格式错误，尝试修复
                print(f"    ⚠️  JSON格式有误，尝试修复...")
                fixed_result = self._fix_json_format(analysis_text)
                if fixed_result:
                    fixed_result['status'] = 'success'
                    return fixed_result
                
                # 修复失败，如果不是最后一次尝试，则重新生成
                if attempt < max_retries - 1:
                    print(f"    ⚠️  修复失败，{2 ** attempt}秒后重试...")
                    time.sleep(2 ** attempt)  # 指数退避
                
            except Exception as e:
                print(f"    ❌ 尝试 {attempt + 1} 失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    # 所有尝试都失败，返回降级响应
                    return self._generate_error_response(company_name, news_data, str(e))
        
        # 所有重试都失败
        return self._generate_error_response(company_name, news_data, "多次尝试后仍无法生成有效分析")
    
    def _format_news_for_analysis(self, news_data: List[Dict[str, Any]]) -> str:
        """
        格式化新闻数据用于分析，包含实际的news_id和完整上下文
        
        Args:
            news_data: 新闻数据列表
            
        Returns:
            str: 格式化后的新闻内容
        """
        formatted_news = []
        
        for news in news_data:
            metadata = news.get('metadata', {})
            # 获取实际的news_id
            news_id = metadata.get('news_id', '未知ID')
            title = metadata.get('article_title', metadata.get('title', '无标题'))
            content = metadata.get('text', metadata.get('content', '无内容'))
            published_at = metadata.get('article_published_time', metadata.get('published_at', '未知时间'))
            source = metadata.get('source', '未知来源')
            url = metadata.get('article_url', metadata.get('url', ''))
            
            # 确保内容有足够的上下文信息
            # 如果内容太短，提醒AI需要提取更完整的上下文
            content_note = ""
            if len(content) < 200:
                content_note = "\n[注意：此新闻内容较短，在引用时请确保包含完整的上下文]"
            
            formatted_news.append(f"""
===== 新闻 ID: {news_id} =====
标题: {title}
时间: {published_at}
来源: {source}
链接: {url}
完整内容: {content}{content_note}
==================
            """)
        
        return '\n'.join(formatted_news)
    
    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        尝试解析JSON，处理可能的代码块包裹
        
        Args:
            text: 要解析的文本
            
        Returns:
            解析后的字典，失败返回None
        """
        if not text:
            return None
            
        # 1. 尝试直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 2. 清理代码块并重试
        cleaned_text = text.strip()
        if cleaned_text.startswith('```json'):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith('```'):
            cleaned_text = cleaned_text[3:]
        
        if cleaned_text.endswith('```'):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        try:
            return json.loads(cleaned_text)
        except:
            pass
        
        # 3. 使用正则提取JSON部分
        json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        return None
    
    def _validate_json_structure(self, data: Any) -> bool:
        """
        验证JSON结构是否符合预期格式（支持新的多Summary结构）
        
        Args:
            data: 要验证的数据
            
        Returns:
            是否有效
        """
        if not isinstance(data, dict):
            return False
        
        # 必须包含facts和opinions
        if 'facts' not in data or 'opinions' not in data:
            return False
        
        # facts和opinions必须是列表
        if not isinstance(data['facts'], list) or not isinstance(data['opinions'], list):
            return False
        
        # 验证facts结构
        for fact in data['facts']:
            if not isinstance(fact, dict):
                return False
            if 'topic' not in fact or 'summaries' not in fact:
                return False
            if not isinstance(fact['summaries'], list):
                return False
            
            # 验证每个summary结构
            for summary in fact['summaries']:
                if not isinstance(summary, dict):
                    return False
                if 'aspect' not in summary or 'content' not in summary or 'citations' not in summary:
                    return False
                if not isinstance(summary['citations'], list):
                    return False
                
                # 验证citations结构
                for citation in summary['citations']:
                    if not isinstance(citation, dict):
                        return False
                    if 'news_id' not in citation or 'content' not in citation:
                        return False
        
        # 验证opinions结构（与facts相同）
        for opinion in data['opinions']:
            if not isinstance(opinion, dict):
                return False
            if 'topic' not in opinion or 'summaries' not in opinion:
                return False
            if not isinstance(opinion['summaries'], list):
                return False
            
            # 验证每个summary结构
            for summary in opinion['summaries']:
                if not isinstance(summary, dict):
                    return False
                if 'aspect' not in summary or 'content' not in summary or 'citations' not in summary:
                    return False
                if not isinstance(summary['citations'], list):
                    return False
                
                # 验证citations结构
                for citation in summary['citations']:
                    if not isinstance(citation, dict):
                        return False
                    if 'news_id' not in citation or 'content' not in citation:
                        return False
        
        return True
    
    def _fix_json_format(self, malformed_text: str, max_fix_attempts: int = 3) -> Optional[Dict[str, Any]]:
        """
        使用AI修复格式错误的JSON
        
        Args:
            malformed_text: 格式错误的文本
            max_fix_attempts: 最大修复尝试次数
            
        Returns:
            修复后的JSON字典，失败返回None
        """
        fix_prompt = f"""
请修复以下格式错误的JSON文本，使其成为有效的JSON格式。

原始文本：
{malformed_text}

要求：
1. 只返回修复后的JSON，不要有任何其他文字或解释
2. 保持原有的数据内容，只修复格式问题
3. 确保包含 facts 和 opinions 两个数组
4. 如果原文本不包含某些必需字段，请添加空数组

正确的JSON结构示例：
{{
  "facts": [
    {{
      "topic": "xxx",
      "summaries": [
        {{
          "aspect": "xxx",
          "content": "xxx",
          "citations": [
            {{
              "news_id": "xxx",
              "content": "xxx"
            }}
          ]
        }}
      ]
    }}
  ],
  "opinions": [
    {{
      "topic": "xxx", 
      "summaries": [
        {{
          "aspect": "xxx",
          "content": "xxx",
          "citations": [
            {{
              "news_id": "xxx",
              "content": "xxx"
            }}
          ]
        }}
      ]
    }}
  ]
}}
        """
        
        for attempt in range(max_fix_attempts):
            try:
                print(f"    🔧 尝试修复JSON格式... (尝试 {attempt + 1}/{max_fix_attempts})")
                
                response = self.client.models.generate_content(
                    model=self.generation_model,
                    contents=[fix_prompt]
                )
                
                if response and response.text:
                    fixed_json = self._try_parse_json(response.text)
                    if fixed_json and self._validate_json_structure(fixed_json):
                        print(f"    ✅ JSON修复成功")
                        return fixed_json
                
                if attempt < max_fix_attempts - 1:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"    ❌ 修复尝试 {attempt + 1} 失败: {e}")
        
        return None
    
    def _generate_error_response(self, company_name: str, news_data: List[Dict[str, Any]], error_msg: str) -> Dict[str, Any]:
        """
        生成错误响应
        
        Args:
            company_name: 公司名称
            news_data: 新闻数据
            error_msg: 错误信息
            
        Returns:
            错误响应字典
        """
        print(f"    ⚠️  生成降级响应")
        
        # 简单提取一些基本信息
        facts = []
        if news_data:
            fact_summary = f"找到{len(news_data)}条关于{company_name}的相关新闻。"
            
            # 获取第一条新闻的信息作为示例
            first_news = news_data[0]
            metadata = first_news.get('metadata', {})
            news_id = metadata.get('news_id', '未知ID')
            title = metadata.get('article_title', metadata.get('title', ''))[:100]
            
            if title:
                fact_summary += f" 其中包括：{title}等。"
            
            facts.append({
                "topic": f"{company_name}相关新闻",
                "summaries": [{
                    "aspect": "新闻概览",
                    "content": fact_summary,
                    "citations": [{
                        "news_id": news_id,
                        "content": title
                    }]
                }]
            })
        
        return {
            "status": "partial_success",
            "facts": facts,
            "opinions": [],
            "error": error_msg,
            "message": "由于技术问题，仅能提供部分分析结果。"
        }