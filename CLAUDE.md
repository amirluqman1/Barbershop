# Kilang Video TikTok Affiliate

Repo ni untuk buat video affiliate TikTok (9:16) secara pukal. Pemilik cakap Bahasa Melayu santai.

## Tetapan tetap (jangan tanya semula)
- **Suara voiceover:** ikut `settings/voice.json`, iaitu ElevenLabs **"Aisyah – Relatable Gen Z Girl"**
  (`voice_id` OKXs3meiBjKES3o87ubz, model `eleven_v4`, satu take sahaja: generations_count 1).
  Kalau kuota ElevenLabs habis, guna fallback Edge TTS `ms-MY-YasminNeural`.
- **Background:** pilih automatik dari folder `background/`. Jangan minta pemilik upload background.
- **Skrip video:** `tools/make_video2.py` (voiceover + tajuk atas + subtitle + glitch). `tools/make_video.py` versi lama tanpa suara.
- **Buang background produk:** rembg model `birefnet-general-lite` (paling bersih untuk gambar yang background sesak).

## Gaya skrip voiceover (penting)
Tiru gaya video affiliate Malaysia yang laku:
- Ayat **pendek-pendek**, cakap terus dengan penonton ("akak", "korang").
- Perkataan harian: "grab", "tinggal tarik je", "murah gila", "terus naik seri".
- Mula dengan cerita ringkas ("Hari tu akak singgah...", "Lepas pindah rumah hari tu...").
- Tutup dengan desakan: "Kalau akak berminat, grab kat link bawah ni. Grab terus, nanti naik harga pula!"
- Panjang 15–25 saat (lebih kurang 250–350 aksara).
- **Jangan reka fakta produk.** Kalau tak tahu spesifikasi, tanya pemilik.

## Peringatan
- Video yang guna scene/visual AI kena on label "AI-generated" masa upload TikTok.
- Jangan guna video atau suara creator lain (termasuk clone suara orang).
- Commit guna email noreply: 347319351+amirluqman1@users.noreply.github.com
