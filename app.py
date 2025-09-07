#!/usr/bin/env python3

import sys
import re
import logging
import json
import os
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from modernUi import ModernPopup
from classicUi import ClassicPopup

RECCI_BASE = "https://garantibelgesi.recciteknoloji.com/sorgu/"
KVK_API = "https://guvencesorgula.kvkteknikservis.com/api/device-data?imeiNo="
SERIAL_REGEX = re.compile(r"^R[A-Za-z0-9]{13}$")

# Cache ayarları
CACHE_FILE = "warranty_cache.json"
CACHE_MAX_SIZE = 100
CACHE_EXPIRY_HOURS = 168  # 1 hafta (7 gün)

# HTTP ayarları
MAX_RETRIES = 3
BACKOFF_FACTOR = 0.3
TIMEOUT_RECCI = 8
TIMEOUT_KVK = 10

logging.basicConfig(
    level=logging.INFO,
    filename="garanti.log",
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("garanti")

def log_info(msg: str):
    logger.info(msg)

def log_exc(msg: str):
    logger.exception(msg)

def load_cache():
    """Cache dosyasını yükle"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Süresi dolmuş kayıtları temizle
            current_time = datetime.now()
            expiry_time = timedelta(hours=CACHE_EXPIRY_HOURS)

            valid_cache = {}
            for serial, data in cache_data.items():
                cache_time = datetime.fromisoformat(data['timestamp'])
                if current_time - cache_time < expiry_time:
                    valid_cache[serial] = data

            return valid_cache
    except Exception as e:
        log_exc(f"Cache yükleme hatası: {e}")

    return {}

def save_cache(cache_data):
    """Cache'i dosyaya kaydet"""
    try:
        # Cache boyutu kontrolü
        if len(cache_data) > CACHE_MAX_SIZE:
            # En eski kayıtları sil (LRU mantığı)
            sorted_items = sorted(cache_data.items(),
                                key=lambda x: x[1]['timestamp'])
            cache_data = dict(sorted_items[-CACHE_MAX_SIZE:])

        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_exc(f"Cache kaydetme hatası: {e}")

def get_cached_result(serial, cache_data):
    """Cache'den sonuç al"""
    if serial in cache_data:
        data = cache_data[serial]
        current_time = datetime.now()
        cache_time = datetime.fromisoformat(data['timestamp'])
        expiry_time = timedelta(hours=CACHE_EXPIRY_HOURS)

        if current_time - cache_time < expiry_time:
            log_info(f"Cache hit: {serial}")
            return data

        # Süresi dolmuş cache'i sil
        del cache_data[serial]
        save_cache(cache_data)

    return None

def add_to_cache(serial, result_data, cache_data):
    """Cache'e yeni kayıt ekle"""
    cache_data[serial] = {
        'timestamp': datetime.now().isoformat(),
        'result': result_data
    }
    save_cache(cache_data)
    log_info(f"Cache'e eklendi: {serial}")

def create_http_session():
    """Optimize edilmiş HTTP session oluştur"""
    session = requests.Session()

    # Retry stratejisi
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504],
    )

    # Connection pooling adapter
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=20
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


