# 接口规范

统一前缀：

```text
/api/v1
```

统一响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## 第一阶段接口清单

```text
POST   /api/v1/auth/login
POST   /api/v1/auth/register
GET    /api/v1/users/me
GET    /api/v1/activities
GET    /api/v1/activities/filter-options
GET    /api/v1/activities/{id}
POST   /api/v1/activities/{id}/interactions
GET    /api/v1/recommendations/activities
GET    /api/v1/schedules
POST   /api/v1/schedules/check-conflict
POST   /api/v1/schedules/add-activity
POST   /api/v1/schedules/check-custom-event
POST   /api/v1/schedules/add-custom-event
POST   /api/v1/schedules/recognize-image
DELETE /api/v1/schedules/{event_id}
PATCH  /api/v1/schedules/{event_id}/appearance
GET    /api/v1/schedules/export-ics
GET    /api/v1/schedules/export-ics/file
GET    /api/v1/courses
POST   /api/v1/courses
GET    /api/v1/courses/template
POST   /api/v1/courses/import
POST   /api/v1/courses/ocr
DELETE /api/v1/courses/{id}
POST   /api/v1/admin/activities
POST   /api/v1/admin/activities/recognize-image
PUT    /api/v1/admin/activities/{id}
DELETE /api/v1/admin/activities/{id}
GET    /api/v1/admin/stats
GET    /api/v1/admin/recommendations/preview
POST   /api/v1/admin/crawler/run
GET    /api/v1/admin/crawler/records
```

## 认证与用户

### `POST /api/v1/auth/login`

请求体：

```json
{
  "username": "student001",
  "password": "123456"
}
```

成功响应 `data`：

```json
{
  "token": "jwt token",
  "user": {
    "id": 1,
    "username": "student001",
    "role": "student",
    "major": "计算机科学与技术",
    "college": "计算机科学与技术学院"
  }
}
```

失败响应：

```json
{
  "code": 1001,
  "message": "用户名或密码错误",
  "data": null
}
```

### `GET /api/v1/users/me`

请求头：

```text
Authorization: Bearer <token>
```

成功响应 `data` 为当前用户公开信息，字段同登录响应中的 `user`。

## 活动接口

### `GET /api/v1/activities`

查询参数：

| 参数 | 说明 |
| --- | --- |
| `keyword` | 按标题、简介、主讲人、组织方、地点模糊搜索 |
| `category` | 活动类别 |
| `campus` | 校区 |
| `college` | 学院 |
| `tag` | 活动标签 |
| `start_from` | 活动开始时间下界，ISO datetime |
| `start_to` | 活动开始时间上界，ISO datetime |
| `sort_by` | `time` / `hot` / `recommend` |
| `page` | 页码，从 1 开始 |
| `page_size` | 每页数量 |

