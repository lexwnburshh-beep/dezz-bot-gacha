# DEZZ NOKOS BOT V1 — Demo

Bot Telegram dengan tombol inline dan inventaris SQLite. **V1 hanya untuk nomor demo/fiktif**; tidak menghubungkan provider nomor, tidak menerima OTP, dan tidak membuat akun pada layanan lain.

## 1. Buat bot Telegram
1. Buka Telegram, cari `@BotFather`.
2. Kirim `/newbot`, ikuti instruksi, lalu salin token.
3. Cari ID Telegram kamu menggunakan bot pencari user ID yang tepercaya. Masukkan ID numerik ke `ADMIN_IDS`.

## 2. Deploy di Railway (tanpa Termux)
1. Buat repository GitHub baru dan upload file dalam ZIP ini ke repository.
2. Railway → New Project → Deploy from GitHub Repo → pilih repository.
3. Di Railway, buka service → Variables, tambahkan:
   - `BOT_TOKEN` = token dari BotFather (jangan bagikan).
   - `ADMIN_IDS` = ID Telegram admin, misalnya `123456789` (bisa beberapa, dipisahkan koma).
   - `DB_PATH` = `/data/dezz_nokos.db` (opsional).
4. Jika ingin database bertahan saat redeploy, tambahkan Railway Volume dan mount ke `/data`.
5. Deploy ulang. Lihat Deploy Logs; pastikan worker berjalan tanpa error.
6. Buka bot di Telegram lalu kirim `/start`.

## 3. Menambah stok demo
Admin kirim ke bot:
`/addstock Indonesia|WhatsApp|62|10`

Menambah 10 entri demo. Format nomor yang dihasilkan sengaja tidak valid sebagai nomor telepon nyata.

Perintah admin:
- `/adminstock` — ringkasan stok
- `/addstock negara|layanan|prefix|jumlah` — jumlah 1–500

Perintah pengguna:
- `/start` — menu
- `/stock` — stok demo
- `/prefix 62` — filter prefix
- `/prefix reset` — matikan filter

## Catatan
- Jangan pernah memasukkan token bot ke source code atau membagikannya. Jika token terlanjur bocor, reset melalui BotFather.
- Railway free/paid availability dan penyimpanan volume mengikuti kebijakan akun Railway yang berlaku.
- Tombol “Copy All” mengirim daftar demo ke chat; Telegram bot tidak dapat menyalin langsung ke clipboard HP.
