from tuvi_engine.ai_context import build_ai_context, load_relationship_knowledge


def test_relationship_knowledge_contains_four_relations():
    data = load_relationship_knowledge()
    relations = data["relations"]
    assert set(relations) == {"xung_chieu", "tam_hop", "nhi_hop", "giap_cung"}
    assert relations["xung_chieu"]["offset"] == 6
    assert relations["tam_hop"]["offsets"] == [4, 8]
    assert relations["giap_cung"]["offsets"] == [-1, 1]


def test_build_ai_context_uses_explicit_cach_cuc_match():
    chart = {
        "input": {"nam": 1990},
        "thien_ban": {"menh": "Mệnh"},
        "12_cung": [],
        "cach_cuc": [],
    }
    payload = build_ai_context(chart)
    assert payload["schema_version"] == "3.5-ai-context-canonical-four-van-layers"
    assert payload["relationship_knowledge"]["relations"]["xung_chieu"]["label"] == "Xung Chiếu"
    assert payload["matched_cach_cuc"] == []
    assert payload["reasoning_contract"]["use_only_matched_cach_cuc"] is True
    assert payload["question_scope"]["id"] == "tong_hop_nam"
    assert payload["reasoning_contract"]["weights"] == {
        "dai_van": 0.55,
        "luu_nien_dai_van": 0.18,
        "tieu_van": 0.15,
        "luu_nien_nam": 0.12,
    }


def test_question_scope_prefers_specific_luu_nien_dai_van_over_generic_dai_van():
    chart = {"input": {}, "thien_ban": {}, "12_cung": {}, "cach_cuc": []}
    context = build_ai_context(chart, question="Lưu niên Đại vận năm 2026 thế nào?")
    assert context["question_scope"]["id"] == "luu_nien_dai_van"
    assert context["reasoning_contract"]["weights"]["luu_nien_dai_van"] == 0.50


def test_question_scope_tieu_han_focuses_tieu_van():
    chart = {"input": {}, "thien_ban": {}, "12_cung": {}, "cach_cuc": []}
    context = build_ai_context(chart, question="Tiểu hạn năm 2026 công việc thế nào?")
    assert context["question_scope"]["id"] == "tieu_van"
    assert context["reasoning_contract"]["weights"]["tieu_van"] == 0.40
