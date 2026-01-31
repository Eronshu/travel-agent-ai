# backend/app/tools/search.py
import os
import requests
from dotenv import load_dotenv, find_dotenv

# --- 1. 关键修复：先加载环境变量，再初始化工具 ---
# 强制加载 .env (防止找不到 Key)
load_dotenv(find_dotenv(usecwd=True))

# 检查 Key 是否存在 (方便调试)
if not os.getenv("TAVILY_API_KEY"):
    print("❌ 错误: 未找到 TAVILY_API_KEY，请检查 .env 文件！")

# 尝试导入新版 Tavily (消灭黄色警告)
from langchain_tavily import TavilySearch
from app.tools.cache import cached_tool # 导入我们的缓存装饰器

# --- 2. 初始化工具 ---
# 只有在 load_dotenv 之后执行这一行，才能读到 Key
_tavily_client = TavilySearch(max_results=5)

@cached_tool(ttl_seconds=3600) # 缓存 1 小时
def search_tavily(query: str):
    """
    联网搜索工具 (带缓存)
    """
    try:
        # Tavily 返回的是列表，我们需要把它转成字符串给 LLM
        results = _tavily_client.invoke(query)
        content_list = []
        for res in results:
            content_list.append(f"- {res.get('content', '')} (来源: {res.get('url', '')})")
        return "\n".join(content_list)
    except Exception as e:
        return f"搜索失败: {str(e)}"

@cached_tool(ttl_seconds=1800) # 天气变动快，缓存 30 分钟
def get_weather(city: str):
    """
    查询天气 (优先 OpenWeather，失败则回退到 Tavily)
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    # 1. 尝试 OpenWeather
    if api_key:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                desc = data['weather'][0]['description']
                temp = data['main']['temp']
                return f"{city} 实时天气: {desc}, 温度: {temp}°C"
        except Exception as e:
            print(f"⚠️ OpenWeather 调用失败，切换到搜索模式: {e}")
    
    # 2. 回退方案：用 Tavily 搜
    return search_tavily(f"current weather in {city}")

# --- 测试代码 ---
if __name__ == "__main__":
    print("🔍 开始测试工具层...")
    
    print("\n--- Test 1: 第一次调用 (应该显示 [Cache Miss]) ---")
    # 搜一个冷门点的，防止你刚才搜过 Hamilton 已经在缓存里了
    print(get_weather("Banff, Alberta"))
    
    print("\n--- Test 2: 第二次调用 (应该显示 [Cache Hit]) ---")
    print(get_weather("Banff, Alberta"))