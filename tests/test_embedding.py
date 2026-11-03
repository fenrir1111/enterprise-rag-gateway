import math

from rag_gateway.embedding import cosine, embed_with_bigrams


def test_embed_deterministic_and_normalized():
    a = embed_with_bigrams("报销流程需要三级审批", 256)
    b = embed_with_bigrams("报销流程需要三级审批", 256)
    assert a == b
    assert abs(sum(v * v for v in a) - 1.0) < 1e-6  # L2 归一化


def test_cosine_related_higher():
    base = embed_with_bigrams("报销流程需要三级审批", 256)
    near = embed_with_bigrams("报销流程是几级审批", 256)
    far = embed_with_bigrams("安全生产作业前风险辨识", 256)
    assert cosine(base, near) > cosine(base, far)


def test_empty_embed():
    v = embed_with_bigrams("", 256)
    assert all(x == 0.0 for x in v)
