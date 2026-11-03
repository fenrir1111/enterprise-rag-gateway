from __future__ import annotations

from .models import Chunk, User


def can_access(user: User, chunk: Chunk) -> bool:
    """文档级权限判定（召回阶段过滤，越权片段不进入上下文）。

    - 空白名单 = 租户内公开；
    - 角色白名单：用户任一角色命中即放行；
    - 组织白名单：用户组织命中即放行；
    - 角色与组织为「与」关系（都配置了须同时满足），单配置则只看该项。
    """
    if not chunk.allowed_roles and not chunk.allowed_orgs:
        return True

    role_ok = True
    org_ok = True
    if chunk.allowed_roles:
        role_ok = any(r in chunk.allowed_roles for r in user.roles)
    if chunk.allowed_orgs:
        org_ok = user.org in chunk.allowed_orgs
    return role_ok and org_ok


def filter_by_permission(chunks: list[Chunk], user: User) -> list[Chunk]:
    return [c for c in chunks if can_access(user, c)]
