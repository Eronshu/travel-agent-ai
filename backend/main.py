# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # 👈 引入 CORS 中间件
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv, find_dotenv

# 导入我们的图
from app.agents.graph import graph

load_dotenv(find_dotenv(usecwd=True))

app = FastAPI(title="Travel Agent AI", version="1.0")

# ==========================================
# 🛡️ 核心修复：配置 CORS (允许前端访问)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    # 允许的来源：生产环境要写具体域名，开发环境用 "*" (允许所有)
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], # 允许所有方法 (POST, GET...)
    allow_headers=["*"], # 允许所有 Header
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Travel Agent Backend is Running!"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    print(f"📨 收到前端请求: {req.message}")
    
    initial_state = {
        "messages": [HumanMessage(content=req.message)]
    }
    
    try:
        # 运行 Graph
        final_state = graph.invoke(initial_state)
        
        # 提取结果
        response_text = final_state.get("draft_plan", "生成失败")
        # 如果有 critique_comments 且不是 PASS，说明最后还在纠结，但也返回出来
        
        return {
            "reply": response_text,
            "details": {
                "weather": final_state.get("weather_info"),
                "attractions": final_state.get("attractions_info"),
                "critique": final_state.get("critique_comments")
            }
        }
        
    except Exception as e:
        print(f"❌ 后端处理出错: {e}")
        # 返回 500 错误给前端
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)