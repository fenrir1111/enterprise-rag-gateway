from __future__ import annotations

import hashlib
import math
import re

_TOKEN = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+")


def _tokens(text: str) -> list[str]:
    """中文按单字、英文/数字按连续串切分，得到词元列表。"""
    return _TOKEN.findall((text or "").lower())


def embed(text: str, dim: int = 256) -> list[float]:
    """确定性哈希向量：词元 → 桶累加 → L2 归一化。

    无外部依赖、可离线复现，保证余弦相似度检索可单测。
    生产可替换为真实向量模型（接口不变）。
    """
    vec = [0.0] * dim
    for tok in _tokens(text):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
        # 二字组合，缓解同字不同义的混淆
        # （简单增强，保持确定性）
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def embed_with_bigrams(text: str, dim: int = 256) -> list[float]:
    """带二字组合的确定性向量（对中文短句召回更稳）。"""
    vec = [0.0] * dim
    toks = _tokens(text)
    grams = list(toks)
    grams += [toks[i] + toks[i + 1] for i in range(len(toks) - 1)]
    for tok in grams:
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def cosine(a: list[float], b: list[float]) -> float:
    """余弦相似度（输入已归一化，等价于点积）。"""
    return sum(x * y for x, y in zip(a, b))
