from __future__ import annotations

"""敏感词过滤 + 回答水印。

内置一个最小敏感词库做演示，生产应接入行业词表 / 外部敏感词服务。
"""

import re

DEFAULT_SENSITIVE_WORDS: list[str] = [
    "薪酬",
    "薪资",
    "银行账号",
    "涉密",
    "薪酬总额",
]

_MASK = "██"


def filter_sensitive(text: str, words: list[str] | None = None) -> tuple[str, int]:
    """返回 (过滤后文本, 命中敏感词次数)。"""
    words = words or DEFAULT_SENSITIVE_WORDS
    hits = 0
    out = text
    for w in words:
        if w and w in out:
            hits += out.count(w)
            out = out.replace(w, _MASK)
    return out, hits


def add_watermark(text: str, watermark: str) -> str:
    """在回答末尾追加轻量水印（溯源/导出管控）。"""
    if not watermark or not text:
        return text
    return f"{text}\n—— 来源：企业知识库（水印：{watermark}）"
