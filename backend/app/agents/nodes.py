# backend/app/agents/nodes.py
import os
import json
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# 1. 导入数据模型 (Schema)
from app.models.schemas import TripRequest

# 2. 导入状态定义 (State)
from app.agents.state import AgentState

# 3. 导入 MCP 服务 (这是唯一的工具来源)
from app.services.mcp import mcp_service

# ==========================================
# 初始化配置
# ==========================================

# 1. 准备大脑 (LLM)
llm = ChatGoogleGenerativeAI(
    model=os.getenv("LLM_MODEL_ID", "gemini-1.5-flash"),
    temperature=0,
    google_api_key=os.getenv("LLM_API_KEY")
)

# 2. 准备工具箱 (从 MCP 服务获取)
# 我们把工具列表转换成字典，方便通过名字调用: tools_map['get_weather']
tools = mcp_service.get_tools()
tools_map = {t.name: t for t in tools}

print(f"🔧 [Nodes] 已连接 MCP 服务，可用工具: {list(tools_map.keys())}")

# ==========================================
# 节点 1: 意图提取 (Extractor)
# ==========================================
def extractor_node(state: AgentState):
    """
    入口节点：把用户的自然语言转成结构化的 TripRequest
    """
    last_msg = state['messages'][-1].content
    print(f"👂 [Extractor] 分析用户需求: {last_msg}")
    
    prompt = f"""
    请从用户的话中提取：目的地(city)、日期(date_range)、兴趣(interests)。
    返回 JSON 格式，例如: {{"city": "Paris", "date_range": "3 days", "interests": "food"}}
    用户输入: {last_msg}
    """
    
    try:
        response = llm.invoke(prompt)
        # 清洗 JSON (去掉 Markdown 标记)
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        
        # 构造 Pydantic 模型
        request = TripRequest(
            city=data.get("city", "Hamilton"), # 默认值容错
            days=3,
            date_range=data.get("date_range", "近期"),
            interests=data.get("interests", "当地特色")
        )
        return {"request": request}
    except Exception as e:
        print(f"⚠️ 解析失败，使用默认参数: {e}")
        return {"request": TripRequest(city="Hamilton", days=3, date_range="近期", interests="General")}

# ==========================================
# 节点 2: 天气专家 (Weather Agent)
# ==========================================
def weather_node(state: AgentState):
    request = state['request']
    print(f"🌤️ [WeatherAgent] 正在调用 MCP 工具查询 {request.city} 天气...")
    
    # --- MCP 标准化调用 ---
    # 我们不关心 get_weather 内部是 OpenWeather 还是 Yahoo，直接调
    try:
        tool = tools_map["get_weather"]
        result = tool.invoke({"city": request.city})
    except Exception as e:
        result = f"查询错误: {e}"
        
    return {"weather_info": str(result)}

# ==========================================
# 节点 3: 景点专家 (Attraction Agent)
# ==========================================
def attraction_node(state: AgentState):
    request = state['request']
    print(f"🏰 [AttractionAgent] 正在调用 MCP 工具搜索 {request.interests}...")
    
    # 1. 调用 RAG 工具 (独家数据)
    try:
        rag_tool = tools_map["search_local_guide"]
        rag_query = f"{request.city} {request.interests}"
        rag_data = rag_tool.invoke(rag_query)
    except Exception as e:
        rag_data = "暂无本地独家情报"

    # 2. 调用联网搜索工具 (补充数据)
    try:
        web_tool = tools_map["search_tavily"]
        web_query = f"top tourist attractions in {request.city} for {request.interests}"
        web_data = web_tool.invoke(web_query)
    except Exception as e:
        web_data = "网络搜索失败"
    
    summary = f"【独家本地情报】\n{rag_data}\n\n【网络热门推荐】\n{web_data}"
    return {"attractions_info": summary}

# ==========================================
# 节点 4: 酒店专家 (Hotel Agent)
# ==========================================
def hotel_node(state: AgentState):
    request = state['request']
    print(f"🏨 [HotelAgent] 正在调用 MCP 工具查询酒店...")
    
    try:
        tool = tools_map["search_tavily"]
        query = f"recommended hotels in {request.city} safe area price range mid"
        result = tool.invoke(query)
    except Exception as e:
        result = "酒店查询失败"
        
    return {"hotels_info": str(result)}

# ==========================================
# 节点 5: 总规划师 (Planner Agent)
# ==========================================
def planner_node(state: AgentState):
    print("📝 [PlannerAgent] 正在撰写行程草稿...")
    
    # 汇总上下文
    context = f"""
    【用户需求】
    目的地: {state['request'].city}
    日期: {state['request'].date_range}
    偏好: {state['request'].interests}
    
    【情报汇总】
    1. 天气: {state.get('weather_info')}
    2. 景点: {state.get('attractions_info')}
    3. 酒店: {state.get('hotels_info')}
    
    【审核历史】
    {state.get('critique_comments', '无')}
    """
    
    prompt = f"""
    你是专业的旅行规划师。请根据上述情报，生成一份详细的旅行计划。
    
    要求：
    1. 逻辑自洽：根据天气安排活动（如下雨则安排室内）。
    2. 深度体验：**必须**优先包含【独家本地情报】中的推荐。
    3. 完整性：必须包含推荐的酒店。
    4. 修正：如果【审核历史】中有批评意见，必须针对性修改。
    
    请直接输出行程内容，不要有多余的寒暄。
    """
    
    response = llm.invoke([SystemMessage(content=context), HumanMessage(content=prompt)])
    return {"draft_plan": response.content}

# ==========================================
# 节点 6: 审核员 (Critic Agent)
# ==========================================
def critic_node(state: AgentState):
    print("🧐 [CriticAgent] 正在审核行程...")
    
    plan = state.get('draft_plan', "")
    
    prompt = f"""
    请审核以下旅行计划。
    
    核心检查点：
    1. 是否包含“独家本地情报”里的景点？(若全是大众景点 -> FAIL)
    2. 是否安排了具体的酒店？(若无 -> FAIL)
    3. 天气逻辑是否合理？
    
    如果通过，请仅回复 "PASS"。
    如果不通过，请回复 "FAIL: [具体原因]"。
    
    计划内容：
    {plan}
    """
    
    response = llm.invoke(prompt)
    comment = response.content.strip()
    
    if "FAIL" in comment:
        print(f"❌ [Critic] 驳回: {comment}")
        return {
            "critique_comments": comment,
            "critique_count": state.get("critique_count", 0) + 1
        }
    else:
        print("✅ [Critic] 通过")
        return {
            "critique_comments": "PASS",
            # 在真实项目中，这里会调用 Structured Output 转成 TripPlan 对象
            # 这里简化处理，直接结束
        }