# Database

数据库目录负责维护第一阶段 MySQL 结构和测试数据。

## Files

- `schema.sql`: 建表脚本。
- `seed.sql`: 初始化样例数据。
- `migrations/`: 后续数据库变更脚本。
- `er/`: ER 图和数据库说明。

## Local MySQL

```bash
mysql -u root -p < database/schema.sql
mysql -u root -p < database/seed.sql
```
