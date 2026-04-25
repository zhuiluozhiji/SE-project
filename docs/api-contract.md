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
