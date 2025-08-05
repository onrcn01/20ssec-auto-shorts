# 20SSEC Auto Shorts (GitHub Actions + Pexels + FFmpeg)

Bu repo her gün otomatik drift Shorts üretir:
- Pexels API'den 10 dikey klip indirir
- FFmpeg ile 5 tanesini işler (9:16, hook, freeze, mini-replay, logo, müzik)
- H.264 / yuv420p / faststart çıkış verir

## Kurulum (10 dakika)
1) Pexels API → https://www.pexels.com/api/ → API Key al.
2) GitHub'da boş public repo oluştur.
3) Bu zip'i **yerelde çıkar**, içindeki klasör/dosyaları GitHub'da repo sayfasına
   **Add file → Upload files** ile **tamamını** sürükle-bırak.
   - `.github/workflows/daily.yml` dosyasının da yüklendiğinden emin ol.
   - Eğer ".github" klasörünü web'den yükleyemiyorsan, GitHub'da **Create new file**
     deyip dosya adını `.github/workflows/daily.yml` yap ve içeriğini bu zip'teki ile kopyala.
4) Repo → Settings → Secrets → Actions → New secret:
   - Name: `PEXELS_API_KEY`
   - Value: (Pexels API Key)
5) Actions sekmesine gir → `daily-shorts` workflow'unu **Run workflow** ile çalıştır.
   - İş bitince sayfanın altında **Artifacts → shorts_outputs**'tan MP4'leri indir.
6) `logo/20ssec_logo.png` (opsiyonel) → şeffaf PNG yüklersen videolara eklenir.
7) `music/` klasörüne MP3 eklersen rastgele müzik eklenir (yoksa sessiz çıkar).

## Zamanlama
`.github/workflows/daily.yml` içindeki `cron` satırını TR saatine göre düzenleyebilirsin.

## Not
İstersen Google Drive'a otomatik yükleme (rclone) adımı da eklenebilir.
