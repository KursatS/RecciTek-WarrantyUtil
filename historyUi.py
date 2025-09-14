#!/usr/bin/env python3

import logging
import json
import csv
import os
from datetime import datetime
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QListWidget, QListWidgetItem, QScrollArea, QTextEdit
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


class HistoryPopup(QWidget):
    """Geçmiş sorgular için basit ve stabil pencere"""
    def __init__(self, parent=None):
        super().__init__(parent)

        # Basit pencere ayarları - crash riski olmadan
        self.setWindowTitle("Geçmiş Sorgular")
        self.setFixedSize(700, 500)
        self.setWindowFlags(Qt.WindowType.Window)

        # Roborock logosunu ayarla
        try:
            if os.path.exists("logo.png"):
                self.setWindowIcon(QtGui.QIcon("logo.png"))
            elif os.path.exists("logo.ico"):
                self.setWindowIcon(QtGui.QIcon("logo.ico"))
        except:
            pass  # Logo yüklenemezse devam et

        # Ana layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Başlık
        title = QLabel("GEÇMİŞ SORGULAR")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        main_layout.addWidget(title)

        # İstatistikler
        self.stats_label = QLabel("")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_label.setStyleSheet("font-size: 12px; color: #666; padding: 5px;")
        main_layout.addWidget(self.stats_label)

        # Liste için scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Liste widget'ı
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(5, 5, 5, 5)
        self.list_layout.setSpacing(2)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_area.setWidget(self.list_widget)
        main_layout.addWidget(scroll_area)

        # Filtreleme butonları
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        # Hepsini göster butonu
        self.show_all_btn = QPushButton("🔍 Hepsini Göster")
        self.show_all_btn.clicked.connect(lambda: self.filter_devices("all"))
        self.show_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #094771;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0a5a8a;
            }
        """)
        filter_layout.addWidget(self.show_all_btn)

        # Not alınanları göster butonu
        self.show_notes_btn = QPushButton("📝 Not Alınanları Göster")
        self.show_notes_btn.clicked.connect(lambda: self.filter_devices("notes"))
        self.show_notes_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        filter_layout.addWidget(self.show_notes_btn)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Butonlar
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        # CSV dışa aktar butonu
        self.export_btn = QPushButton("📊 CSV Dışa Aktar")
        self.export_btn.clicked.connect(self.export_to_csv)
        buttons_layout.addWidget(self.export_btn)

        # Kapat butonu
        close_btn = QPushButton("Kapat")
        close_btn.clicked.connect(self.close_popup)
        buttons_layout.addWidget(close_btn)

        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)

        # Geçmiş verileri
        self.history_data = []
        self.all_items = []  # Tüm öğeler için
        self.notes_file = "device_notes.json"
        self.device_notes = self.load_notes()

    def load_history(self):
        """Geçmiş verilerini yükle ve göster"""
        try:
            cache_file = "warranty_cache.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # Verileri tarihe göre sırala (en yeni üstte)
                sorted_data = sorted(cache_data.items(),
                                   key=lambda x: x[1]['timestamp'],
                                   reverse=True)

                self.history_data = []
                total_queries = 0
                recci_warranty = 0
                kvk_warranty = 0
                no_warranty = 0

                # Mevcut list widget'larını temizle
                for i in reversed(range(self.list_layout.count())):
                    widget = self.list_layout.itemAt(i).widget()
                    if widget:
                        widget.setParent(None)

                for serial, data in sorted_data:
                    total_queries += 1
                    result = data['result']
                    timestamp = datetime.fromisoformat(data['timestamp'])

                    # İstatistik hesapla
                    if result.get('status_color') == 'green':
                        recci_warranty += 1
                    elif result.get('status_color') == 'blue':
                        kvk_warranty += 1
                    else:
                        no_warranty += 1

                    # Model bilgisini hazırla
                    model_info = result.get('copy_model_payload', '')
                    if not model_info or model_info.strip() == '':
                        model_info = 'MODEL İSMİ BULUNAMADI'
                    else:
                        # "Sonic" kelimesini çıkar (örn: "S8 Sonic" → "S8")
                        import re
                        model_info = re.sub(r'\s+Sonic\s*', ' ', model_info, flags=re.IGNORECASE)
                        model_info = model_info.strip()

                    # History item oluştur
                    item_widget = self.create_history_item(serial, result, timestamp, model_info)
                    self.list_layout.addWidget(item_widget)

                    # Öğeyi all_items listesine ekle
                    self.all_items.append({
                        'widget': item_widget,
                        'serial': serial
                    })

                    # Durum metnini hazırla
                    status_color = result.get('status_color', '')
                    if status_color == 'green':
                        status_text = 'RECCI GARANTİLİ'
                    elif status_color == 'blue':
                        status_text = 'KVK GARANTİLİ'
                    else:
                        status_text = 'GARANTİ DIŞI'

                    # CSV için veri hazırla
                    self.history_data.append({
                        'serial': serial,
                        'model': model_info,
                        'color': status_text,
                        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    })

                # İstatistikleri güncelle
                self.stats_label.setText(
                    f"Toplam: {total_queries} | Recci Garantili: {recci_warranty} | "
                    f"KVK Garantili: {kvk_warranty} | Garanti Dışı: {no_warranty}"
                )

                # Boşluk ekle
                self.list_layout.addStretch()

            else:
                self.stats_label.setText("Henüz sorgu geçmişi bulunmuyor.")
                self.export_btn.setVisible(False)

        except Exception as e:
            log_exc(f"History load error: {e}")
            self.stats_label.setText("Geçmiş yüklenirken hata oluştu.")

    def create_history_item(self, serial, result, timestamp, model_info):
        """Tek bir geçmiş öğesi oluştur"""
        item_frame = QFrame()
        item_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px;
                margin: 2px 0px;
            }
        """)

        layout = QVBoxLayout(item_frame)
        layout.setContentsMargins(10, 5, 10, 5)

        # Üst satır: Seri numarası ve durum
        top_layout = QHBoxLayout()

        # Seri numarası
        serial_label = QLabel(f"Seri: {serial}")
        serial_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
        top_layout.addWidget(serial_label)

        # Durum göstergesi
        status_color = result.get('status_color', 'red')
        if status_color == 'green':
            status_text = "RECCI"
            bg_color = "rgba(34, 197, 94, 0.8)"
        elif status_color == 'blue':
            status_text = "KVK"
            bg_color = "rgba(59, 130, 246, 0.8)"
        else:
            status_text = "DIŞI"
            bg_color = "rgba(239, 68, 68, 0.8)"

        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'JetBrains Mono', monospace;
            }}
        """)
        top_layout.addWidget(status_label)

        # Zaman (Tarih ve Saat)
        time_label = QLabel(timestamp.strftime('%d.%m.%Y %H:%M:%S'))
        time_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.7);
                font-size: 10px;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
        top_layout.addWidget(time_label)

        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Alt satır: Model bilgisi
        model_label = QLabel(f"Model: {model_info}")
        model_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 11px;
                font-family: 'JetBrains Mono', monospace;
            }
        """)
        layout.addWidget(model_label)

        # Not alma bölümü
        notes_layout = QHBoxLayout()

        # Not etiketi
        notes_label = QLabel("📝 Not:")
        notes_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.8);
                font-size: 10px;
                font-weight: bold;
            }
        """)
        notes_layout.addWidget(notes_label)

        # Not text box'ı
        notes_text = QtWidgets.QLineEdit()
        notes_text.setPlaceholderText("Bu cihaz için not ekleyin...")
        notes_text.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                color: #333;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
                font-family: 'JetBrains Mono', monospace;
            }
            QLineEdit:focus {
                border: 1px solid #094771;
                background-color: white;
            }
        """)

        # Mevcut notu yükle
        if serial in self.device_notes:
            notes_text.setText(self.device_notes[serial])

        # Text değiştiğinde notu kaydet
        notes_text.textChanged.connect(lambda text, s=serial: self.save_note(s, text))

        notes_layout.addWidget(notes_text)
        layout.addLayout(notes_layout)

        return item_frame

    def export_to_csv(self):
        """Geçmiş verilerini CSV olarak dışa aktar - Kullanıcı konum seçsin"""
        try:
            if not self.history_data:
                show_simple_message("UYARI", "Dışa aktarılacak veri bulunmuyor.", "blue")
                return

            # Kullanıcıdan dosya konumunu seçmesini iste
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"warranty_history_{timestamp}.csv"

            # QFileDialog ile dosya kaydetme dialog'u
            filename, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "CSV Dosyasını Kaydet",
                default_filename,
                "CSV Dosyaları (*.csv);;Tüm Dosyalar (*)"
            )

            # Kullanıcı vazgeçtiyse çık
            if not filename:
                return

            # CSV dosyasını yaz
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['serial', 'model', 'color', 'timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Başlıkları yaz
                writer.writerow({
                    'serial': 'Seri Numarası',
                    'model': 'Model',
                    'color': 'Durum',
                    'timestamp': 'Zaman'
                })

                # Verileri yaz
                for row in self.history_data:
                    writer.writerow(row)

            log_info(f"CSV dışa aktarıldı: {filename}")

            # Başarılı mesajı göster
            show_simple_message("BAŞARILI", f"Veriler '{os.path.basename(filename)}' dosyasına kaydedildi.", "green")

        except Exception as e:
            log_exc(f"CSV export error: {e}")

            # Hata mesajı göster
            show_simple_message("HATA", "CSV dışa aktarma sırasında hata oluştu.", "red")

    def show_at_center(self):
        """Popup'u ekranın merkezinde göster - Güvenli yöntem"""
        try:
            log_info("=== SHOW_AT_CENTER METODU BAŞLATILDI ===")

            # Basit ve güvenli pozisyon hesaplama
            log_info("Pozisyon hesaplanıyor...")
            screen_geometry = QtCore.QRect(0, 0, 1920, 1080)  # Varsayılan ekran boyutu
            w = self.width()
            h = self.height()

            # Ekranın ortasına yerleştir
            x = (screen_geometry.width() - w) // 2
            y = (screen_geometry.height() - h) // 2

            log_info(f"Popup boyutları - Width: {w}, Height: {h}")
            log_info(f"Hesaplanan pozisyon - X: {x}, Y: {y}")

            # Pozisyonu ayarla
            self.move(x, y)
            log_info("Pozisyon ayarlandı")

            # Pencereyi göster
            self.show()
            log_info("Pencere gösterildi")

            # Timer'ı başlat (daha sonra)
            try:
                self.autoclose_timer.start()
                log_info("Timer başlatıldı")
            except:
                log_info("Timer başlatılamadı (normal)")

            log_info("=== SHOW_AT_CENTER METODU BAŞARIYLA TAMAMLANDI ===")
            return True

        except Exception as e:
            log_exc(f"=== SHOW_AT_CENTER METODU HATASI ===")
            log_exc(f"Hata detayı: {str(e)}")
            log_exc(f"Hata türü: {type(e).__name__}")

            # Hata durumunda pencereyi gizle
            try:
                self.hide()
            except:
                pass

            return False

    def load_notes(self):
        """Cihaz notlarını yükle"""
        try:
            if os.path.exists(self.notes_file):
                with open(self.notes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}

    def save_note(self, serial, note_text):
        """Tek bir cihaz notunu kaydet"""
        try:
            # Notu güncelle
            if note_text.strip():
                self.device_notes[serial] = note_text.strip()
            else:
                # Boş not ise sil
                if serial in self.device_notes:
                    del self.device_notes[serial]

            # Tüm notları kaydet
            self.save_notes()

        except Exception as e:
            log_exc(f"Save note error: {e}")

    def save_notes(self):
        """Cihaz notlarını kaydet"""
        try:
            with open(self.notes_file, 'w', encoding='utf-8') as f:
                json.dump(self.device_notes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_exc(f"Notes save error: {e}")

    def filter_devices(self, filter_type):
        """Cihazları filtrele"""
        try:
            # Mevcut öğeleri gizle/göster
            for item_info in self.all_items:
                widget = item_info['widget']
                serial = item_info['serial']

                if filter_type == "all":
                    widget.show()
                elif filter_type == "notes":
                    # Notu olanları göster
                    if serial in self.device_notes and self.device_notes[serial].strip():
                        widget.show()
                    else:
                        widget.hide()

        except Exception as e:
            log_exc(f"Filter error: {e}")

    def close_popup(self):
        """Popup'u kapat"""
        try:
            self.hide()
            self.autoclose_timer.stop()
        except Exception as e:
            log_exc(f"History popup close error: {e}")


# Basit mesaj gösterme fonksiyonu
def show_simple_message(title: str, message: str, status_color: str = "blue"):
    """Basit mesaj popup'ı göster"""
    try:
        # Basit bir message box göster
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        if status_color == "green":
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        elif status_color == "red":
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Critical)
        else:
            msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)

        msg_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        msg_box.exec()

    except Exception as e:
        log_exc(f"Simple message error: {e}")
