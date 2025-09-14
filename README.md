# RecciTek Garanti Takip Uygulaması

[![Sürüm](https://img.shields.io/badge/sürüm-1.2.0-blue.svg)](https://github.com/KursatS/RecciTek-WarrantyUtil)
[![Lisans](https://img.shields.io/badge/lisans-MIT-green.svg)](LICENSE)

RecciTek Garanti Takip Uygulaması, kullanıcıların cihaz garanti bilgilerini etkili bir şekilde kontrol etmelerine ve yönetmelerine yardımcı olmak için tasarlanmış kapsamlı bir garanti takip uygulamasıdır. Uygulama, çeşitli cihaz türleri için gerçek zamanlı garanti durumu kontrolü sağlar ve birden fazla API entegrasyonu ile çalışır.

## Özellikler

### 🔍 Garanti Kontrolü
- **Çoklu Kaynak Entegrasyonu**: RecciTek ve KVK API'lerinden garanti durumunu kontrol eder
- **Gerçek Zamanlı Güncellemeler**: Anlık garanti bilgisi alma
- **Akıllı Tespit**: Panodan seri numaralarını otomatik olarak algılar
- **Önbellek Sistemi**: Geliştirilmiş performans ve azaltılmış API çağrıları için akıllı önbellekleme

### 📱 Kullanıcı Arayüzü
- **Modern Arayüz**: Temiz ve sezgisel modern tasarım
- **Sistem Tepsisi Entegrasyonu**: Kolay erişim için sistem tepsisinde çalışır
- **Arayüz Değiştirme**: Modern ve Klasik UI temaları arasında seçim
- **Duyarlı Tasarım**: Farklı ekran boyutları için optimize edilmiş

### 📊 Geçmiş ve Yönetim
- **Sorgu Geçmişi**: Tüm garanti kontrollerinin tam geçmişi
- **Cihaz Notları**: Takip edilen cihazlara kişisel not ekleme
- **Filtreleme Seçenekleri**: Tarih, durum ve cihaz türüne göre gelişmiş filtreleme
- **CSV Dışa Aktarma**: Harici analiz için garanti verilerini CSV formatına aktarma

### ⚙️ Gelişmiş Özellikler
- **Önbellek Yönetimi**: Onay ile manuel önbellek temizleme
- **Otomatik Başlatma**: Windows ile birlikte başlatma seçeneği
- **Tarih/Saat Takibi**: Tüm işlemler için detaylı zaman damgası bilgileri
- **Hata Yönetimi**: Kullanıcı dostu mesajlarla sağlam hata yönetimi

## Kurulum

### Ön Koşullar
- Windows 10/11
- Python 3.8 veya üzeri (geliştirme için)
- PyQt6
- Gerekli Python paketleri (requirements.txt dosyasına bakın)

### Kaynaktan Kurulum
1. Depoyu klonlayın:
```bash
git clone https://github.com/KursatS/RecciTek-WarrantyUtil.git
cd RecciTek-WarrantyUtil
```

2. Bağımlılıkları yükleyin:
```bash
pip install -r requirements.txt
```

3. Uygulamayı çalıştırın:
```bash
python app.py
```

### Yükleyici Kullanarak
1. [Releases](https://github.com/KursatS/RecciTek-WarrantyUtil/releases) sayfasından en son yükleyiciyi indirin
2. Yükleyici yürütülebilir dosyasını çalıştırın
3. Kurulum sihirbazını takip edin
4. Uygulama otomatik olarak sistem tepsisinde başlayacaktır

## Kullanım

### Temel İşlem
1. **Başlatma**: Uygulama sistem tepsisinde başlar
2. **Seri Kopyalama**: Cihaz seri numarasını panoya kopyalayın
3. **Otomatik Tespit**: Uygulama seri numarasını otomatik olarak algılar ve işler
4. **Sonuçları Görüntüleme**: Garanti bilgileri açılır pencerede görünür

### Manuel Giriş
- Sistem tepsisi simgesine sağ tıklayın
- "Modern" veya "Klasik" arayüzü seçin
- Seri numarasını manuel olarak girin
- "Garanti Kontrolü" butonuna tıklayın

### Geçmiş Yönetimi
- Sistem tepsisi menüsünden "Geçmiş Sorgular"a erişin
- Tüm önceki garanti kontrollerini görüntüleyin
- Cihazlara not ekleyin
- Verileri filtreleyin ve dışa aktarın

### Ayarlar
- Sistem tepsisi menüsünden ayarlara erişin
- Arayüz tercihlerini değiştirin
- Önbelleği temizleyin
- Uygulama davranışını özelleştirin

## Test Seri Numaraları

Uygulamayı test etmek için aşağıdaki seri numaralarını kullanabilirsiniz:

### KVK Sisteminden
- **R58EBR33801764**: KVK garantili cihaz

### RecciTek Sisteminden
- **R58VBR41200741**: RecciTek garantili cihaz
- **RCFVBY51101472**: RecciTek sistem dışı cihaz

### Garanti Dışı
- **R35EBD32102855**: Garanti süresi dolmuş cihaz

## API Entegrasyonları

### RecciTek API
- Resmi RecciTek garanti sorgulama sistemi
- Detaylı cihaz bilgileri (marka, model, renk)
- Gerçek zamanlı garanti durumu

### KVK Teknik Servis API
- KVK onaylı teknik servis ağı
- Geniş cihaz desteği
- Güvenilir garanti bilgileri

## Sistem Gereksinimleri

- **İşletim Sistemi**: Windows 10/11 (64-bit)
- **RAM**: Minimum 2GB, önerilen 4GB
- **Disk Alanı**: 100MB boş alan
- **Ağ**: İnternet bağlantısı (API sorguları için)

## Geliştirme

### Proje Yapısı
```
RecciTek-WarrantyUtil/
├── app.py                 # Ana uygulama dosyası
├── modernUi.py           # Modern arayüz modülü
├── classicUi.py          # Klasik arayüz modülü
├── historyUi.py          # Geçmiş sorgular arayüzü
├── device_notes.json     # Cihaz notları veritabanı
├── warranty_cache.json   # Garanti önbelleği
├── logo.ico             # Uygulama simgesi
├── logo.png             # Logo dosyası
├── installer.iss        # Inno Setup yükleyici betiği
└── README.md            # Bu dosya
```

### Katkıda Bulunma
1. Bu depoyu fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## Sorun Giderme

### Yaygın Sorunlar

**Uygulama başlamıyor:**
- Python ve PyQt6'nın doğru kurulduğundan emin olun
- Sistem tepsisi desteğinin aktif olduğunu kontrol edin

**API bağlantı hatası:**
- İnternet bağlantınızı kontrol edin
- Güvenlik duvarı ayarlarını kontrol edin
- API endpoint'lerinin erişilebilir olduğundan emin olun

**Önbellek sorunları:**
- Sistem tepsisi menüsünden önbelleği temizleyin
- Uygulamayı yeniden başlatın

### Log Dosyaları
Uygulama logları `%APPDATA%\RecciTek Warranty Util\logs\` klasöründe bulunur.

## Lisans

Bu proje MIT Lisansı altında lisanslanmıştır - detaylar için [LICENSE](LICENSE) dosyasına bakın.

## İletişim

- **GitHub**: [https://github.com/KursatS/RecciTek-WarrantyUtil](https://github.com/KursatS/RecciTek-WarrantyUtil)
- **Geliştirici**: KursatS
- **E-posta**: [GitHub üzerinden iletişime geçin](https://github.com/KursatS)

## Sürüm Geçmişi

### v1.2.0 (Güncel)
- Geçmiş sorgular ekranı eklendi
- Cihaz not alma özelliği
- Filtreleme butonları
- CSV dışa aktarma
- Önbellek temizleme onayı
- Tarih/saat bilgisi iyileştirmeleri

### v1.1.0
- Modern ve klasik arayüz seçenekleri
- Sistem tepsisi entegrasyonu
- Otomatik seri numarası tespiti
- Önbellek sistemi

### v1.0.0
- İlk sürüm
- Temel garanti kontrolü
- RecciTek ve KVK API entegrasyonları

---

**Not**: Bu uygulama sadece garanti bilgilerini kontrol etmek için tasarlanmıştır. Resmi garanti talepleri için lütfen üretici veya yetkili servislerle iletişime geçin.
