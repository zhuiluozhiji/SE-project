
# NOTE
- `docs/`：开发项目的时候喂给vibe coding初始化，了解项目任务，可以用`docs/` 下面的各文档，
- `progress/`：大家各自的进展可以放在底下的文件夹下，同时有一份`总进度.md`记录整体项目推进到了哪里，可以由负责测试的同学维护

# 环境配置

本节说明组员第一次拉取项目后，如何把本地环境配置到可以运行前端、后端和基础测试的状态。

当前项目涉及：

```text
前端：Node.js + npm
后端：Python + venv + pip
数据库：MySQL
协作：Git
```

推荐版本：

```text
Node.js >= 18
npm >= 9
Python >= 3.10
MySQL 8.0
```

可以先检查本机是否已安装：

```bash
git --version
node --version
npm --version
python --version
mysql --version
```

如果某个命令不存在，需要先安装对应软件。

## 1. 拉取项目

第一次拉取：

```bash
git clone 项目仓库地址
cd SE-project
```

如果已经拉取过：

```bash
git pull
```

## 2. 配置环境变量

项目提供了环境变量模板：

```bash
cp .env.example .env
```

然后根据本机 MySQL 配置修改 `.env`：

```text
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=se_project
MYSQL_USER=你的 MySQL 用户名
MYSQL_PASSWORD=你的 MySQL 密码
DATABASE_URL=mysql+pymysql://你的 MySQL 用户名:你的 MySQL 密码@localhost:3306/se_project
```

注意：

```text
.env.example 可以提交到仓库
.env 是个人本地配置，不要提交
```

## 3. 配置后端环境

在项目根目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Windows PowerShell 可以使用：

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

安装完成后，运行后端测试：

```bash
pytest
```

如果测试通过，会看到类似：

```text
1 passed
```

## 4. 配置前端环境

进入前端目录：

```bash
cd frontend
npm install
npm run build
```

如果 `npm run build` 通过，说明前端依赖和构建配置正常。

执行完成后回到项目根目录：

```bash
cd ..
```

## 5. 配置数据库

确保本机 MySQL 已启动，然后在项目根目录执行：

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```

如果你不是用 `root` 用户，请替换成自己的 MySQL 用户名：

```bash
mysql -u 你的用户名 -p < database/schema.sql
mysql -u 你的用户名 -p < database/seed.sql
```

这两份 SQL 的作用：

```text
database/schema.sql  # 创建数据库和核心表
database/seed.sql    # 写入测试用户、测试活动、课程和日程样例数据
```

## 6. 启动后端服务

在项目根目录执行：

```bash
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

启动成功后访问：

```text
健康检查：http://localhost:8000/health
接口文档：http://localhost:8000/docs
活动列表：http://localhost:8000/api/v1/activities
```

## 7. 启动前端服务

另开一个终端，进入前端目录：

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

启动成功后访问：

```text
前端页面：http://localhost:5173/
```

## 8. 最短跑通流程

如果已经安装好 Git、Node.js、npm、Python、MySQL，可以按下面顺序直接跑：

```bash
git pull
cp .env.example .env

python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pytest

mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql

cd frontend
npm install
npm run build
cd ..
```

然后分别启动两个服务：

```bash
# 终端 1：后端
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

```bash
# 终端 2：前端
cd frontend
npm run dev -- --host 0.0.0.0
```

最后打开：

```text
http://localhost:5173/
http://localhost:8000/docs
```

## 9. 已自动完成和不需要重复做的事情

项目初始化时已经完成：

```text
前端 Vue 3 + Vite 工程
后端 FastAPI 工程
基础 API 路由
Swagger 接口文档
数据库 SQL 脚本
测试目录和测试样例
爬虫目录骨架
Docker 配置占位
```

组员不需要重新创建这些工程，只需要在现有目录上继续开发。

不要提交这些本地生成内容：

```text
.venv/
node_modules/
.env
frontend/dist/
__pycache__/
.pytest_cache/
```

这些已经写入 `.gitignore`。

## 10. 常见问题

### `uvicorn: command not found`

说明没有激活虚拟环境，或者后端依赖没有安装：

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### `ModuleNotFoundError: No module named 'app'`

启动后端时需要带上 `--app-dir backend`：

```bash
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

### 前端端口被占用

可以换端口：

```bash
npm run dev -- --host 0.0.0.0 --port 5174
```

### 后端端口被占用

可以换端口：

```bash
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8001
```

如果后端端口改了，前端接口地址也要同步调整。

### 数据库连接失败

优先检查：

```text
MySQL 是否启动
.env 中用户名和密码是否正确
DATABASE_URL 是否正确
database/schema.sql 是否已经导入
```

当前大部分接口仍是 mock 数据，所以数据库连接失败不一定会影响接口占位访问，但后续真实业务会依赖 MySQL。


# GitHub 提交规范

为了方便 6 人协作开发、代码审查和后期写项目报告，大家提交代码时统一遵守下面的 Git/GitHub 规范。

## 1. 分支命名规范

不要直接在 `main` 分支上开发功能。每个任务新建独立分支：

```text
main                        # 稳定主分支
frontend/xxx                # 前端功能
backend/xxx                 # 后端功能
crawler/xxx                 # 爬虫功能
database/xxx                # 数据库相关
docs/xxx                    # 文档相关
test/xxx                    # 测试相关
fix/xxx                     # Bug 修复
```

示例：

```text
frontend/activity-list
frontend/calendar-view
backend/auth-login
backend/schedule-conflict
crawler/cs-zju
database/init-schema
docs/test-plan
fix/activity-filter
```

## 2. Commit Message 规范

