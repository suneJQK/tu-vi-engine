from types import SimpleNamespace

from tuvi_engine.engine.serializer import serialize_palace
from tuvi_engine.rules.evaluator import get_tam_phuong_tu_chinh, get_luc_hop_cung


def _palace(name, so, chi, stars=None):
    return {
        "cung": name,
        "cung_so": so,
        "dia_chi": chi,
        "sao": [{"ten": s, "dac_tinh": "Miếu địa"} for s in (stars or [])],
    }


def test_serialize_palace_preserves_cung_so():
    palace = SimpleNamespace(
        cungChu="Mệnh",
        cungTen="Mệnh Hợi",
        cungDiaChi="Hợi",
        cungHanh="Thủy",
        cungAmDuong=1,
        cungThan=True,
        tuanTrung=False,
        trietLo=False,
        cungDaiHan=None,
        cungTieuHan=None,
        cungSao=[],
    )
    result = serialize_palace(palace, cung_so=1)
    assert result["cung_so"] == 1


def test_relationship_geometry_has_tp4_and_luc_hop():
    chart = {
        "12_cung": {
            "Mệnh": _palace("Mệnh · Thân cư", 1, "Hợi", ["Hóa Lộc"]),
            "Phụ Mẫu": _palace("Phụ Mẫu", 2, "Tý"),
            "Phúc Đức": _palace("Phúc Đức", 3, "Sửu"),
            "Điền Trạch": _palace("Điền Trạch", 4, "Dần"),
            "Quan Lộc": _palace("Quan Lộc", 5, "Mão", ["Hóa Quyền"]),
            "Nô Bộc": _palace("Nô Bộc", 6, "Thìn"),
            "Thiên Di": _palace("Thiên Di", 7, "Tỵ"),
            "Tật Ách": _palace("Tật Ách", 8, "Ngọ"),
            "Tài Bạch": _palace("Tài Bạch", 9, "Mùi"),
            "Tử Tức": _palace("Tử Tức", 10, "Thân"),
            "Phu Thê": _palace("Phu Thê", 11, "Dậu"),
            "Huynh Đệ": _palace("Huynh Đệ", 12, "Tuất"),
        }
    }
    tp4 = get_tam_phuong_tu_chinh(chart, 1)
    assert {p["cung_so"] for p in tp4} == {1, 5, 9, 7}
    assert get_luc_hop_cung(chart, 1)["cung_so"] == 4
