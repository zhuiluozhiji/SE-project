# 测试用例矩阵

本文档按 `docs/测试文档/测试提纲.md` 的章节组织测试用例，作为自动化测试、手工联调和最终测试报告的统一映射表。

状态说明：

- `已自动化`：已有 pytest 用例直接覆盖。
- `已联调`：已通过 Docker Compose 运行态接口或页面访问验证。
- `已截图`：已保存基础页面截图，可用于测试报告。
- `记录缺陷`：测试目标是确认当前限制或缺陷，并写入缺陷记录。

## 4 功能验证测试

| 编号 | 章节 | 模块 | 测试点 | 前置条件 | 操作步骤 | 期望结果 | 证据/脚本 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-4.1-001 | 4.1 | 登录注册与权限 | 学生正常登录 | 存在 `student001` | POST `/api/v1/auth/login` | 返回 `code=0`、token、student 用户信息 | `test_auth_activity.py` | 已自动化 |
| TC-4.1-002 | 4.1 | 登录注册与权限 | 获取当前用户 | 已登录 | GET `/api/v1/users/me` | 返回当前用户公开信息 | `test_auth_activity.py` | 已自动化 |
| TC-4.1-003 | 4.1 | 登录注册与权限 | 新用户注册 | 用户名未占用 | POST `/api/v1/auth/register` | 创建 student 用户并返回 token | `test_auth_activity.py` | 已自动化 |
| TC-4.1-004 | 4.1 | 登录注册与权限 | 重复用户名注册 | 已存在 `student001` | POST `/api/v1/auth/register` | 返回业务错误 `code=1004` | `test_auth_activity.py` | 已自动化 |
| TC-4.1-005 | 4.1 | 登录注册与权限 | 学生访问后台被拒 | 学生已登录 | GET `/api/v1/admin/stats` | HTTP 403，提示需要管理员权限 | `test_auth_activity.py` | 已自动化 |
| TC-4.1-006 | 4.1 | 登录注册与权限 | 管理员访问后台成功 | 管理员已登录 | GET `/api/v1/admin/stats` | 返回后台统计数据 | `test_auth_activity.py` | 已自动化 |
| TC-4.2-001 | 4.2 | 活动浏览 | 活动列表分页 | 存在 open 活动 | GET `/api/v1/activities` | 返回分页结构和活动条目 | `test_auth_activity.py` | 已自动化 |
| TC-4.2-002 | 4.2 | 活动浏览 | 活动详情 | 存在活动 ID | GET `/api/v1/activities/{id}` | 返回详情字段和标签 | `test_auth_activity.py` | 已自动化 |
| TC-4.2-003 | 4.2 | 活动筛选 | 关键词筛选 | 存在匹配活动 | GET `/api/v1/activities?keyword=...` | 只返回匹配活动 | `test_activity_features.py` | 已自动化 |
| TC-4.2-004 | 4.2 | 活动筛选 | 分类、校区、标签组合筛选 | 存在带标签活动 | GET `/api/v1/activities?category=&campus=&tag=` | 返回符合条件的活动 | `test_activity_features.py` | 已自动化 |
| TC-4.2-005 | 4.2 | 活动筛选 | 筛选项查询 | 存在 open 活动和标签 | GET `/api/v1/activities/filter-options` | 返回 categories、campuses、colleges、tags | `test_activity_features.py` | 已自动化 |
| TC-4.2-006 | 4.2 | 活动交互 | 匿名交互跳过 | 未登录 | POST `/activities/{id}/interactions` | 返回成功但 `recorded=false` | `test_activity_features.py` | 已自动化 |
| TC-4.2-007 | 4.2 | 活动交互 | 登录交互写入 | 学生已登录 | POST `/activities/{id}/interactions` | 返回 `recorded=true` 和交互信息 | `test_activity_features.py` | 已自动化 |
| TC-4.3-001 | 4.3 | 个性化推荐 | 未登录通用推荐 | 存在 open 活动 | GET `/recommendations/activities` | 返回推荐项和推荐字段 | `test_recommendations.py` | 已自动化 |
| TC-4.3-002 | 4.3 | 个性化推荐 | 登录用户兴趣推荐 | 用户有兴趣标签 | GET `/recommendations/activities` 携带 token | 命中兴趣标签，包含推荐原因 | `test_recommendations.py` | 已自动化 |
| TC-4.3-003 | 4.3 | 个性化推荐 | 行为历史影响推荐 | 用户有浏览行为 | GET 推荐接口 | `behavior_history` 分值大于 0 | `test_recommendations.py` | 已自动化 |
| TC-4.3-004 | 4.3 | 个性化推荐 | 冲突惩罚 | 用户已有冲突日程 | GET 推荐接口 | 返回 `has_conflict=true` 和惩罚分 | `test_recommendations.py` | 已自动化 |
| TC-4.3-005 | 4.3 | 个性化推荐 | 推荐数量限制 | limit 合法/非法 | GET `?limit=1/0` | 合法返回指定数量，非法 422 | `test_recommendations.py` | 已自动化 |
| TC-4.3-006 | 4.3 | 后台推荐预览 | 管理员预览推荐 | 管理员已登录 | GET `/admin/recommendations/preview` | 返回推荐项；学生访问被拒 | `test_recommendations.py` | 已自动化 |
| TC-4.4-001 | 4.4 | 课表管理 | 手动新增课程 | 存在测试用户 | POST `/api/v1/courses` | 写入课程并生成课程日程 | `test_schedule_course.py` | 已自动化 |
| TC-4.4-002 | 4.4 | 课表管理 | 查询课程列表 | 已有课程 | GET `/api/v1/courses` | 返回课程条目 | `test_schedule_course.py` | 已自动化 |
| TC-4.4-003 | 4.4 | 课表导入 | CSV 导入 | 准备 CSV 文件 | POST `/courses/import` | 返回导入数量和课程明细 | `test_schedule_course.py` | 已自动化 |
| TC-4.4-004 | 4.4 | 课表导入 | 浙大导出格式 CSV | 准备教务格式行 | POST `/courses/import` | 拆分出多个课程时段 | `test_schedule_course.py` | 已自动化 |
| TC-4.4-005 | 4.4 | 课表导入 | XLSX 导入 | 准备 Excel 文件 | POST `/courses/import` | 正确解析课程 | `test_schedule_course.py` | 已自动化 |
| TC-4.4-006 | 4.4 | 课程删除 | 删除课程 | 已存在课程和日程 | DELETE `/courses/{id}` | 删除课程并同步删除课程日程 | `test_schedule_course.py` | 已自动化 |
| TC-4.4-007 | 4.4 | 课程删除 | 按范围删除课程 | 同一课程多时段 | DELETE `?scope=one/day/all` | 按范围删除对应课程规则 | `test_schedule_course.py` | 已自动化 |
| TC-4.4-008 | 4.4 | 课表 OCR | OCR 预留接口 | 准备图片文件 | POST `/courses/ocr` | 返回 reserved 说明 | `test_schedule_course.py` | 已自动化 |
| TC-4.4-009 | 4.4 | 课表管理 | 登录用户个人数据持久化与隔离 | 已存在 `student001`、`student002` 两个普通用户 | 以 `student002` 身份新增/导入课程后查询课程和日程，再切换为 `student001` 查询 | `student002` 重新查询仍能看到自己的课程日程，`student001` 看不到 `student002` 的个人数据 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-001 | 4.5 | 日程管理 | 查询日程 | 已有课程和活动 | GET `/api/v1/schedules` | 返回课程/活动日程 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-002 | 4.5 | 日程管理 | 课程周次展开 | 指定周范围 | GET `/schedules?start_date=&end_date=` | 按周次、单双周、春夏学期展开 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-003 | 4.5 | 冲突检测 | 活动与课程冲突 | 已有冲突课程 | POST `/schedules/check-conflict` | 返回冲突课程明细 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-004 | 4.5 | 日程加入 | 未强制加入冲突活动 | 存在冲突 | POST `/schedules/add-activity` | 返回业务错误 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-005 | 4.5 | 日程加入 | 强制加入冲突活动 | `force_add=true` | POST `/schedules/add-activity` | 写入活动日程并保留冲突信息 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-006 | 4.5 | 自定义日程 | OCR 文本转自定义日程 | 有识别结果 | POST `/check-custom-event` + `/add-custom-event` | 检测冲突并写入个人日程 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-007 | 4.5 | 日程外观 | 修改颜色、标识、备注 | 已有日程 | PATCH `/schedules/{id}/appearance` | 更新外观且不改变类型 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-008 | 4.5 | 日程删除 | 删除活动日程 | 已加入活动 | DELETE `/schedules/{id}` | 只删除个人日程，不删除活动 | `test_schedule_course.py` | 已自动化 |
| TC-4.5-009 | 4.5 | ICS 导出 | 导出日历文件 | 已有日程 | GET `/schedules/export-ics/file` | 返回 `text/calendar` 和 VCALENDAR 内容 | `test_schedule_course.py` | 已自动化 |
| TC-4.6-001 | 4.6 | 后台管理 | 新增活动 | 管理员已登录 | POST `/admin/activities` | 新增活动可在前台查询 | `test_auth_activity.py` | 已自动化 |
| TC-4.6-002 | 4.6 | 后台管理 | 编辑活动 | 管理员已登录 | PUT `/admin/activities/{id}` | 前台详情同步更新 | `test_auth_activity.py` | 已自动化 |
| TC-4.6-003 | 4.6 | 后台管理 | 下架活动 | 管理员已登录 | DELETE `/admin/activities/{id}` | 前台不可见 | `test_auth_activity.py` | 已自动化 |
| TC-4.6-004 | 4.6 | 后台管理 | 后台统计 | 管理员已登录 | GET `/admin/stats` | 返回活动、用户、标签等统计 | `test_auth_activity.py` | 已自动化 |
| TC-4.7-001 | 4.7 | OCR | 管理员活动截图识别 | 管理员已登录 | POST `/admin/activities/recognize-image` | 返回识别文本和活动字段 | `test_ocr_and_crawler.py` | 已自动化 |
| TC-4.7-002 | 4.7 | OCR | 普通用户日程截图识别 | 上传日程截图 | POST `/schedules/recognize-image` | 返回预览事件和冲突信息 | `test_ocr_and_crawler.py` | 已自动化 |
| TC-4.7-003 | 4.7 | OCR | 多截图合并识别 | 最多 5 张图片 | 调用 OCR 服务 | 合并文本并提取标题/时间/地点 | `test_activity_ocr_service.py` | 已自动化 |
| TC-4.7-004 | 4.7 | 爬虫 | 触发爬虫成功 | mock 爬虫结果 | POST `/admin/crawler/run` | 返回抓取数、入库数、过滤数 | `test_ocr_and_crawler.py` | 已自动化 |
| TC-4.7-005 | 4.7 | 爬虫 | 查询爬虫记录 | 存在记录 | GET `/admin/crawler/records` | 返回历史运行记录 | `test_ocr_and_crawler.py` | 已自动化 |
| TC-4.7-006 | 4.7 | 爬虫 | 真实官网抓取 | Docker 环境可联网 | POST `/admin/crawler/run` | 抓取 CS ZJU 官网并入库 | 执行记录 | 已联调 |

