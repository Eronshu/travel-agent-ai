# backend/app/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# --- 1. 基础组件 ---
class Location(BaseModel):
    """位置信息(经纬度坐标)"""
    longitude: float = Field(..., description="经度", ge=-180, le=180)
    latitude: float = Field(..., description="纬度", ge=-90, le=90)

# --- 2. 实体模型 (景点/酒店/餐饮) ---
class Attraction(BaseModel):
    """景点信息"""
    name: str = Field(..., description="景点名称")
    description: str = Field(..., description="景点描述")
    address: Optional[str] = Field(None, description="地址")
    # 注意：为了简化，有些字段设为 Optional，防止 AI 搜不到报错
    location: Optional[Location] = Field(None, description="经纬度坐标")
    visit_duration: int = Field(default=60, description="建议游览时间(分钟)")
    ticket_price: int = Field(default=0, description="门票价格(元)")
    image_url: Optional[str] = Field(None, description="图片URL")

class Hotel(BaseModel):
    """酒店信息"""
    name: str = Field(..., description="酒店名称")
    description: Optional[str] = Field(None, description="描述")
    address: Optional[str] = Field(None, description="地址")
    price_range: str = Field(default="中等", description="价格范围")
    rating: Optional[str] = Field(None, description="评分")

class Meal(BaseModel):
    """餐饮信息"""
    name: str = Field(..., description="餐饮名称")
    type: str = Field(..., description="类型：早餐/午餐/晚餐")
    description: Optional[str] = Field(None, description="推荐理由")

# --- 3. 辅助信息 (天气/预算) ---
class WeatherInfo(BaseModel):
    """天气信息"""
    date: str = Field(..., description="日期")
    condition: str = Field(..., description="天气状况")
    temp: str = Field(..., description="温度范围")

class Budget(BaseModel):
    """预算明细"""
    total: int = Field(..., description="总费用")
    breakdown: str = Field(..., description="费用明细描述")

# --- 4. 核心行程模型 ---
class DayPlan(BaseModel):
    """单日行程"""
    day_index: int = Field(..., description="第几天")
    date: str = Field(..., description="日期")
    city: str = Field(..., description="城市")
    weather: Optional[WeatherInfo] = Field(None, description="当日天气")
    attractions: List[Attraction] = Field(default_factory=list, description="游玩景点")
    meals: List[Meal] = Field(default_factory=list, description="餐饮安排")
    hotel: Optional[Hotel] = Field(None, description="住宿安排")
    daily_summary: str = Field(..., description="当日行程小结")

class TripPlan(BaseModel):
    """最终生成的完整旅行计划"""
    city: str = Field(..., description="目的地")
    duration: int = Field(..., description="天数")
    days: List[DayPlan] = Field(..., description="每日详情")
    total_budget: Optional[Budget] = Field(None, description="总预算预估")
    summary: str = Field(..., description="整趟旅程的总结建议")

# --- 5. 前端请求模型 ---
class TripRequest(BaseModel):
    """前端传过来的用户需求"""
    city: str = Field(..., description="想去哪里")
    days: int = Field(3, description="玩几天")
    interests: Optional[str] = Field(None, description="兴趣偏好 (如: 户外, 历史, 美食)")
    date_range: Optional[str] = Field(None, description="具体日期")