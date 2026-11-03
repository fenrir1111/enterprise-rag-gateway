"""全链路 demo：无需起服务，直接跑私有化 RAG 网关。

运行： uv run python -m rag_gateway.demo
覆盖：租户隔离、文档级权限（角色/组织）、召回阶段过滤、敏感词过滤、水印、审计。
"""

from __future__ import annotations

from .config import get_settings
from .gateway import Gateway, load_corpus
from .models import User


def main() -> None:
    s = get_settings()
    gw = Gateway()
    docs = load_corpus(s.corpus_path)
    res = gw.sync_corpus(docs)
    print("=" * 72)
    print("enterprise-rag-gateway 全链路 demo")
    print("=" * 72)
    print(
        f"语料同步：新增 {res.added}，更新 {res.updated}，"
        f"清理 {res.removed}，分块 {res.chunks}"
    )

    users = {
        "national": User(id="u-national", tenant_id="corp", roles=["national"], org="运营部"),
        "hr": User(id="u-hr", tenant_id="corp", roles=["hr"], org="人力资源部"),
        "prod": User(id="u-prod", tenant_id="corp", roles=[], org="生产部"),
    }
    cases = [
        ("报销流程需要几级审批？", "national", "公开制度，所有人可见"),
        ("涉密文件的借阅要求？", "hr", "角色 hr 命中白名单 → 可见"),
        ("涉密文件的借阅要求？", "prod", "prod 无 hr/national 角色 → 召回阶段过滤 → 未命中"),
        ("薪酬结构是怎样的？", "hr", "角色 hr → 可见（敏感词“薪酬”将被过滤）"),
        ("安全生产怎么管控？", "prod", "组织 生产部 命中白名单 → 可见"),
        ("项目验收需要满足哪些指标？", "national", "跨租户：corp 租户看不到 project 资料 → 未命中"),
    ]
    for question, role, note in cases:
        r = gw.query(question, users[role])
        print("-" * 72)
        print(f"Q   : {question}")
        print(f"角色 : {role}   说明 : {note}")
        print(f"状态 : {r['status']}  命中 {len(r['sources'])}  敏感词 {r['sensitive_hits']} 处")
        src = "；".join(x["title"] for x in r["sources"]) or "（无）"
        print(f"来源 : {src}")
        print(f"回答 : {r['answer']}")
    print("-" * 72)
    print(f"审计记录 {len(gw.audit.recent(500))} 条 → {s.audit_log_path}")


if __name__ == "__main__":
    main()
