#!/usr/bin/env python3

import logging
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect
)

logging.basicConfig(
    level=logging.INFO,
    filename=str(Path.home() / "garanti.log"),
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("garanti")

def log_info(msg: str):
    logger.info(msg)

def log_exc(msg: str):
    logger.exception(msg)


class ModernPopup(QWidget):
    """Modern frameless popup sınıfı"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 300)

        # Ana container - şeffaf arka plan
        self.container = QFrame(self)
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0);
                border-radius: 25px;
            }
        """)
        self.container.setGeometry(0, 0, 450, 300)

        # Gölge efekti
        shadow = QGraphicsDropShadowEffect(self.container)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)

        # Ana bubble - dinamik gradyan
        self.bubble = QFrame(self.container)
        self.bubble.setGeometry(15, 15, 420, 270)

        # İç layout
        layout = QVBoxLayout(self.bubble)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Başlık
        self.title_label = QLabel("")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
        layout.addWidget(self.title_label)

        # Mesaj
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                font-size: 14px;
                padding: 15px;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
        layout.addWidget(self.message_label)

        # Kopyalama butonları için yatay layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(12)

        # Model kopyalama butonu
        self.copy_model_btn = QPushButton("📋 Model")
        self.copy_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_model_btn.setFixedHeight(32)
        self.copy_model_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 12px;
                font-family: 'JetBrains Mono', monospace;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
                border-color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.copy_model_btn.clicked.connect(self.copy_model)
        self.copy_model_btn.setVisible(False)
        buttons_layout.addWidget(self.copy_model_btn)

        # Tarih kopyalama butonu
        self.copy_date_btn = QPushButton("📅 Tarih")
        self.copy_date_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_date_btn.setFixedHeight(32)
        self.copy_date_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.15);
                color: white;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 600;
                font-size: 12px;
                font-family: 'JetBrains Mono', monospace;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
                border-color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.copy_date_btn.clicked.connect(self.copy_date)
        self.copy_date_btn.setVisible(False)
        buttons_layout.addWidget(self.copy_date_btn)

        # Butonları layout'a ekle
        layout.addLayout(buttons_layout)

        # Kapat butonu - sağ üstte
        self.close_btn = QtWidgets.QPushButton("×")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                text-align: center;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        self.close_btn.clicked.connect(self.close_popup)

        # Butonu container'ın içine konumlandır
        self.close_btn.setParent(self.container)
        self.close_btn.move(395, 20)  # Container içindeki konum

        # Otomatik kapanma
        self.autoclose_timer = QTimer(self)
        self.autoclose_timer.setInterval(5000)  # 5 saniye
        self.autoclose_timer.timeout.connect(self.close_popup)

        # Kopyalama payload'ları
        self.copy_model_payload = None
        self.copy_date_payload = None

    def set_content(self, title: str, info: str, copy_model_payload: str = None, copy_date_payload: str = None, status_color: str = "red", serial: str = None):
        """Modern popup için içerik ayarla"""
        try:
            # Özel başlangıç popup kontrolü
            is_startup_popup = title == "GARANTİ TAKİP SİSTEMİ BAŞLATILDI."
            is_warranty_error = info == "Hiçbir sistemde garanti bilgisi bulunamadı."

            # Garanti durumuna göre renk ayarla
            if is_startup_popup:
                # Başlangıç popup için açık mordan koyu mora gradyan
                bubble_color = "qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(147, 51, 234, 255), stop:1 rgba(88, 28, 135, 255))"
                title_text = title
                title_font_size = "16px"  # Küçültülmüş font
            elif is_warranty_error:
                # Garanti dışı cihaz için özel mesaj
                bubble_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(239, 68, 68, 255), stop:1 rgba(185, 28, 28, 255))"
                title_text = "GARANTİ DIŞI"
                title_font_size = "20px"
                # Özel mesaj ayarla
                info = "Cihazın iki sistemde de garantisi bulunamadı."
            elif status_color == "green":
                bubble_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(34, 197, 94, 255), stop:1 rgba(22, 163, 74, 255))"
                title_text = "RECCI GARANTİLİ" if title == "" else title
                title_font_size = "20px"
            elif status_color == "blue":
                bubble_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(59, 130, 246, 255), stop:1 rgba(30, 64, 175, 255))"
                title_text = "KVK GARANTİLİ" if title == "" else title
                title_font_size = "20px"
            else:
                bubble_color = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(239, 68, 68, 255), stop:1 rgba(185, 28, 28, 255))"
                title_text = "GARANTİ DIŞI" if title == "" else title
                title_font_size = "20px"

            self.bubble.setStyleSheet(f"""
                QFrame {{
                    background: {bubble_color};
                    border-radius: 20px;
                    border: 3px solid white;
                }}
            """)

            # Başlık için özel font boyutu ayarla
            self.title_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    font-size: {title_font_size};
                    font-weight: bold;
                    font-family: 'JetBrains Mono', monospace;
                }}
            """)

            self.title_label.setText(title_text)
            self.message_label.setText(info)

            # Kopyalama payload'larını sakla ve butonları göster/gizle
            self.copy_model_payload = copy_model_payload
            self.copy_date_payload = copy_date_payload

            # Butonların görünürlüğünü ayarla
            self.copy_model_btn.setVisible(bool(copy_model_payload))
            self.copy_date_btn.setVisible(bool(copy_date_payload))

            self.show_at_bottom_right()

        except Exception as e:
            log_exc(f"Modern popup set_content error: {e}")

    def show_at_bottom_right(self):
        """Modern popup'u sağ altta göster"""
        try:
            screen = QApplication.primaryScreen()
            geo = screen.availableGeometry()
            w = self.width()
            h = self.height()
            x = geo.right() - w - 20
            y = geo.bottom() - h - 20
            self.move(x, y)
            self.show()
            self.autoclose_timer.start()
        except Exception as e:
            log_exc(f"Modern popup show error: {e}")

    def close_popup(self):
        """Modern popup'u kapat"""
        try:
            self.hide()
            self.autoclose_timer.stop()
        except Exception as e:
            log_exc(f"Modern popup close error: {e}")

    def copy_model(self):
        """Model bilgisini panoya kopyala"""
        try:
            if self.copy_model_payload and self.copy_model_payload != "":
                QApplication.clipboard().setText(str(self.copy_model_payload))
                log_info(f"Modern popup - Model kopyalandı: {self.copy_model_payload}")
        except Exception as e:
            log_exc(f"Modern popup copy model error: {e}")

    def copy_date(self):
        """Tarih bilgisini panoya kopyala"""
        try:
            if self.copy_date_payload and self.copy_date_payload != "":
                QApplication.clipboard().setText(str(self.copy_date_payload))
                log_info(f"Modern popup - Tarih kopyalandı: {self.copy_date_payload}")
        except Exception as e:
            log_exc(f"Modern popup copy date error: {e}")
