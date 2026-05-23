# Crawler

Crawler skeleton for collecting public academic activity pages.

第一阶段建议只接入一个学院数据源，例如计算机学院官网，跑通：

```text
目标网页 -> 抓取 HTML -> 字段解析 -> 去重清洗 -> 写入 activity 表
```

## Start

```bash
docker compose up --build -d
docker compose exec backend python -m crawler.spiders.cs_zju
```

爬虫依赖由 `backend/requirements.txt` 在 backend 镜像构建时统一安装，不再要求组员本地单独维护 Python 虚拟环境。
