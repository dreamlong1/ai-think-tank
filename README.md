# AI 智囊团 (AI Think Tank)

> 基于 LangGraph 的动态多代理决策系统 · 群聊交互式体验

本项目是一个多代理(Multi-Agent)协作系统，旨在模拟一个专业的智囊团讨论过程。用户提出一个问题，系统会自动识别该领域并召集 3-6 位各具背景的虚拟专家进行异步并发讨论，最后由分析师汇总给出综合分析报告。

## 🌟 核心亮点

- **动态多代理编排**: 使用 `LangGraph` 的 `StateGraph` 和 `Send` API 实现运行时的动态并发 (Fan-Out) 和结果聚合 (Reduce)。
- **结构化输出 (Structured Output)**: 全链路使用 Pydantic 进行类型校验，确保 LLM 输出高可靠的 JSON 数据。
- **SSE 推送**: 后端使用 FastAPI 的 `EventSourceResponse` 实时的流式消息推送，模拟真实的社交消息体验。
- **沉浸式群聊 UI**: 前端采用 React 构建现代化的群聊界面，具有打字动画、专家角色头像和分组件渲染功能。

## 📂 项目结构

- `backend/`: 基于 FastAPI + LangGraph 的异步后端服务。
- `frontend/`: 基于 React + Vite 的响应式网页前端。
- `ai_think_tank_plan.md`: 详细的项目实施方案和架构设计。

## 🚀 快速启动

详见各目录下的 `README.md` 或参考 [详细实施方案](ai_think_tank_plan.md)。

### 后端

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 📜 许可

本项目仅供学习参考。