## 5 边界测试

| 编号 | 章节 | 模块 | 边界点 | 前置条件 | 操作步骤 | 期望结果 | 证据/脚本 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-5.1-001 | 5.1 | 登录注册 | 错误密码 | 存在用户 | POST `/auth/login` 使用错误密码 | 返回登录失败 | `test_auth_activity.py` | 已自动化 |
| TC-5.1-002 | 5.1 | 登录注册 | 重复用户名 | 存在用户 | POST `/auth/register` | 返回 `code=1004` | `test_auth_activity.py` | 已自动化 |
| TC-5.1-003 | 5.1 | 权限 | token 缺失 | 无 token | GET `/users/me` | HTTP 401 | `test_auth_activity.py` | 已自动化 |
| TC-5.1-004 | 5.1 | 权限 | 普通用户访问后台 | 学生已登录 | GET `/admin/stats` | HTTP 403 | `test_auth_activity.py` | 已自动化 |
| TC-5.2-001 | 5.2 | 活动 | 不存在活动 ID | 无 | GET `/activities/999` | 返回 `code=1003` | `test_activity_features.py` | 已自动化 |
| TC-5.2-002 | 5.2 | 活动 | 无结果筛选 | 无匹配关键词 | GET `/activities?keyword=...` | total 为 0 | `test_activity_features.py` | 已自动化 |
| TC-5.2-003 | 5.2 | 活动 | 非法排序参数 | sort_by 非法 | GET `/activities?sort_by=unknown` | HTTP 422 | `test_activity_features.py` | 已自动化 |
| TC-5.2-004 | 5.2 | 活动 | 非法分页参数 | page=0 | GET `/activities?page=0` | HTTP 422 | `test_activity_features.py` | 已自动化 |
| TC-5.3-001 | 5.3 | 课表导入 | 空文件 | 上传空 CSV | POST `/courses/import` | 返回错误和示例 | `test_schedule_course.py` | 已自动化 |
| TC-5.3-002 | 5.3 | 课表导入 | 错误表头 | 缺少必要列 | POST `/courses/import` | 返回缺失表头说明 | `test_schedule_course.py` | 已自动化 |
| TC-5.3-003 | 5.3 | 课表导入 | 重复课程 | 数据重复 | POST `/courses/import` | 跳过重复并给出错误说明 | `test_schedule_course.py` | 已自动化 |
| TC-5.3-004 | 5.3 | 课表导入 | 旧版 `.xls` | 上传 xls | POST `/courses/import` | 返回暂不支持提示 | `test_schedule_course.py` | 已自动化 |
| TC-5.4-001 | 5.4 | 日程 | 冲突但不强制 | 存在冲突课程 | POST `/add-activity` | 返回冲突错误 | `test_schedule_course.py` | 已自动化 |
| TC-5.4-002 | 5.4 | 日程 | 单双周边界 | 课程 weeks 含单双周 | 查询不同周 | 仅对应周展示 | `test_schedule_course.py` | 已自动化 |
| TC-5.4-003 | 5.4 | 日程 | 春夏学期边界 | weeks 为春/夏 | 查询不同周 | 按学期范围展示 | `test_schedule_course.py` | 已自动化 |
| TC-5.4-004 | 5.4 | 日程 | 默认 16 周边界 | 未填写 weeks | 查询第 16/17 周 | 第 17 周不展示 | `test_schedule_course.py` | 已自动化 |
| TC-5.5-001 | 5.5 | OCR | 超过 5 张截图 | 6 张图片 | 调用 OCR 服务 | 抛出数量限制错误 | `test_activity_ocr_service.py` | 已自动化 |
| TC-5.5-002 | 5.5 | OCR | 仅开始时间 | OCR 文本缺结束时间 | 解析文本 | 保留开始时间并返回提醒 | `test_activity_ocr_service.py` | 已自动化 |
| TC-5.5-003 | 5.5 | OCR | 竖排文本 | 竖排标题 TSV | 解析 OCR 候选 | 重建标题 | `test_activity_ocr_service.py` | 已自动化 |
| TC-5.5-004 | 5.5 | OCR | 接口文件缺失 | 不上传文件 | POST OCR 接口 | 返回业务错误 | `test_ocr_and_crawler.py` | 已自动化 |
| TC-5.6-001 | 5.6 | 后台 | 不存在活动编辑/下架 | 活动不存在 | PUT/DELETE `/admin/activities/999` | 返回 `code=1003` | `test_auth_activity.py` | 已自动化 |
| TC-5.6-002 | 5.6 | 爬虫 | 不支持来源 | source 非 `cs_zju` | POST `/admin/crawler/run` | 返回 `code=5001` | `test_ocr_and_crawler.py` | 已自动化 |
| TC-5.6-003 | 5.6 | 爬虫权限 | 非管理员触发爬虫 | 未登录或学生登录 | POST `/admin/crawler/run` | 当前可触发，记录权限缺陷 | `test_ocr_and_crawler.py`/执行记录 | 记录缺陷 |

