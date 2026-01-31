# backend/app/rag/ingest.py
import os
import sys
from dotenv import load_dotenv, find_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_milvus import Milvus

# 强制加载 .env (防止路径问题)
load_dotenv(find_dotenv(usecwd=True))

# 1. 准备“独家”知识库
# 这些是 DeepSeek/GPT 可能不知道的“本地秘密”
# 在真实项目中，这里会是读取 PDF 或爬虫数据的代码
knowledge_base = [
    {
        "content": "Hamilton 的 'The Mule' 餐厅：这里的墨西哥卷饼是全城最好的，但一定要点 'Brussels Sprout Tacos'，这是隐藏菜单。人均消费 $25。",
        "category": "美食",
        "tags": "tacos, mexican, hidden_gem"
    },
    {
        "content": "Hamilton 隐秘景点 'Sam Lawrence Park'：大多数游客去 Albion Falls，但本地人晚上回去 Sam Lawrence 看夜景，那是俯瞰下城区的最佳位置，而且完全免费。",
        "category": "景点",
        "tags": "view, night, park"
    },
    {
        "content": "Hamilton 避雷指南：千万不要在周五下午 4 点走 Highway 403 往西方向，绝对堵死。建议走 Main Street West。",
        "category": "交通",
        "tags": "traffic, warning"
    },
    {
        "content": "Hamilton 咖啡店推荐：'Smalls Coffee' 是个很小的窗口店，但他家的 Latte 是用独特的燕麦奶配方调的，比星巴克好喝一百倍。地址在 James Street North。",
        "category": "美食",
        "tags": "coffee, cafe"
    },
    {
        "content": "Hamilton 停车小技巧：去 James Street North 吃饭，不要停路边，去 Vine Street 的停车场，晚上6点后免费。",
        "category": "交通",
        "tags": "parking, tips"
    },
    {
        "content": "Dundurn Castle 只有上午 11 点到下午 4 点开放，而且必须跟导游团。如果你只想拍外观，建议在日落时分去后花园，光线最好。",
        "category": "景点",
        "tags": "history, photography"
    }
]

def ingest_data():
    print("🚀 开始构建 RAG 知识库...")
    
    # 2. 检查 Key
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print("❌ 错误: 未找到 GOOGLE_API_KEY")
        return

    # 3. 初始化 Embedding 模型
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=api_key
    )

    # 4. 转换数据格式
    docs = []
    for item in knowledge_base:
        doc = Document(
            page_content=item["content"],
            metadata={"category": item["category"], "tags": item["tags"]}
        )
        docs.append(doc)

    # 5. 存入 Milvus (本地文件版)
    # 这一步会自动把文字变成向量并存入 travel_data.db
    vector_store = Milvus.from_documents(
        docs,
        embeddings,
        connection_args={"uri": "./travel_data.db"}, # 数据库文件路径
        collection_name="hamilton_travel_guides",
        drop_old=True  # 每次运行都重写，方便测试
    )
    
    print(f"✅ 成功写入 {len(docs)} 条独家数据到 Milvus！")
    print("💾 数据库文件已生成: ./travel_data.db")

if __name__ == "__main__":
    ingest_data()