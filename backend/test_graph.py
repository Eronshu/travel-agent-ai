# backend/test_graph.py
from app.agents.graph import graph
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

if __name__ == "__main__":
    print("🚀 启动 Multi-Agent 系统...")
    
    user_input = "我想去 Hamilton 玩两天，这周末去，喜欢看自然风光和吃tacos"
    
    initial_state = {
        "messages": [HumanMessage(content=user_input)]
    }
    
    # 使用 invoke 直接运行到结束，并获取最终状态
    # (相比 stream，invoke 更适合拿最终结果)
    final_state = graph.invoke(initial_state)
    
    print("\n" + "="*30)
    print("🌟 最终生成的旅行计划 🌟")
    print("="*30 + "\n")
    
    # 打印最终的草稿
    print(final_state.get("draft_plan", "❌ 生成失败，未找到行程草稿"))
    
    print("\n" + "="*30)