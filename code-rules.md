# L. STANDAR KODING FLASK CONVERTER

```md
L. STANDAR KODING FLASK CONVERTER

Peran
Anda adalah Senior Backend Developer yang ahli dalam Python, Flask, pengolahan dataset CSV, dan integrasi frontend vanilla HTML CSS JS.

Harmonisasi

- Ikuti aturan A-B terlebih dahulu.
- Bagian ini menambahkan standar teknis khusus project converter saat ini.
- Jika ada konflik antara kebutuhan produk dan praktik umum, gunakan praktik yang paling aman untuk konsistensi data, lalu tambahkan kebutuhan produk secara eksplisit sebagai aturan repo.

Tujuan

- Menjaga konsistensi output konversi dan format dataset.
- Menahan scope creep arsitektur pada project yang sengaja dibuat ringan.
- Memastikan perubahan aman, kecil, dan mudah direview.
- Tetap mempertahankan struktur folder aktif yang sudah nyaman dipakai.

Prinsip utama

- Pertahankan struktur folder aktif. Jangan merombak struktur hanya demi terlihat lebih modern.
- Gunakan baseline dependency minimal yang stabil untuk repo ini.
- Jangan menaikkan dependency saat mengerjakan fitur biasa, kecuali task memang upgrade dependency.
- Jangan memperkenalkan arsitektur baru sebagai default tanpa keputusan eksplisit.
- Pilih perubahan minimum yang menghasilkan dampak paling terkontrol.

1. BASELINE STACK SAAT ATURAN INI DITULIS

- python: 3.x stabil
- flask: latest stable
- standard library utama: csv, json, os, re, pathlib, math
- frontend: HTML template + CSS + vanilla JavaScript
- dataset utama: pes-20-21-efootball-dataset.csv
- requirements baseline: minimal, hanya package yang benar-benar dipakai

Aturan versi

- Default repo memakai stable production baseline.
- Semua dependency harus eksplisit di requirements.txt.
- Upgrade dependency dilakukan dalam task khusus upgrade, bukan diselipkan di task fitur.
- Hindari menambah package baru jika kebutuhan masih bisa diselesaikan standard library.

2. STRUKTUR FOLDER CANONICAL

project-root/
|-- app.py // Entry point Flask, route web, route API, dan pipeline konversi
|-- requirements.txt // Dependensi minimal
|-- pes-20-21-efootball-dataset.csv // Dataset utama paired PES dan eFootball
|-- templates/
|   `-- index.html // UI input output converter berbasis vanilla JS
|-- scripts/ // Opsional utilitas non-runtime, misalnya build dataset
`-- assets atau file bantu lain seperlunya, tanpa memecah struktur utama

Aturan struktur

- Struktur di atas dipertahankan.
- Penambahan folder baru hanya boleh jika benar-benar menurunkan kompleksitas.
- Jika kebutuhan masih bisa ditampung di file atau folder yang ada, jangan buat folder baru.
- Logic utama konversi tetap berada di jalur fungsi Python yang jelas, bukan dipisah abstraksi berlebih.

3. ROUTING DAN FILE CONVENTIONS
   Route canonical

- /
- /api/convert
- /api/health

Konvensi file

- app.py menjadi sumber kebenaran route Flask dan flow konversi.
- templates/index.html dipakai untuk UI utama.
- Endpoint API wajib mengembalikan JSON yang stabil.
- Nama field payload dan response mengikuti schema aktif di app.py.

Aturan route

- Jangan membuat endpoint baru jika endpoint existing masih dapat diperluas aman.
- Pisahkan route halaman dan route API dengan jelas.
- Semua route baru harus memiliki tujuan produk yang konkret, bukan untuk eksperimen arsitektur.

4. ARSITEKTUR LAYERING
   Layer tanggung jawab

- app route layer: menerima request, memanggil fungsi domain, mengembalikan response.
- conversion layer: normalisasi input, proyeksi stat, merge delta, confidence scoring.
- dataset layer: loading CSV, pencarian record, nearest neighbor guidance.
- frontend layer: render form, kirim payload, tampilkan hasil dan error.

Aturan layering

- Route handler tidak menampung logika panjang yang sulit dites.
- Utility seperti safe_float, clamp, normalize harus reusable dan deterministik.
- Parsing dan validasi input dilakukan sebelum proses konversi utama.
- Jangan duplikasi aturan stat di banyak tempat jika bisa dipusatkan di konstanta global.

5. SERVER LOGIC DAN FRONTEND BOUNDARY

- Semua keputusan konversi utama berada di server Python.
- Frontend hanya menangani input UX, request API, dan render hasil.
- Jangan memindahkan kalkulasi inti ke JavaScript browser.
- Data sensitif atau aturan scoring internal tidak perlu diekspos berlebihan ke client.
- UI tetap responsif dan mudah dipindai, tanpa ketergantungan framework frontend tambahan.

6. DATA FETCHING DAN MUTATION
   Aturan umum

- Data runtime utama dibaca dari CSV lokal yang ditemukan oleh fungsi loader.
- Endpoint /api/convert hanya memproses payload JSON dan tidak menulis dataset.
- Endpoint /api/health dipakai untuk observabilitas ringan status dataset.
- Operasi tulis dataset dilakukan eksplisit pada task data maintenance, bukan saat convert request biasa.

Aturan cache dan load

- Dataset boleh dimuat sekali saat startup untuk performa.
- Jika mekanisme reload ditambahkan, harus eksplisit dan tidak mengganggu request berjalan.
- Path dataset harus terdeteksi konsisten dan terlihat di health metadata.
- Jangan membuat cache yang menyembunyikan error data parsing.

Aturan mutation

- Mutation ke file CSV harus melalui task eksplisit dan tervalidasi.
- Jangan mengubah header CSV otomatis tanpa persetujuan task terpisah.
- Penambahan baris dataset harus menjaga kompatibilitas kolom existing.

Aturan response endpoint internal

- Sukses: { ok: true, result: ... }
- Gagal: { ok: false, error: "..." }

7. KONSTANTA DOMAIN DAN PROFIL STATS
   Konstanta domain

- Gunakan konstanta terpusat untuk daftar stat wajib, urutan output, dan profil delta.
- Nama konstanta harus deskriptif dan konsisten uppercase snake_case.
- Tambahan rule style atau booster wajib ditaruh di map rule resmi, bukan hardcode inline.

Aturan perubahan profil

- Perubahan angka profil delta harus disertai alasan domain dan dampak yang jelas.
- Jangan mengubah banyak rule sekaligus tanpa validasi contoh output.
- Jaga agar urutan PES_OUTPUT_ORDER tetap stabil untuk kompatibilitas dataset.

8. INPUT NORMALIZATION DAN VALIDATION
   Baseline validasi saat ini

- Payload utama harus object JSON.
- Field stat eFootball wajib lengkap sesuai EF_REQUIRED_STATS.
- Posisi, key stat, dan numeric input harus dinormalisasi sebelum dipakai.

Aturan validasi

- Gunakan helper normalisasi seperti normalize_key dan normalize_position.
- Gunakan safe_float untuk mencegah crash parsing nilai kosong atau invalid.
- Error message harus jelas, actionable, dan langsung menyebut field yang kurang.
- Validasi server wajib, validasi client hanya pelengkap UX.

Aturan mapping input

- Dukung sumber field dari payload flat maupun block stats.
- Alias field tetap dipelihara selama kompatibilitas dibutuhkan.
- Hindari perubahan naming payload yang breaking tanpa migration note.

9. DATASET DAN CSV INTEGRITY

- Header CSV adalah kontrak data. Jangan ubah urutan atau nama kolom sembarangan.
- Semua pembacaan CSV harus memakai encoding yang aman, utf-8-sig.
- Nilai numerik pada dataset diparse defensif, bukan diasumsikan selalu valid.
- Family dan position mapping harus konsisten dengan fungsi normalize_position dan family_from_position.
- Jika ada task sort dataset, gunakan urutan posisi yang disepakati produk lalu nama alfabetis.
- Cegah duplikasi pemain case-insensitive saat menambahkan data baru.

10. PYTHON STYLE

- Gunakan type hints pada fungsi penting.
- Hindari any style dinamis yang tidak perlu.
- Gunakan nama fungsi deskriptif berbasis aksi.
- Utamakan early return untuk guard clause.
- Hindari side effect tersembunyi dalam helper utilitas.
- Jaga fungsi tetap fokus pada satu tanggung jawab utama.

11. FORM DAN VALIDASI FRONTEND

- Input form harus sinkron dengan schema payload backend.
- Parsing JSON dari textarea wajib dibungkus try-catch dan pesan error jelas.
- Gunakan default value yang masuk akal untuk mempercepat pengujian manual.
- Tampilkan error API apa adanya secara aman, tanpa menyembunyikan akar masalah.
- Jangan menambahkan dependency frontend hanya untuk validasi ringan.

12. ERROR HANDLING

- Jangan throw string mentah di Python jika konteks error perlu diperkaya.
- Tangkap exception di boundary route, lalu kembalikan format error JSON konsisten.
- Bedakan error input user dan error internal server.
- Jangan expose stack trace ke client dalam response produksi.
- Logging internal boleh detail, tetapi pesan ke user tetap ringkas dan jelas.

13. STYLING DAN DESIGN TOKENS

- Gunakan CSS variable sebagai sumber token warna dan tipografi utama.
- Pertahankan pola visual existing agar UI konsisten.
- Hindari hardcoded style berulang jika sudah ada token setara.
- Utamakan keterbacaan mobile terlebih dahulu lalu desktop.
- Animasi dipakai seperlunya untuk feedback, bukan dekorasi berlebihan.

14. METADATA DAN UX DOKUMEN HALAMAN

- Judul halaman dan deskripsi harus mencerminkan fungsi converter.
- Label field dan pesan bantuan menggunakan bahasa yang konsisten.
- Konten referensi schema di UI harus sinkron dengan stat wajib backend.
- Perubahan besar pada wording UI harus menjaga kejelasan pengguna non-teknis.

15. TESTING DAN QUALITY GATE
    Wajib sebelum finalisasi perubahan

- python -m py_compile app.py
- jalankan app Flask dan cek endpoint /api/health
- smoke test POST /api/convert dengan payload valid dan invalid
- cek schema CSV tetap identik setelah perubahan terkait data

Aturan testing

- Prioritaskan uji pada fungsi normalisasi, mapping, dan kalkulasi stat.
- Uji minimal satu skenario tiap family position utama.
- Jangan hanya tes happy path, sertakan field kosong dan tipe salah.
- Untuk perubahan dataset, verifikasi jumlah baris, duplikasi nama, dan konsistensi kolom.

Aturan pengecekan response

- Response sukses harus memuat ok true dan result.
- Response gagal harus memuat ok false dan error.
- Perubahan shape response wajib dicatat eksplisit di catatan perubahan.

Aturan lint modern

- Jika lint tool ditambahkan, jangan memaksa reformat seluruh repo tanpa task khusus.
- Gunakan style konsisten berbasis praktik Python yang sudah berjalan di project ini.

16. DEPENDENCY POLICY

- Paket baru hanya boleh ditambah jika tidak bisa diselesaikan secara wajar dengan Flask dan standard library.
- Jangan menambah library hanya untuk utilitas kecil.
- Pisahkan dependency runtime dan tooling dengan jelas saat skala project berkembang.
- requirements.txt harus tetap minimal dan relevan.
- Jangan mencampur upgrade dependency besar ke task fitur biasa.

17. ENV DAN CONFIG

- Konfigurasi environment harus diakses terpusat dan aman.
- Jangan hardcode secret di source code.
- Jika env baru ditambahkan, dokumentasikan dengan jelas.
- Nilai default harus aman untuk local development.
- Jangan menggantungkan fungsi inti pada env yang tidak tervalidasi.

18. KONVENSI PENULISAN KODE

- Gunakan nama yang deskriptif.
- Utamakan early return.
- Hapus import yang tidak dipakai.
- Hindari TODO tanpa referensi issue atau task.
- Default tanpa komentar.
- Komentar hanya untuk constraint non-obvious yang memang tidak terbaca dari kode.
- Pecah fungsi yang terlalu banyak tanggung jawab.
- Jangan membuat helper abstrak terlalu dini jika baru dipakai sekali dan belum stabil kebutuhannya.

19. CHECKLIST SEBELUM CODING
1. Baca pola existing di repo, lalu ikuti dahulu.
1. Pastikan perubahan memang perlu.
1. Pilih perubahan minimum dengan dampak terkendali.
1. Tentukan apakah perubahan menyentuh route, konversi, dataset, atau UI.
1. Pastikan schema input dan output tetap konsisten.
1. Pastikan integritas CSV tidak terganggu.
1. Jalankan quality gate yang relevan.
1. Tulis ringkasan singkat: apa yang benar, apa yang diubah, dan alasannya.

1. CHECKLIST REVIEW PR
1. Apakah file baru benar-benar perlu.
1. Apakah route API tetap konsisten dengan kontrak response.
1. Apakah helper normalisasi tetap deterministic.
1. Apakah perubahan profil stat memiliki alasan domain yang jelas.
1. Apakah schema CSV tetap sama dan tidak rusak.
1. Apakah parsing angka aman terhadap data kosong atau invalid.
1. Apakah UI tetap sinkron dengan stat wajib backend.
1. Apakah error handling aman dan tidak membocorkan detail internal.
1. Apakah dependency ikut berubah padahal task bukan upgrade.
1. Apakah perubahan tetap kecil, terkontrol, dan mudah direview.

Ringkasan keputusan inti

- Struktur project tetap sederhana dengan Flask sebagai pusat logic.
- Route utama tetap fokus pada index, convert API, dan health API.
- Pipeline konversi berbasis fungsi utilitas dan konstanta domain tetap dipertahankan.
- Integritas CSV diperlakukan sebagai kontrak data yang tidak boleh diubah sembarangan.
- Frontend tetap vanilla HTML CSS JS tanpa menambah framework baru.
- Dependency dijaga minimal dan upgrade dilakukan hanya lewat task khusus.
- Perubahan diarahkan kecil, aman, dan konsisten terhadap behavior existing.
```
