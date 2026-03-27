# Backend Service 文档

## 项目介绍
本后端服务是一个集成 **RAG（检索增强生成）、Embedding 向量处理、LLM 调用、关系型数据库+向量数据库** 的高性能后端系统，基于 Python + FastAPI 构建，采用模块化设计，支持灵活扩展与协作开发。

核心功能包括：
- 提供标准化 API 接口（对话交互、知识库检索、向量生成等）
- 集成 LLM 服务（支持多厂商切换、重试机制）
- RAG 检索增强生成（知识库管理、相似性检索、上下文拼接）
- 双数据库支持（关系型存储业务数据、向量库存储嵌入数据）
- 环境隔离、配置统一管理、完善的测试体系

## 项目结构说明
```
backend/
├── app/                  # 核心业务代码目录
│   ├── __init__.py
│   ├── main.py           # 项目入口（FastAPI 初始化、路由注册）
│   ├── api/              # 接口层（对外服务窗口）
│   │   ├── __init__.py
│   │   ├── router.py     # 路由聚合（统一注册所有接口）
│   │   ├── endpoints/    # 具体接口实现（如 /api/chat、/api/embedding）
│   │   └── dependencies/ # 接口级依赖（权限校验、参数预处理）
│   ├── core/             # 全局核心配置
│   │   ├── __init__.py
│   │   └── config.py     # 环境变量加载、全局配置项
│   ├── models/           # 数据模型层（数据结构定义）
│   │   ├── sql/          # 关系型数据库模型（用户表、知识库表等）
│   │   └── vector/       # 向量数据库模型（嵌入向量、文档元数据等）
│   ├── schemas/          # 数据校验与序列化（接口数据契约）
│   │   └── __init__.py
│   ├── services/         # 业务逻辑层（核心大脑）
│   │   ├── rag/          # RAG 核心逻辑（检索+LLM 调用）
│   │   ├── embedding/    # 向量生成与相似度计算
│   │   └── llm/          # LLM 服务调用（多厂商适配、重试）
│   ├── utils/            # 通用工具库（日志、加密、格式化等）
│   └── dependencies/     # 全局依赖（数据库会话、向量库连接等）
├── tests/                # 测试目录
│   ├── unit/             # 单元测试（单个函数/类测试）
│   └── integration/      # 集成测试（模块联动测试）
├── scripts/              # 辅助脚本（数据库初始化、知识库导入等）
├── requirements.txt      # 项目依赖清单
├── .env.example          # 环境变量模板（敏感信息不提交）
├── .gitignore            # Git 忽略文件配置
└── README.md             # 项目文档（本文档）
```

### 目录职责说明
| 目录/文件               | 核心职责                                                                 |
|-------------------------|--------------------------------------------------------------------------|
| `app/main.py`           | 项目入口，初始化 FastAPI、注册路由、加载中间件                           |
| `app/api/endpoints`     | 接口实现，仅处理请求/响应，不包含业务逻辑                                 |
| `app/core/config.py`    | 统一管理配置，加载环境变量，避免硬编码                                   |
| `app/models/`           | 定义数据结构（数据库表、向量数据格式），作为单一数据源                     |
| `app/schemas/`          | 接口请求/响应校验、序列化，定义数据契约                                   |
| `app/services/`         | 核心业务逻辑实现（RAG、LLM 调用、向量处理），与接口解耦                   |
| `app/utils/`            | 通用工具函数（日志、加密等），避免代码重复                               |
| `tests/`                | 单元测试+集成测试，保障代码质量                                         |
| `scripts/`              | 辅助脚本（数据初始化、迁移等），不参与服务运行                           |

## 环境准备

### 方式 1：Anaconda 环境（推荐，适合数据科学/AI 场景）
```bash
# 1. 进入项目目录
cd backend

# 2. 创建并激活 conda 环境（Python 3.10+ 推荐）
conda create -n backend-env python=3.10
conda activate backend-env

# 3. 安装依赖
pip install -r requirements.txt

# 4. （可选）导出环境（供协作/部署）
conda env export > environment.yml
```

