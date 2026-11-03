from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from .embedding import embed_with_bigrams
from .models import Chunk, Document

_SENT_SPLIT = re.compile(r"(?<=[。！？.!?])")


def content_checksum(content: str) -> str:
    return hashlib.md5((content or "").encode("utf-8")).hexdigest()


def chunk_text(content: str, max_len: int = 120) -> list[str]:
    """按句子边界切块，尽量不切碎句子；超长句再硬切。"""
    content = (content or "").strip()
    if not content:
        return []
    sentences = [s for s in _SENT_SPLIT.split(content) if s.strip()]
    blocks: list[str] = []
    buf = ""
    for s in sentences:
        if buf and len(buf) + len(s) > max_len:
            blocks.append(buf)
            buf = s
        else:
            buf += s
        while len(buf) > max_len:
            blocks.append(buf[:max_len])
            buf = buf[max_len:]
    if buf:
        blocks.append(buf)
    return [b for b in blocks if b.strip()]


@dataclass
class IngestResult:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    chunks: int = 0
    removed_ids: list[str] = field(default_factory=list)


def build_chunks(doc: Document, dim: int = 256) -> list[Chunk]:
    """为文档构建带权限标签的向量分块。"""
    doc.checksum = content_checksum(doc.content)
    chunks = []
    for i, text in enumerate(chunk_text(doc.content)):
        chunks.append(
            Chunk(
                id=f"{doc.id}#{i}",
                doc_id=doc.id,
                tenant_id=doc.tenant_id,
                text=text,
                embedding=embed_with_bigrams(text, dim),
                allowed_roles=list(doc.allowed_roles),
                allowed_orgs=list(doc.allowed_orgs),
                doc_title=doc.title,
            )
        )
    return chunks


def sync_state(doc: Document, store: dict[str, Document]) -> str:
    """增量同步判定：'new' / 'updated' / 'unchanged'。

    先为新文档计算内容校验和，避免外部来源（如 load_corpus）未携带
    checksum 时把“无变化”误判为“更新”。
    """
    doc.checksum = content_checksum(doc.content)
    if doc.id not in store:
        return "new"
    old = store[doc.id]
    return "updated" if old.checksum != doc.checksum else "unchanged"
