from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .audit import AuditLogger
from .config import get_settings
from .embedding import embed_with_bigrams
from .filter import add_watermark, filter_sensitive
from .generator import extractive_answer, llm_answer
from .ingestion import IngestResult, build_chunks, chunk_text, sync_state
from .models import Chunk, Document, Tenant, User
from .permission import filter_by_permission
from .retrieval import recall, rerank


class Gateway:
    """企业 RAG 网关：多租户 + 文档权限 + 增量同步 + 召回/重排 + 审计 + 敏感过滤。

    设计原则：先控权限，再做问答。权限在**召回阶段**过滤，越权片段不进入上下文。
    """

    def __init__(self, audit: Optional[AuditLogger] = None) -> None:
        s = get_settings()
        self.dim = s.embedding_dim
        self.top_k = s.top_k
        self.rerank = s.rerank
        self.llm = s
        self.audit = audit or AuditLogger(path=s.audit_log_path)
        self.tenants: dict[str, Tenant] = {}
        self.documents: dict[str, Document] = {}
        self.chunks: list[Chunk] = []

    # ---------- 租户 ----------
    def ensure_tenant(self, tenant_id: str, name: str = "") -> Tenant:
        if tenant_id not in self.tenants:
            self.tenants[tenant_id] = Tenant(id=tenant_id, name=name or tenant_id)
        return self.tenants[tenant_id]

    # ---------- 文档 / 增量同步 ----------
    def ingest(self, doc: Document) -> dict:
        """单文档入库（增量）：new/updated/unchanged。"""
        self.ensure_tenant(doc.tenant_id)
        state = sync_state(doc, self.documents)
        if state == "unchanged":
            return {"id": doc.id, "state": "unchanged"}
        # 移除该文档旧分块
        self.chunks = [c for c in self.chunks if c.doc_id != doc.id]
        self.chunks.extend(build_chunks(doc, self.dim))
        doc.version += 1 if state == "updated" else 1
        self.documents[doc.id] = doc
        return {"id": doc.id, "state": state}

    def sync_corpus(self, docs: list[Document]) -> IngestResult:
        """全量对账：新增/更新入库，清理语料中已不存在的文档。"""
        res = IngestResult()
        incoming_ids = {d.id for d in docs}
        for doc in docs:
            self.ensure_tenant(doc.tenant_id)
            state = sync_state(doc, self.documents)
            if state == "unchanged":
                res.unchanged += 1
                continue
            self.chunks = [c for c in self.chunks if c.doc_id != doc.id]
            self.chunks.extend(build_chunks(doc, self.dim))
            self.documents[doc.id] = doc
            if state == "new":
                res.added += 1
            else:
                res.updated += 1
        # 清理：全量对账兜底，移除语料中已不存在的文档
        for doc_id in list(self.documents.keys()):
            if doc_id not in incoming_ids:
                self.chunks = [c for c in self.chunks if c.doc_id != doc_id]
                removed_doc = self.documents.pop(doc_id)
                res.removed += 1
                res.removed_ids.append(doc_id)
        res.chunks = len(self.chunks)
        return res

    # ---------- 问答 ----------
    def query(
        self,
        question: str,
        user: User,
        rerank: Optional[bool] = None,
        sensitive_words: Optional[list[str]] = None,
        watermark: str = "",
    ) -> dict:
        """问答主链路：鉴权 → 租户内召回（权限过滤）→ 重排 → 生成 → 敏感过滤 → 水印 → 审计。"""
        if user.tenant_id not in self.tenants:
            self.ensure_tenant(user.tenant_id)
        # 1. 租户内候选
        tenant_chunks = [c for c in self.chunks if c.tenant_id == user.tenant_id]
        # 2. 权限过滤（召回阶段，越权不进上下文）
        allowed = filter_by_permission(tenant_chunks, user)
        # 3. 向量召回
        qvec = embed_with_bigrams(question, self.dim)
        recalled = recall(allowed, question, qvec, self.top_k)
        # 4. 重排（可选）
        use_rerank = self.rerank if rerank is None else rerank
        if use_rerank and recalled:
            recalled = rerank(recalled, question)
        # 5. 无命中 → 拒答（不编造）
        if not recalled:
            answer = "未找到相关制度。"
            status = "no_hit"
        else:
            # 6. 生成
            llm_out = (
                llm_answer(recalled, question, self.llm.llm_model,
                           self.llm.llm_api_base, self.llm.llm_api_key)
                if self.llm.llm_enabled
                else None
            )
            answer = llm_out or extractive_answer(recalled)
            status = "ok"
        # 7. 敏感词过滤
        answer, hits = filter_sensitive(answer, sensitive_words)
        # 8. 水印
        if watermark:
            answer = add_watermark(answer, watermark)
        # 9. 审计
        sources = [{"doc_id": c.doc_id, "title": c.doc_title} for c in recalled]
        self.audit.record(
            {
                "user": user.id,
                "tenant": user.tenant_id,
                "question": question,
                "status": status,
                "hits": len(recalled),
                "sources": sources,
                "sensitive_hits": hits,
            }
        )
        return {
            "status": status,
            "answer": answer,
            "sources": sources,
            "sensitive_hits": hits,
        }


def load_corpus(path: str) -> list[Document]:
    """从 JSON 加载种子语料。"""
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    docs = []
    for d in data.get("documents", []):
        docs.append(
            Document(
                id=d["id"],
                tenant_id=d.get("tenant_id", "default"),
                title=d.get("title", ""),
                content=d.get("content", ""),
                allowed_roles=list(d.get("allowed_roles", [])),
                allowed_orgs=list(d.get("allowed_orgs", [])),
            )
        )
    return docs
