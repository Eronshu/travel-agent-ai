// frontend/src/App.jsx
import { useState, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import DatePicker from 'react-datepicker'
import { Country, State, City } from 'country-state-city' // 📦 地理数据
import { format } from 'date-fns' // 📅 日期格式化
import "react-datepicker/dist/react-datepicker.css" // 引入日历样式
import './App.css'

function App() {
  // --- 1. 结构化表单状态 ---
  const [selectedCountry, setSelectedCountry] = useState(null)
  const [selectedState, setSelectedState] = useState(null)
  const [selectedCity, setSelectedCity] = useState(null)
  const [dateRange, setDateRange] = useState([null, null])
  const [startDate, endDate] = dateRange
  const [interests, setInterests] = useState('') // 兴趣还是保留文本框

  // --- 2. 聊天与UI状态 ---
  const [messages, setMessages] = useState([
    { role: 'ai', content: '👋 你好！请在下方选择你的目的地和时间，我会为你规划行程。' }
  ])
  const [loading, setLoading] = useState(false)
  const [debugInfo, setDebugInfo] = useState(null)

  // --- 3. 处理地理数据 (只保留美国和加拿大) ---
  // Country.getAllCountries() 会返回几百个，我们过滤一下 ISO Code
  const countries = Country.getAllCountries().filter(c => ['US', 'CA'].includes(c.isoCode))
  
  // 根据选中的国家，获取省份列表
  const states = selectedCountry ? State.getStatesOfCountry(selectedCountry.isoCode) : []
  
  // 根据选中的省份，获取城市列表
  const cities = selectedState ? City.getCitiesOfState(selectedCountry.isoCode, selectedState.isoCode) : []

  // --- 4. 发送逻辑 (Prompt Engineering on Frontend) ---
  const handleGenerate = async () => {
    // 校验：必须选完城市和日期
    if (!selectedCity || !startDate || !endDate) {
      alert("请完整选择目的地和旅行日期！")
      return
    }

    setLoading(true)
    setDebugInfo(null)

    // 💡 关键技巧：把结构化数据拼装成自然语言发给后端
    // 这样后端 Agent 依然能读懂，而且极度精准
    const formattedStart = format(startDate, 'yyyy-MM-dd')
    const formattedEnd = format(endDate, 'yyyy-MM-dd')
    const locationStr = `${selectedCity.name}, ${selectedState.name}, ${selectedCountry.name}`
    
    // 构造 Prompt
    const userPrompt = `我想去 ${locationStr} 玩。
    时间是 ${formattedStart} 到 ${formattedEnd}。
    我的兴趣偏好是：${interests || '大众热门景点'}。
    请帮我规划行程。`

    // 显示用户消息
    const displayMsg = `📅 计划：${formattedStart} 至 ${formattedEnd} \n📍 目的地：${locationStr} \n❤️ 偏好：${interests || '无'}`
    setMessages(prev => [...prev, { role: 'user', content: displayMsg }])

    try {
      const response = await axios.post('http://localhost:8000/chat', {
        message: userPrompt
      })

      const aiMsg = { role: 'ai', content: response.data.reply }
      setMessages(prev => [...prev, aiMsg])
      setDebugInfo(response.data.details)

    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { role: 'ai', content: '❌ 请求失败，请检查后端。' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      {/* --- 左侧：配置面板 (新功能) --- */}
      <div className="config-panel">
        <h2>✈️ 行程配置</h2>
        
        <div className="form-group">
          <label>1. 选择国家</label>
          <select 
            onChange={(e) => {
              const c = countries.find(x => x.isoCode === e.target.value)
              setSelectedCountry(c)
              setSelectedState(null) // 重置下级
              setSelectedCity(null)
            }}
            value={selectedCountry?.isoCode || ''}
          >
            <option value="">-- 请选择 --</option>
            {countries.map(c => (
              <option key={c.isoCode} value={c.isoCode}>{c.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>2. 选择省/州</label>
          <select 
            disabled={!selectedCountry}
            onChange={(e) => {
              const s = states.find(x => x.isoCode === e.target.value)
              setSelectedState(s)
              setSelectedCity(null)
            }}
            value={selectedState?.isoCode || ''}
          >
            <option value="">-- 请选择 --</option>
            {states.map(s => (
              <option key={s.isoCode} value={s.isoCode}>{s.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>3. 选择城市</label>
          <select 
            disabled={!selectedState}
            onChange={(e) => setSelectedCity(cities.find(x => x.name === e.target.value))}
            value={selectedCity?.name || ''}
          >
            <option value="">-- 请选择 --</option>
            {cities.map(c => (
              <option key={c.name} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>4. 选择日期 (范围)</label>
          <DatePicker
            selectsRange={true}
            startDate={startDate}
            endDate={endDate}
            onChange={(update) => setDateRange(update)}
            placeholderText="点击选择起止日期"
            className="date-input"
            dateFormat="yyyy/MM/dd"
          />
        </div>

        <div className="form-group">
          <label>5. 兴趣偏好 (可选)</label>
          <input 
            type="text" 
            placeholder="例如：自然风光, 博物馆, 墨西哥菜..."
            value={interests}
            onChange={e => setInterests(e.target.value)}
          />
        </div>

        <button 
          className="generate-btn" 
          onClick={handleGenerate} 
          disabled={loading}
        >
          {loading ? '规划中...' : '🚀 生成行程'}
        </button>
      </div>

      {/* --- 中间：聊天展示区 --- */}
      <div className="chat-box">
        <header>
          <h1>Travel Agent AI</h1>
          <p>LangGraph x RAG x React</p>
        </header>

        <div className="messages-area">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.role}`}>
              <div className="bubble">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          ))}
          {loading && <div className="message ai"><div className="bubble">Thinking... (各个 Agent 正在吵架中...)</div></div>}
        </div>
      </div>

      {/* --- 右侧：Debug 面板 --- */}
      {debugInfo && (
        <div className="debug-panel">
          <h3>🧠 Agent 思考过程</h3>
          <div className="debug-item">
            <h4>🌤️ 天气情报</h4>
            <p>{debugInfo.weather || '未调用'}</p>
          </div>
          <div className="debug-item">
            <h4>🏰 景点/RAG情报</h4>
            <p>{debugInfo.attractions || '未调用'}</p>
          </div>
          <div className="debug-item fail">
            <h4>🧐 Critic 审核意见</h4>
            <p>{debugInfo.critique || '无意见'}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default App