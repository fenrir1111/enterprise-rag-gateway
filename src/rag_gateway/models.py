from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tenant:
    """租户：独立向量空间，数据互不干扰。"""

    id: str
    name: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass
class User:
    """用户身份：来自外部 IAM/OA 同步的角色与组织。"""

    id: str
    tenant_id: str
    roles: list[str] = field(default_factory=list)
    org: str = ""
    name: str = ""


@dataclass
class Document:
    """文档：绑定租户 + 访问白名单（组织 / 角色）。空=租户内公开。"""

    id: str
    tenant_id: str
    title: str
    content: str
    allowed_roles: list[str] = field(default_factory=list)
    allowed_orgs: list[str] = field(default_factory=list)
    version: int = 1
    checksum: str = ""
    updated_at: float = field(default_factory=time.time)

    @property
    def is_public(self) -> bool:
        return not self.allowed_roles and not self.allowed_orgs


@dataclass
class Chunk:
    """分块：继承文档权限标签，带确定性向量。"""

    id: str
    doc_id: str
    tenant_id: str
    text: str
    embedding: list[float]
    # 继承文档权限（召回阶段据此过滤）
    allowed_roles: list[str] = field(default_factory=list)
    allowed_orgs: list[str] = field(default_factory=list)
    doc_title: str = ""