成功响应 `data`：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10,
  "filters": {}
}
```

活动条目字段：`id`、`title`、`description`、`speaker`、`organizer`、`college`、`category`、`campus`、`location`、`start_time`、`end_time`、`source_url`、`source_type`、`hot_score`、`status`、`tags`。

当 `sort_by=recommend` 时，活动条目额外包含 `recommend_score`，用于按通用推荐分排序。

### `GET /api/v1/activities/filter-options`

返回当前开放活动可用的筛选项：

```json
{
  "categories": ["讲座", "沙龙"],
  "campuses": ["紫金港", "玉泉", "西溪", "华家池", "之江", "舟山", "海宁"],
  "colleges": ["计算机科学与技术学院"],
  "tags": ["人工智能", "数据库"]
}
```

### `GET /api/v1/activities/{id}`

成功响应 `data` 为单个活动详情，字段与活动列表项一致。

活动不存在时返回：

```json
{
  "code": 1003,
  "message": "活动不存在",
  "data": null
}
```

### `POST /api/v1/activities/{id}/interactions`

记录当前用户对活动的行为，用于个性化推荐画像。认证为可选：携带合法 `Authorization: Bearer <token>` 时写入行为日志；未登录或 token 无效时返回成功但不写入，避免影响活动详情浏览。

请求体：

```json
{
  "action_type": "view",
  "source": "activity_detail"
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `action_type` | `view` / `add_schedule` |
| `source` | 可选。行为来源，例如 `activity_detail` |

成功响应 `data`：

```json
{
  "recorded": true,
  "id": 1,
  "activity_id": 101,
  "action_type": "view",
  "source": "activity_detail",
  "created_at": "2026-05-26T10:00:00"
}
```

未登录时：

```json
{
  "recorded": false,
  "reason": "anonymous_user",
  "activity_id": 101,
  "action_type": "view"
}
```

## 推荐接口

### `GET /api/v1/recommendations/activities`

查询参数：

| 参数 | 说明 |
| --- | --- |
| `limit` | 返回数量，范围 1-50，默认 10 |

认证为可选。请求头包含 `Authorization: Bearer <token>` 时，按当前用户兴趣标签、最近 60 天活动行为、学院和日程冲突计算个性化推荐；不包含 token 时，按热度和时间临近度返回通用推荐。

推荐流程采用“候选生成 → 打分排序 → 多样性重排”：

```text
recommend_score =
  显式兴趣匹配分
  + 历史行为标签分
  + 热度分
  + 时间临近分
  + 学院相关分
  - 时间冲突惩罚
```

候选集只包含 `status=open` 且未结束的活动；登录用户已加入日程的活动会被排除。历史行为只统计 `view` 和 `add_schedule`，其中 `add_schedule` 权重高于普通浏览。

成功响应 `data`：

```json
{
  "items": []
}
```

推荐活动字段包含活动基础字段，并额外包含：

| 字段 | 说明 |
| --- | --- |
| `recommend_score` | 推荐分 |
| `reason` | 推荐理由 |
| `matched_tags` | 命中的用户兴趣标签 |
| `has_conflict` | 是否与当前用户已有日程冲突 |
| `score_breakdown` | 推荐分明细：`explicit_interest`、`behavior_history`、`hot`、`time`、`college`、`conflict_penalty`、`total` |

## 日程与课表接口

### `GET /api/v1/schedules`

查询当前用户的课程和已加入活动日程。可选参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `start_date` | string | 开始日期，格式 `YYYY-MM-DD` 或 ISO datetime |
| `end_date` | string | 结束日期，格式 `YYYY-MM-DD` 或 ISO datetime |

课程日程由 `course_schedule` 按请求周动态展开；当前学期按 `2026-03-02` 为第 1 周周一计算，因此 `2026-05-25` 所在周为第 13 周。`weeks` 中的 `1-16`、`单周`、`双周` 会用于过滤对应周次。

返回 `data.items`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | int | 日程 ID |
| `title` | string | 日程标题 |
| `type` | string | `course` 或 `activity` |
| `course_id` | int/null | 关联课程 ID，仅课程日程有值 |
| `activity_id` | int/null | 关联活动 ID |
| `start_time` | datetime | 开始时间 |
| `end_time` | datetime | 结束时间 |
| `location` | string/null | 地点 |
| `remark` | string/null | 用户编辑的日程备注，日历块中最多显示一行 |
| `status` | string | `open` 或 `closed` |
| `color_type` | string | 颜色 key：`blue` / `green` / `teal` / `amber` / `orange` / `red` / `purple` / `pink` / `gray` |
| `marker_label` | string | 日历块标题前显示的单字标识 |
| `is_conflict` | bool | 是否与其他日程时间重叠，独立于颜色 |

### `POST /api/v1/schedules/check-conflict`

请求：

```json
{
  "activity_id": 101
}
```

返回活动与当前用户已有日程的冲突结果：

```json
{
  "activity_id": 101,
  "has_conflict": true,
  "activity": {},
  "conflicts": []
}
```

### `POST /api/v1/schedules/add-activity`

请求：

```json
{
  "activity_id": 101,
  "force_add": false
}
```

规则：

- 若无冲突，直接写入 `schedule_event`。
- 若有冲突且 `force_add=false`，返回失败响应，提示用户确认。
- 若有冲突且 `force_add=true`，仍写入日程，并默认使用红色标识；冲突状态通过 `is_conflict` 返回，不与颜色绑定。

### `POST /api/v1/schedules/recognize-image`

普通用户从活动截图中识别日程信息。接口只解析并返回预览，不直接写入日程。

请求类型：`multipart/form-data`

| 字段 | 说明 |
| --- | --- |
| `files` | 活动截图，可重复提交，最多 5 张，支持 PNG、JPG、WEBP、BMP、TIFF |
| `file` | 兼容旧版单张截图上传 |

若截图只识别到开始时间，`end_time` 返回 `null`，并在 `warnings` 中提示填写预计时长；前端根据用户填写的预计时长自动生成结束时间。

成功响应 `data`：

```json
{
  "filenames": ["activity-1.png", "activity-2.png"],
  "raw_text": "人工智能前沿讲座\n时间:2026年5月10日 14:00-16:00\n地点:紫金港东1A-101",
  "screenshots": [
    {
      "filename": "activity-1.png",
      "raw_text": "人工智能前沿讲座\n时间:2026年5月10日 14:00-16:00"
    },
    {
      "filename": "activity-2.png",
      "raw_text": "地点:紫金港东1A-101"
    }
  ],
  "activity": {
    "title": "人工智能前沿讲座",
    "location": "紫金港东1A-101",
    "start_time": "2026-05-10T14:00:00",
    "end_time": "2026-05-10T16:00:00"
  },
  "event": {
    "title": "人工智能前沿讲座",
    "type": "activity",
    "activity_id": null,
    "start_time": "2026-05-10T14:00:00",
    "end_time": "2026-05-10T16:00:00",
    "location": "紫金港东1A-101",
    "remark": null,
    "color_type": "green",
    "marker_label": "活",
    "is_conflict": false
  },
  "has_conflict": false,
  "conflicts": [],
  "warnings": []
}
```

### `POST /api/v1/schedules/check-custom-event`

检测一个未入库的自定义活动日程是否与已有课程/活动冲突。

请求：

```json
{
  "title": "人工智能前沿讲座",
  "start_time": "2026-05-10T14:00:00",
  "end_time": "2026-05-10T16:00:00",
  "location": "紫金港东1A-101",
  "remark": "请提前到场"
}
```

成功响应 `data`：`has_conflict`、`event`、`conflicts`。

### `POST /api/v1/schedules/add-custom-event`

把截图识别或手动补全的自定义活动加入个人日程，不要求活动先进入活动库。

请求：

```json
{
  "title": "人工智能前沿讲座",
  "start_time": "2026-05-10T14:00:00",
  "end_time": "2026-05-10T16:00:00",
  "location": "紫金港东1A-101",
  "remark": "请提前到场",
  "color_type": "green",
  "marker_label": "讲",
  "force_add": true
}
```

若有冲突且 `force_add=false`，返回 `code=3007`；用户确认后用 `force_add=true` 可加入。

### `DELETE /api/v1/schedules/{event_id}`

删除当前用户的一条非课程日程。当前用于从个人日历中移除已加入活动，不会下架活动本身。

成功响应：

```json
{
  "id": 12,
  "title": "人工智能前沿讲座",
  "type": "activity",
  "activity_id": 101
}
```

课程日程需继续使用 `DELETE /api/v1/courses/{id}`，以保证课程记录和对应日程同步删除。

### `PATCH /api/v1/schedules/{event_id}/appearance`

更新课程或活动日程的展示标识。颜色和类型互不影响。

请求：

```json
{
  "color_type": "pink",
  "marker_label": "讲",
  "remark": "带学生证"
}
```

`color_type` 可选值：`blue`、`green`、`teal`、`amber`、`orange`、`red`、`purple`、`pink`、`gray`。`marker_label` 必须是一个字；`remark` 可为空，最长 500 字。

成功响应 `data` 为更新后的日程事件对象，字段同 `GET /api/v1/schedules` 的单条 `items`。

### `GET /api/v1/schedules/export-ics`

返回统一响应，包含 ICS 文件下载地址：

```json
{
  "download_url": "/api/v1/schedules/export-ics/file",
  "event_count": 2
}
```

### `GET /api/v1/schedules/export-ics/file`

下载当前用户全部日程，响应类型为 `text/calendar`，文件名为 `schedule.ics`。

### `GET /api/v1/courses`

查询当前用户已导入或手动新增的课程列表。

### `POST /api/v1/courses`

手动新增课程。请求：

```json
{
  "course_name": "软件工程",
  "weekday": 2,
  "start_section": 3,
  "end_section": 4,
  "location": "玉泉曹楼",
  "teacher": "李老师",
  "weeks": "1-16"
}
```

写入 `course_schedule` 后，会同步生成一条 `schedule_event` 作为颜色/标识模板；日历查询时再按请求周和 `weeks` 动态展开课程日程。

### `DELETE /api/v1/courses/{id}`

删除当前用户课程，并同步删除对应的课程日程事件。支持查询参数 `scope`：

| 参数值 | 说明 |
| --- | --- |
| `one` | 默认值，仅删除当前点击的这一条课程时段 |
| `day` | 删除同一门课在同一星期的所有课程时段 |
| `all` | 删除同一门课的全部课程时段 |

```json
{
  "id": 1,
  "scope": "one",
  "course_name": "软件工程",
  "deleted_courses": 1,
  "deleted_course_ids": [1],
  "deleted_events": 1
}
```

前端入口在日历课程块的详情弹窗中，不在“即将开始”列表中删除。

### `POST /api/v1/courses/import`

上传 CSV/XLSX/XLSM 课表文件。支持列名：

```text
课程名/课程名称/course_name
星期/周几/weekday
节次/sections 或 开始节次/start_section + 结束节次/end_section
地点/location
教师/teacher
周次/weeks
```

同时支持教务导出的课表格式，例如 `课表_3230106240.xlsx`：

```text
第 1 行：2025-2026学年春夏学期某某的课表
第 2 行：课程代码 | 课程名称 | 教师姓名 | 学期 | 上课时间 | 上课地点 | ...
数据行：CS3100M | 编译原理 | 刘老师 | 春夏 | 周一第3,4,5节;周三第1,2节 | 玉泉教4-310;玉泉曹光彪西-503
```

导入时会自动把一个课程的多个上课时段拆成多条 `course_schedule` 规则；地点按分号顺序与上课时段对应。`{单周}`、`{双周}` 等信息会写入 `weeks` 字段，日历查询时再按周次动态展开。

节次时间映射：

```text
1  08:00-08:45
2  08:50-09:35
3  10:00-10:45
4  10:50-11:35
5  11:40-12:25
6  13:25-14:10
7  14:15-15:00
8  15:05-15:50
9  16:15-17:00
10 17:05-17:50
11 18:50-19:35
12 19:40-20:25
13 20:30-21:15
```

返回导入数量、跳过数量、已导入课程和错误行说明。

### `GET /api/v1/courses/template`

返回课表导入模板，供前端展示和下载。响应包含：

| 字段 | 说明 |
| --- | --- |
| `headers` / `rows` / `csv` | 普通 CSV 模板 |
| `zju_title` / `zju_headers` / `zju_rows` / `zju_csv` | 教务导出示例，结构与 `课表_3230106240.xlsx` 类似 |
| `supported_extensions` | 支持的文件后缀：`.csv`、`.xlsx`、`.xlsm` |
| `notes` | 导入注意事项 |

### `POST /api/v1/courses/ocr`

课表截图 OCR 预留接口，第一阶段返回 `reserved` 状态。

## mxy 认证接口补充（2026-05-24）

### `POST /api/v1/auth/register`

注册普通学生用户。注册接口不允许指定管理员角色，新用户固定写入为 `student`。

请求体：

```json
{
  "username": "newstudent",
  "password": "123456",
  "major": "软件工程",
  "college": "软件学院"
}
```

成功响应 `data`：

```json
{
  "token": "jwt token",
  "user": {
    "id": 3,
    "username": "newstudent",
    "role": "student",
    "major": "软件工程",
    "college": "软件学院"
  }
}
```

用户名已存在时返回：

```json
{
  "code": 1004,
  "message": "用户名已存在",
  "data": null
}
```

### 管理员登录与权限

管理员继续使用 `POST /api/v1/auth/login` 登录。只要 `user.role = "admin"`，登录响应中的 `user.role` 会返回 `admin`，JWT 里也会携带管理员角色。

当前测试管理员账号：

```text
admin001 / 123456
```

所有 `/api/v1/admin/*` 接口现在要求请求头携带管理员 token：

```text
Authorization: Bearer <admin token>
```

未登录返回 HTTP 401，非管理员用户返回 HTTP 403。

## 后台接口

### `POST /api/v1/admin/activities`

管理员新增活动，要求携带管理员 token。活动写入 `activity` 表，默认 `source_type=manual`、`hot_score=0`、`status=open`；成功后可在活动列表查询到。

### `POST /api/v1/admin/activities/recognize-image`

用于从活动截图中识别标题、时间、地点等字段，只返回识别结果，不直接创建活动。

请求类型：`multipart/form-data`

| 字段 | 说明 |
| --- | --- |
| `files` | 活动截图，可重复提交，最多 5 张，支持 PNG、JPG、WEBP、BMP、TIFF |
| `file` | 兼容旧版单张截图上传 |

若截图只识别到开始时间，`end_time` 返回 `null`，并在 `warnings` 中提示填写预计时长；前端根据用户填写的预计时长自动生成结束时间。

成功响应 `data`：

```json
{
  "filename": "activity.png",
  "filenames": ["activity-1.png", "activity-2.png"],
  "raw_text": "人工智能前沿讲座\n时间:2026年5月10日 14:00-16:00\n地点:紫金港东1A-101",
  "screenshots": [
    {
      "filename": "activity-1.png",
      "raw_text": "人工智能前沿讲座\n时间:2026年5月10日 14:00-16:00"
    },
    {
      "filename": "activity-2.png",
      "raw_text": "地点:紫金港东1A-101"
    }
  ],
  "activity": {
    "title": "人工智能前沿讲座",
    "description": "时间:2026年5月10日 14:00-16:00\n地点:紫金港东1A-101",
    "speaker": null,
    "organizer": null,
    "college": null,
    "category": "学术讲座",
    "campus": "紫金港",
    "location": "紫金港东1A-101",
    "start_time": "2026-05-10T14:00:00",
    "end_time": "2026-05-10T16:00:00",
    "source_url": null
  },
  "warnings": []
}
```

失败响应：

```json
{
  "code": 4001,
  "message": "OCR 引擎未安装，请重新构建 backend 镜像后再试。",
  "data": null
}
```

### `PUT /api/v1/admin/activities/{id}`

管理员编辑已存在活动并持久化到 `activity` 表。活动不存在时返回 `code=1003`。

### `DELETE /api/v1/admin/activities/{id}`

管理员下架活动，将 `activity.status` 更新为 `offline`；下架后普通活动列表和详情不再展示该活动。

### `GET /api/v1/admin/stats`

返回后台辅助统计：

```json
{
  "activity_count": 2,
  "open_activity_count": 2,
  "offline_activity_count": 0,
  "user_count": 2,
  "tag_count": 5,
  "campus_count": 2,
  "category_count": 2,
  "average_hot_score": 75.5,
  "max_hot_score": 87
}
```

### `GET /api/v1/admin/recommendations/preview`

查询参数：

| 参数 | 说明 |
| --- | --- |
| `user_id` | 可选。指定用户后按该用户兴趣和日程预览推荐；为空时返回通用推荐 |
| `limit` | 返回数量，范围 1-50，默认 10 |

成功响应字段同 `GET /api/v1/recommendations/activities`。
