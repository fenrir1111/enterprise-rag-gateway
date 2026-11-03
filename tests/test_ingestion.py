from rag_gateway.ingestion import build_chunks, chunk_text, content_checksum, sync_state
from rag_gateway.models import Document


def test_chunk_text_by_sentence():
    text = "报销流程需要三级审批。单笔超过五万元需附加预算依据。"
    blocks = chunk_text(text, max_len=10)
    assert len(blocks) >= 2
    assert all(b for b in blocks)


def test_chunk_text_empty():
    assert chunk_text("") == []


def test_checksum_stable():
    assert content_checksum("abc") == content_checksum("abc")
    assert content_checksum("abc") != content_checksum("abd")


def test_build_chunks_inherit_permission(sample_doc):
    doc = Document(id="d", tenant_id="corp", title="t", content="内容一。内容二。",
                   allowed_roles=["hr"], allowed_orgs=[])
    chunks = build_chunks(doc, dim=64)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.allowed_roles == ["hr"]
        assert c.tenant_id == "corp"


def test_sync_state_new_updated_unchanged():
    doc = Document(id="d", tenant_id="corp", title="t", content="内容")
    store: dict[str, Document] = {}
    assert sync_state(doc, store) == "new"
    doc.checksum = content_checksum(doc.content)
    store["d"] = Document(id="d", tenant_id="corp", title="t", content=doc.content,
                          checksum=doc.checksum)
    assert sync_state(doc, store) == "unchanged"
    doc2 = Document(id="d", tenant_id="corp", title="t", content="内容改")
    doc2.checksum = content_checksum(doc2.content)
    assert sync_state(doc2, store) == "updated"