### 方式 2：原生 Python 虚拟环境
```bash
# 1. 进入项目目录
cd backend

# 2. 创建并激活虚拟环境
python -m venv venv

# Windows 激活
venv\Scripts\activate
# macOS/Linux 激活
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. （可选）导出依赖清单
pip freeze > requirements.txt
```

## 配置说明
1. 复制环境变量模板，修改为实际配置：
   ```bash
   # Windows
   copy .env.example .env
   # macOS/Linux
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，配置核心参数（根据实际需求修改）：
   ```env
   # 服务配置
   APP_NAME=Backend Service
   APP_HOST=0.0.0.0
   APP_PORT=8000
   DEBUG=True

   # 关系型数据库配置（示例：SQLite）
   DATABASE_URL=sqlite:///./backend.db
   # 或 PostgreSQL：postgresql://user:password@localhost:5432/backend

   # 向量数据库配置（示例：Chroma）
   VECTOR_DB_PATH=./vector_db
   EMBEDDING_DIM=1536

   # LLM 配置
   LLM_PROVIDER=openai
   OPENAI_API_KEY=your-api-key
   OPENAI_MODEL=gpt-3.5-turbo

   # 日志配置
   LOG_LEVEL=INFO
   LOG_DIR=./logs
   ```

## 运行服务
```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式（禁用自动重载）
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

服务启动后，可访问：
- API 文档：`http://localhost:8000/docs`（Swagger UI）
- 备用文档：`http://localhost:8000/redoc`（ReDoc）

## 测试
```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/ -v

# 运行集成测试
pytest tests/integration/ -v

# 生成测试覆盖率报告
pytest --cov=app --cov-report=html
```
覆盖率报告将生成在 `htmlcov/` 目录，打开 `index.html` 可查看详细覆盖情况。

## 辅助脚本
`scripts/` 目录包含常用辅助脚本，示例用法：
```bash
# 数据库初始化（创建表结构）
python scripts/init_db.py

# 知识库批量导入（将文档转为向量存入向量库）
python scripts/import_knowledge.py --dir ./docs

# 数据迁移（如数据库表结构更新）
python scripts/migrate_db.py
```

## 开发规范
1. **代码风格**：遵循 PEP 8 规范，使用 `black` 格式化代码，`flake8` 检查语法错误；
2. **模块职责**：严格遵守“单一职责”，接口层不写业务逻辑，业务层不处理请求响应；
3. **配置管理**：所有可变配置通过 `.env` 注入，禁止硬编码敏感信息（API 密钥、数据库密码等）；
4. **测试要求**：新增业务逻辑需配套单元测试，接口新增需配套集成测试，测试覆盖率≥80%；
5. **提交规范**：Git 提交信息遵循 `feat: 新增功能`、`fix: 修复bug`、`docs: 文档更新` 格式。

## 部署说明
1. 确保生产环境已安装 Python 3.10+ 或 Anaconda；
2. 复制项目代码到生产服务器，配置 `.env` 文件（`DEBUG=False`）；
3. 安装依赖：`pip install -r requirements.txt`；
4. 使用进程管理工具启动服务（示例：gunicorn）：
   ```bash
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
   ```
5. （可选）配置 Nginx 反向代理，优化性能与安全。

## 协作说明
1. 克隆项目后，先按「环境准备」步骤配置本地环境；
2. 基于 `develop` 分支创建feature分支开发（`git checkout -b feat/xxx`）；
3. 开发完成后，提交 PR 到 `develop` 分支，需通过所有测试与代码检查；
4. 依赖更新需同步修改 `requirements.txt`，并提交 `environment.yml`（conda 用户）。

## 常见问题
1. **依赖安装失败**：检查 Python 版本是否符合要求（3.10+），或尝试更新 pip：`pip install --upgrade pip`；
2. **服务启动失败**：检查 `.env` 配置是否完整，端口是否被占用（更换 `APP_PORT`）；
3. **数据库连接失败**：验证 `DATABASE_URL` 格式是否正确，数据库服务是否正常运行；
4. **LLM 调用失败**：检查 API 密钥是否有效，网络是否能访问 LLM 服务提供商。

## 联系方式
如需技术支持或协作沟通，可联系项目负责人。

---
*最后更新时间：2026-01-22*