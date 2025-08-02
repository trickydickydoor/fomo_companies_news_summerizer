import os
from supabase import create_client
from pinecone import Pinecone
from google import genai
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client():
    """初始化Supabase客户端"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("缺少Supabase配置，请检查环境变量")
    
    # 使用简化的客户端创建方式
    return create_client(url, key)

def get_pinecone_client():
    """初始化Pinecone客户端"""
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME")
    
    if not api_key or not index_name:
        raise ValueError("缺少Pinecone配置，请检查环境变量")
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    return index

def get_gemini_client():
    """初始化Gemini客户端"""
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError("缺少Google API Key，请检查环境变量")
    
    return genai.Client(api_key=api_key)