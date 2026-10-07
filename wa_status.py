# -*- coding: utf-8 -*-
"""Menayangkan berkas sebagai Status WhatsApp lewat WhatsApp Web.

SATU BRAND SATU PROFIL CHROME. Lihat wa_inti.profil_brand().

WhatsApp TIDAK punya penjadwalan - tidak ada tombolnya, manual pun sama.
Yang ada cuma terbit sekarang, jadi slot 12.00/14.00/19.30 berarti
perintahnya benar-benar dijalankan di jam itu.

Alur composer yang sudah dipetakan dan dibuktikan 7 Oktober 2026:

    tombol aria-label 'Status'          buka tab Status
    tombol aria-label 'Add Status'      buka pilihan
    [aria-label='Foto & Video']         diklik DI DALAM expect_file_chooser,
                                        jadi dialog Windows tidak pernah muncul
    elemen <video> muncul               pratinjau jadi, sekitar 3 detik
    div[contenteditable=true]           kotak 'Tambah keterangan'
    tombol aria-label diawali 'Kirim'   kirim - labelnya 'Kirim 1 yang dipilih'

Bawaannya PRATINJAU: media diunggah, pratinjaunya dipotret, lalu dibatalkan
dengan Escape. Tanpa --tulis tidak ada Status yang terbit.
"""
import os
import subprocess
import time

import wa_inti as inti

ALAMAT = "https://web.whatsapp.com/"
BATAS_DETIK = 30                    # batas video Status WhatsApp
BATAS_BYTE = 16 * 1024 * 1024
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"


def potret(hal, nama):
    os.makedirs(inti.PROFIL_AKAR, exist_ok=True)
    j = os.path.join(inti.PROFIL_AKAR, nama + ".png")
    try:
        hal.screenshot(path=j)
        inti.info("   potret: %s" % j)
    except Exception:
        pass
    return j


def buka(brand):
    """Buka profil brand dan tunggu KEADAAN, bukan jeda tetap.

    Jeda tetap itu bom waktu - lolos tiap hari sampai satu hari layanannya
    lebih lambat, lalu gagal dengan pesan yang menunjuk tempat yang salah.
    """
    p = inti.profil_brand(brand)
    if not os.path.isdir(p):
        inti.gagal("Profil %s belum ada. Jalankan dulu: python wa.py login %s"
                   % (p, brand))
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    ktx = pw.chromium.launch_persistent_context(
        p, channel="chrome", headless=False, args=inti.argumen_jendela(),
        viewport={"width": 1500, "height": 1000})
    hal = ktx.pages[0] if ktx.pages else ktx.new_page()
    inti.kecilkan_jendela(ktx, hal)
    hal.goto(ALAMAT, wait_until="domcontentloaded", timeout=120000)
    for _ in range(75):
        if hal.locator("button[aria-label='Status']").count():
            time.sleep(3)
            return pw, ktx, hal
        t = hal.evaluate("() => document.body.innerText || ''")
        if "Scan" in t or "Tautkan" in t or "Log in" in t:
            potret(hal, "belum-login-%s" % brand)
            ktx.close(); pw.stop()
            inti.gagal("Profil %s BELUM LOGIN.\n  Jalankan: python wa.py login %s"
                       % (brand, brand))
        time.sleep(2)
    potret(hal, "tak-siap-%s" % brand)
    ktx.close(); pw.stop()
    inti.gagal("WhatsApp tidak siap dalam 150 detik untuk %s." % brand)


def nama_akun(hal):
    """Nama bisnis dari panel Profil. INI yang membuktikan nomornya milik siapa.

    Nama FOLDER profil tidak membuktikan apa-apa - di Lacon sudah empat kali
    profil tertukar karena beberapa jendela login dibuka bersamaan.
    """
    hal.locator("button[aria-label='Profil']").first.click()
    time.sleep(4)
    baris = [x.strip() for x in
             (hal.evaluate("() => document.body.innerText || ''")).split("\n")
             if x.strip()]
    nama = ""
    for i, b in enumerate(baris):
        if b in ("Nama bisnis", "Business name") and i + 1 < len(baris):
            nama = baris[i + 1]
            break
    hal.keyboard.press("Escape")
    time.sleep(1)
    return nama, baris[:14]


