# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/) 与语义化版本。

## [0.1.0] - 2026-11-03

### Added
- 多租户隔离：租户独立向量空间，召回只在租户内进行。
- 文档级细粒度权限：组织 / 角色白名单，**召回阶段过滤**（越权片段不进上下文）。
- 文档 Ingestion：分块（按句边界）、内容校验和、增量同步判定（new/updated/unchanged）、全量对账清理。
- 检索链路：确定性哈希向量召回（余弦）+ 词重叠 Rerank（可开关）。
- 生成：抽取式回答（兜底）+ 可选 LLM 生成（litellm）。
- 敏感词过滤 + 回答水印 + 无命中拒答（不编造）。
- 全链路审计日志：JSONL 落盘 + 内存环形缓冲，`GET /audit` 可查。
- FastAPI 接口：`POST /query`、`POST /sync`、`GET /docs`、`GET /tenants`、`GET /audit`、`GET /health`。
- 内置企业制度种子语料（多租户、含角色/组织权限标签）。
- 全链路 demo（`make demo`）与 pytest 测试。
- 工程化：`Makefile`、`Dockerfile`、`docker-compose.yml`、`.env.example`、PRD / architecture / limitation 文档、Streamlit 可视化后台、OA 同步适配器示例。

> 说明：当前为 v0 版本，定位 POC / 试点交付辅助底座，**不建议不经评估直接上核心生产**。

## [0.0.1] - 2026-11-03
### Planned
- v0.2：OA / 文件中心适配器、增量同步
- v0.3：溯源引用、水印、导出管控
- v0.4：对接 enterprise-ai-eval-harness 自动评测 RAG 效果
