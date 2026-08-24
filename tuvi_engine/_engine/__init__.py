from .DiaBan import diaBan,cungDiaBan
from . import Sao as _sao
for _n in ('saoTrangSinh','saoMocDuc','saoQuanDoi','saoLamQuan','saoDeVuong','saoSuy','saoBenh','saoTu','saoMo','saoTuyet','saoThai','saoDuong'):
    getattr(_sao,_n).vongTrangSinh=1
from .App import lapDiaBan
from .ThienBan import lapThienBan
