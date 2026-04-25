我已读完 `reference/` 下三份文档。当前项目应按“第一阶段 MVP”推进：先做出可展示、可联调、可验收的核心闭环，而不是一开始把需求报告里的全部高级功能都做满。

**项目定位**
做一个“校园学术活动智能推荐平台”，第一阶段主流程是：

用户登录 → 浏览/筛选活动 → 查看推荐 → 导入课表 → 加入日程 → 冲突检测 → 日历展示 → ICS 导出 → 管理员维护活动/查看爬虫数据。

第二阶段再扩展：笔记评价、组队、学术轨迹、复杂 NLP 推荐、SSO/CAS、地图通勤、实时消息、高可用监控等。

**推荐框架形态**
仓库建议搭成前后端分离结构：

```text
SE-project/
├── frontend/                 # Vue 3 前端
├── backend/                  # FastAPI 后端
├── crawler/                  # 活动爬虫脚本
├── database/                 # 建表 SQL、种子数据、ER 图
├── docs/                     # 接口文档、开发计划、测试文档
├── tests/                    # 测试用例与脚本
├── README.md
└── docker-compose.yml        # 后期可选，本地一键启动 MySQL/后端/前端
```

**前端会做成这样**
技术栈：`Vue 3 + Vite + Element Plus + Vue Router + Pinia + Axios`。

页面骨架先搭这些：

```text
frontend/src/
├── api/                      # auth、activities、schedules、courses、admin 接口封装
├── assets/
├── components/               # 活动卡片、筛选栏、日历事件、状态标签
├── views/
│   ├── LoginView.vue
│   ├── HomeView.vue          # 推荐活动 + 热门活动
│   ├── ActivityListView.vue  # 搜索、筛选、排序、分页
│   ├── ActivityDetailView.vue
│   ├── CalendarView.vue      # 课程/活动/冲突颜色展示
│   ├── CourseImportView.vue
│   ├── ProfileView.vue
│   └── AdminView.vue         # 简化后台
├── router/
├── store/
└── utils/
```

视觉上建议做成“信息平台 + 日历工作台”：左侧/顶部导航，主区域显示活动列表、推荐卡片、日历视图；课程蓝色，已加入活动绿色，推荐活动紫/橙色，冲突红色，结束活动灰色。

**后端会做成这样**
技术栈：`Python + FastAPI + SQLAlchemy + Pydantic + MySQL`，接口自动生成 Swagger 文档。

```text
backend/
├── app/
│   ├── main.py
│   ├── core/                 # 配置、JWT、安全、统一响应
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
│   ├── models/               # ORM 模型
│   ├── schemas/              # 请求/响应结构
│   ├── services/             # 推荐、冲突检测、ICS、课表解析
│   ├── db/
│   └── utils/
├── requirements.txt
└── README.md
```

接口统一走：

```text
/api/v1/...
```

统一返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

**核心模块优先级**
第一批必须搭好的模块：

1. `auth`：注册、登录、JWT、当前用户。
2. `activities`：活动列表、详情、筛选、排序、后台 CRUD。
3. `recommendations`：规则推荐，先做兴趣标签 + 热度 + 时间临近。
4. `schedules`：个人日程、冲突检测、一键加入日程、ICS 导出。
5. `courses`：手动课程、CSV/Excel 导入，OCR 先留接口。
6. `crawler`：先爬一个学院数据源，记录运行日志。
7. `admin`：活动修正、下架、爬虫记录、简单统计。

**数据库先这样设计**
第一阶段核心表：

```text
user
activity
activity_tag
user_interest
schedule_event
course_schedule
registration
crawl_record
admin_log
```

其中 `activity`、`schedule_event`、`course_schedule` 是主流程核心；`registration` 可以先表达“已加入/已报名”；`admin_log` 和 `crawl_record` 用来支撑答辩展示系统完整性。

**第一步框架搭建目标**
不是直接做完整业务，而是先搭出“能跑、能看、能联调”的骨架：

1. 前端能启动，路由页面齐全，有 mock 数据。
2. 后端能启动，`/docs` 能看到 Swagger。
3. 数据库有 `schema.sql` 和 `seed.sql`。
4. 活动列表接口和前端活动页能打通。
5. 日历页能用 mock 或 seed 数据展示课程、活动、冲突状态。
6. README 写清启动方式、目录说明、接口规范。

**建议第一周只做这些**
前端：初始化 Vue 项目，完成登录页、首页、活动列表、日历静态页。  
后端：初始化 FastAPI 项目，完成配置、统一响应、Swagger、基础路由。  
数据库：确定表结构，准备 20-50 条活动样例数据。  
爬虫：确定第一个数据源，先写字段抽取方案。  
文档：整理接口字段、开发分工、测试用例模板。

我建议下一步先不碰复杂 OCR、SSO、地图 API、WebSocket 和高并发指标。框架里预留位置就好，第一版先把核心闭环跑通，这样答辩展示会最稳。