class GarantiTrayApp(QtCore.QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app

        # Icon ayarla
        self.tray_icon = QSystemTrayIcon(QIcon("logo.ico"))
        self.tray_icon.setToolTip("Garanti Takip Sistemi")

        # Menü oluştur
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                padding: 2px;
                color: #ffffff;
            }
            QMenu::item {
                background-color: transparent;
                padding: 8px 16px;
                border-radius: 0px;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            QMenu::item:hover {
                background-color: #094771;
            }
        """)

        # Arayüz menüsü
        interface_menu = self.menu.addMenu("Arayüz")

        # Modern arayüz seçeneği
        modern_action = QAction("Modern", self)
        modern_action.triggered.connect(lambda: self.change_interface("modern"))
        interface_menu.addAction(modern_action)

        # Klasik arayüz seçeneği
        classic_action = QAction("Klasik", self)
        classic_action.triggered.connect(lambda: self.change_interface("classic"))
        interface_menu.addAction(classic_action)

        # Ayırıcı çizgi
        self.menu.addSeparator()

        # Çıkış butonu
        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.quit)
        self.menu.addAction(exit_action)

        # Menüyü tray icon'a bağla
        self.tray_icon.setContextMenu(self.menu)

        # Tray icon görünürlüğünü sağla
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.setVisible(True)
            self.tray_icon.show()

            # Birkaç kez tekrar göster
            QTimer.singleShot(500, lambda: self.tray_icon.show())
            QTimer.singleShot(1500, lambda: self.tray_icon.show())
            QTimer.singleShot(3000, lambda: self.tray_icon.show())

        # Arayüz seçimi (varsayılan: modern)
        self.current_interface = "modern"
        self.current_popup = None

        # Clipboard izleme
        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        self._last_serial = None

    def change_interface(self, interface_type):
        """Arayüzü değiştir"""
        try:
            old_interface = self.current_interface
            self.current_interface = interface_type
            log_info(f"Arayüz değiştirildi: {old_interface} → {interface_type}")

            # Mevcut popup varsa kapat
            if self.current_popup and hasattr(self.current_popup, 'isVisible') and self.current_popup.isVisible():
                self.current_popup.close_popup()

        except Exception as e:
            log_exc(f"Arayüz değiştirme hatası: {e}")

    def show_popup(self, title: str, info: str, copy_model_payload: str = None, copy_date_payload: str = None, status_color: str = "red", serial: str = None):
        """Seçili arayüze göre popup göster"""
        try:
            # Mevcut popup varsa kapat
            if self.current_popup and hasattr(self.current_popup, 'isVisible') and self.current_popup.isVisible():
                self.current_popup.close_popup()

            # Yeni popup oluştur
            if self.current_interface == "modern":
                self.current_popup = ModernPopup()
            else:  # classic
                self.current_popup = ClassicPopup()

            # Popup içeriğini ayarla
            self.current_popup.set_content(title, info, copy_model_payload, copy_date_payload, status_color, serial)

        except Exception as e:
            log_exc(f"Popup gösterme hatası: {e}")

    def quit(self):
        try:
            log_info("Uygulama kapatılıyor.")
            QtCore.QCoreApplication.quit()
        except Exception as e:
            log_exc("Quit error: " + str(e))

    def on_clipboard_change(self):
        try:
            text = self.clipboard.text().strip()
            if not text:
                return
            token = None
            for part in re.split(r"\s+|[,;]", text):
                if SERIAL_REGEX.fullmatch(part):
                    token = part
                    break
            if not token:
                return
            if token == self._last_serial:
                return
            self._last_serial = token
            log_info(f"Detected serial in clipboard: {token}")
            QtCore.QTimer.singleShot(100, lambda: self.check_warranty(token))
        except Exception as e:
            log_exc("Clipboard handler error: " + str(e))

    def check_warranty(self, serial: str):
        try:
            # Cache kontrolü
            cache_data = load_cache()
            cached_result = get_cached_result(serial, cache_data)

            if cached_result:
                # Cache'den sonuç var
                result = cached_result['result']
                self.show_popup(
                    result.get('title', ''),
                    result.get('info', ''),
                    result.get('copy_model_payload'),
                    result.get('copy_date_payload'),
                    result.get('status_color', 'red'),
                    serial
                )
                log_info(f"Cache'den sonuç gösterildi: {serial}")
                return

            # 1. Recci kontrolü
            recci_url = RECCI_BASE + serial
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            # Optimize edilmiş HTTP session kullan
            session = create_http_session()
            recci_resp = session.get(recci_url, headers=headers, timeout=TIMEOUT_RECCI)
            recci_resp.raise_for_status()
            soup = BeautifulSoup(recci_resp.text, "html.parser")

            recci_in_warranty = False
            if soup.find(string=re.compile(r"Garanti Kapsam[ıi]ndadır", re.I)):
                recci_in_warranty = True
            else:
                badge = soup.find("div", class_=lambda v: v and "bg-emerald-100" in v)
                if badge:
                    recci_in_warranty = True

            if recci_in_warranty:
                def extract_label_value(soup, label_names):
                    for lab in label_names:
                        el = soup.find(lambda tag: tag.name == "div" and tag.get_text(strip=True).lower() == lab.lower())
                        if el and el.parent:
                            children = [c for c in el.parent.find_all("div", recursive=False)]
                            if len(children) >= 2:
                                return children[1].get_text(strip=True)
                    return None

                brand = extract_label_value(soup, ["Marka", "marka"])
                model = extract_label_value(soup, ["Model", "model"])
                color = extract_label_value(soup, ["Renk", "renk"])

                if not (brand or model or color):
                    grid = soup.find(lambda tag: tag.name == "div" and tag.get("class") and any("grid" in c for c in tag.get("class")))
                    if grid:
                        texts = [t.get_text(strip=True) for t in grid.find_all("div", recursive=False)]
                        for i in range(len(texts)-1):
                            t = texts[i].lower()
                            if t == "marka" and i+1 < len(texts):
                                brand = texts[i+1]
                            if t == "model" and i+1 < len(texts):
                                model = texts[i+1]
                            if t == "renk" and i+1 < len(texts):
                                color = texts[i+1]

                model_up = model.upper() if model else None
                color_up = color.upper() if color else None
                brand_up = brand.upper() if brand else None

                if not model or model.strip() == "":
                    display_text = "MODEL BULUNAMADI. LÜTFEN CİHAZ ÜZERİNDEN ÖĞRENİNİZ."
                    copy_model_payload = None
                else:
                    display_parts = [p for p in [brand_up, model_up, color_up] if p]
                    display_text = " - ".join(display_parts) if display_parts else "Recci bilgisi bulunamadı."
                    copy_model_payload = " - ".join([p for p in [model_up, color_up] if p]) or None

                self.show_popup("", display_text, copy_model_payload=copy_model_payload, copy_date_payload=None, status_color="green", serial=serial)

                # Cache'e kaydet
                result_data = {
                    'title': '',
                    'info': display_text,
                    'copy_model_payload': copy_model_payload,
                    'copy_date_payload': None,
                    'status_color': 'green'
                }
                add_to_cache(serial, result_data, cache_data)

                log_info(f"Recci garantili: {serial} | {display_text}")
                return

            if serial.startswith("RCCVBY") or serial.startswith("RCFVBY"):
                self.show_popup("", "MODEL BULUNAMADI. LÜTFEN CİHAZ ÜZERİNDEN ÖĞRENİNİZ.", status_color="green", serial=serial)

                # Cache'e kaydet
                result_data = {
                    'title': '',
                    'info': "MODEL BULUNAMADI. LÜTFEN CİHAZ ÜZERİNDEN ÖĞRENİNİZ.",
                    'copy_model_payload': None,
                    'copy_date_payload': None,
                    'status_color': 'green'
                }
                add_to_cache(serial, result_data, cache_data)

                log_info(f"Özel seri garantili: {serial}")
                return

            # 2. KVK API kontrolü
            kvk_no_data = False
            try:
                kvk_api_url = KVK_API + serial
                import subprocess
                import json

                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                command = [
                    "curl",
                    "-s", "-L", "--tlsv1.2",
                    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    kvk_api_url
                ]

                result = subprocess.run(
                    command, capture_output=True, text=True, encoding='utf-8',
                    timeout=10, check=True, startupinfo=startupinfo
                )
                kvk_data = json.loads(result.stdout)

                # KVK'da veri var mı kontrol et
                if kvk_data.get("IsSucceeded") == 1:
                    result_data = kvk_data.get("ResultData")
                    if result_data and isinstance(result_data, list) and len(result_data) > 0:
                        device_data = result_data[0]
                        description = device_data.get("DESCRIPTION", "")
                        warranty_end = device_data.get("WARRANTYEND", "")

                        if description and "no data found" not in description.lower():
                            # KVK'da garanti bulundu
                            modified_description = re.sub(r'ROBOROCK', '', description, flags=re.IGNORECASE)
                            modified_description = re.sub(r'ROBOT SÜPÜRGE', '', modified_description, flags=re.IGNORECASE)
                            modified_description = re.sub(r'\s+', ' ', modified_description).strip()

                            formatted_copy_model_payload = None
                            if modified_description:
                                parts = modified_description.rsplit(' ', 1)
                                if len(parts) == 2:
                                    formatted_copy_model_payload = f"{parts[0].upper()} - {parts[1].upper()}"
                                else:
                                    formatted_copy_model_payload = modified_description.upper()

                            display_text = f"{description}\nBitiş: {warranty_end}"
                            self.show_popup("", display_text, copy_model_payload=formatted_copy_model_payload, copy_date_payload=warranty_end, status_color="blue", serial=serial)

                            # Cache'e kaydet
                            result_data = {
                                'title': '',
                                'info': display_text,
                                'copy_model_payload': formatted_copy_model_payload,
                                'copy_date_payload': warranty_end,
                                'status_color': 'blue'
                            }
                            add_to_cache(serial, result_data, cache_data)

                            log_info(f"KVK garantili: {serial} | {formatted_copy_model_payload} | Bitiş: {warranty_end}")
                            return
                        else:
                            # KVK'da "no data found" var
                            kvk_no_data = True
                    else:
                        # KVK'da ResultData boş veya liste değil
                        kvk_no_data = True
                else:
                    # KVK başarısız
                    kvk_no_data = True

            except FileNotFoundError:
                self.show_popup("HATA", "curl komutu sistemde bulunamadı.", status_color="red", serial=serial)

                # Cache'e kaydet
                result_data = {
                    'title': 'HATA',
                    'info': "curl komutu sistemde bulunamadı.",
                    'copy_model_payload': None,
                    'copy_date_payload': None,
                    'status_color': 'red'
                }
                add_to_cache(serial, result_data, cache_data)

                return
            except subprocess.TimeoutExpired:
                self.show_popup("", "KVK sorgusu zaman aşımına uğradı.", status_color="red", serial=serial)

                # Cache'e kaydet
                result_data = {
                    'title': '',
                    'info': "KVK sorgusu zaman aşımına uğradı.",
                    'copy_model_payload': None,
                    'copy_date_payload': None,
                    'status_color': 'red'
                }
                add_to_cache(serial, result_data, cache_data)

                return
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                kvk_no_data = True

            # 3. Her iki sistemde de garanti bulunamadıysa
            if kvk_no_data:
                self.show_popup("", "Hiçbir sistemde garanti bilgisi bulunamadı.", copy_model_payload=None, copy_date_payload=None, status_color="red", serial=serial)

                # Cache'e kaydet
                result_data = {
                    'title': '',
                    'info': "Hiçbir sistemde garanti bilgisi bulunamadı.",
                    'copy_model_payload': None,
                    'copy_date_payload': None,
                    'status_color': 'red'
                }
                add_to_cache(serial, result_data, cache_data)

                log_info(f"Garanti dışı: {serial} (Recci ve KVK'da bulunamadı)")
            else:
                # Sadece Recci'de bulunamadı, KVK kontrol edilemedi
                self.show_popup("", "Hiçbir sistemde garanti bilgisi bulunamadı.", copy_model_payload=None, copy_date_payload=None, status_color="red", serial=serial)

                # Cache'e kaydet
                result_data = {
                    'title': '',
                    'info': "Hiçbir sistemde garanti bilgisi bulunamadı.",
                    'copy_model_payload': None,
                    'copy_date_payload': None,
                    'status_color': 'red'
                }
                add_to_cache(serial, result_data, cache_data)

                log_info(f"Garanti dışı: {serial} (Recci'de bulunamadı, KVK kontrol edilemedi)")

        except requests.exceptions.Timeout:
            self.show_popup("HATA", "Sorgu zaman aşımına uğradı.", status_color="red", serial=serial)

            # Cache'e kaydet
            result_data = {
                'title': 'HATA',
                'info': "Sorgu zaman aşımına uğradı.",
                'copy_model_payload': None,
                'copy_date_payload': None,
                'status_color': 'red'
            }
            add_to_cache(serial, result_data, cache_data)

        except requests.exceptions.RequestException as req_e:
            self.show_popup("HATA", f"Sorgu hatası: {str(req_e)}", status_color="red", serial=serial)

            # Cache'e kaydet
            result_data = {
                'title': 'HATA',
                'info': f"Sorgu hatası: {str(req_e)}",
                'copy_model_payload': None,
                'copy_date_payload': None,
                'status_color': 'red'
            }
            add_to_cache(serial, result_data, cache_data)

        except Exception as e:
            self.show_popup("HATA", f"Beklenmeyen bir hata oluştu: {str(e)}", status_color="red", serial=serial)

            # Cache'e kaydet
            result_data = {
                'title': 'HATA',
                'info': f"Beklenmeyen bir hata oluştu: {str(e)}",
                'copy_model_payload': None,
                'copy_date_payload': None,
                'status_color': 'red'
            }
            add_to_cache(serial, result_data, cache_data)


def main():
    try:
        app = QApplication(sys.argv)
        tray_app = GarantiTrayApp(app)
        log_info("Garanti tepsi uygulaması başlatıldı.")

        # Başlangıç popup'ı göster
        start_popup = ModernPopup()
        start_popup.set_content("GARANTİ TAKİP SİSTEMİ BAŞLATILDI.", "Geliştirici: KURSAT SINAN", status_color="green")
        QTimer.singleShot(1000, lambda: start_popup.show_at_bottom_right())

        sys.exit(app.exec())
    except Exception as e:
        log_exc("Uygulama fatal hata: " + str(e))
        raise

if __name__ == "__main__":
    main()
