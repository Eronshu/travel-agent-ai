# backend/app/agents/graph.py
from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.nodes import (
    extractor_node,
    weather_node,
    attraction_node,
    hotel_node,
    planner_node,
    critic_node
)

# 1. 初始化图
workflow = StateGraph(AgentState)

# 2. 添加节点 (也就是我们的 5 个 Agent + 1 个提取器)
workflow.add_node("extractor", extractor_node)       # 入口：意图识别
workflow.add_node("weather_agent", weather_node)     # 专家：天气
workflow.add_node("attraction_agent", attraction_node) # 专家：景点
workflow.add_node("hotel_agent", hotel_node)         # 专家：酒店
workflow.add_node("planner", planner_node)           # 核心：规划师
workflow.add_node("critic", critic_node)             # 核心：审核员

# 3. 定义边 (连接逻辑)

# [第一阶段] 入口 -> 提取 -> 并行分发
workflow.set_entry_point("extractor")

# 提取完信息后，同时把任务扔给三个专家 (Fan-out)
# LangGraph 中，只要添加多条边，它们就会并行运行！
workflow.add_edge("extractor", "weather_agent")
workflow.add_edge("extractor", "attraction_agent")
workflow.add_edge("extractor", "hotel_agent")

# [第二阶段] 专家 -> 规划师 (Fan-in)
# 三个专家干完活，都去向 Planner 汇报
workflow.add_edge("weather_agent", "planner")
workflow.add_edge("attraction_agent", "planner")
workflow.add_edge("hotel_agent", "planner")

# [第三阶段] 规划师 -> 审核员 -> (循环或结束)
workflow.add_edge("planner", "critic")

# 4. 定义条件边 (Conditional Edges)
# 审核员决定是 "PASS" 还是 "FAIL"
def critic_condition(state: AgentState):
    # 获取 Critic 的最新意见
    comment = state.get("critique_comments", "PASS")
    count = state.get("critique_count", 0)
    
    # 如果包含 FAIL 且重试次数不超过 3 次 -> 打回 Planner
    if "FAIL" in comment and count <= 3:
        print(f"🔄 [Loop] 审核未通过，打回重写 (第 {count} 次)...")
        return "planner"
    else:
        # 通过，或者重试太多次了，强制结束
        print("✅ [Finish] 流程结束")
        return END

# 把逻辑挂载到 Critic 节点上
workflow.add_conditional_edges(
    "critic",
    critic_condition,
    {
        "planner": "planner", # 对应上面的 return "planner"
        END: END              # 对应上面的 return END
    }
)

# 5. 编译图
# 这就是我们要导出的 App，之后前端就是调用它
graph = workflow.compile()