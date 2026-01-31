# backend/app/agents/state.py
import operator
from typing import Annotated, TypedDict, List, Optional
from langgraph.graph.message import add_messages
from app.models.schemas import TripRequest, TripPlan

class AgentState(TypedDict):
    """
    智能体的状态（共享内存）
    """
    # 1. 聊天记录 (所有人都能看到历史对话)
    # add_messages 表示新消息会追加到列表中，而不是覆盖
    messages: Annotated[list, add_messages]
    
    # 2. 用户需求 (从前端传来)
    request: TripRequest
    
    # 3. 各路专家的调查结果 (结构化数据)
    # 这些字段会被景点、天气、酒店 Agent 并行填充
    weather_info: Optional[str]
    attractions_info: Optional[str]
    hotels_info: Optional[str]
    
    # 4. 规划师生成的初稿
    draft_plan: Optional[str]
    
    # 5. 审核员的意见
    critique_comments: Optional[str]
    critique_count: int # 记录审核了几次，防止死循环
    
    # 6. 最终成品
    final_plan: Optional[TripPlan]