# TVAiPlatform 开发规范说明

## 项目简介

TVAiPlatform 是一个 AI 短剧生成平台，支持从剧本编写、角色设计、分镜板到视频合成的全流程自动化。

## 项目结构

```
TVAiPlatform/
├── api/                    # 后端 FastAPI 应用
│   ├── config.py           # 配置管理 (pydantic-settings)
│   ├── main.py             # FastAPI 入口
│   ├── models/             # SQLAlchemy 数据模型
│   ├── routers/            # API 路由
│   ├── services/           # 业务逻辑服务
│   ├── workflows/          # Dify 工作流
│   ├── json_templates/     # 内置 JSON 模板
│   └── requirements.txt    # Python 依赖
├── web/                    # 前端 Vue 3 应用
│   ├── src/
│   │   ├── api/            # API 调用封装
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   └── router/         # 路由配置
│   ├── package.json
│   └── vite.config.ts
├── tts/                    # TTS 服务
│   ├── chattts_server.py   # ChatTTS FastAPI 服务器 (端口 8090)
│   └── requirements.txt
├── scripts/                # 运维脚本
│   ├── start_all.sh        # 一键启动
│   ├── stop_all.sh         # 一键停止
│   ├── init_db.py          # 数据库初始化
│   ├── init_templates.py   # 模板初始化
│   ├── check_versions.py   # 版本检查
│   ├── cleanup_temp.sh     # 临时文件清理
│   └── batch_export.py     # 批量导出
├── config.yaml             # 应用配置
├── .env                    # 环境变量（不入库）
├── supervisord.conf        # Supervisor 进程管理
├── SHARED_CONTRACT.md      # 共享开发合约
└── docs/
```

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL 17, Redis 7 |
| 前端 | Vue 3, TypeScript, Pinia, Vite, Element Plus |
| TTS | ChatTTS (自建 FastAPI 服务) / Edge-TTS / ElevenLabs |
| 图像 | ComfyUI |
| 编排 | Dify (AI 工作流) |
| 进程管理 | Supervisor |

## 开发约定

### 代码规范
- **Python**: 使用 `ruff` 格式化，类型注解全部使用 `from __future__ import annotations`
- **TypeScript**: 使用 ESLint + Prettier
- **提交信息**: 使用 Conventional Commits (`feat:`, `fix:`, `docs:` 等)

### 数据库
- 所有表使用 UUID 主键
- 时间字段统一使用 UTC
- JSONB 字段用于灵活的结构化数据
- 使用 SQLAlchemy 2.0 异步风格

### API
- 统一响应格式: `{ code: 0, message: "success", data: ... }`
- 路由前缀: `/api/`
- 错误码: `0` = 成功，非零 = 错误

### 环境变量
- 敏感信息通过 `.env` 管理
- `config.yaml` 中的 `${VAR}` 占位符会被环境变量替换

## 快速开始

### 1. 环境检查
```bash
python scripts/check_versions.py
```

### 2. 安装依赖
```bash
# 后端
cd api && pip install -r requirements.txt

# 前端
cd web && pnpm install

# TTS
cd tts && pip install -r requirements.txt
```

### 3. 初始化
```bash
# 初始化数据库
python scripts/init_db.py

# 初始化内置模板
python scripts/init_templates.py
```

### 4. 启动服务
```bash
# 一键启动
bash scripts/start_all.sh

# 或使用 Supervisor
supervisord -c supervisord.conf
```

### 5. 访问
- **API**: http://localhost:8000
- **Web**: http://localhost:3100
- **ChatTTS**: http://localhost:8090
- **API 文档**: http://localhost:8000/docs

## 生产部署

使用 Supervisor 管理所有进程：
```bash
supervisord -c supervisord.conf
supervisorctl -c supervisord.conf status
```

## Agent 分工

| Agent | 职责 |
|---|---|
| Agent-1 | 后端基础: 模型、配置、路由 |
| Agent-2 | 后端服务: 业务逻辑、Dify 工作流 |
| Agent-3 | 前端基础: Store、API 封装、组件 |
| Agent-4 | 前端页面: 视图页面 |
| Agent-5 | 管线+脚本: 生产管线、TTS、部署脚本 |