## 6 压力/稳定性测试

| 编号 | 章节 | 模块 | 测试点 | 前置条件 | 操作步骤 | 期望结果 | 证据/脚本 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-6.2-001 | 6.2 | 登录 | 连续登录 | 初始化用户 | 重复 POST `/auth/login` | 均返回成功 | `test_stability.py` | 已自动化 |
| TC-6.2-002 | 6.2 | 活动查询 | 连续列表查询 | 初始化活动 | 重复 GET `/activities` | 均返回成功且耗时可接受 | `test_stability.py` | 已自动化 |
| TC-6.3-001 | 6.3 | 推荐 | 连续推荐查询 | 初始化推荐数据 | 重复 GET `/recommendations/activities` | 均返回成功 | `test_stability.py` | 已自动化 |
| TC-6.3-002 | 6.3 | 日程 | 连续日程查询 | 初始化日程 | 重复 GET `/schedules` | 均返回成功 | `test_stability.py` | 已自动化 |
| TC-6.3-003 | 6.3 | ICS | 连续 ICS 导出 | 初始化日程 | 重复 GET `/schedules/export-ics/file` | 均返回 VCALENDAR | `test_stability.py` | 已自动化 |
| TC-6.4-001 | 6.4 | 后台 | 连续后台统计 | 管理员已登录 | 重复 GET `/admin/stats` | 均返回成功 | `test_stability.py` | 已自动化 |

