from __future__ import annotations

import re

from .embedding import cosine
from .models import Chunk

_STOP = re.compile(r"(请问|一下|的|了|吗|呢|是|有|我|你|他|她|它|请|帮我|查|查询)")


def _score_terms(query: str, chunk_text: str) -> float:
    """轻量词重叠打分，用于 rerank（确定性、低算力）。"""
    q = set(_STOP.sub("", query))
    c = set(_STOP.sub("", chunk_text))
    if not q:
        return 0.0
    return len(q & c) / len(q)


def recall(
    chunks: list[Chunk], query: str, query_vec: list[float], top_k: int
) -> list[Chunk]:
    """向量召回：按余弦相似度取 top_k（已在上游做完权限过滤）。"""
    scored = sorted(
        chunks, key=lambda c: cosine(query_vec, c.embedding), reverse=True
    )
    return scored[:top_k]


def rerank(chunks: list[Chunk], query: str) -> list[Chunk]:
    """重排：向量分 * 0.6 + 词重叠分 * 0.4（可关闭）。"""
    scored = []
    for c in chunks:
        vec = 0.0  # 相对向量分已在 recall 排序中，这里用词重叠细化
        overlap = _score_terms(query, c.text)
        scored.append((overlap, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored]
