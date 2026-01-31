# 产品需求文档 (PRD) - AI 智能旅行助手 (Smart Travel Agent)

| 文档版本 | V1.0 (MVP 2.0) |
| :--- | :--- |
| **最后更新** | 2026-01-29 |
| **状态** | 开发中 |
| **作者** | [你的名字] |

---

## 1. 项目背景与目标 (Background & Goals)
本项目旨在开发一款基于 RAG (检索增强生成) 的智能旅行规划小程序。区别于传统的搜索工具，本产品利用 LLM 的语义理解能力和向量数据库的检索能力，为用户提供**高度个性化**、**结构化**且**可视化**的旅行方案。

**核心价值 (Value Proposition):**
1.  **深度个性化**：基于真实攻略数据，针对亲子、特种兵、穷游等不同需求定制行程。
2.  **地图可视化**：集成 Google Maps，将文字行程转化为可视化路线。
3.  **动态交互**：支持基于对话记忆 (Memory) 的多轮调整。

---

## 2. 用户画像 (User Persona)
* **目标用户**：自由行爱好者、不想花费大量时间查阅攻略的游客。
* **典型场景**：用户计划去巴黎玩 3 天，带有 5 岁儿童，希望行程轻松且包含迪士尼，预算中等。

---

## 3. 功能需求 (Functional Requirements)

### 3.1 用户输入与偏好采集 (User Input)
前端需提供多维度表单，支持以下标签选择：
* **目的地 (Destination)**: 文本输入 (e.g., "Tokyo")
* **旅行天数 (Duration)**: 数字选择 (1-14天)
* **旅行节奏 (Pace)**:
    * 特种兵 (High Intensity)
    * City Walk (Moderate)
    * 休闲度假 (Relaxed)
* **出行伙伴 (Company)**:
    * 独自 (Solo)
    * 情侣 (Couple)
    * 亲子 (Family with kids) - *需过滤不适合儿童的场所*
    * 长辈 (With parents) - *需减少步行距离*
* **预算偏好 (Budget)**: 穷游 / 舒适 / 奢华
* **其他需求 (Free text)**: 文本框 (e.g., "海鲜过敏", "必须去秋叶原")

### 3.2 智能行程生成 (Core AI Features)
* **RAG 检索**:
    * 系统需根据用户选择的标签（如"亲子"），在向量数据库中过滤 (Metadata Filter) 相关攻略。
* **结构化输出**:
    * LLM 必须输出标准的 JSON 格式，而非纯文本，以便前端渲染。
* **流式响应 (Streaming)**:
    * 通过 WebSocket 或 SSE (Server-Sent Events) 实现打字机效果，减少用户等待焦虑。
* **对话记忆 (Memory)**:
    * 系统需记录当前的行程版本和用户的修改意见，支持“把第二天下午换成购物”这类指令。

### 3.3 地图与数据集成 (Map & Integration)
* **Google Places API 集成**:
    * 后端需解析 LLM 生成的地点名称，调用 Google API 获取：
        * 精确经纬度 (Lat/Lng)
        * 营业时间 (Opening Hours)
        * 评分 (Rating)
        * 图片引用 (Photo Reference)
* **可视化渲染**:
    * 在地图上为不同日期的行程绘制不同颜色的折线 (Polyline)。
    * 点击 Marker 显示详情卡片（含 Google Maps 跳转链接）。

---

## 4. 技术架构 (Technical Architecture)

### 4.1 技术栈
* **前端**: 小程序 / Flutter / React (Web)
* **后端**: Python FastAPI (支持 Async/Await 高并发)
* **大模型**: OpenAI GPT-4o 或 gpt-3.5-turbo
* **向量数据库**: Milvus 或 Chroma
* **编排框架**: LangChain / LangGraph
* **外部 API**: Google Maps Platform (Places API)

### 4.2 数据流向 (Data Flow)
1.  **User** 提交表单 -> **Backend** 接收请求。
2.  **Backend** 将用户偏好转化为 Embedding -> **Vector DB** 检索相关攻略。
3.  **Backend** 组装 Prompt (Prompt + Docs + Format Instructions) -> **LLM**。
4.  **LLM** 生成初步 JSON (含地点名)。
5.  **Backend** 解析 JSON，并发调用 **Google Maps API** 填充经纬度与详情。
6.  **Backend** 将最终 JSON 流式推送到 **Frontend**。
7.  **Frontend** 渲染文本与地图。

---

## 5. 数据结构定义 (Data Schema)

后端返回给前端的核心 JSON 结构：

```json
{
  "trip_title": "东京亲子三日游",
  "summary": "这是一次轻松的旅程，重点体验东京的动漫文化与历史...",
  "days": [
    {
      "day_index": 1,
      "date": "2026-02-01",
      "theme": "历史与文化",
      "color_hex": "#FF5733",
      "route_points": [
        {
          "order": 1,
          "place_name": "浅草寺",
          "type": "sight",
          "description": "东京最古老的寺庙，体验江户风情。",
          "google_data": {
             "place_id": "ChIJ...",
             "lat": 35.7147,
             "lng": 139.7967,
             "rating": 4.5,
             "open_now": true,
             "map_url": "[https://maps.google.com/](https://maps.google.com/)...",
             "photo_url": "https://..." 
          }
        }
      ]
    }
  ]
}
## 6. 开发里程碑 (Milestones)
Phase 1: 数据基建 (Data Foundation)

[ ] 编写爬虫 (Firecrawl/Jina Reader) 抓取 50+ 篇高质量攻略。

[ ] 数据清洗与切分 (MarkdownHeaderTextSplitter)。

[ ] 向量化入库，并添加 Metadata (City, Tags)。

Phase 2: 后端核心逻辑 (Backend Core)

[ ] 搭建 FastAPI 项目框架。

[ ] 实现 RAG 检索工具 (带 Filter 功能)。

[ ] 实现 Pydantic Output Parser，强制 LLM 输出 JSON。

Phase 3: 地图服务对接 (Map Integration)

[ ] 申请 Google Maps API Key。

[ ] 编写 Python 服务，实现“地点名 -> 经纬度”的自动补全逻辑。

Phase 4: 前端交互与记忆 (UI & Memory)

[ ] 实现地图 SDK 接入与画线逻辑。

[ ] 引入 LangChain Memory，实现多轮对话修改行程。


---

### 给你的建议：
1.  **保存位置**：将此文件命名为 `README.md` 或 `PRD.md`，放在你 GitHub 项目的根目录下。
2.  **简历加分**：在你的简历项目描述中，附上 GitHub 链接。面试官点进去，第一眼看到这样专业的文档，会对你的好感度倍增。
3.  **实时更新**：开发过程中如果有了新想法，随时回来修改这个文档，保持文档和代码的一致性。