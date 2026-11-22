# Kilang Video TikTok

## Folder
- `background/`: semua background video. Letak gambar baru kat sini sekali je (JPG/PNG, sebaiknya menegak 9:16).
  Setiap video akan pilih background **secara rawak** dari folder ni, jadi tak perlu set setiap kali.
- `tools/make_video.py`: skrip buat video (produk bergoyang + zoom background + caption pop-in).

## Pilih background tertentu (pilihan)
Dalam fail config video, tambah `"background": "background/kereta-vios.jpg"`.
Kalau tak tulis, skrip pilih sendiri. Tambah `"seed": 1` (nombor lain = background lain) kalau nak hasil yang sama setiap kali.
