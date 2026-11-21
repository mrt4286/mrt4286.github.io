# Seiko Presage Dynamic – Galaxy Watch 7 kurulumu (Wi‑Fi / ADB)

Paket: `com.mrt4286.seikopresage` · Watch Face Format v2 · Wear OS 5+ (API 34)

## 1) Saatte hazırlık (bir kez)
1. **Ayarlar → Saat hakkında → Yazılım** → *Yazılım sürümü*'ne 7 kez dokun (Geliştirici modu açılır).
2. **Ayarlar → Geliştirici seçenekleri** → **ADB hata ayıklama: Açık**.
3. Aynı yerde **Kablosuz hata ayıklama: Açık** (saat ile bilgisayar/telefon aynı Wi‑Fi'de olmalı).

## 2) Eşleştirme + kurulum (PC)
`adb` (Android platform-tools) kurulu olmalı. Sonra proje klasöründe:

    ./install_to_watch.sh          # Windows: install_to_watch.bat

Script senden şunları ister:
- **Pairing adresi + 6 haneli kod:** Kablosuz hata ayıklama ekranında *Yeni cihaz eşleştir* → IP:PORT ve kod.
- **Bağlantı adresi:** Kablosuz hata ayıklama ana ekranındaki IP:PORT (eşleştirme portundan **farklıdır**).

Elle yapmak istersen:

    adb pair   <PAIR_IP:PORT>      # kodu gir
    adb connect <CONNECT_IP:PORT>
    adb -s <CONNECT_IP:PORT> install -r SeikoPresageDynamic-debug.apk

## 3) Kadranı seç
Saatte mevcut kadrana uzun bas → en sona kaydır → **+ Kadran ekle** → **Seiko Presage Dynamic**.

## 4) Tek seferlik ayarlar
- **Sıcaklık (12 altı):** Kadrana uzun bas → *Özelleştir* → sıcaklık alanına dokun → **Hava durumu** komplikasyonunu seç.
  (WFF v2 şemasında "varsayılan hava durumu sağlayıcısı" yok, bu yüzden slot ilk başta boştur.)
- **Adım sayacı 0 gösteriyorsa:** Ayarlar → Uygulamalar → Seiko Presage Dynamic → İzinler → *Fiziksel aktivite* → İzin ver.

## Sorun giderme
| Belirti | Çözüm |
|---|---|
| `adb connect` zaman aşımı | Saat ve PC aynı Wi‑Fi mi? Kablosuz hata ayıklama ekranı açık mı? Bağlantı portu eşleştirme portu değil. |
| `INSTALL_FAILED_...` | `adb uninstall com.mrt4286.seikopresage` sonra tekrar kur. |
| Kadran listede yok | Saati yeniden başlat; kadran seçicide en sonda aranır. |
| Kurulum bitti | Pil için: `adb disconnect` ve saatte Kablosuz hata ayıklamayı kapat. |

## Projeyi yeniden derleme
- **Normal makine (Android SDK 34 + internet):** `./gradlew assembleDebug` → `app/build/outputs/apk/debug/`
- **SDK'sız / kısıtlı ortam:** `tools/build_apk_offline.sh` (aapt2 + zipalign + apksigner kullanır)
- Renk/yerleşim değişikliği: `config.py` → `python3 generate_assets.py && python3 generate_watchface_xml.py`
- XML doğrulama: `python3 tools/validate_wff.py`
