# backend/app/services/mcp.py
from langchain_core.tools import StructuredTool

# 导入底层的“工人”
from app.tools.search import search_tavily, get_weather
from app.rag.retriever import search_knowledge_base

class MCPService:
    """
    MCP 服务层：负责将底层工具统一包装并暴露给 Agent
    """
    def __init__(self):
        self._tools = []
        self._initialize_registry()

    def _initialize_registry(self):
        """
        在这里进行“注册”。
        我们将普通的 Python 函数转换为 AI 可调用的 Tool 对象。
        """
        # 1. 注册天气工具
        # StructuredTool.from_function 会自动读取函数的 docstring 作为工具说明
        self._tools.append(StructuredTool.from_function(get_weather))

        # 2. 注册搜索工具
        self._tools.append(StructuredTool.from_function(search_tavily))

        # 3. 注册 RAG 工具 (给它起个好听的名字让 AI 容易懂)
        self._tools.append(StructuredTool.from_function(
            func=search_knowledge_base,
            name="search_local_guide",
            description="查询本地独家旅行知识库。当用户询问推荐、隐秘景点或避雷指南时必须使用此工具。"
        ))
        
        print(f"🔌 [MCP Service] 已加载 {len(self._tools)} 个工具")

    def get_tools(self):
        """供 Agent 调用，获取所有工具列表"""
        return self._tools

# 单例模式：整个应用共用一个服务实例
mcp_service = MCPService()