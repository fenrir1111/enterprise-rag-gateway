"""如何把客户的 OA / 文件中心对接成增量同步源。

思路：写一个适配器，周期性拉取文件中心的「文档列表 + 内容 + 权限元数据」，
封装成 Document 列表，调用 `gateway.sync_corpus(docs)` 即可。
`sync_corpus` 会做增量（新增/更新）+ 全量对账（清理已删除）。
"""

from __future__ import annotations

import json
from typing import Any

from rag_gateway.config import get_settings
from rag_gateway.gateway import Gateway
from rag_gateway.models import Document

# 模拟客户文件中心 API 返回
FAKE_FILE_CENTER: list[dict[str, Any]] = [
    {
        "id": "doc-001",
        "tenant_id": "corp",
        "title": "费用报销制度",
        "content": "报销流程需要三级审批，依次为部门审批、财务审批、主管审批。",
        "roles": [],
        "orgs": [],
    },
    {
        "id": "doc-900",
        "tenant_id": "corp",
        "title": "新增制度（演示增量）",
        "content": "差旅住宿标准：一线城市每晚不超过 500 元，需提前申请。",
        "roles": [],
        "orgs": [],
    },
]


def fetch_from_file_center() -> list[Document]:
    """适配器：把文件中心原始数据转成 Document。"""
    docs = []
    for item in FAKE_FILE_CENTER:
        docs.append(
            Document(
                id=item["id"],
                tenant_id=item["tenant_id"],
                title=item["title"],
                content=item["content"],
                allowed_roles=item.get("roles", []),
                allowed_orgs=item.get("orgs", []),
            )
        )
    return docs


def main() -> None:
    s = get_settings()
    gw = Gateway()
    # 先把内置种子语料入库
    from rag_gateway.gateway import load_corpus

    gw.sync_corpus(load_corpus(s.corpus_path))
    before = len(gw.documents)
    # 增量同步：新增 doc-900
    res = gw.sync_corpus(fetch_from_file_center())
    print(
        f"同步前文档 {before} 篇 → 同步后 {len(gw.documents)} 篇 | "
        f"新增 {res.added} 更新 {res.updated} 清理 {res.removed} 分块 {res.chunks}"
    )
    print("审计最近一条：", json.dumps(gw.audit.recent(1), ensure_ascii=False))


if __name__ == "__main__":
    main()
