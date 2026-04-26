# AGENTS.md — AI Agent 开发规范

本文档为 AI 编程助手提供项目上下文和开发规范。在对本项目进行任何代码生成、修改或建议之前，必须先阅读并遵循本文档。

---

## 1. 项目概述

**项目名称**：校园学术活动智能推荐平台（Campus Academic Activity Recommender）

**核心功能**：
- 学术活动信息聚合（爬虫 + 手动录入）
- 活动搜索、筛选、排序
- 个性化推荐（基于兴趣标签的规则推荐）
- 课表导入与日程管理
- 活动-课程时间冲突检测
- 后台管理（活动审核、标签维护）

**团队规模**：6 人协作开发

---

## 2. 技术栈

```text
前端：Vue 3 + Vite 6 + Element Plus + Vue Router 4 + Pinia + Axios
后端：Python 3.10+ + FastAPI 0.115 + Pydantic 2 + SQLAlchemy 2 + PyMySQL
数据库：MySQL 8.0，字符集 utf8mb4
爬虫：Python requests + BeautifulSoup4
测试：pytest + httpx（后端），npm run build 验证（前端）
部署：Docker Compose（预留）
接口文档：FastAPI 内置 Swagger UI（/docs）
```

**不要引入未在上述列表中的框架或库**，除非用户明确要求。

---

## 3. 仓库目录结构

```text
SE-project/
├── frontend/                 # 前端 Vue 3 + Vite 项目
│   ├── src/
│   │   ├── api/              # Axios 接口封装（http.js, activities.js, ...）
│   │   ├── components/       # 通用组件
│   │   ├── views/            # 页面级组件
│   │   ├── router/           # Vue Router 路由配置
│   │   ├── store/            # Pinia 状态管理
│   │   ├── styles/           # 全局样式
│   │   └── utils/            # 工具函数
│   ├── package.json
│   └── vite.config.js
├── backend/                  # 后端 FastAPI 项目
│   ├── app/
│   │   ├── main.py           # FastAPI 应用入口
│   │   ├── core/             # 配置、JWT 安全、统一响应
│   │   ├── api/v1/           # 路由层（每个模块一个文件）
│   │   ├── services/         # 业务逻辑层
│   │   ├── models/           # SQLAlchemy ORM 模型
│   │   ├── schemas/          # Pydantic 请求/响应模型
│   │   ├── db/               # 数据库连接（session.py）
│   │   └── utils/            # 工具函数
│   └── requirements.txt
├── crawler/                  # 爬虫脚本
│   ├── spiders/              # 爬虫实现
│   ├── pipelines/            # 数据存储管道
│   └── utils/                # 文本清洗工具
├── database/                 # 数据库脚本
│   ├── schema.sql            # 建库建表（权威数据源）
│   ├── seed.sql              # 测试种子数据
│   ├── migrations/           # 迁移脚本（预留）
│   └── er/                   # ER 图（预留）
├── docs/                     # 项目文档
│   ├── api-contract.md       # 接口规范
│   └── ...
├── tests/                    # 测试
│   ├── api/                  # 接口测试
│   ├── data/                 # 测试数据
│   └── e2e/                  # 端到端测试（预留）
├── progress/                 # 进度记录
├── AGENTS.md                 # 本文件
├── README.md                 # 项目总说明与环境配置
├── .env.example              # 环境变量模板
├── pytest.ini                # pytest 配置
└── docker-compose.yml        # Docker 部署配置
```

---

## 4. 后端架构规范

### 4.1 分层架构

后端严格遵循三层分离：

```text
api/v1/（路由层）→ services/（业务逻辑层）→ models/ + db/（数据访问层）
```

**规则**：
- **路由层**（`api/v1/*.py`）：只负责参数接收、权限校验、调用 service、返回响应。不写业务逻辑。
- **服务层**（`services/*.py`）：所有业务逻辑在此实现，包括查询组装、推荐计算、数据处理等。
- **模型层**（`models/*.py`）：SQLAlchemy ORM 模型定义，与 `database/schema.sql` 保持一致。
- **Schema 层**（`schemas/*.py`）：Pydantic 模型，用于请求参数校验和响应序列化。

