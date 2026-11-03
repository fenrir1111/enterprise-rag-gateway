from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置，支持 .env / 环境变量覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 种子语料 / 审计日志
    corpus_path: str = "./data/corpus.json"
    audit_log_path: str = "./data/audit.log"

    # 向量维度（确定性哈希向量，POC 零依赖）
    embedding_dim: int = 256
    # 召回 / 重排
    top_k: int = 5
    rerank: bool = False

    # 可选 LLM（不装 litellm 时走抽取式回答）
    llm_enabled: bool = False
    llm_model: str = "gpt-4o-mini"
    llm_api_base: str = ""
    llm_api_key: str = ""

    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