提交信息统一使用：

```text
类型: 简短描述
```

常用类型：

| 类型 | 含义 | 示例 |
| --- | --- | --- |
| `feat` | 新增功能 | `feat: add activity list page` |
| `fix` | 修复 Bug | `fix: fix schedule conflict check` |
| `docs` | 文档修改 | `docs: update environment setup guide` |
| `style` | 样式调整，不影响逻辑 | `style: polish login page layout` |
| `refactor` | 重构代码，不新增功能 | `refactor: split activity service` |
| `test` | 测试相关 | `test: add auth api tests` |
| `chore` | 配置、依赖、脚手架等杂项 | `chore: update gitignore` |
| `build` | 构建或打包配置 | `build: add frontend dockerfile` |
| `ci` | CI/CD 配置 | `ci: add github actions workflow` |

推荐示例：

```bash
git commit -m "feat: add activity list api"
git commit -m "fix: handle empty course import file"
git commit -m "docs: add github commit guide"
git commit -m "test: add schedule conflict test cases"
```

不推荐：

```text
update
修改了一下
111
final version
```

## 3. 提交流程

每次开始新任务前：

```bash
git pull
git checkout -b frontend/activity-list
```

开发完成后：

```bash
git status
git add 修改的文件
git commit -m "feat: add activity list page"
git push origin frontend/activity-list
```

然后在 GitHub 上发起 Pull Request，合并到 `main`。

## 4. 合并前检查

提交 PR 前至少确认：

```bash
pytest
cd frontend
npm run build
```

如果只改文档，可以不跑前端构建和后端测试，但 PR 描述里要说明“仅文档修改”。

## 5. 协作注意事项

1. 不要提交 `.env`、`.venv/`、`node_modules/`、`frontend/dist/`。
2. 不要直接修改别人负责模块的大段代码，确实需要时先沟通。
3. 接口字段变化时，必须同步更新 `docs/api-contract.md`。
4. 数据库字段变化时，必须同步更新 `database/schema.sql`。
5. 前端调用接口前，先看 Swagger 和 `docs/api-contract.md`。
6. PR 标题建议和 commit 类型保持一致，例如 `feat: add course import api`。
7. 每个 PR 尽量只做一类事情，不要把前端、后端、文档、格式化混在一次提交里。


# 项目架构
## **仓库目录结构**

```text
SE-project/
├── frontend/                 # 前端项目，负责页面和交互
├── backend/                  # 后端项目，负责 API 和业务逻辑
├── crawler/                  # 爬虫脚本，负责采集学院活动数据
├── database/                 # 数据库建表、种子数据、ER 图
├── docs/                     # 项目文档、需求文档、接口规范、测试文档
├── tests/                    # 自动化测试、接口测试、测试数据
├── prompts/                  # 给 AI/成员使用的提示词和开发上下文
│   └── hh/                   # 当前测试/文书同学可使用的 prompt 区域
├── README.md                 # 项目总说明
└── docker-compose.yml        # 后期可选，一键启动服务
```

## **前端架构**
```text
frontend/
├── src/
│   ├── api/                  # Axios 接口封装
│   ├── assets/               # 静态资源
│   ├── components/           # 通用组件
│   ├── views/                # 页面级组件
│   ├── router/               # 路由配置
│   ├── store/                # Pinia 状态管理
│   └── utils/                # 工具函数
└── package.json
```

前端主要页面：

```text
LoginView                # 登录/注册
HomeView                 # 首页、推荐活动
ActivityListView         # 活动列表、搜索、筛选、排序
ActivityDetailView       # 活动详情、一键加入日程
CalendarView             # 日历视图、冲突展示
CourseImportView         # 课表导入
ProfileView              # 个人中心
AdminView                # 简化后台管理
```

## **后端架构**
```text
backend/
├── app/
│   ├── main.py
│   ├── core/                 # 配置、JWT、统一响应、异常处理
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── activities.py
│   │       ├── recommendations.py
│   │       ├── schedules.py
│   │       ├── courses.py
│   │       ├── admin.py
│   │       └── crawler.py
│   ├── models/               # SQLAlchemy 模型
│   ├── schemas/              # Pydantic 请求/响应模型
│   ├── services/             # 业务逻辑
│   ├── db/                   # 数据库连接
│   └── utils/                # 工具函数
└── requirements.txt
```

核心后端模块：

```text
auth                 # 登录、注册、Token 鉴权
activities           # 活动列表、详情、筛选、后台 CRUD
recommendations      # 规则推荐
schedules            # 日程查询、冲突检测、加入日程、ICS 导出
courses              # 课表手动录入、CSV/Excel 导入、OCR 预留
crawler              # 手动触发爬虫、爬虫记录查询
admin                # 下架活动、修正活动、查看统计
```

## **数据库架构**
第一阶段建议核心表：

```text
user                 # 用户
activity             # 活动
activity_tag         # 活动标签
user_interest        # 用户兴趣
schedule_event       # 用户日程
course_schedule      # 课程表
registration         # 报名/加入记录
crawl_record         # 爬虫运行记录
admin_log            # 管理员操作日志
```

主流程里最重要的是：

```text
activity → 活动展示、筛选、推荐
course_schedule → 课表导入与冲突检测
schedule_event → 日历展示、加入日程、ICS 导出
registration → 记录用户和活动关系
```


# 技术栈
前端：Vue 3 + Vite + Element Plus
后端：Python + FastAPI
数据库：MySQL
爬虫：Python requests + BeautifulSoup
测试：接口测试 + 文档测试 + 手工验收用例
接口文档：FastAPI Swagger / docs 接口文档
