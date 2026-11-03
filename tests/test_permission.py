from rag_gateway.models import Chunk, User
from rag_gateway.permission import can_access, filter_by_permission


def _chunk(roles, orgs):
    return Chunk(
        id="c", doc_id="d", tenant_id="corp", text="t",
        embedding=[0.0], allowed_roles=roles, allowed_orgs=orgs,
    )


def test_public_chunk_accessible():
    assert can_access(User(id="u", tenant_id="corp", roles=[], org="x"), _chunk([], []))


def test_role_whitelist():
    c = _chunk(["hr", "national"], [])
    assert can_access(User(id="u", tenant_id="corp", roles=["hr"]), c)
    assert not can_access(User(id="u", tenant_id="corp", roles=["prod"]), c)


def test_org_whitelist():
    c = _chunk([], ["生产部"])
    assert can_access(User(id="u", tenant_id="corp", roles=[], org="生产部"), c)
    assert not can_access(User(id="u", tenant_id="corp", roles=[], org="运营部"), c)


def test_role_and_org_both_required():
    c = _chunk(["hr"], ["人力资源部"])
    # 只有角色没有组织 → 不满足（与关系）
    assert not can_access(User(id="u", tenant_id="corp", roles=["hr"], org="运营部"), c)
    assert can_access(User(id="u", tenant_id="corp", roles=["hr"], org="人力资源部"), c)


def test_filter_by_permission():
    chunks = [_chunk(["hr"], []), _chunk([], [])]
    out = filter_by_permission(chunks, User(id="u", tenant_id="corp", roles=["hr"]))
    assert len(out) == 2  # hr 可见受限 + 公开
    out2 = filter_by_permission(chunks, User(id="u", tenant_id="corp", roles=[]))
    assert len(out2) == 1  # 非 hr 只能看公开
