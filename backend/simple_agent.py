import os
import json
import requests
from datetime import datetime
from typing import Annotated, TypedDict
from dotenv import load_dotenv

# --- LangGraph & LangChain 核心 ---
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool

# --- 模型 ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch

load_dotenv()

# ==========================================
# 🆕 新增：自定义 OpenWeather 工具
# ==========================================
# @tool 装饰器是关键，它把一个普通 Python 函数变成了 AI 能理解的“技能”
@tool
def get_current_weather(city: str):
    """
    查询指定城市的实时天气数据。
    Args:
        city: 城市名称 (例如: "Hamilton,CA")
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "错误：未配置 OpenWeather API Key。"
    
    # 调用 OpenWeather API
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            # 提取关键信息返回给 AI (省得它读一堆废话)
            weather_desc = data['weather'][0]['description']
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            return f"{city} 天气: {weather_desc}, 温度: {temp}°C, 体感: {feels_like}°C"
        else:
            return f"查询失败: {data.get('message', '未知错误')}"
    except Exception as e:
        return f"请求异常: {str(e)}"

# ==========================================
# 1. 定义记忆 (State)
# ==========================================
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# ==========================================
# 2. 准备工具箱 (Tools)
# ==========================================
# 现在我们要给 AI 两个工具：
# 1. OpenWeather (专门查天气)
# 2. Tavily (专门查景点/攻略)
tavily_tool = TavilySearch(max_results=3)
tools = [get_current_weather, tavily_tool]

# ==========================================
# 3. 初始化大脑
# ==========================================
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=os.getenv("LLM_API_KEY")
)

# 绑定工具
llm_with_tools = llm.bind_tools(tools)

# ==========================================
# 4. 定义节点 (Nodes)
# ==========================================
def chatbot_node(state: AgentState):
    # 🆕 关键修改：在调用模型前，注入“当前时间”
    # 这样 AI 就知道“明天”是几号了
    current_date = datetime.now().strftime("%Y-%m-%d %A")
    system_prompt = SystemMessage(content=f"你是智能旅行助手。今天是 {current_date}。查询天气请优先使用 get_current_weather 工具。")
    
    # 把 System Prompt 插在消息列表最前面
    messages = [system_prompt] + state["messages"]
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

tool_node = ToolNode(tools)

# ==========================================
# 5. 定义逻辑流 & 组装图
# ==========================================
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("planner", chatbot_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("planner")
workflow.add_conditional_edges("planner", should_continue, ["tools", END])
workflow.add_edge("tools", "planner")

app = workflow.compile()

# ==========================================
# 6. 运行测试 (无截断版)
# ==========================================
if __name__ == "__main__":
    print("🤖 智能旅行助手 v2 (OpenWeather版) 已启动...\n")
    
    # 这里的 prompt 故意说“明天”，测试它能不能识别出具体日期
    user_input = "帮我查一下 Hamilton Ontario 明天的天气（如果查不到明天的就查实时的），并推荐一个户外景点。"
    print(f"👤 用户: {user_input}\n")

    initial_state = {"messages": [HumanMessage(content=user_input)]}

    for event in app.stream(initial_state):
        for key, value in event.items():
            print(f"👉 正在执行节点: {key}")
            
            # 获取最新的一条消息
            last_msg = value["messages"][-1]
            
            # --- 🛠️ 打印工具调用情况 ---
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                for tool_call in last_msg.tool_calls:
                     print(f"   🛠️  AI 决定调用工具: {tool_call['name']}")
                     print(f"   📄 参数: {tool_call['args']}")
            
            # --- 📝 打印 AI 的回复 (无截断) ---
            # 如果是工具运行完的结果
            if key == "tools":
                # 工具的消息是 ToolMessage，我们要看它的 content
                print(f"   🔙 工具返回结果:\n{last_msg.content}\n")
            
            # 如果是 Planner 的思考/回答
            if key == "planner" and last_msg.content:
                 print(f"   🗣️  AI 思考/回答:\n{last_msg.content}\n")
            
            print("-" * 50)
            
    print("\n✅ 流程结束！")