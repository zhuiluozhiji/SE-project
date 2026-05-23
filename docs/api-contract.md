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
GET    /api/v1/users/me
GET    /api/v1/activities
GET    /api/v1/activities/{id}
GET    /api/v1/recommendations/activities
GET    /api/v1/schedules
POST   /api/v1/schedules/check-conflict
POST   /api/v1/schedules/add-activity
GET    /api/v1/schedules/export-ics
GET    /api/v1/schedules/export-ics/file
GET    /api/v1/courses
POST   /api/v1/courses
GET    /api/v1/courses/template
POST   /api/v1/courses/import
POST   /api/v1/courses/ocr
DELETE /api/v1/courses/{id}
POST   /api/v1/admin/activities
PUT    /api/v1/admin/activities/{id}
DELETE /api/v1/admin/activities/{id}
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
| `keyword` | 按标题、简介、主讲人、组织方模糊搜索 |
| `category` | 活动类别 |
| `campus` | 校区 |
| `college` | 学院 |
| `tag` | 活动标签 |
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

## 日程与课表接口

### `GET /api/v1/schedules`

查询当前用户的课程和已加入活动日程。可选参数：

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `start_date` | string | 开始日期，格式 `YYYY-MM-DD` 或 ISO datetime |
| `end_date` | string | 结束日期，格式 `YYYY-MM-DD` 或 ISO datetime |

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
| `status` | string | `open` 或 `closed` |
| `color_type` | string | `course` / `activity` / `conflict` |

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
- 若有冲突且 `force_add=true`，仍写入日程，并将新事件 `color_type` 标记为 `conflict`。

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

写入 `course_schedule` 后，会同步生成一条 `schedule_event` 课程日程。

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

导入时会自动把一个课程的多个上课时段拆成多条课程日程；地点按分号顺序与上课时段对应。`{单周}`、`{双周}` 等信息会写入 `weeks` 字段。

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
