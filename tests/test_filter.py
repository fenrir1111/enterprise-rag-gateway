from rag_gateway.filter import add_watermark, filter_sensitive


def test_filter_sensitive_masks():
    out, hits = filter_sensitive("本月薪酬总额已核算")
    assert "薪酬" not in out
    assert hits >= 1
    assert "██" in out


def test_filter_no_hit():
    out, hits = filter_sensitive("报销流程需要三级审批")
    assert hits == 0
    assert out == "报销流程需要三级审批"


def test_add_watermark():
    out = add_watermark("答案内容", "u-national")
    assert "u-national" in out
    assert add_watermark("答案内容", "") == "答案内容"
