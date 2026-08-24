# -*- coding: utf-8 -*-
"""Engine an sao Tử Vi."""
from .AmDuong import (
    diaChi, dichCung, ngayThangNam, ngayThangNamCanChi, nguHanh, thienCan,
    timCoThan, timCuc, timHoaLinh, timLuuTru, timPhaToai, timThienKhoi,
    timThienMa, timThienQuanThienPhuc, timTrangSinh, timTriet, timTuVi,
)
from .Sao import *


def lapDiaBan(diaBan, nn, tt, nnnn, gioSinh, gioiTinh, duongLich, timeZone):
    if duongLich is True:
        nn, tt, nnnn, thangNhuan = ngayThangNam(nn, tt, nnnn, duongLich, timeZone)
    canThang, canNam, chiNam = ngayThangNamCanChi(nn, tt, nnnn, False, timeZone)
    diaBan = diaBan(tt, gioSinh, thienCan[canNam])
    amDuongNamSinh = thienCan[canNam]["amDuong"]
    amDuongChiNamSinh = diaChi[chiNam]["amDuong"]
    hanhCuc = timCuc(diaBan.cungMenh, canNam)
    cucSo = nguHanh(hanhCuc)['cuc']
    diaBan = diaBan.nhapDaiHan(cucSo, gioiTinh * amDuongChiNamSinh)
    khoiHan = dichCung(11, -3 * (chiNam - 1))
    diaBan = diaBan.nhapTieuHan(khoiHan, gioiTinh, chiNam)

    viTriTuVi = timTuVi(cucSo, nn)
    viTriLiemTrinh = dichCung(viTriTuVi, 4)
    viTriThienDong = dichCung(viTriTuVi, 7)
    viTriVuKhuc = dichCung(viTriTuVi, 8)
    viTriThaiDuong = dichCung(viTriTuVi, 9)
    viTriThienCo = dichCung(viTriTuVi, 11)
    for pos, sao in [
        (viTriTuVi, saoTuVi),
        (viTriLiemTrinh, saoLiemTrinh),
        (viTriThienDong, saoThienDong),
        (viTriVuKhuc, saoVuKhuc),
        (viTriThaiDuong, saoThaiDuong),
        (viTriThienCo, saoThienCo),
    ]: diaBan.nhapSao(pos, sao)

    viTriThienPhu = dichCung(3, 3 - viTriTuVi)
    for offset, sao in [(0,saoThienPhu),(1,saoThaiAm),(2,saoThamLang),(3,saoCuMon),(4,saoThienTuong),(5,saoThienLuong),(6,saoThatSat),(10,saoPhaQuan)]:
        diaBan.nhapSao(dichCung(viTriThienPhu, offset), sao)
    viTriThaiAm=dichCung(viTriThienPhu,1); viTriThamLang=dichCung(viTriThienPhu,2); viTriCuMon=dichCung(viTriThienPhu,3); viTriThienLuong=dichCung(viTriThienPhu,5); viTriPhaQuan=dichCung(viTriThienPhu,10)

    viTriLocTon=thienCan[canNam]['vitriDiaBan']; diaBan.nhapSao(viTriLocTon,saoLocTon); diaBan.nhapSao(viTriLocTon,saoBacSy)
    amDuongNamNu=gioiTinh*amDuongNamSinh
    for offset,sao in [(1,saoLucSi),(2,saoThanhLong),(3,saoTieuHao),(4,saoTuongQuan),(5,saoTauThu),(6,saoPhiLiem),(7,saoHyThan),(8,saoBenhPhu),(9,saoDaiHao),(10,saoPhucBinh),(11,saoQuanPhu2)]: diaBan.nhapSao(dichCung(viTriLocTon,offset*amDuongNamNu),sao)

    viTriThaiTue=chiNam; diaBan.nhapSao(viTriThaiTue,saoThaiTue)
    viTriThieuDuong=dichCung(viTriThaiTue,1); diaBan.nhapSao(viTriThieuDuong,saoThieuDuong); diaBan.nhapSao(viTriThieuDuong,saoThienKhong)
    for offset,sao in [(2,saoTangMon),(3,saoThieuAm),(4,saoQuanPhu3)]: diaBan.nhapSao(dichCung(viTriThaiTue,offset),sao)
    viTriTuPhu=dichCung(viTriThaiTue,5); diaBan.nhapSao(viTriTuPhu,saoTuPhu); diaBan.nhapSao(viTriTuPhu,saoNguyetDuc)
    for offset,sao in [(6,saoTuePha),(7,saoLongDuc),(8,saoBachHo)]: diaBan.nhapSao(dichCung(viTriThaiTue,offset),sao)
    viTriPhucDuc=dichCung(viTriThaiTue,9); diaBan.nhapSao(viTriPhucDuc,saoPhucDuc); diaBan.nhapSao(viTriPhucDuc,saoThienDuc)
    for offset,sao in [(10,saoDieuKhach),(11,saoTrucPhu)]: diaBan.nhapSao(dichCung(viTriThaiTue,offset),sao)

    viTriTrangSinh=timTrangSinh(cucSo); diaBan.nhapSao(viTriTrangSinh,saoTrangSinh)
    for offset,sao in [(1,saoMocDuc),(2,saoQuanDoi),(3,saoLamQuan),(4,saoDeVuong),(5,saoSuy),(6,saoBenh),(7,saoTu),(8,saoMo),(9,saoTuyet),(-1,saoThai),(-2,saoDuong)]: diaBan.nhapSao(dichCung(viTriTrangSinh,amDuongNamNu*offset),sao)

    viTriDaLa=dichCung(viTriLocTon,-1); diaBan.nhapSao(viTriDaLa,saoDaLa)
    viTriKinhDuong=dichCung(viTriLocTon,1); diaBan.nhapSao(viTriKinhDuong,saoKinhDuong)
    viTriDiaKiep=dichCung(11,gioSinh); diaBan.nhapSao(viTriDiaKiep,saoDiaKiep)
    viTriDiaKhong=dichCung(12,12-viTriDiaKiep); diaBan.nhapSao(viTriDiaKhong,saoDiaKhong)
    viTriHoaTinh,viTriLinhTinh=timHoaLinh(chiNam,gioSinh,gioiTinh,amDuongNamSinh); diaBan.nhapSao(viTriHoaTinh,saoHoaTinh); diaBan.nhapSao(viTriLinhTinh,saoLinhTinh)

    viTriLongTri=dichCung(5,chiNam-1); diaBan.nhapSao(viTriLongTri,saoLongTri)
    viTriPhuongCac=dichCung(2,2-viTriLongTri); diaBan.nhapSao(viTriPhuongCac,saoPhuongCac); diaBan.nhapSao(viTriPhuongCac,saoGiaiThan)
    viTriTaPhu=dichCung(5,tt-1); diaBan.nhapSao(viTriTaPhu,saoTaPhu)
    viTriHuuBat=dichCung(2,2-viTriTaPhu); diaBan.nhapSao(viTriHuuBat,saoHuuBat)
    viTriVanKhuc=dichCung(5,gioSinh-1); diaBan.nhapSao(viTriVanKhuc,saoVanKhuc)
    viTriVanXuong=dichCung(2,2-viTriVanKhuc); diaBan.nhapSao(viTriVanXuong,saoVanXuong)
    viTriTamThai=dichCung(5,tt+nn-2); diaBan.nhapSao(viTriTamThai,saoTamThai)
    viTriBatToa=dichCung(2,2-viTriTamThai); diaBan.nhapSao(viTriBatToa,saoBatToa)
    viTriAnQuang=dichCung(viTriVanXuong,nn-2); diaBan.nhapSao(viTriAnQuang,saoAnQuang)
    viTriThienQuy=dichCung(2,2-viTriAnQuang); diaBan.nhapSao(viTriThienQuy,saoThienQuy)

    viTriThienKhoi=timThienKhoi(canNam); diaBan.nhapSao(viTriThienKhoi,saoThienKhoi)
    viTriThienViet=dichCung(5,5-viTriThienKhoi); diaBan.nhapSao(viTriThienViet,saoThienViet)
    viTriThienHu=dichCung(7,chiNam-1); diaBan.nhapSao(viTriThienHu,saoThienHu)
    viTriThienKhoc=dichCung(7,-chiNam+1); diaBan.nhapSao(viTriThienKhoc,saoThienKhoc)
    viTriThienTai=dichCung(diaBan.cungMenh,chiNam-1); diaBan.nhapSao(viTriThienTai,saoThienTai)
    viTriThienTho=dichCung(diaBan.cungThan,chiNam-1); diaBan.nhapSao(viTriThienTho,saoThienTho)
    viTriHongLoan=dichCung(4,-chiNam+1); diaBan.nhapSao(viTriHongLoan,saoHongLoan)
    viTriThienHy=dichCung(viTriHongLoan,6); diaBan.nhapSao(viTriThienHy,saoThienHy)
    viTriThienQuan,viTriThienPhuc=timThienQuanThienPhuc(canNam); diaBan.nhapSao(viTriThienQuan,saoThienQuan); diaBan.nhapSao(viTriThienPhuc,saoThienPhuc)
    viTriThienHinh=dichCung(10,tt-1); diaBan.nhapSao(viTriThienHinh,saoThienHinh)
    viTriThienRieu=dichCung(viTriThienHinh,4); diaBan.nhapSao(viTriThienRieu,saoThienRieu); diaBan.nhapSao(viTriThienRieu,saoThienY)
    viTriCoThan=timCoThan(chiNam); diaBan.nhapSao(viTriCoThan,saoCoThan); diaBan.nhapSao(dichCung(viTriCoThan,-4),saoQuaTu)
    viTriVanTinh=dichCung(viTriKinhDuong,2); diaBan.nhapSao(viTriVanTinh,saoVanTinh)
    viTriDuongPhu=dichCung(viTriVanTinh,2); diaBan.nhapSao(viTriDuongPhu,saoDuongPhu)
    viTriQuocAn=dichCung(viTriDuongPhu,3); diaBan.nhapSao(viTriQuocAn,saoQuocAn)
    viTriThaiPhu=dichCung(viTriVanKhuc,2); diaBan.nhapSao(viTriThaiPhu,saoThaiPhu)
    viTriPhongCao=dichCung(viTriVanKhuc,-2); diaBan.nhapSao(viTriPhongCao,saoPhongCao)

    # Thiên Giải: lấy cung Thân (9) làm tháng Giêng, đếm thuận 1 cung mỗi tháng.
    # Tháng 1 -> cung Thân; tháng 2 -> cung Dậu; ...
    viTriThienGiai=dichCung(9,tt-1)
    diaBan.nhapSao(viTriThienGiai,saoThienGiai)

    viTriDiaGiai=dichCung(viTriTaPhu,3); diaBan.nhapSao(viTriDiaGiai,saoDiaGiai)
    diaBan.nhapSao(5,saoThienLa); diaBan.nhapSao(11,saoDiaVong)
    diaBan.nhapSao(diaBan.cungNoboc,saoThienThuong); diaBan.nhapSao(diaBan.cungTatAch,saoThienSu)
    viTriThienMa=timThienMa(chiNam); diaBan.nhapSao(viTriThienMa,saoThienMa)
    diaBan.nhapSao(dichCung(viTriThienMa,2),saoHoaCai); diaBan.nhapSao(dichCung(viTriThienMa,3),saoKiepSat); diaBan.nhapSao(dichCung(viTriThienMa,7),saoDaoHoa)
    viTriPhaToai=timPhaToai(chiNam); diaBan.nhapSao(viTriPhaToai,saoPhaToai)
    viTriDauQuan=dichCung(chiNam,-tt+gioSinh); diaBan.nhapSao(viTriDauQuan,saoDauQuan)

    if canNam==1: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriLiemTrinh,viTriPhaQuan,viTriVuKhuc,viTriThaiDuong
    elif canNam==2: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriThienCo,viTriThienLuong,viTriTuVi,viTriThaiAm
    elif canNam==3: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=dichCung(viTriTuVi,7),viTriThienCo,viTriVanXuong,viTriLiemTrinh
    elif canNam==4: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriThaiAm,dichCung(viTriTuVi,7),viTriThienCo,viTriCuMon
    elif canNam==5: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriThamLang,viTriThaiAm,viTriHuuBat,viTriThienCo
    elif canNam==6: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriVuKhuc,viTriThamLang,viTriThienLuong,viTriVanKhuc
    elif canNam==7: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriThaiDuong,viTriVuKhuc,dichCung(viTriTuVi,7),viTriThaiAm
    elif canNam==8: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriCuMon,viTriThaiDuong,viTriVanKhuc,viTriVanXuong
    elif canNam==9: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriThienLuong,viTriTuVi,viTriThienPhu,viTriVuKhuc
    else: viTriHoaLoc,viTriHoaQuyen,viTriHoaKhoa,viTriHoaKy=viTriPhaQuan,viTriCuMon,viTriThaiAm,viTriThamLang
    for pos,sao in [(viTriHoaLoc,saoHoaLoc),(viTriHoaQuyen,saoHoaQuyen),(viTriHoaKhoa,saoHoaKhoa),(viTriHoaKy,saoHoaKy)]: diaBan.nhapSao(pos,sao)
    viTriLuuHa,viTriThienTru=timLuuTru(canNam); diaBan.nhapSao(viTriLuuHa,saoLuuHa); diaBan.nhapSao(viTriThienTru,saoThienTru)
    ketThucTuan=dichCung(chiNam,10-canNam); viTriTuan1=dichCung(ketThucTuan,1); viTriTuan2=dichCung(viTriTuan1,1); diaBan.nhapTuan(viTriTuan1,viTriTuan2)
    viTriTriet1,viTriTriet2=timTriet(canNam); diaBan.nhapTriet(viTriTriet1,viTriTriet2)
    return diaBan
