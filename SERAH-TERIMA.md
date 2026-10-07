# Serah terima - yang harus ditanyakan sebelum dipakai

Daftar ini dipakai **sekali**, waktu tim mulai memakai alat ini. Arahan user
7 Oktober 2026: jangan menebak empat hal di bawah, tanyakan.

Jalankan dulu untuk melihat posisi sekarang:

    python wa.py siap

Perintah itu hanya membaca - tidak mengubah apa pun, tidak membuka WhatsApp.

---

## 1. Link sheet jadwal kontennya

**Tanyakan, jangan pakai yang sudah ada.** Nilai di `config.json` sekarang
disalin dari proyek Lacon milik tim sosmed. Tim yang memakai alat ini belum
tentu memakai sheet yang sama.

Yang perlu dipastikan sesudah linknya diterima:

- id-nya dimasukkan ke `config.json` > `sheet_id`
- satu tab per brand, dan nama tabnya sama dengan nama brand
- kolom A tanggal, C kode konten, D penanda sudah tayang, F platform,
  G jam. Kalau susunannya beda, `wa_konten.baris_hari` harus disesuaikan -
  jangan dipaksa jalan.
- akun Google yang dipakai alat ini punya akses baca ke sheet itu

Perintah `siap` akan menyebutkan nama sheet dan daftar tabnya. **Baca
namanya** - itu yang membuktikan sheetnya benar, bukan id-nya yang panjang.

## 2. Link folder Drive berkasnya

Sama: **tanyakan**. Masukkan id-nya ke `config.json` > `drive_folder_id`,
lalu `python wa.py indeks` untuk menelusurinya.

Yang perlu diperiksa sesudah indeks jadi:

- `siap` menyebutkan nama foldernya - cocokkan dengan yang mereka maksud
- susunan folder akarnya nama brand. Kalau nama folder brandnya beda dari
  daftar di `wa_inti.FOLDER_BRAND`, stok brand itu akan terbaca **nol** -
  diamnya berbunyi, tapi tetap harus diperiksa sekali di awal.
- kalau ada folder berisi berkas yang **belum lolos kurasi**, namanya harus
  `Return`. Alat ini menyaring keluar berkas yang namanya ada di situ. Kalau
  tim memakai nama lain, saringannya tidak akan bekerja dan konten tolakan
  bisa tayang - ini pernah terjadi, 16 berkas.

## 3. Jam tayangnya

**Tim CS yang menetapkan.** Alat ini tidak menentukan jam dan tidak
menjadwalkan - WhatsApp memang tidak punya penjadwalan.

Yang perlu ditanyakan:

- jam berapa saja dalam sehari
- apakah sama untuk semua brand atau beda-beda
- siapa yang menjalankan perintahnya di jam itu

Selama jamnya belum ditetapkan, pakai `kirim`, bukan `slot`.

## 4. Login WhatsApp tiap brand

**Mereka yang scan QR.** Jangan pernah meminta, membaca, atau menyimpan
sandi dan kode OTP siapa pun.

Satu brand pada satu waktu:

    python wa.py login edufio      lalu mereka scan, lalu TUTUP jendelanya
    python wa.py akun edufio       baca nama akunnya, cocokkan

Jangan membuka beberapa jendela sekaligus. Semua halaman login WhatsApp
tampilannya sama persis, jadi tidak ada cara membedakan jendela mana milik
siapa. Di proyek sebelahnya ini sudah **empat kali** terjadi, dan akibatnya
konten brand satu tayang di akun brand lain.

Kalau nama akunnya tidak memuat nama brand, daftarkan nama persisnya di
`config.json` > `nama_akun`. Selama belum didaftarkan, perintah `status`
menolak jalan - itu disengaja.

Sebelas nomor yang dibutuhkan:

arabi, edubia, edubisa, edufio, edulob, edumisi, edumoka, eduosmo,
edupoint, eduraya, edusora

---

## Uji pertama: satu brand, tanpa mengirim

Sesudah satu brand login, buktikan rantainya utuh dulu:

    python wa.py unduh <tgl> --brand edufio --tulis
    python wa.py kirim <tgl> --brand edufio

Perintah kedua **tanpa** `--tulis`: media diunggah ke composer, pratinjaunya
dipotret ke `.chrome/kirim-edufio-....png`, lalu dibatalkan. Tidak ada Status
yang terbit.

**Buka potretnya.** Jangan percaya tulisan di layar saja - sudah tiga kali
di proyek sebelahnya teks halaman bilang berhasil sementara gambarnya bilang
lain.

Baru sesudah potretnya benar, tambahkan `--tulis`.
