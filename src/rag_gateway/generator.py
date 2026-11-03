from __future__ import annotations

from typing import Optional

from .models import Chunk

SYSTEM_PROMPT = (
    "你是企业知识库助手。仅依据给定资料回答；资料中没有的信息明确说“未找到相关制度”。"
    "不要编造。回答需简洁，并可用【来源：文档标题】标注出处。"
)


def extractive_answer(chunks: list[Chunk]) -> str:
    """抽取式回答：拼接 top 分块作为答案（无 LLM 时的确定性兜底）。"""
    if not chunks:
        return "未找到相关制度。"
    parts = [c.text.strip() for c in chunks[:3] if c.text.strip()]
    return "\n".join(parts) if parts else "未找到相关制度。"


def llm_answer(chunks: list[Chunk], question: str, model: str, api_base: str, api_key: str) -> Optional[str]:
    """LLM 生成回答：仅当安装 litellm 且配置 api_key 时可用。"""
    if not api_key:
        return None
    try:
        import litellm
    except Exception:
        return None
    context = "\n\n".join(f"[{c.doc_title}] {c.text}" for c in chunks) or "（无相关资料）"
    try:
        resp = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"资料：\n{context}\n\n问题：{question}"},
            ],
            base_url=api_base or None,
            api_key=api_key,
            temperature=0,
            max_tokens=512,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return None
