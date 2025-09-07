#!/usr/bin/env python3

import sys
import re
import logging
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup
import urllib3

# SSL uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QIcon, QPixmap, QAction
from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu,
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
)

# Ayarlar
RECCI_BASE = "https://garantibelgesi.recciteknoloji.com/sorgu/"
KVK_API = "https://guvencesorgula.kvkteknikservis.com/api/device-data?imeiNo="
SERIAL_REGEX = re.compile(r"^R[A-Za-z0-9]{13}$")
LOG_FILE = Path.home() / "garanti.log"

# Logging
logging.basicConfig(
    level=logging.INFO,
    filename=str(LOG_FILE),
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("garanti")

def log_info(msg: str):
    logger.info(msg)

def log_exc(msg: str):
    logger.exception(msg)


class Popup(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("main_popup")
        self.copy_model_payload = None
        self.copy_date_payload = None
        self.current_serial = None

        self._build_ui()

    def _build_ui(self):
        self.resize(380, 220)
        outer = QFrame(self)
        outer.setObjectName("outer")
        outer.setStyleSheet("""
            QFrame#outer { background-color: rgba(0,0,0,160); border-radius: 12px; }
        """)
        outer.setGeometry(0, 0, self.width(), self.height())

        self.bubble = QFrame(outer)
        self.bubble.setObjectName("bubble")
        self.bubble.setStyleSheet("""
            QFrame#bubble { background-color: rgba(22,163,74,255); border-radius: 10px; }
        """)
        self.bubble.setGeometry(12, 12, self.width() - 24, self.height() - 24)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(14, 12, 14, 12)
        vbox.setSpacing(8)

        self.title_label = QLabel("GARANTİ DURUMU")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-weight:700; font-size:14px; color: white;")

        self.serial_label = QLabel("")
        self.serial_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.serial_label.setStyleSheet("font-weight: bold; font-size:12px; color: #ffffff99;")
        self.serial_label.setVisible(False)

        self.info_label = QLabel("")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("font-weight: bold; font-size:13px; color: #ffffffdd;")

        self.copy_model_btn = QPushButton("Modeli Kopyala")
        self.copy_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_model_btn.setFixedHeight(30)
        self.copy_model_btn.setStyleSheet("""
            QPushButton {
                background-color: #111111;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight:600;
            }
            QPushButton:hover {
                background-color: #222222;
            }
        """)
        self.copy_model_btn.clicked.connect(self._on_copy_model)
        self.copy_model_btn.setVisible(False)

        self.copy_date_btn = QPushButton("Tarihi Kopyala")
        self.copy_date_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_date_btn.setFixedHeight(30)
        self.copy_date_btn.setStyleSheet("""
            QPushButton {
                background-color: #111111;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 6px 10px;
                font-weight:600;
            }
            QPushButton:hover {
                background-color: #222222;
            }
        """)
        self.copy_date_btn.clicked.connect(self._on_copy_date)
        self.copy_date_btn.setVisible(False)

        hbtn_layout = QHBoxLayout()
        hbtn_layout.setContentsMargins(0,0,0,0)
        hbtn_layout.setSpacing(10)
        hbtn_layout.addStretch(1)
        hbtn_layout.addWidget(self.copy_model_btn)
        hbtn_layout.addWidget(self.copy_date_btn)
        hbtn_layout.addStretch(1)

        vbox.addWidget(self.title_label)
        vbox.addWidget(self.serial_label)
        vbox.addWidget(self.info_label)
        vbox.addLayout(hbtn_layout)

        self.bubble.setLayout(vbox)

        self.close_btn = QPushButton("×", self.bubble)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                padding-bottom: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        self.close_btn.clicked.connect(self.close_popup)

        close_btn_x = self.bubble.width() - self.close_btn.width() - 5
        close_btn_y = 5
        self.close_btn.move(close_btn_x, close_btn_y)

        self.autoclose_timer = QTimer(self)
        self.autoclose_timer.setInterval(7000)  # 7 saniye
        self.autoclose_timer.timeout.connect(self.close_popup)

    def _on_copy_model(self):
        try:
            if self.copy_model_payload:
                QApplication.clipboard().setText(self.copy_model_payload)
                log_info(f"Copied model to clipboard: {self.copy_model_payload}")
        except Exception as e:
            log_exc("Copy model failed: " + str(e))

    def _on_copy_date(self):
        try:
            if self.copy_date_payload:
                QApplication.clipboard().setText(self.copy_date_payload)
                log_info(f"Copied date to clipboard: {self.copy_date_payload}")
        except Exception as e:
            log_exc("Copy date failed: " + str(e))

    def close_popup(self):
        try:
            self.hide()
            self.autoclose_timer.stop()
        except Exception as e:
            log_exc("Popup close error: " + str(e))

    def show_at_bottom_right(self):
        try:
            screen = QApplication.primaryScreen()
            geo = screen.availableGeometry()
            self.adjustSize()
            w = self.width()
            h = self.height()
            x = geo.right() - w - 20
            y = geo.bottom() - h - 20
            self.move(x, y)
            self.show()
            self.autoclose_timer.start()
        except Exception as e:
            log_exc("Show popup error: " + str(e))

    def set_content(self, title: str, info: str, copy_model_payload: str = None, copy_date_payload: str = None, status_color: str = "red", serial: str = None):
        try:
            if status_color == "green":
                if title == "GARANTİ TAKİP SİSTEMİ BAŞLATILDI.":
                    bubble_color = "rgba(75,0,130,255)"
                    title_text = "GARANTİ TAKİP SİSTEMİ BAŞLATILDI."
                else:
                    bubble_color = "rgba(22,163,74,255)"
                    title_text = "RECCI GARANTİLİ"
            elif status_color == "blue":
                bubble_color = "rgba(59,130,246,255)"
                title_text = "KVK GARANTİLİ"
            else:
                bubble_color = "rgba(220,38,38,255)"
                title_text = "GARANTİ DIŞI" if title == "" else title

            self.bubble.setStyleSheet(f"QFrame#bubble {{ background-color: {bubble_color}; border-radius: 10px; }}")
            self.title_label.setText(title_text)

            if serial:
                self.serial_label.setText(f"Seri No: {serial}")
                self.serial_label.setVisible(True)
            else:
                self.serial_label.setVisible(False)

            self.info_label.setText(info)
            self.copy_model_payload = copy_model_payload
            self.copy_date_payload = copy_date_payload
            self.current_serial = serial

            self.copy_model_btn.setVisible(bool(copy_model_payload))
            self.copy_date_btn.setVisible(bool(copy_date_payload))

            if not info and not copy_model_payload and not copy_date_payload:
                 self.hide()
            else:
                self.show_at_bottom_right()

        except Exception as e:
            log_exc("set_content error: " + str(e))


class GarantiTrayApp(QtCore.QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        
        # Icon ayarla
        icon_path = None
        try:
            # PyInstaller exe içindeki dosyalar için
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path.cwd()

            ico_path = base_path / "logo.ico"
            png_path = base_path / "logo.png"

            if ico_path.exists():
                icon_path = ico_path
            elif png_path.exists():
                icon_path = png_path

            if icon_path:
                self.tray_icon = QSystemTrayIcon(QIcon(str(icon_path)))
            else:
                self.tray_icon = QSystemTrayIcon(QIcon())
        except Exception as e:
            log_exc(f"Icon yükleme hatası: {e}")
            self.tray_icon = QSystemTrayIcon(QIcon())
            
        self.tray_icon.setToolTip("Garanti Takip Sistemi")
        
        # Menü oluştur - Windows koyu tema uyumlu
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
        
        # Çıkış butonu
        exit_action = QAction("Çıkış", self)
        exit_action.triggered.connect(self.quit)
        self.menu.addAction(exit_action)
        
        # Menüyü tray icon'a bağla
        self.tray_icon.setContextMenu(self.menu)

        # Tray icon görünürlüğünü sağlamak için
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.setVisible(True)
            self.tray_icon.show()

            # Birkaç kez tekrar göster
            QTimer.singleShot(500, lambda: self.tray_icon.show())
            QTimer.singleShot(1500, lambda: self.tray_icon.show())
            QTimer.singleShot(3000, lambda: self.tray_icon.show())
        else:
            log_info("System tray mevcut değil")

        self.popup = Popup()

        self.clipboard = QApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_change)
        self._last_serial = None

    def quit(self):
        try:
            log_info("Uygulama kapatılıyor (Çıkış menüsü).")
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
            # 1. Recci kontrolü
            recci_url = RECCI_BASE + serial
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            recci_resp = requests.get(recci_url, headers=headers, timeout=12)
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



                self.popup.set_content("", display_text, copy_model_payload=copy_model_payload, copy_date_payload=None, status_color="green", serial=serial)
                log_info(f"Recci garantili: {serial} | {display_text}")
                return # Recci'de bulunduysa KVK'ya bakmaya gerek yok

            # Özel seri kontrolü (sadece Recci'de bulunamazsa)
            if serial.startswith("RCCVBY") or serial.startswith("RCFVBY"):
                self.popup.set_content("", "MODEL BULUNAMADI. LÜTFEN CİHAZ ÜZERİNDEN ÖĞRENİNİZ.", status_color="green", serial=serial)
                log_info(f"Özel seri garantili: {serial}")
                return

            # 2. Recci'de bulunamazsa KVK API kontrolü (curl ile)
            try:
                kvk_api_url = KVK_API + serial
                import subprocess
                import json

                # Windows'ta komut penceresinin açılmasını engellemek için
                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                command = [
                    "curl",
                    "-s",  # Sessiz mod
                    "-L",  # Yönlendirmeleri takip et
                    "--tlsv1.2", # TLS 1.2'yi zorla
                    "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    kvk_api_url
                ]
                
                result = subprocess.run(
                    command, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8', # Türkçe karakterler için
                    timeout=15, 
                    check=True,
                    startupinfo=startupinfo
                )
                kvk_data = json.loads(result.stdout)

                if kvk_data.get("IsSucceeded") == 1 and kvk_data.get("ResultData"):
                    device_data = kvk_data["ResultData"][0]
                    description = device_data.get("DESCRIPTION", "")
                    warranty_end = device_data.get("WARRANTYEND", "")

                    if description and "no data found" not in description.lower():
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
                        self.popup.set_content("", display_text, copy_model_payload=formatted_copy_model_payload, copy_date_payload=warranty_end, status_color="blue", serial=serial)
                        log_info(f"KVK garantili (curl): {serial} | {formatted_copy_model_payload} | Bitiş: {warranty_end}")
                        return

            except FileNotFoundError:
                log_exc("curl komutu bulunamadı.")
                self.popup.set_content("HATA", "curl komutu sistemde bulunamadı.", status_color="red", serial=serial)
                return
            except subprocess.TimeoutExpired:
                log_exc(f"KVK curl zaman aşımı {serial}")
                self.popup.set_content("", "KVK sorgusu (curl) zaman aşımına uğradı.", status_color="red", serial=serial)
                return
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                log_exc(f"KVK curl/JSON hatası {serial}: {e}")
                # Hata durumunda genel mesaja düşmesi için devam et
            except Exception as kvk_e:
                log_exc(f"KVK genel hata (curl) {serial}: {kvk_e}")
                # Hata durumunda genel mesaja düşmesi için devam et

            # 3. Ne Recci ne de KVK'da bulunamazsa
            self.popup.set_content("", "Hiçbir sistemde garanti bilgisi bulunamadı.", copy_model_payload=None, copy_date_payload=None, status_color="red", serial=serial)
            log_info(f"Garanti dışı: {serial}")

        except requests.exceptions.Timeout:
            log_exc(f"Sorgu zaman aşımına uğradı: {serial}")
            self.popup.set_content("HATA", "Sorgu zaman aşımına uğradı.", status_color="red", serial=serial)
        except requests.exceptions.RequestException as req_e:
            log_exc(f"HTTP isteği hatası {serial}: {req_e}")
            self.popup.set_content("HATA", f"Sorgu hatası: {str(req_e)}", status_color="red", serial=serial)
        except Exception as e:
            log_exc(f"Genel hata {serial}: {e}")
            self.popup.set_content("HATA", f"Beklenmeyen bir hata oluştu: {str(e)}", status_color="red", serial=serial)

def main():
    try:
        app = QApplication(sys.argv)
        tray_app = GarantiTrayApp(app)
        log_info("Garanti tepsi uygulaması başlatıldı.")

        # Başlangıç popup'ı göster
        start_popup = Popup()
        start_popup.set_content("GARANTİ TAKİP SİSTEMİ BAŞLATILDI.", "Geliştirici: KURSAT SINAN", status_color="green")
        QTimer.singleShot(1000, lambda: start_popup.show_at_bottom_right())

        sys.exit(app.exec())
    except Exception as e:
        log_exc("Uygulama fatal hata: " + str(e))
        raise

if __name__ == "__main__":
    main()
