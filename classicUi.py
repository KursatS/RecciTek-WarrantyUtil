#!/usr/bin/env python3

import logging
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
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


class ClassicPopup(QWidget):
    """Klasik frameless popup sınıfı"""
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
        self.copy_model_btn.clicked.connect(self.copy_model)
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
        self.copy_date_btn.clicked.connect(self.copy_date)
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
        self.autoclose_timer.setInterval(5000)  # 5 saniye
        self.autoclose_timer.timeout.connect(self.close_popup)

    def set_content(self, title: str, info: str, copy_model_payload: str = None, copy_date_payload: str = None, status_color: str = "red", serial: str = None):
        """Klasik popup için içerik ayarla"""
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
            log_exc(f"Classic popup set_content error: {e}")

    def show_at_bottom_right(self):
        """Klasik popup'u sağ altta göster"""
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
            log_exc(f"Classic popup show error: {e}")

    def close_popup(self):
        """Klasik popup'u kapat"""
        try:
            self.hide()
            self.autoclose_timer.stop()
        except Exception as e:
            log_exc(f"Classic popup close error: {e}")

    def copy_model(self):
        """Model bilgisini panoya kopyala"""
        try:
            if self.copy_model_payload:
                QApplication.clipboard().setText(self.copy_model_payload)
                log_info(f"Classic popup - Model kopyalandı: {self.copy_model_payload}")
        except Exception as e:
            log_exc(f"Classic popup copy model error: {e}")

    def copy_date(self):
        """Tarih bilgisini panoya kopyala"""
        try:
            if self.copy_date_payload:
                QApplication.clipboard().setText(self.copy_date_payload)
                log_info(f"Classic popup - Tarih kopyalandı: {self.copy_date_payload}")
        except Exception as e:
            log_exc(f"Classic popup copy date error: {e}")
