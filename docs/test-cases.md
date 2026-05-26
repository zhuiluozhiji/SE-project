# 测试用例

| 编号 | 模块 | 测试点 | 前置条件 | 操作步骤 | 期望结果 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-001 | 登录 | 正常登录 | 存在测试用户 | 输入账号密码并登录 | 返回 token 并进入首页 | 未执行 |
| TC-002 | 活动 | 活动列表查询 | 存在活动数据 | 打开活动列表页 | 显示活动卡片和分页 | 已自动化 |
| TC-003 | 日程 | 冲突检测 | 已导入课程 | 添加冲突活动 | 显示冲突提示 | 已自动化 |
| TC-004 | 后台 | 下架活动 | 管理员登录 | 下架一条活动 | 前台不再展示该活动 | 未执行 |
| TC-005 | 课程 | 手动录入课程 | 已登录普通用户 | 调用 `POST /api/v1/courses` | 写入课程表并生成课程日程 | 已自动化 |
| TC-006 | 课程 | CSV/Excel 课表导入 | 准备符合模板或教务导出格式的文件，包括 `课表_3230106240.xlsx` 类似文件 | 调用 `POST /api/v1/courses/import` | 返回导入数量、课程明细和跳过说明 | 已自动化 |
| TC-007 | 日程 | 冲突活动强制加入 | 已存在冲突课程 | 调用 `POST /api/v1/schedules/add-activity` 且 `force_add=true` | 写入活动日程并保留冲突明细 | 已自动化 |
| TC-008 | 日程 | ICS 导出 | 已存在课程或活动日程 | 调用 `GET /api/v1/schedules/export-ics` 和 `/file` | 返回下载地址和 `text/calendar` ICS 文件 | 已自动化 |
| TC-009 | 课程 | 删除课程 | 已存在课程及对应日程 | 调用 `DELETE /api/v1/courses/{id}` | 删除当前课程并同步删除课程日程 | 已自动化 |
| TC-010 | 课程 | 按范围删除课程 | 已存在同一门课的多个时段 | 调用 `DELETE /api/v1/courses/{id}?scope=day/all` | 可删除当天这门课或全部这门课，并保留无关课程 | 已自动化 |
| TC-011 | 日程 | 日程标识与备注更新 | 已存在课程或活动日程 | 调用 `PATCH /api/v1/schedules/{event_id}/appearance` | 更新日程 `color_type`、`marker_label` 和 `remark`，类型不随颜色变化 | 已自动化 |
| TC-012 | 日程 | 删除活动日程 | 已加入活动日程 | 调用 `DELETE /api/v1/schedules/{event_id}` | 仅移除个人日程，不删除活动本身 | 已自动化 |
| TC-013 | 后台 | 活动截图识别解析 | 已准备包含标题、时间、地点的活动截图或 OCR 文本，单个活动最多 5 张截图 | 调用 `POST /api/v1/admin/activities/recognize-image`，或直接测试解析服务 | 返回识别文本，并提取活动标题、地点、开始时间；结束时间缺失时返回提醒，由前端预计时长补全 | 已自动化 |
| TC-014 | 日程 | 普通用户截图加入日程 | OCR 已提取活动标题、时间、地点且与课程冲突；前端支持上传或 `Option/Alt + Shift + S` 快捷截屏，并可补充备注 | 调用 `POST /api/v1/schedules/check-custom-event` 后再用 `force_add=true` 调用 `/add-custom-event` | 先返回冲突明细，确认后写入带备注的个人活动日程 | 已自动化 |

## mxy 接口测试补充

| 编号 | 模块 | 测试点 | 前置条件 | 操作步骤 | 期望结果 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| TC-MXY-001 | 登录 | 正确账号密码登录 | 数据库存在 `student001` | POST `/api/v1/auth/login`，密码 `123456` | 返回 `code=0`、JWT token 和用户信息 | 已加入自动化测试 |
| TC-MXY-002 | 用户 | 获取当前用户 | 已通过登录拿到 token | GET `/api/v1/users/me`，携带 Bearer token | 返回当前用户公开信息 | 已加入自动化测试 |
| TC-MXY-003 | 活动 | 活动列表查询 | 数据库存在 open 活动 | GET `/api/v1/activities?page=1&page_size=10` | 返回分页结构、活动条目和标签 | 已加入自动化测试 |
| TC-MXY-004 | 活动 | 活动详情查询 | 数据库存在活动 101 | GET `/api/v1/activities/101` | 返回活动详情字段 | 已加入自动化测试 |
| TC-MXY-005 | 注册 | 新用户注册 | 用户名未被占用 | POST `/api/v1/auth/register` | 返回 `code=0`、JWT token 和 `student` 用户信息 | 已加入自动化测试 |
| TC-MXY-006 | 注册 | 重复用户名注册 | 数据库已存在 `student001` | POST `/api/v1/auth/register` | 返回 `code=1004` | 已加入自动化测试 |
| TC-MXY-007 | 后台权限 | 学生访问后台被拒 | 学生已登录 | GET `/api/v1/admin/stats`，携带学生 token | 返回 HTTP 403 | 已加入自动化测试 |
| TC-MXY-008 | 后台权限 | 管理员访问后台成功 | 管理员已登录 | GET `/api/v1/admin/stats`，携带管理员 token | 返回后台统计数据 | 已加入自动化测试 |
