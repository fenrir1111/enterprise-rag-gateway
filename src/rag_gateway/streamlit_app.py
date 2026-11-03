"""Streamlit 可视化后台：问答 / 文档权限 / 租户 / 审计。

启动： uv run streamlit run src/rag_gateway/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit 以「独立脚本」方式执行本文件（无 __package__），相对导入会直接 ImportError。
# 这里把 src/ 加入 sys.path 并改用绝对导入，保证「clone 即跑」和「已安装」两种场景都能启动。
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rag_gateway.config import get_settings  # noqa: E402
from rag_gateway.gateway import Gateway, load_corpus  # noqa: E402
from rag_gateway.models import User  # noqa: E402


@st.cache_resource
def _gw():
    s = get_settings()
    gw = Gateway()
    gw.sync_corpus(load_corpus(s.corpus_path))
    return gw


st.set_page_config(page_title="企业 RAG 网关", layout="wide")
gw = _gw()
st.title("enterprise-rag-gateway｜私有化企业 RAG 网关")
st.caption("多租户隔离 · 文档级权限（召回阶段过滤）· 增量同步 · 审计 · 敏感过滤 —— 先控权限，再做问答")

# 预置演示用户
USERS = {
    "national（运营部）": User(id="u-national", tenant_id="corp", roles=["national"], org="运营部"),
    "hr（人力资源部）": User(id="u-hr", tenant_id="corp", roles=["hr"], org="人力资源部"),
    "prod（生产部）": User(id="u-prod", tenant_id="corp", roles=[], org="生产部"),
}

tab_q, tab_doc, tab_t, tab_a = st.tabs(
    ["① 问答", "② 文档权限", "③ 租户", "④ 审计"]
)

with tab_q:
    c1, c2 = st.columns([2, 1])
    with c1:
        question = st.text_input("问题", "报销流程需要几级审批？")
    with c2:
        ukey = st.selectbox("提问人（身份）", list(USERS.keys()))
        tenant = st.selectbox("租户", ["corp", "project"], index=0)
    if st.button("提问", type="primary") and question:
        u = USERS[ukey]
        u = User(u.id, tenant, u.roles, u.org)
        r = gw.query(question, u)
        st.session_state["qr"] = r
    r = st.session_state.get("qr")
    if r:
        st.markdown("**状态**：" + r["status"])
        src = "；".join(x["title"] for x in r["sources"]) or "（无）"
        st.markdown("**来源**：" + src)
        if r["sensitive_hits"]:
            st.warning(f"敏感词过滤：{r['sensitive_hits']} 处")
        st.markdown("**回答**：")
        st.write(r["answer"])

with tab_doc:
    rows = [
        {
            "id": d.id,
            "tenant": d.tenant_id,
            "title": d.title,
            "public": d.is_public,
            "roles": ",".join(d.allowed_roles) or "-",
            "orgs": ",".join(d.allowed_orgs) or "-",
        }
        for d in gw.documents.values()
    ]
    st.dataframe(rows, hide_index=True)
    st.caption("public=是 表示租户内公开；否则按 roles / orgs 白名单在召回阶段过滤。")

with tab_t:
    for t in gw.tenants.values():
        n = sum(1 for d in gw.documents.values() if d.tenant_id == t.id)
        st.markdown(f"- **{t.id}**（{t.name}）：{n} 篇文档")

with tab_a:
    st.dataframe(gw.audit.recent(50), hide_index=True)
