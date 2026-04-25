# Crawler

Crawler skeleton for collecting public academic activity pages.

第一阶段建议只接入一个学院数据源，例如计算机学院官网，跑通：

```text
目标网页 -> 抓取 HTML -> 字段解析 -> 去重清洗 -> 写入 activity 表
```

## Start

```bash
pip install -r requirements.txt
python -m spiders.cs_zju
```