## 7 用户接口测试

| 编号 | 章节 | 页面 | 测试点 | 前置条件 | 操作步骤 | 期望结果 | 证据 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-7.1-001 | 7.1 | 登录页 | 登录/注册入口 | 前端运行 | 打开 `/login` | 输入框、按钮、提示可见 | `screenshots/01-login.png` | 已截图 |
| TC-7.2-001 | 7.2 | 首页推荐 | 推荐卡片展示 | 前端运行 | 打开 `/` | 推荐活动卡片展示并可跳详情 | `screenshots/02-home-recommendations.png` | 已截图 |
| TC-7.3-001 | 7.3 | 活动列表 | 搜索筛选分页 | 前端运行 | 打开 `/activities` | 可搜索、筛选、进入详情 | `screenshots/03-activity-list.png` | 已截图 |
| TC-7.4-001 | 7.4 | 活动详情 | 加入日程反馈 | 学生登录 | 打开活动详情并加入日程 | 正常提示或冲突提示 | `screenshots/04-activity-detail.png` | 已截图 |
| TC-7.5-001 | 7.5 | 课表导入 | 文件导入与手动录入 | 学生登录 | 打开 `/courses/import` | 导入摘要和错误提示清晰 | `screenshots/05-course-import.png` | 已截图 |
| TC-7.6-001 | 7.6 | 日历页 | 周视图、删除、导出 | 学生登录 | 打开 `/calendar` | 日程展示、编辑、导出可操作 | `screenshots/06-calendar.png` | 已截图 |
| TC-7.7-001 | 7.7 | 后台页 | 管理员操作 | 管理员登录 | 打开 `/admin` | 新增、编辑、下架、爬虫日志可操作 | `screenshots/07-admin.png` | 已截图 |
| TC-7.7-002 | 7.7 | 后台页 | 普通用户权限隔离 | 学生登录 | 打开 `/admin` 并请求后台数据 | 后端返回 403，前端提示失败 | 执行记录 | 已联调/记录缺陷 |