### 4.2 路由注册

所有 v1 路由在 `backend/app/api/v1/__init__.py` 中统一注册：

```python
from fastapi import APIRouter
from app.api.v1 import activities, admin, auth, courses, crawler, recommendations, schedules, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
# ... 其他路由
```

新增模块时，在对应目录下创建路由文件，然后在 `__init__.py` 中注册。

### 4.3 统一响应格式

所有接口必须使用 `app.core.response` 中的包装函数：

```python
from app.core.response import success, fail

# 成功响应
return success(data)
# → {"code": 0, "message": "success", "data": ...}

# 失败响应
return fail(code=1001, message="活动不存在")
# → {"code": 1001, "message": "活动不存在", "data": null}
```

### 4.4 分页约定

分页接口统一使用 `page` + `page_size` 参数，返回格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 10
  }
}
```

### 4.5 数据库会话

通过 FastAPI 依赖注入获取数据库 session：

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

@router.get("/example")
def example(db: Session = Depends(get_db)):
    ...
```

### 4.6 配置管理

所有配置项通过 `app.core.config.settings` 读取，来源为环境变量，模板见 `.env.example`：

```python
from app.core.config import settings

settings.database_url      # MySQL 连接串
settings.secret_key        # JWT 密钥
settings.api_v1_prefix     # "/api/v1"
```

### 4.7 后端启动命令

```bash
# 从项目根目录
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

注意 `--app-dir backend` 是必须的，否则会报 `ModuleNotFoundError`。

---

## 5. 数据库规范

### 5.1 数据库名

```text
se_project
```

### 5.2 当前表结构

权威数据源是 `database/schema.sql`。当前已定义 9 张表：

| 表名 | 用途 |
|---|---|
| `user` | 用户（学生/管理员） |
| `activity` | 活动信息 |
| `activity_tag` | 活动标签（多对多） |
| `user_interest` | 用户兴趣标签 |
| `course_schedule` | 课程表 |
| `schedule_event` | 用户日程 |
| `registration` | 用户-活动报名记录 |
| `crawl_record` | 爬虫运行记录 |
| `admin_log` | 管理员操作日志 |

### 5.3 关键字段命名

以下字段名已在数据库中确定，代码中必须保持一致：

```text
activity.hot_score        # 热度分（不是 heat_score）
activity.status           # 状态：open / offline
activity.source_type      # 来源：manual / crawled
activity.created_at       # 创建/发布时间（数据库中无 publish_time 字段）
activity.updated_at       # 更新时间
activity_tag.tag_name     # 标签名称
user_interest.tag_name    # 用户兴趣标签名称
user.role                 # 角色：student / admin
```

### 5.4 数据库修改规则

- 任何表结构变更必须同步更新 `database/schema.sql`
- 更新后同步修改对应的 SQLAlchemy 模型（`backend/app/models/`）
- 同步更新 `docs/api-contract.md`
- 不要使用 Alembic 自动迁移（当前项目未配置）

---

## 6. 前端架构规范

### 6.1 API 调用

所有 API 请求通过 `src/api/http.js` 封装的 Axios 实例发出：

```javascript
import { http } from './http'

