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
POST   /api/v1/courses
POST   /api/v1/courses/import
POST   /api/v1/courses/ocr
POST   /api/v1/admin/activities
PUT    /api/v1/admin/activities/{id}
DELETE /api/v1/admin/activities/{id}
POST   /api/v1/admin/crawler/run
GET    /api/v1/admin/crawler/records
```

## mxy 已落地接口

### POST /api/v1/auth/login

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

### GET /api/v1/users/me

请求头：

```text
Authorization: Bearer <token>
```

成功响应 `data` 为当前用户公开信息，字段同登录响应中的 `user`。

### GET /api/v1/activities

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
  "page_size": 10
}
```

活动条目字段：`id`、`title`、`description`、`speaker`、`organizer`、`college`、`category`、`campus`、`location`、`start_time`、`end_time`、`source_url`、`source_type`、`hot_score`、`status`、`tags`。

### GET /api/v1/activities/{id}

成功响应 `data` 为单个活动详情，字段与活动列表项一致。

活动不存在时返回：

```json
{
  "code": 1003,
  "message": "活动不存在",
  "data": null
}
```
