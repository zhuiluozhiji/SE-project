
# NOTE
开发项目的时候喂给ai初始化，了解项目任务，可以用`docs/` 下面的各文档，
大家的进展可以放在



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


