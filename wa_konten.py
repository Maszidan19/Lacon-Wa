# -*- coding: utf-8 -*-
"""Sumber konten: sheet 'Jadwal Up Konten' + folder Drive 'creative-makers'.

    sheet   satu tab per brand. Kolom A tanggal - CUMA DIISI di baris pertama
            tiap kelompok, jadi harus diisi-turun dulu. Kolom C kode konten,
            kolom G jam tayang.
    Drive   bertingkat: brand > kategori > motion > folder tanggal > berkas.
            Kode konten dicocokkan ke NAMA BERKASNYA, bukan ke jalurnya.

Foldernya dalam dan isinya ribuan, jadi diindeks sekali lalu disimpan di
indeks_drive.json. Sekali telusur sekitar lima menit.

INDEKS BISA BASI, DAN BASINYA MENYAMAR JADI 'STOK HABIS'. Kalau sebuah kode
tidak ketemu padahal berkasnya yakin ada, susun ulang indeksnya DULU sebelum
melapor apa pun.
"""
import io
import json
import os
import re

import wa_inti as inti

LEWATI_TAB = {"lilo", "konten gmaps"}


# ----------------------------------------------------------------- indeks

def susun_indeks():
    """Telusuri folder Drive, simpan daftar videonya."""
    _, drive = inti.layanan()
    cfg = inti.baca_config()
    akar = cfg.get("drive_folder_id")
    if not akar:
        inti.gagal("config.json belum punya 'drive_folder_id'.")

    hasil, antre, n_folder = [], [(akar, "")], 0
    while antre:
        fid, jalur = antre.pop(0)
        n_folder += 1
        halaman = None
        while True:
            r = drive.files().list(
                q="'%s' in parents and trashed=false" % fid,
                fields="nextPageToken, files(id,name,mimeType,size)",
                pageSize=1000, pageToken=halaman,
                supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            for f in r.get("files", []):
                if f["mimeType"] == "application/vnd.google-apps.folder":
                    antre.append((f["id"], jalur + "/" + f["name"]))
                elif f["name"].lower().endswith((".mp4", ".mov", ".m4v")):
                    hasil.append({"id": f["id"], "nama": f["name"],
                                  "jalur": jalur, "size": f.get("size", "")})
            halaman = r.get("nextPageToken")
            if not halaman:
                break
        if n_folder % 50 == 0:
            inti.info("  %d folder, %d video" % (n_folder, len(hasil)))

    with io.open(inti.INDEKS, "w", encoding="utf-8") as f:
        f.write(json.dumps(hasil, ensure_ascii=False, indent=1))
    inti.info("%d folder ditelusuri, %d video ketemu" % (n_folder, len(hasil)))
    inti.info("tersimpan: %s" % inti.INDEKS)
    inti.catat("indeks disusun: %d folder, %d video" % (n_folder, len(hasil)))


# ----------------------------------------------------------------- sheet

def baris_hari(hari, brand=None):
    """Semua konten pada satu tanggal, dari seluruh tab brand."""
    sheets, _ = inti.layanan()
    cfg = inti.baca_config()
    sid = cfg.get("sheet_id")
    if not sid:
        inti.gagal("config.json belum punya 'sheet_id'.")

    meta = sheets.spreadsheets().get(
        spreadsheetId=sid, fields="sheets/properties/title").execute()
    keluar = []
    for s in meta["sheets"]:
        tab = s["properties"]["title"]
        if tab.lower() in LEWATI_TAB:
            continue
        if brand and tab.lower() not in brand:
            continue
        r = sheets.spreadsheets().values().get(
            spreadsheetId=sid, range="'%s'!A1:I400" % tab).execute()
        tgl = None
        for i, b in enumerate(r.get("values", []), 1):
            b = list(b) + [""] * (9 - len(b))
            t = inti.baca_tanggal_sheet(b[0])
            if t:
                tgl = t          # tanggal diisi-turun
            kode = (b[2] or "").strip()
            if tgl == hari and kode:
                keluar.append({"brand": tab.lower(), "baris": i, "kode": kode,
                               # D = penanda tim: TRUE berarti SUDAH tayang
                               "sudah": (b[3] or "").strip().upper() == "TRUE",
                               "platform": (b[5] or "").strip(),
                               "jam": (b[6] or "").strip()})
    return keluar


def jam_rapi(j):
    """'12.00 WIB' -> '12:00'.

    Kolomnya SELALU berakhiran ' WIB' - 1079 baris diperiksa, tidak ada yang
    jam telanjang. Pola yang menuntut jam saja menolak SEMUANYA, dan
    gejalanya terbaca seolah tim belum mengisi jadwalnya.
    """
    m = re.search(r"(\d{1,2})[.:](\d{2})", j or "")
    return "%02d:%s" % (int(m.group(1)), m.group(2)) if m else ""


def berjam(isi):
    """Sisakan baris yang siap diposting.

    JAM TIDAK MENENTUKAN APA-APA DI SINI. Keputusan user 7 Oktober 2026:
    "jamnya gausah di tetapkan dulu, biar nanti tim cs yang menetapkan".
    Jadi baris tanpa jam TETAP ikut - alat ini menyiapkan dan mengirim
    waktu disuruh, bukan menentukan kapan tayangnya. Kolom jam cuma dibawa
    sebagai keterangan kalau kebetulan sudah diisi.

    Dua hal yang masih membuat sebuah baris dilewati, dan dua-duanya
    DISEBUT di layar - jangan dibuang diam-diam:

      kolom D TRUE                tim sudah menayangkannya
      platform bukan 'WA Story'   barisnya bukan untuk WhatsApp
    """
    ada, tanpa = [], []
    for x in isi:
        if x.get("sudah"):
            x["alasan"] = "SUDAH TAYANG menurut kolom D sheet"
        elif x.get("platform") and x["platform"].lower() != "wa story":
            x["alasan"] = "platform di sheet %r, bukan WA Story" % x["platform"]
        else:
            ada.append(x)
            continue
        tanpa.append(x)
    return ada, tanpa


# ----------------------------------------------------------------- unduh

def rencana(hari, brand=None, diam=False):
    """Daftar konten hari itu, lengkap dengan berkas Drive-nya."""
    isi = baris_hari(hari, brand)
    if not isi:
        inti.gagal("Tidak ada konten untuk %s di sheet.\n"
                   "  Kalau yakin ada, periksa BAHASA tanggal di kolom A - "
                   "pembaca ini kenal Indonesia dan Inggris, di luar itu "
                   "barisnya terlewat." % hari)
    isi, tanpa_jam = berjam(isi)
    peta = inti.muat_indeks(diam=diam)

    siap, hilang = [], []
    for x in sorted(isi, key=lambda d: (d["brand"], jam_rapi(d["jam"]))):
        v = inti.cocokkan(peta, x["kode"])
        if not v:
            hilang.append(x)
            continue
        # Penjaga: berkas yang ketemu harus milik brand tab itu juga.
        punya = inti.brand_berkas(v["nama"])
        if punya != x["brand"]:
            inti.info("  LEWAT %s: kode %s ketemu berkas %s milik %r"
                      % (x["brand"], x["kode"], v["nama"], punya))
            hilang.append(x)
            continue
        y = dict(x)
        y["berkas"] = v
        siap.append(y)
    return siap, hilang, tanpa_jam


def unduh(hari, brand=None, tulis=False):
    siap, hilang, tanpa_jam = rencana(hari, brand)
    tujuan = os.path.join(inti.UNDUHAN, inti.nama_folder_tanggal(hari))
    inti.info("\n%s - %d konten siap" % (inti.nama_folder_tanggal(hari), len(siap)))
    inti.info("tujuan: %s\n" % tujuan)

    for i, x in enumerate(siap, 1):
        inti.info("  %02d %-10s %-6s %s" % (i, x["brand"], jam_rapi(x["jam"]),
                                            x["berkas"]["nama"]))
    for x in hilang:
        inti.info("  -- %-10s %-6s %-42s TIDAK KETEMU DI DRIVE"
                  % (x["brand"], jam_rapi(x["jam"]), x["kode"]))
    if hilang:
        inti.info("     kalau berkasnya baru, susun ulang indeks: python wa.py indeks")
    for x in tanpa_jam:
        inti.info("  -- %-10s %-6s %-42s %s"
                  % (x["brand"], jam_rapi(x["jam"]) or "-", x["kode"],
                     x.get("alasan", "dilewati")))

    if not tulis:
        inti.info("\nPRATINJAU. Belum ada yang diunduh.")
        inti.info("Tambahkan --tulis kalau sudah benar.")
        return tujuan, siap

    from googleapiclient.http import MediaIoBaseDownload
    _, drive = inti.layanan()
    os.makedirs(tujuan, exist_ok=True)
    inti.info("")
    for i, x in enumerate(siap, 1):
        # Nomor urut di DEPAN supaya urutannya tidak bergantung pengurutan
        # folder. Jam ikut HANYA kalau tim sudah mengisinya - kalau belum,
        # namanya cuma nomor + nama berkas, dan tim CS yang menentukan
        # kapan dikirim.
        j = jam_rapi(x["jam"]).replace(":", ".")
        nama = ("%02d - %s - %s" % (i, j, x["berkas"]["nama"])) if j else \
               ("%02d - %s" % (i, x["berkas"]["nama"]))
        jalur = os.path.join(tujuan, nama)
        if os.path.exists(jalur):
            inti.info("  %s sudah ada, dilewati" % nama)
            x["jalur"] = jalur
            continue
        req = drive.files().get_media(fileId=x["berkas"]["id"],
                                      supportsAllDrives=True)
        with io.FileIO(jalur, "wb") as fh:
            unduhan = MediaIoBaseDownload(fh, req, chunksize=8 * 1024 * 1024)
            selesai = False
            while not selesai:
                _, selesai = unduhan.next_chunk()
        x["jalur"] = jalur
        inti.info("  %s  (%.1f MB)" % (nama, os.path.getsize(jalur) / 1048576.0))
    inti.catat("unduh %s: %d berkas" % (inti.nama_folder_tanggal(hari), len(siap)))
    inti.info("\nSelesai. %d berkas di %s" % (len(siap), tujuan))
    return tujuan, siap
