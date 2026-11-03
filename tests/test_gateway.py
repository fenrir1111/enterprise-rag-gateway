from rag_gateway.models import Document, User


def test_query_public_doc(gateway, user_prod):
    r = gateway.query("报销流程需要几级审批？", user_prod)
    assert r["status"] == "ok"
    assert "三级审批" in r["answer"]
    assert any(s["doc_id"] == "doc-001" for s in r["sources"])


def test_role_restricted_visible_to_hr(gateway, user_hr):
    r = gateway.query("涉密文件的借阅要求？", user_hr)
    assert r["status"] == "ok"
    assert any(s["doc_id"] == "doc-003" for s in r["sources"])


def test_role_restricted_hidden_from_prod(gateway, user_prod):
    # prod 无 hr/national 角色 → doc-003 召回阶段过滤 → 命不中涉密
    r = gateway.query("涉密文件的借阅要求？", user_prod)
    assert all(s["doc_id"] != "doc-003" for s in r["sources"])


def test_org_restricted_visible_to_prod(gateway, user_prod):
    r = gateway.query("安全生产怎么管控？", user_prod)
    assert r["status"] == "ok"
    assert any(s["doc_id"] == "doc-005" for s in r["sources"])


def test_tenant_isolation(gateway):
    # corp 租户查不到 project 租户的资料
    user = User(id="u", tenant_id="corp", roles=[], org="运营部")
    r = gateway.query("项目验收需要满足哪些指标？", user)
    assert all(s["doc_id"] != "doc-101" for s in r["sources"])
    # project 租户内可查到
    user2 = User(id="u2", tenant_id="project", roles=[], org="x")
    r2 = gateway.query("项目验收需要满足哪些指标？", user2)
    assert any(s["doc_id"] == "doc-101" for s in r2["sources"])


def test_sensitive_word_filtered(gateway, user_hr):
    r = gateway.query("薪酬结构是怎样的？", user_hr, watermark="u-hr")
    # 薪酬被脱敏 + 追加水印
    assert "薪酬" not in r["answer"] or "██" in r["answer"]
    assert "u-hr" in r["answer"]


def test_no_hit_refuses_not_hallucinate(gateway, user_prod):
    r = gateway.query("量子计算怎么部署？", user_prod)
    assert r["status"] in ("no_hit", "ok")
    # 无命中时回答应明确“未找到”
    if r["status"] == "no_hit":
        assert "未找到" in r["answer"]


def test_sync_incremental_and_reconcile(gateway):
    # 全量对账：给一份“删掉 doc-004”的语料 → 应清理 doc-004
    docs = [d for d in gateway.documents.values() if d.id != "doc-004"]
    # 重新构造 Document 列表（仅保留现存字段）
    from rag_gateway.gateway import load_corpus
    from rag_gateway.config import get_settings

    all_docs = load_corpus(get_settings().corpus_path)
    keep = [d for d in all_docs if d.id != "doc-004"]
    res = gateway.sync_corpus(keep)
    assert res.removed >= 1
    assert "doc-004" not in gateway.documents
    assert "doc-004" in res.removed_ids


def test_sync_unchanged(gateway):
    from rag_gateway.gateway import load_corpus
    from rag_gateway.config import get_settings

    res = gateway.sync_corpus(load_corpus(get_settings().corpus_path))
    assert res.added == 0
    assert res.unchanged >= 1
