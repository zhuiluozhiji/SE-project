# Tests

测试同学的主要开发目录。

## Structure

- `api/`: 接口测试脚本或 HTTP collection。
- `e2e/`: 端到端测试脚本。
- `data/`: 测试数据。

## Suggested order

1. 先用 Swagger 或 `.http` 文件验证接口返回格式。
2. 再补充 pytest/httpx 自动化测试。
3. 最后按 `docs/test-cases.md` 做完整手工验收。
