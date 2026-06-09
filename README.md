# InkSpark 创作助手

基于 **Redis 任务队列 + CrewAI 多 Agent + FastAPI 编排层** 的分布式 AI 文章创作系统。用户通过 Web UI 提交创作需求，系统按「调研 → 大纲 → 逐节撰写 → 审核」四阶段流水线协作生成文章，每步支持人工确认或修改后再继续。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3、Vite、Tailwind CSS、Pinia、SSE |
| Web API | FastAPI、Pydantic、Uvicorn、sse-starlette |
| 编排 & 状态 | Redis（Hash / List / PubSub）、threading |
| Worker | CrewAI、LangChain OpenAI（通义千问）、Serper 搜索 |
| 通信 | REST + SSE（前端）、Redis 队列（API ↔ Worker）、gRPC（可选上报） |

## 系统架构

```
Browser (Vue 3)  ←→  REST + SSE  ←→  FastAPI Orchestrator (web/backend)
                                              ↕ Redis Queue + State
                                       Worker (main.py + CrewAI Agents)
```

- **Worker**（`main.py`）— 消费 `tasks:default` 队列，执行 CrewAI Agent 任务，结果写入 `task:{id}:state`
- **Web API**（`web/backend/`）— 会话编排、步骤状态管理、SSE 实时推送、用户交互 REST 接口
- **Frontend**（`web/frontend/`）— InkSpark 风格 UI，左侧步骤卡片 + 右侧 Markdown 预览

详细设计见 [docs/inkspark-design.md](docs/inkspark-design.md)  
**面试技术 QA** 见 [docs/backend-interview-qa.md](docs/backend-interview-qa.md)

## 快速启动

### 1. 创建 Conda 环境

```bash
conda env create -f environment.yml
conda activate inkspark
```

或手动创建：

```bash
conda create -n inkspark python=3.11 -y
conda activate inkspark
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
copy .env.example .env
```

编辑 `.env`，填入：

| 变量 | 说明 |
|------|------|
| `DASHSCOPE_API_KEY` | 阿里云 DashScope（通义千问） |
| `SERPER_API_KEY` | Serper 网络搜索 |
| `WEB_HOST` / `WEB_PORT` | API 监听地址（默认 `0.0.0.0:5000`） |

### 3. 启动 Redis

确保 Redis 运行在 `localhost:6379`：

```bash
redis-cli ping   # 应返回 PONG
```

### 4. 启动三个进程

```bash
# 终端 1：Worker
conda activate inkspark
python main.py

# 终端 2：Web API
conda activate inkspark
python web/backend/main.py

# 终端 3：Frontend
cd web/frontend
npm install
npm run dev
```

### 5. 访问

打开 http://localhost:5173

## 目录结构

```
project5_2/
├── docs/
│   ├── inkspark-design.md       # 系统设计文档
│   └── backend-interview-qa.md  # 后端面试技术 QA
├── web/
│   ├── backend/                 # FastAPI 编排层
│   │   ├── main.py              # 入口
│   │   ├── orchestrator.py      # 工作流编排
│   │   ├── redis_store.py       # 会话 & 任务 Redis 封装
│   │   ├── models.py            # Pydantic 模型
│   │   └── routes/              # REST & SSE 路由
│   └── frontend/                # Vue 3 前端
├── src/                         # Worker 运行时
├── extend/                      # 分布式组件（队列、锁、重试、gRPC）
├── config/                      # CrewAI Agent/Task YAML 配置
├── main.py                      # Worker 入口
└── requirements.txt
```

## API 概览

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/conversations` | 创建会话 |
| POST | `/api/conversations/{id}/start` | 启动创作流程 |
| GET | `/api/conversations/{id}/stream` | SSE 事件流 |
| GET | `/api/conversations/{id}/steps` | 获取步骤列表 |
| GET | `/api/conversations/{id}/artifacts/{step_id}` | 获取步骤产出 |
| POST | `/api/conversations/{id}/actions` | 用户确认/修改/取消 |
| GET | `/api/conversations/{id}/export` | 导出 Markdown |
| GET | `/api/health` | 健康检查 |

## 创作流水线

| 阶段 | Agent | 用户交互 |
|------|-------|----------|
| research | 小美（调研） | 选择写作角度 |
| outline | 小青（大纲） | 确认或修改大纲 |
| section | 小青（撰写） | 每节确认或重写 |
| review | 小尹（审核） | 确认并导出 |

## 常见问题

| 问题 | 处理 |
|------|------|
| Redis 连接失败 | 确认 Redis 已启动：`redis-cli ping` |
| Worker 无响应 | 检查 `main.py` 是否在运行，队列名是否为 `tasks:default` |
| 前端无法连 API | 确认 FastAPI 在 `:5000` 运行，Vite proxy 配置正确 |
| CrewAI 导入错误 | 确认 `conda activate inkspark` 且 Python 3.11 |

## 文档索引

- [系统设计文档](docs/inkspark-design.md) — 架构、数据模型、API 契约、验收标准
- [后端面试 QA](docs/backend-interview-qa.md) — 面向后端岗位的技术问答梳理


## 演示



https://github.com/user-attachments/assets/7e77a75b-b959-4681-a184-18bc94775fb8


