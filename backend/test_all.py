import os
import requests
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from pymilvus import MilvusClient

# 1. 加载环境变量
load_dotenv()

def print_result(name, success, message=""):
    """漂亮的打印函数"""
    icon = "✅" if success else "❌"
    print(f"{icon} [{name}]: {message}")

def test_gemini():
    """测试 Google Gemini API"""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        print_result("Gemini", False, "未找到 LLM_API_KEY")
        return

    try:
        # 使用 1.5-flash 模型，速度快
        llm = ChatGoogleGenerativeAI(
            model=os.getenv("LLM_MODEL_ID"),
            google_api_key=api_key
        )
        response = llm.invoke("Say 'Hello' in one word.")
        print_result("Gemini", True, f"响应成功: {response.content}")
    except Exception as e:
        print_result("Gemini", False, f"连接失败: {str(e)}")

def test_tavily():
    """测试 Tavily 搜索 API"""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        print_result("Tavily", False, "未找到 TAVILY_API_KEY")
        return

    try:
        tool = TavilySearchResults(tavily_api_key=api_key)
        # 搜一个简单的问题
        results = tool.invoke("What is the capital of Canada?")
        if len(results) > 0:
            print_result("Tavily", True, f"搜索成功，获取到 {len(results)} 条结果")
        else:
            print_result("Tavily", False, "连接成功但未返回结果")
    except Exception as e:
        print_result("Tavily", False, f"错误: {str(e)}")

def test_milvus():
    """测试 Milvus Lite 本地向量库"""
    uri = os.getenv("MILVUS_URI", "./travel_data.db")
    try:
        # 连接本地 Milvus (如果没有文件会自动创建)
        client = MilvusClient(uri=uri)
        # 尝试列出集合来验证连接
        collections = client.list_collections()
        print_result("Milvus Lite", True, f"本地数据库连接正常 (URI: {uri})")
    except Exception as e:
        print_result("Milvus Lite", False, f"无法创建/连接数据库: {str(e)}")

def test_openweather():
    """测试 OpenWeather API"""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        print("⚠️ [OpenWeather]: 跳过 (未配置 Key，我们将使用 Tavily 搜天气)")
        return

    try:
        # 构造一个简单的请求：查询伦敦天气
        url = f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            weather = data['weather'][0]['description']
            print_result("OpenWeather", True, f"API 响应正常: {weather}")
        elif response.status_code == 401:
            print_result("OpenWeather", False, "API Key 无效 (401 Unauthorized)")
        else:
            print_result("OpenWeather", False, f"状态码: {response.status_code}")
    except Exception as e:
        print_result("OpenWeather", False, f"请求失败: {str(e)}")

def test_langsmith():
    """检查 LangSmith 配置"""
    api_key = os.getenv("LANGSMITH_API_KEY")
    tracing = os.getenv("LANGSMITH_TRACING")
    
    if api_key and tracing == "true":
        print_result("LangSmith", True, "配置已加载 (请在运行 Agent 后去 smith.langchain.com 查看后台)")
    else:
        print("⚠️ [LangSmith]: 跳过 (未开启 Tracing，调试时可能看不到流程图)")

if __name__ == "__main__":
    print("------ 开始全栈环境自检 ------")
    test_gemini()
    test_tavily()
    test_milvus()
    test_openweather()
    test_langsmith()
    print("----------------------------")