from rag_gateway.embedding import embed_with_bigrams
from rag_gateway.models import Chunk
from rag_gateway.retrieval import recall, rerank


def _chunk(text):
    return Chunk(id=text[:4], doc_id="d", tenant_id="corp", text=text,
                 embedding=embed_with_bigrams(text, 64))


def test_recall_topk():
    chunks = [_chunk("报销流程需要三级审批"), _chunk("安全生产作业前风险辨识"),
              _chunk("年假最多 15 天")]
    qvec = embed_with_bigrams("报销流程几级审批", 64)
    out = recall(chunks, "报销流程几级审批", qvec, top_k=1)
    assert len(out) == 1
    assert "报销" in out[0].text


def test_rerank_keeps_all():
    chunks = [_chunk("报销流程需要三级审批"), _chunk("报销需预算依据")]
    out = rerank(chunks, "报销流程")
    assert len(out) == 2