// 响应拦截器已自动解包 response.data
// 调用方直接得到 {code, message, data} 对象
```

每个后端模块对应一个前端 API 文件：

```text
src/api/auth.js            → /api/v1/auth/*
src/api/activities.js      → /api/v1/activities/*
src/api/recommendations.js → /api/v1/recommendations/*
src/api/schedules.js       → /api/v1/schedules/*
src/api/courses.js         → /api/v1/courses/*
src/api/admin.js           → /api/v1/admin/*
```

### 6.2 开发代理

Vite 开发服务器已配置反向代理，将 `/api` 请求转发到 `http://localhost:8000`：

```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

### 6.3 前端启动命令

```bash
cd frontend
npm install    # 首次或依赖更新后
npm run dev    # 开发模式，http://localhost:5173
```

---

## 7. 当前项目状态

当前处于**骨架搭建完成、业务功能未实现**阶段。所有接口返回 mock/硬编码数据。

### 7.1 已完成的基础设施

```text
✅ FastAPI 应用入口、CORS、路由注册
✅ 统一响应格式 success() / fail()
✅ JWT 工具（密码哈希、Token 生成）
✅ 数据库连接层（engine, SessionLocal, get_db）
✅ SQLAlchemy 基类和 Activity 模型（部分）
✅ Pydantic Schema（ActivityCreate, ActivityUpdate, LoginRequest 等）
✅ 所有路由文件占位（auth, users, activities, recommendations, schedules, courses, admin, crawler）
✅ 数据库 schema.sql（9 张表）+ seed.sql（测试数据）
✅ 前端 Vue 3 工程（8 个页面骨架 + API 封装）
✅ Docker Compose 配置
```

### 7.2 尚未实现的功能

```text
❌ 真实数据库查询（所有 service 层都是 mock）
❌ 用户注册
❌ 真实登录校验
❌ JWT Token 解析中间件（get_current_user 依赖）
❌ 管理员权限校验
❌ 完整 ORM 模型（缺 ActivityTag, UserInterest, Registration, AdminLog 等）
❌ 搜索筛选真实逻辑
❌ 推荐分真实计算
❌ 课程导入解析
❌ 日程冲突检测
❌ ICS 文件导出
❌ 爬虫真实抓取
❌ 前端真实数据渲染
```

---

## 8. 代码风格规范

### 8.1 Python（后端）

- Python 3.10+ 类型标注语法：使用 `str | None` 而非 `Optional[str]`
- 使用 `Mapped[T]` + `mapped_column()` 定义 SQLAlchemy 模型（2.0 风格）
- 函数/变量命名：`snake_case`
- 类命名：`PascalCase`
- 显式导入，不使用通配符 `from x import *`
- 新增依赖必须同步写入 `backend/requirements.txt`，锁定版本号

### 8.2 JavaScript（前端）

- 使用 ES Module（`import`/`export`）
- Vue 3 Composition API 或 Options API 均可（现有代码使用 Options API）
- 组件命名：`PascalCase`（如 `ActivityListView.vue`）
- Element Plus 组件库：使用 `el-` 前缀组件
- 新增依赖通过 `npm install`，确认写入 `package.json`

### 8.3 SQL

- 表名：`snake_case`，单数形式（`user` 而非 `users`）
- 字段名：`snake_case`
- 必须有主键 `id INT PRIMARY KEY AUTO_INCREMENT`
- 时间字段使用 `DATETIME`，默认值 `CURRENT_TIMESTAMP`
- 外键使用 `CONSTRAINT fk_xxx FOREIGN KEY ... ON DELETE CASCADE/SET NULL`
- 字符集：`utf8mb4`

---

## 9. Git 协作规范

### 9.1 分支命名

```text
main                        # 稳定主分支，不直接开发
frontend/xxx                # 前端功能分支
backend/xxx                 # 后端功能分支
crawler/xxx                 # 爬虫功能分支
database/xxx                # 数据库相关
docs/xxx                    # 文档相关
test/xxx                    # 测试相关
fix/xxx                     # Bug 修复
```

### 9.2 Commit Message

```text
格式：类型: 简短描述（英文）

feat: add activity search with keyword filter
fix: fix pagination total count
docs: update api-contract for filter-options
refactor: extract recommendation score calculation
test: add activity list api tests
chore: update gitignore
```

### 9.3 不可提交的文件

以下内容已在 `.gitignore` 中配置，绝对不要提交：

```text
.venv/  node_modules/  .env  frontend/dist/  __pycache__/  .pytest_cache/
```

---

## 10. 接口变更同步规则

修改任何后端接口时，必须同步更新以下文件：

```text
1. backend/app/schemas/     → Pydantic 请求/响应模型
2. docs/api-contract.md     → 接口清单和字段说明
3. frontend/src/api/        → 前端 API 封装
4. docs/test-cases.md       → 相关测试用例
```

---

## 11. 测试规范

### 11.1 运行测试

```bash
# 从项目根目录
source .venv/bin/activate
pytest
```

`pytest.ini` 已配置 `pythonpath = backend`，`testpaths = tests`。

### 11.2 测试文件位置

```text
tests/api/          # 接口测试（test_*.py）
tests/data/         # 测试数据（JSON 等）
tests/e2e/          # 端到端测试（预留）
```

### 11.3 编写接口测试

使用 `httpx.AsyncClient` 或 FastAPI `TestClient`：

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_list_activities():
    response = client.get("/api/v1/activities")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 0
```

---

## 12. 模块职责与文件映射

### 12.1 后端模块

| 功能模块 | 路由文件 | 服务文件 | Schema 文件 |
|---|---|---|---|
| 认证登录 | `api/v1/auth.py` | — | `schemas/auth.py` |
| 用户信息 | `api/v1/users.py` | — | `schemas/user.py` |
| 活动搜索筛选 | `api/v1/activities.py` | `services/activity_service.py` | `schemas/activity.py` |
| 个性化推荐 | `api/v1/recommendations.py` | `services/recommendation_service.py` | — |
| 日程管理 | `api/v1/schedules.py` | `services/schedule_service.py` | `schemas/schedule.py` |
| 课程导入 | `api/v1/courses.py` | — | `schemas/course.py` |
| 后台管理 | `api/v1/admin.py` | — | `schemas/activity.py` |
| 爬虫管理 | `api/v1/crawler.py` | — | `schemas/crawler.py` |

### 12.2 前端页面

| 页面 | 文件 | 对应后端接口 |
|---|---|---|
| 首页/推荐 | `views/HomeView.vue` | `GET /api/v1/recommendations/activities` |
| 登录 | `views/LoginView.vue` | `POST /api/v1/auth/login` |
| 活动列表 | `views/ActivityListView.vue` | `GET /api/v1/activities` |
| 活动详情 | `views/ActivityDetailView.vue` | `GET /api/v1/activities/{id}` |
| 日历 | `views/CalendarView.vue` | `GET /api/v1/schedules` |
| 课表导入 | `views/CourseImportView.vue` | `POST /api/v1/courses/import` |
| 个人中心 | `views/ProfileView.vue` | `GET /api/v1/users/me` |
| 后台管理 | `views/AdminView.vue` | `POST/PUT/DELETE /api/v1/admin/activities/*` |

---

## 13. 开发注意事项

1. **不要重建项目骨架**：前端 Vue 项目和后端 FastAPI 项目已初始化完成，直接在现有文件上开发。
2. **优先替换 mock 数据**：当前所有 service 层返回硬编码数据，开发任务是将 mock 替换为真实数据库查询。
3. **不要修改他人模块**：未经沟通不要修改其他成员负责的路由和服务文件。
4. **保持 schema.sql 同步**：数据库表结构变更后，必须同步更新 `database/schema.sql` 和对应 ORM 模型。
5. **使用 service 层**：不要把业务逻辑直接写在路由函数中，放到 `services/` 目录下。
6. **第一阶段优先主流程**：先保证搜索、推荐、日程管理等核心功能可用，不要过早投入 OCR、社交等二阶段功能。

---

## 14. 环境变量参考

```bash
# .env.example 中的配置项
PROJECT_NAME=Campus Academic Activity Recommender
ENV=development
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
API_V1_PREFIX=/api/v1
SECRET_KEY=change-me-in-local-env
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=se_project
MYSQL_USER=se_user
MYSQL_PASSWORD=se_password
DATABASE_URL=mysql+pymysql://se_user:se_password@localhost:3306/se_project
VITE_API_BASE_URL=http://localhost:8000/api/v1
```
