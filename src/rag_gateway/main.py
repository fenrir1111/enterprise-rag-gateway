"""FastAPI 服务入口。

接口：
- POST /query        问答（带身份，用于权限过滤 + 审计 + 敏感过滤）
- POST /sync         全量同步语料（增量 + 对账）
- GET  /health       健康检查
- GET  /tenants      租户列表
- GET  /documents    文档列表（含权限标签）
- GET  /audit        审计日志
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel, Field

from .audit import AuditLogger
from .config import get_settings
from .gateway import Gateway, load_corpus
from .models import User


class QueryRequest(BaseModel):
    question: str = Field(..., examples=["报销流程需要几级审批？"])
    user_id: str = Field("u-national", description="用户身份 ID")
    tenant_id: str = Field("corp", description="租户 ID")
    roles: list[str] = Field(default_factory=list, description="用户角色（来自外部 IAM 同步）")
    org: str = Field("", description="用户组织")
    rerank: Optional[bool] = None
    watermark: str = ""


class SyncDoc(BaseModel):
    id: str
    tenant_id: str
    title: str
    content: str
    allowed_roles: list[str] = Field(default_factory=list)
    allowed_orgs: list[str] = Field(default_factory=list)


class SyncRequest(BaseModel):
    documents: list[SyncDoc]


def _default_gateway() -> Gateway:
    s = get_settings()
    gw = Gateway(audit=AuditLogger(path=s.audit_log_path))
    gw.sync_corpus(load_corpus(s.corpus_path))
    return gw


def build_app(gateway: Optional[Gateway] = None) -> FastAPI:
    gw = gateway or _default_gateway()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield

    app = FastAPI(
        title="enterprise-rag-gateway",
        description="私有化企业 RAG 网关｜多租户 + 文档级权限 + 增量同步 + 审计 + 敏感过滤",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "tenants": len(gw.tenants),
            "documents": len(gw.documents),
            "chunks": len(gw.chunks),
        }

    @app.get("/tenants")
    def tenants() -> list[dict]:
        return [{"id": t.id, "name": t.name} for t in gw.tenants.values()]

    @app.get("/documents")
    def docs(tenant_id: Optional[str] = None) -> list[dict]:
        out = []
        for d in gw.documents.values():
            if tenant_id and d.tenant_id != tenant_id:
                continue
            out.append(
                {
                    "id": d.id,
                    "tenant_id": d.tenant_id,
                    "title": d.title,
                    "public": d.is_public,
                    "allowed_roles": d.allowed_roles,
                    "allowed_orgs": d.allowed_orgs,
                }
            )
        return out

    @app.post("/sync")
    def sync(req: SyncRequest) -> dict:
        from .models import Document

        docs = [
            Document(
                id=d.id,
                tenant_id=d.tenant_id,
                title=d.title,
                content=d.content,
                allowed_roles=d.allowed_roles,
                allowed_orgs=d.allowed_orgs,
            )
            for d in req.documents
        ]
        res = gw.sync_corpus(docs)
        return {
            "added": res.added,
            "updated": res.updated,
            "unchanged": res.unchanged,
            "removed": res.removed,
            "chunks": res.chunks,
        }

    @app.post("/query")
    def query(req: QueryRequest) -> dict:
        user = User(
            id=req.user_id,
            tenant_id=req.tenant_id,
            roles=req.roles,
            org=req.org,
        )
        return gw.query(
            req.question,
            user,
            rerank=req.rerank,
            watermark=req.watermark,
        )

    @app.get("/audit")
    def audit(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
        return gw.audit.recent(limit)

    return app


app = build_app()
