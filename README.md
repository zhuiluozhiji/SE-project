# 环境配置

本项目统一使用 Docker Compose 管理开发环境。所有组员都使用同一套 `mysql + backend + frontend` 容器，不再混用本地 `venv`、本地 `npm` 和本地 MySQL。

## 1. 组员需要安装什么

每位组员本机只需要安装：

```text
Git
Docker
Docker Compose
```

可先检查：

```bash
git --version
docker --version
docker compose version
```

如果上面命令能正常输出版本号，就可以继续。

## 2. 第一次拉代码后怎么配置

第一次拉取项目后，在项目根目录执行：

```bash
git clone 项目仓库地址
cd SE-project
cp .env.example .env
docker compose up --build
```

说明：

- `.env.example` 是团队统一模板，复制成 `.env` 后即可直接使用。
- `docker compose up --build` 会统一构建并启动前端、后端、数据库三个服务。
- MySQL 第一次启动时会自动执行 `database/schema.sql` 和 `database/seed.sql`。

启动成功后访问：

```text
前端：http://localhost:5173/
后端健康检查：http://localhost:8000/health
Swagger：http://localhost:8000/docs
活动列表示例：http://localhost:8000/api/v1/activities
```

## 3. 团队统一开发命令

所有组员统一只使用下面这套命令：

```bash
docker compose up --build
docker compose up --build -d
docker compose down
docker compose down -v
docker compose exec backend pytest
docker compose exec backend sh
docker compose exec frontend sh
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f mysql
```

常用说明：

- `docker compose up --build`
  启动整个开发环境，前台查看日志。
- `docker compose up --build -d`
  后台启动整个开发环境。
- `docker compose down`
  停止并删除容器。
- `docker compose down -v`
  停止并删除容器，同时删除 MySQL 数据卷；下次启动会重新执行建表和种子数据。
- `docker compose exec backend pytest`
  在后端容器内执行测试。
- `docker compose exec backend sh`
  进入后端容器排查问题、运行 Python 命令。
- `docker compose exec frontend sh`
  进入前端容器排查前端依赖或开发服务问题。

## 4. 组员日常开发应该怎么做

每次开始开发前：

```bash
git pull
docker compose up -d
```

开发过程中：

- 前端代码改动会通过 Vite 热更新自动生效。
- 后端代码改动会通过 `uvicorn --reload` 自动重载。
- 数据库统一使用 Compose 里的 MySQL，不要自己再本地单独起一个库来联调。

开发完成后，提交前至少执行：

```bash
docker compose exec backend pytest
```

如果你改了前端页面，建议同时手动打开：

```text
http://localhost:5173/
```

检查页面是否正常。

## 5. 环境变量约定

项目统一提供 `.env.example`。组员必须从它复制生成自己的 `.env`：

```bash
cp .env.example .env
```

默认情况下不需要修改，关键项如下：

```text
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=se_project
MYSQL_USER=se_user
MYSQL_PASSWORD=se_password
MYSQL_ROOT_PASSWORD=root_password
DATABASE_URL=mysql+pymysql://se_user:se_password@mysql:3306/se_project
VITE_API_BASE_URL=/api/v1
VITE_DEV_PROXY_TARGET=http://backend:8000
```

注意：

- `.env.example` 可以提交到仓库。
- `.env` 是每个人本地文件，不要提交。
- 如果组长后续修改了环境变量模板，其他组员需要 `git pull` 后同步更新自己的 `.env`。

## 6. 常见问题

### `docker compose up --build` 后服务启动失败

先看日志：

```bash
docker compose logs -f mysql
docker compose logs -f backend
docker compose logs -f frontend
```

重点检查：

- Docker 是否已经正常启动。
- `3306`、`8000`、`5173` 端口是否被占用。
- `.env` 是否确实由 `.env.example` 复制而来。

### 需要重置数据库

执行：

```bash
docker compose down -v
docker compose up --build
```

这会删除旧数据卷，并重新执行 `schema.sql` 和 `seed.sql`。

### 不要做的事情

组员不要这样做：

- 不要提交 `.env`。
- 不要手动维护某个人本机容器再让别人 `docker commit` / `docker save` / `docker load`。
- 不要一部分人用 Docker，一部分人用本地 `venv` 或本地 MySQL。
- 不要跳过 `docker compose` 直接在宿主机运行 `uvicorn`、`pytest`、`npm run dev` 作为团队标准流程。

# 分工

| 成员 | 角色 | 主要负责内容 | 第一阶段重点交付 |
| --- | --- | --- | --- |
| zzy | 前端负责人 | 页面与交互开发 | 活动列表、活动详情、日历、课表导入、后台页面联调 |
| gsj | 爬虫与数据库负责人 | 数据来源与数据库设计 | 表结构、种子数据、活动样例数据、计院爬虫与入库 |
| mxy | 后端负责人 1 | 后端基础与通用接口 | 数据库连接、ORM 基础、登录注册、用户信息、活动基础接口 |
| lyy | 后端负责人 2 | 日历与课表业务 | 课表导入、截图识别接口预留、冲突检测、日程、ICS 导出 |
| pxl | 后端负责人 3 | 推荐与筛选排序 | 活动搜索、标签/类别/校区筛选、排序、推荐规则、后台辅助统计 |
| hh | 测试与文书负责人 | 测试管理与项目文档 | 测试用例、接口测试、Bug 记录、进度记录、用户手册和报告材料 |


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

如果团队不使用 Pull Request，可以由组长或模块负责人确认后直接合并到 `main`：

```bash
git checkout main
git pull
git merge frontend/activity-list
git push origin main
```

合并完成后可以删除已完成的功能分支：

```bash
git branch -d frontend/activity-list
git push origin --delete frontend/activity-list
```

## 4. 合并前检查

合并到 `main` 前至少确认：

```bash
docker compose exec backend pytest
```

如果只改文档，可以不跑前端构建和后端测试，但提交信息或进度记录里要说明“仅文档修改”。

## 5. 协作注意事项

1. 不要提交 `.env`、`.venv/`、`node_modules/`、`frontend/dist/`。
2. 不要直接修改别人负责模块的大段代码，确实需要时先沟通。
3. 接口字段变化时，必须同步更新 `docs/api-contract.md`。
4. 数据库字段变化时，必须同步更新 `database/schema.sql`。
5. 前端调用接口前，先看 Swagger 和 `docs/api-contract.md`。
6. 分支合并前建议在群里说明本次改动范围，例如 `feat: add course import api`。
7. 每次合并尽量只做一类事情，不要把前端、后端、文档、格式化混在一次提交里。
8. 团队统一使用 Docker Compose，不要再把本地 `venv`、本地 `npm`、本地 MySQL 当成主开发流程。
