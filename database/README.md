# Database

数据库目录负责维护第一阶段 MySQL 结构和测试数据。

## Files

- `schema.sql`: 建表脚本。
- `seed.sql`: 初始化样例数据。
- `migrations/`: 后续数据库变更脚本。
- `er/`: ER 图和数据库说明。

## Start

```bash
cp .env.example .env
docker compose up --build -d mysql
```

说明：

- MySQL 由 Docker Compose 统一管理。
- 第一次启动时会自动执行 `database/schema.sql` 和 `database/seed.sql`。
- 如果需要重置数据库，执行 `docker compose down -v` 后再重新启动。
