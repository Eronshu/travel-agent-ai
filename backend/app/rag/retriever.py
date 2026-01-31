# backend/app/rag/retriever.py
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_milvus import Milvus
from dotenv import load_dotenv, find_dotenv

# 加载环境
load_dotenv(find_dotenv(usecwd=True))

def get_retriever():
    """获取 Milvus 检索器实例"""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY not found in environment variables")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key
    )

    # 连接已有的数据库
    vector_store = Milvus(
        embedding_function=embeddings,
        connection_args={"uri": "./travel_data.db"},
        collection_name="hamilton_travel_guides",
        auto_id=True
    )
    
    return vector_store

def search_knowledge_base(query: str, k: int = 2) -> str:
    """
    RAG 核心检索函数
    Args:
        query: 用户的查询 (例如 "Hamilton 哪里看夜景？")
        k: 返回几条最相似的结果
    Returns:
        拼接好的文本内容
    """
    try:
        vector_store = get_retriever()
        # 相似度搜索
        results = vector_store.similarity_search(query, k=k)
        
        if not results:
            return ""
            
        # 格式化输出
        formatted_results = []
        for i, doc in enumerate(results):
            formatted_results.append(f"【独家情报 {i+1}】: {doc.page_content}")
            
        return "\n".join(formatted_results)
        
    except Exception as e:
        print(f"⚠️ RAG 检索失败: {e}")
        return ""

# 测试代码
if __name__ == "__main__":
    # 测试一下能不能查到
    print("🔍 测试 RAG 检索...")
    result = search_knowledge_base("推荐个好喝的咖啡店")
    print(result)