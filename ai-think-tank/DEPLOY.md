# 部署说明

## 目录结构

这个项目采用前后端分离部署：

- `backend`：FastAPI + LangGraph
- `frontend`：React + Vite，生产环境由 Nginx 托管
- `frontend/nginx.conf`：负责把 `/api/` 反向代理到后端

## 环境变量

后端默认支持两种推理模式：

- 配置了 `OPENAI_API_KEY` 时，优先走 OpenAI API
- 没有配置 `OPENAI_API_KEY` 时，自动回退到本地 `codex` CLI

建议至少配置以下环境变量：

```bash
OPENAI_API_KEY=你的key
OPENAI_API_BASE=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
CODEX_CLI_PATH=codex.cmd
CODEX_MODEL_NAME=
MODEL_TIMEOUT_SECONDS=90
```

如果不打算接 OpenAI，可把 `OPENAI_API_KEY` 留空，系统会尝试使用本地 `codex` CLI。
注意：容器化部署里如果要走这条回退链路，需要确保镜像里也能调用到 `codex` CLI。

## 本地启动

先启动后端：

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

再启动前端开发模式：

```bash
cd frontend
npm install
npm run dev
```

开发模式下，前端代码里默认请求 `http://localhost:8000`，适合本地联调。
开发环境同时在 Vite 里配置了 `/api` 代理，所以也可以直接通过同源路径访问后端。

## Docker Compose 启动

在项目根目录执行：

```bash
docker compose up --build
```

启动后访问：

- 前端：`http://localhost:8000`
- 后端：通过前端同源路径 `http://localhost:8000/api/...`

## 设计说明

- 前端生产环境使用 Nginx 托管静态文件。
- 所有 `/api/` 请求由 Nginx 反向代理到 `backend:8000`。
- 前端容器对外监听 `8000`，浏览器通过同源路径 `/api/...` 访问后端。
- SSE 流式接口使用了 `proxy_buffering off`，避免事件被缓存后一次性返回。
- 生产部署不需要额外的 Node 运行时，前端镜像构建完成后只保留 Nginx。