def sudah_pernah(brand, berkas):
    """Status yang sama tidak boleh naik dua kali. Pegangannya riwayat.log."""
    if not os.path.exists(inti.LOG):
        return None
    kunci = "WA Status %s: %s" % (brand.lower(), os.path.basename(berkas))
    for baris in open(inti.LOG, encoding="utf-8", errors="replace"):
        if kunci in baris:
            return baris.strip()
    return None


def periksa_berkas(brand, berkas):
    """Penjaga yang berjalan SEBELUM browser dibuka sama sekali."""
    if not os.path.exists(berkas):
        inti.gagal("Berkas tidak ada: %s" % berkas)
    byt = os.path.getsize(berkas)
    inti.info("berkas : %s" % os.path.basename(berkas))
    inti.info("ukuran : %.1f MB" % (byt / 1048576.0))
    if byt > BATAS_BYTE:
        inti.gagal("Lebih dari 16 MB - Status WhatsApp menolak.")
    try:
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", berkas],
                           capture_output=True, text=True).stdout.strip()
        if d:
            inti.info("durasi : %.1f detik" % float(d))
            if float(d) > BATAS_DETIK:
                inti.gagal("Lebih dari 30 detik - WhatsApp memotongnya jadi "
                           "beberapa Status. Hentikan.")
    except FileNotFoundError:
        inti.info("durasi : (ffprobe tidak terpasang, dilewati)")

    # Nama berkas harus milik brand yang sama. Penjaga ini SENGAJA ada:
    # di jalur Meta Lacon justru belum ada, dan itu tercatat sebagai lubang -
    # sasaran composer diperiksa, nama berkas tidak.
    punya = inti.brand_berkas(berkas)
    if punya is None:
        inti.gagal("Nama berkas tidak menyebut brand mana pun. Jangan ditebak.")
    if isinstance(punya, list):
        inti.gagal("Nama berkas cocok ke beberapa brand %s. Hentikan." % punya)
    if punya != brand.lower():
        inti.gagal("BERKAS MILIK '%s', TAPI SASARANNYA '%s'. Hentikan."
                   % (punya, brand))
    inti.info("brand  : %s (cocok dengan nama berkas)" % brand)

    lama = sudah_pernah(brand, berkas)
    if lama:
        inti.gagal("SUDAH PERNAH NAIK:\n   %s\n  Hapus barisnya dari "
                   "riwayat.log kalau memang sengaja diulang." % lama)


# ----------------------------------------------------------------- perintah

