import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest

from rag_gateway.config import get_settings
from rag_gateway.gateway import Gateway, load_corpus
from rag_gateway.models import Document, User


@pytest.fixture
def gateway():
    s = get_settings()
    gw = Gateway()
    docs = load_corpus(s.corpus_path)
    gw.sync_corpus(docs)
    return gw


@pytest.fixture
def user_national():
    return User(id="u-national", tenant_id="corp", roles=["national"], org="运营部")


@pytest.fixture
def user_hr():
    return User(id="u-hr", tenant_id="corp", roles=["hr"], org="人力资源部")


@pytest.fixture
def user_prod():
    return User(id="u-prod", tenant_id="corp", roles=[], org="生产部")


@pytest.fixture
def sample_doc():
    return Document(
        id="d1",
        tenant_id="corp",
        title="制度",
        content="报销流程需要三级审批。",
        allowed_roles=[],
        allowed_orgs=[],
    )
