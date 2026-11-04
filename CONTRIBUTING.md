# 贡献指南 · enterprise-rag-gateway

感谢你愿意参与这个项目。这个仓库的核心主张只有一句：**先控权限，再做问答。**

所以任何改动，都要先回答：**这个改动会不会让没权限的人看到不该看的内容？**

## 快速开始

```bash
git clone https://github.com/fenrir1111/enterprise-rag-gateway.git
cd enterprise-rag-gateway

uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
uv pip install --python .venv/bin/python -e .

.venv/bin/python -m rag_gateway.demo    # 全链路 demo（租户隔离 + 权限 + 同步 + 审计）
.venv/bin/python -m pytest -q            # 跑测试
.venv/bin/python -m uvicorn rag_gateway.main:app --port 8000
```

## 提交前必做

```bash
.venv/bin/python -m pytest -q --basetemp="$PWD/.pytest-tmp"   # 必须全绿
.venv/bin/python -m rag_gateway.demo                          # 必须退出码 0
```

CI 会自动跑上面两步，再加 FastAPI `/health` 与 Streamlit 控制台冒烟（Python 3.10 / 3.12 双版本）。

## 哪些改动受欢迎

| 类型 | 例子 |
|---|---|
| 向量库适配 | 新增后端的索引存取实现（Qdrant / Milvus / PGVector） |
| OA / 文件中心适配器 | 增量同步与对账逻辑 |
| 行业语料与敏感词表 | 政务、央企、制度类文档样例 |
| 权限模型增强 | 新增组织层级、文档密级、临时授权 |
| 敏感信息处理 | 新的敏感词规则、正则、实体识别 |

## 哪些改动不会被接受

- **把权限过滤从召回阶段挪到生成之后的**：那样越权内容已经进过上下文，遮罩也遮不干净
- **引入跨租户检索的捷径**：租户隔离是硬边界，任何"优化"都不能绕过
- **默认开启 LLM 生成并要求外网 API**：本项目默认零外部依赖，数据不出域
- **在审计日志里记录完整敏感原文**：审计只记元数据与命中位置

## 代码约定

- **Python ≥3.10**，`from __future__ import annotations` 开头，类型标注齐全
- **行宽 100 以内**，命名 `snake_case`，公开 API 用 docstring 说明「为什么」
- **相对导入用绝对导入**：`streamlit_app.py` 会被 Streamlit 当独立脚本执行，
  相对导入会直接 `ImportError` —— 统一写成 `from rag_gateway.xxx import ...`。
  **包括 `if` 分支 / 函数里的延迟导入** —— 那类 bug 首屏正常，只有用户点到该分支才炸，
  AppTest 初始渲染和 HTTP 200 都看不出来。`tests/test_streamlit_app.py` 用 AST 全量扫描 +
  点击主按钮的交互冒烟，在 CI 里守住这条。
- **权限相关改动必须配「越权用例」**：证明无权身份确实拿不到内容
- **审计记录不可省**：每次检索都要落审计（租户、身份、命中文档、敏感词计数）

## 提交信息

```
feat: 新增 Qdrant 向量库适配器
fix: 修复组织层级权限未递归下钻到子部门的问题
docs: 补充敏感词表配置说明
```

## Issue

提 Issue 时请尽量带上：

1. 复现步骤或最小样例
2. 期望行为 vs 实际行为
3. 运行环境（Python 版本、向量库类型）
4. 相关审计日志片段（**注意脱敏**，不要贴真实制度原文）

## 致谢

有效贡献会在 README 的致谢栏署名。

## License

贡献即视为同意以 MIT 协议授权你的改动。