def cmd_login(brand):
    p = inti.profil_brand(brand)
    os.makedirs(p, exist_ok=True)
    inti.info("brand  : %s" % brand)
    inti.info("profil : %s\n" % p)
    inti.info("SATU JENDELA SATU BRAND. Jangan buka brand lain sebelum yang ini")
    inti.info("selesai dan namanya sudah diperiksa.\n")
    # Start-Process supaya jendelanya LEPAS dari shell. Chrome yang menempel
    # pada perintah shell ikut mati begitu perintahnya selesai, jadi user
    # tidak sempat scan. Jendela login SENGAJA tidak diperkecil.
    subprocess.Popen(
        ["powershell", "-NoProfile", "-Command",
         "Start-Process '%s' -ArgumentList '--user-data-dir=%s',"
         "'--no-first-run','--no-default-browser-check',"
         "'--disable-features=Translate','%s'" % (CHROME, p, ALAMAT)],
        creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    inti.info("Jendela dibuka. Di HP: WhatsApp > Perangkat tertaut > Tautkan.")
    inti.info("Sesudah masuk, TUTUP jendelanya, lalu jalankan:")
    inti.info("    python wa.py akun %s" % brand)


def cmd_akun(brand):
    pw, ktx, hal = buka(brand)
    try:
        nama, baris = nama_akun(hal)
        inti.info("profil      : %s" % inti.profil_brand(brand))
        inti.info("NAMA BISNIS : %s" % (nama or "(tidak terbaca)"))
        inti.info("panel       : %s" % " | ".join(baris[:8]))
        potret(hal, "akun-%s" % brand)
        cfg = inti.baca_config()
        harap = (cfg.get("nama_akun") or {}).get(brand.lower())
        if harap:
            inti.info("\nterdaftar di config: %s" % harap)
            inti.info("COCOK" if inti.rapi(harap) == inti.rapi(nama)
                      else "TIDAK COCOK - jangan dipakai sebelum dibereskan")
        elif nama and inti.rapi(brand) in inti.rapi(nama):
            inti.info("\nCOCOK - nama akun memuat '%s'." % brand)
            inti.info("Daftarkan di config.json > nama_akun supaya terkunci.")
        else:
            inti.info("\nBELUM COCOK dengan '%s'." % brand)
            inti.info("Kalau ini memang nomor yang benar, isi config.json >")
            inti.info("nama_akun > %s dengan nama di atas." % brand.lower())
    finally:
        ktx.close(); pw.stop()


def cmd_status(brand, berkas, teks="", tulis=False):
    brand = brand.lower()
    periksa_berkas(brand, berkas)

    pw, ktx, hal = buka(brand)
    try:
        # Penjaga terakhir, dan yang paling penting: nomornya milik brand ini.
        nama, _ = nama_akun(hal)
        inti.info("akun   : %s" % (nama or "(tidak terbaca)"))
        cfg = inti.baca_config()
        harap = (cfg.get("nama_akun") or {}).get(brand)
        if harap:
            if inti.rapi(harap) != inti.rapi(nama):
                inti.gagal("AKUN TIDAK COCOK. config menyebut %r, terbaca %r."
                           % (harap, nama))
        elif not (nama and inti.rapi(brand) in inti.rapi(nama)):
            inti.gagal("Nama akun %r tidak memuat %r, dan brand ini belum\n"
                       "  terdaftar di config.json > nama_akun. Hentikan - "
                       "jangan menebak nomor siapa ini." % (nama, brand))
        inti.info("         cocok dengan brand")

        inti.info("\nbuka tab Status")
        hal.locator("button[aria-label='Status']").first.click()
        time.sleep(3)
        hal.locator("button[aria-label='Add Status']").first.click()
        time.sleep(2)

        inti.info("unggah media")
        with hal.expect_file_chooser(timeout=30000) as tadah:
            hal.locator("[aria-label='Foto & Video']").first.click()
        tadah.value.set_files(berkas)

        siap = False
        for d in range(0, 120, 3):
            if hal.evaluate("() => document.querySelectorAll('video').length"):
                inti.info("   pratinjau muncul setelah %d detik" % d)
                siap = True
                break
            time.sleep(3)
        if not siap:
            potret(hal, "tanpa-pratinjau-%s" % brand)
            inti.gagal("Pratinjau tidak muncul dalam 120 detik. "
                       "Tidak ada yang dikirim.")

        if teks:
            kotak = hal.locator("div[contenteditable='true']").first
            kotak.click()
            time.sleep(0.8)
            kotak.type(teks, delay=25)
            inti.info("   keterangan diisi: %s" % teks[:60])

        gbr = potret(hal, "kirim-%s-%s" % (brand, time.strftime("%Y%m%d-%H%M")))
        kirim = hal.locator("button[aria-label^='Kirim']")
        if not kirim.count():
            potret(hal, "tanpa-tombol-%s" % brand)
            inti.gagal("Tombol kirim tidak ketemu. Tidak ada yang dikirim.")
        inti.info("   tombol kirim: %s" % kirim.first.get_attribute("aria-label"))

        if not tulis:
            hal.keyboard.press("Escape")
            time.sleep(2)
            sisa = hal.evaluate("() => document.querySelectorAll('video').length")
            inti.info("\nPRATINJAU saja - composer dibatalkan, video tersisa %d."
                      % sisa)
            inti.info("Tidak ada Status yang terbit. Buka potretnya: %s" % gbr)
            return

        kirim.first.click()
        time.sleep(8)
        inti.catat("WA Status %s: %s terbit %s"
                   % (brand, os.path.basename(berkas),
                      time.strftime("%Y-%m-%d %H:%M")))
        potret(hal, "sesudah-%s" % brand)
        inti.info("\nTERKIRIM dan dicatat di riwayat.log.")
        inti.info("Buktinya BUKAN tulisan ini. Periksa baris 'Status saya'")
        inti.info("sudah berubah jadi berjam: python wa.py akun %s" % brand)
    finally:
        ktx.close(); pw.stop()
