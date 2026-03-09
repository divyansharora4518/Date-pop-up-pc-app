import sys
import datetime
import json
import os
import ctypes
import win32gui
import win32con

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QMenu, QColorDialog, QFontDialog, QInputDialog, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint, QTimer, QRectF
from PyQt5.QtGui import QIcon, QRegion, QPolygon, QColor, QPainter, QPen, QBrush

# Taskbar Icon Fix
myappid = 'ultimate.taskbar.v7.perfect' 
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class UltimateTaskbarApp(QWidget):
    def __init__(self, message):
        super().__init__()
        self.today_message = message
        self.status_message = ""
        self.settings_file = 'settings.json'
        
        # इंटरनल स्टेट्स
        self._mouse_press_pos = None
        self._start_geometry = None
        self._is_dragging = False

        # डिफ़ॉल्ट बॉर्डर सेटिंग्स (अगर JSON न मिले)
        self.border_enabled = True # डिफ़ॉल्ट चालू
        self.border_width_value = 2 # पतली लाइन के लिए 2px

        self.load_settings()

        # Window Flags
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        if os.path.exists("icon.ico"):
            self.setWindowIcon(QIcon("icon.ico"))

        self.setGeometry(self.pos_x, self.pos_y, self.w, self.h)

        # मुख्य लेआउट (Label के चारों तरफ पैडिंग देता है ताकि मास्क कटे नहीं)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10) 

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        
        self.glow_effect = QGraphicsDropShadowEffect(self)
        self.label.setGraphicsEffect(self.glow_effect)
        
        self.layout.addWidget(self.label)
        
        # Label का अपना कोई बैकग्राउंड नहीं होगा, हम QWidget को पेंट करेंगे
        self.label.setStyleSheet("background: transparent;")

        self.refresh_ui()

        # टाइमर
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.keep_at_bottom)
        self.timer.start(1000)

    def keep_at_bottom(self):
        if not self._is_dragging:
            hwnd = int(self.winId())
            win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                                 win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                try:
                    s = json.load(f)
                    self.current_bg = s.get('bg', 'rgba(15, 15, 15, 245)')
                    self.current_text_color = s.get('text', '#00FFFF')
                    self.border_color = s.get('border_color', '#00FFFF')
                    self.border_enabled = s.get('border_enabled', True) 
                    self.font_size = s.get('font_size', 16)
                    self.w, self.h = s.get('width', 380), s.get('height', 220)
                    self.pos_x, self.pos_y = s.get('pos_x', 100), s.get('pos_y', 100)
                    self.shape_type = s.get('shape', 'Rectangle')
                    self.resize_mode = s.get('resize_mode', False)
                except:
                    self.set_defaults()
        else:
            self.set_defaults()

    def set_defaults(self):
        self.current_bg, self.current_text_color, self.border_color = "rgba(10, 10, 10, 240)", "#00FFFF", "#00FFFF"
        self.font_size = 16
        self.border_enabled = True
        self.w, self.h, self.pos_x, self.pos_y = 380, 220, 100, 100
        self.shape_type, self.resize_mode = "Rectangle", False

    def save_settings(self):
        settings = {
            'bg': self.current_bg, 'text': self.current_text_color,
            'border_color': self.border_color, 'border_enabled': self.border_enabled, 
            'font_size': self.font_size, 'width': self.width(), 'height': self.height(),
            'pos_x': self.x(), 'pos_y': self.y(), 'shape': self.shape_type, 'resize_mode': self.resize_mode
        }
        with open(self.settings_file, 'w') as f: json.dump(settings, f, indent=4)

    def refresh_ui(self):
        # टेक्स्ट फ़ॉर्मेटिंग
        formatted_today_msg = self.today_message.replace("\n", "<br>")
        display_text = f"<div style='line-height: 140%;'>{formatted_today_msg}</div>"
        
        if self.status_message:
            display_text += f"<div style='font-size: {max(8, self.font_size-6)}pt; margin-top: 10px; color: {self.border_color}; opacity: 0.9;'>{self.status_message}</div>"
        
        self.label.setText(display_text)

        # ग्लो इफ़ेक्ट को केवल बॉर्डर इनेबल होने पर ही दिखाएं
        self.glow_effect.setBlurRadius(20 if self.border_enabled else 0)
        self.glow_effect.setColor(QColor(self.border_color))
        self.glow_effect.setOffset(0, 0)

        # टेक्स्ट स्टाइलिंग
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {self.current_text_color};
                font-size: {self.font_size}pt;
                font-weight: bold;
                padding: 10px;
                background: transparent;
            }}
        """)
        
        self.apply_shape()
        self.update() 

    # --- CUSTOM PAINT ENGINE ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = QRectF(self.rect())
        if self.shape_type == "Circle":
            size = min(self.width(), self.height())
            circle_rect = QRectF((self.width()-size)/2, (self.height()-size)/2, size, size)
            painter.setBrush(QBrush(QColor(self.current_bg)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(circle_rect)
            
            if self.border_enabled:
                painter.setBrush(Qt.NoBrush)
                border_pen = QPen(QColor(self.border_color), self.border_width_value)
                painter.setPen(border_pen)
                shrink = self.border_width_value / 2.0
                painter.drawEllipse(circle_rect.adjusted(shrink, shrink, -shrink, -shrink))
                
        elif self.shape_type == "Rounded Rectangle":
            painter.setBrush(QBrush(QColor(self.current_bg)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 35, 35)
            
            if self.border_enabled:
                painter.setBrush(Qt.NoBrush)
                border_pen = QPen(QColor(self.border_color), self.border_width_value)
                painter.setPen(border_pen)
                shrink = self.border_width_value / 2.0
                painter.drawRoundedRect(rect.adjusted(shrink, shrink, -shrink, -shrink), 35, 35)

        elif self.shape_type == "Rectangle":
            painter.setBrush(QBrush(QColor(self.current_bg)))
            painter.setPen(Qt.NoPen)
            painter.drawRect(rect)
            
            if self.border_enabled:
                painter.setBrush(Qt.NoBrush)
                border_pen = QPen(QColor(self.border_color), self.border_width_value)
                painter.setPen(border_pen)
                shrink = self.border_width_value / 2.0
                painter.drawRect(rect.adjusted(shrink, shrink, -shrink, -shrink))

        elif self.shape_type == "Diamond":
            w, h = self.width(), self.height()
            diamond_rect = QPolygon([QPoint(w//2, 0), QPoint(w, h//2), QPoint(w//2, h), QPoint(0, h//2)])
            painter.setBrush(QBrush(QColor(self.current_bg)))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(diamond_rect)
            
            if self.border_enabled:
                painter.setBrush(Qt.NoBrush)
                border_pen = QPen(QColor(self.border_color), self.border_width_value)
                painter.setPen(border_pen)
                shrink = self.border_width_value
                diamond_rect_inner = QPolygon([QPoint(w//2, shrink), QPoint(w-shrink, h//2), QPoint(w//2, h-shrink), QPoint(shrink, h//2)])
                painter.drawPolygon(diamond_rect_inner)
        
        elif self.shape_type == "Hexagon":
            w, h = self.width(), self.height()
            hex_pts = QPolygon([QPoint(w//4, 0), QPoint(3*w//4, 0), QPoint(w, h//2), 
                                QPoint(3*w//4, h), QPoint(w//4, h), QPoint(0, h//2)])
            painter.setBrush(QBrush(QColor(self.current_bg)))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(hex_pts)
            
            if self.border_enabled:
                painter.setBrush(Qt.NoBrush)
                border_pen = QPen(QColor(self.border_color), self.border_width_value)
                painter.setPen(border_pen)
                painter.drawPolygon(hex_pts)

    # --- Shape Masking ---
    def apply_shape(self):
        w, h = self.width(), self.height()
        if self.shape_type in ["Rectangle", "Rounded Rectangle"]:
            self.setMask(QRegion(self.rect()))
        elif self.shape_type == "Circle":
            size = min(w, h)
            self.setMask(QRegion((w-size)//2, (h-size)//2, size, size, QRegion.Ellipse))
        elif self.shape_type == "Diamond":
            pts = [QPoint(w//2, 0), QPoint(w, h//2), QPoint(w//2, h), QPoint(0, h//2)]
            self.setMask(QRegion(QPolygon(pts)))
        elif self.shape_type == "Hexagon":
            pts = [QPoint(w//4, 0), QPoint(3*w//4, 0), QPoint(w, h//2), 
                   QPoint(3*w//4, h), QPoint(w//4, h), QPoint(0, h//2)]
            self.setMask(QRegion(QPolygon(pts)))

    # --- DRAG & RESIZE ENGINE ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.resize_mode:
                # Resize mode ON: manual resize track करो
                self._is_dragging = True
                self._mouse_press_pos = event.globalPos()
                self._start_geometry = self.geometry()
            else:
                # Resize mode OFF: Windows Native Drag — सबसे reliable तरीका
                # HWND_BOTTOM से temporarily हटाएं ताकि drag काम करे
                hwnd = int(self.winId())
                win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                # Windows को बताओ कि Title Bar पकड़ी गई है — native move शुरू होगा
                ctypes.windll.user32.ReleaseCapture()
                ctypes.windll.user32.SendMessageW(hwnd, 0x0112, 0xF012, 0)  # WM_SYSCOMMAND, SC_MOVE+HTCAPTION
                # Drag खत्म होने पर वापस bottom पर भेजो
                win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                                      win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
                self.save_settings()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._is_dragging and self.resize_mode:
            delta = event.globalPos() - self._mouse_press_pos
            new_w = max(180, self._start_geometry.width() + delta.x())
            new_h = max(120, self._start_geometry.height() + delta.y())
            if self.shape_type == "Circle":
                new_w = new_h = max(new_w, new_h)
            self.resize(new_w, new_h)
            self.refresh_ui()
            event.accept()

    def mouseReleaseEvent(self, event):
        if self._is_dragging:
            self._is_dragging = False
            self._mouse_press_pos = None
            self._start_geometry = None
            self.save_settings()
        event.accept()

    # --- Context Menu ---
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("background-color: #151515; color: white; border: 1px solid #00FFFF; padding: 5px;")

        act_bg = menu.addAction("🎨 Background Color")
        act_text = menu.addAction("✍️ Text Color")
        act_b_color = menu.addAction("🌈 Border Color")
        act_font = menu.addAction("📏 Font Size")
        act_toggle_border = menu.addAction(f"🖼️ Border: {'OFF' if self.border_enabled else 'ON'}")

        shape_menu = menu.addMenu("📐 Change Shape")
        shapes = ["Rectangle", "Rounded Rectangle", "Circle", "Diamond", "Hexagon"]
        for s in shapes:
            a = shape_menu.addAction(s)
            if a: a.triggered.connect(lambda checked, shape=s: self.change_shape_logic(shape))

        act_resize = menu.addAction(f"🔄 Resize Mode: {'ON' if self.resize_mode else 'OFF'}")
        
        menu.addSeparator()
        act_add_date = menu.addAction("➕ Add Event")
        act_del_date = menu.addAction("🗑️ Delete Today's Event")
        menu.addSeparator()
        act_quit = menu.addAction("❌ Close App")

        action = menu.exec_(self.mapToGlobal(event.pos()))

        if action == act_bg:
            c = QColorDialog.getColor()
            if c.isValid(): self.current_bg = c.name()
        elif action == act_text:
            c = QColorDialog.getColor()
            if c.isValid(): self.current_text_color = c.name()
        elif action == act_b_color:
            c = QColorDialog.getColor()
            if c.isValid(): self.border_color = c.name()
        elif action == act_font:
            val, ok = QInputDialog.getInt(self, "Font", "Size:", self.font_size, 8, 100)
            if ok: self.font_size = val
        elif action == act_toggle_border:
            self.toggle_border_logic()
        elif action == act_resize:
            self.resize_mode = not self.resize_mode
        elif action == act_add_date:
            self.add_new_event()
        elif action == act_del_date:
            self.delete_event()
        elif action == act_quit:
            self.close()

        self.refresh_ui()
        self.save_settings()

    def toggle_border_logic(self):
        self.border_enabled = not self.border_enabled
        self.refresh_ui()
        self.update()

    def change_shape_logic(self, shape):
        self.shape_type = shape
        if shape == "Circle":
            side = max(self.width(), self.height())
            self.resize(side, side)
        elif shape == "Rectangle" or shape == "Rounded Rectangle":
            if self.width() == self.height():
                self.resize(max(self.width(), 380), max(self.width()//2, 220))
        elif shape == "Diamond":
             if self.width() < self.height() + 100:
                self.resize(self.width() + 100, self.height() + 20)
        self.refresh_ui()

    def add_new_event(self):
        date_text, ok1 = QInputDialog.getText(self, "New Event", "Date (DD-MM):")
        if not (ok1 and date_text): return
        msg, ok2 = QInputDialog.getMultiLineText(self, "Event", "Message:")
        if not (ok2 and msg): return

        date_text = date_text.strip()  # extra spaces remove karo

        file_path = 'dates.json'
        events = {}
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                events = json.load(f)
        
        if date_text in events:
            if isinstance(events[date_text], list): events[date_text].append(msg)
            else: events[date_text] = [events[date_text], msg]
        else:
            events[date_text] = [msg]

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=4, ensure_ascii=False)

        today = datetime.date.today().strftime("%d-%m")
        if date_text == today:
            # aaj ka event — seedha widget mein dikhao bina restart ke
            all_events = events[today] if isinstance(events[today], list) else [events[today]]
            self.today_message = "\n".join(all_events)
            self.status_message = ""
            self.refresh_ui()  # turant popup mein show karo
        else:
            # doosre din ka event — sirf status dikhao
            self.status_message = "✅ Event Added!"
            self.refresh_ui()
            QTimer.singleShot(4000, self.clear_status)

    def delete_event(self):
        file_path = 'dates.json'
        if not os.path.exists(file_path): return
        with open(file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
        today = datetime.date.today().strftime("%d-%m")
        if today not in events:
            self.status_message = "❌ No events found."
            self.refresh_ui()
            return

        current_events = events[today] if isinstance(events[today], list) else [events[today]]
        item, ok = QInputDialog.getItem(self, "Delete", "Select event:", current_events, 0, False)
        
        if ok and item:
            current_events.remove(item)
            if not current_events:
                del events[today]
                self.today_message = "No events today."
            else:
                events[today] = current_events
                self.today_message = "\n".join(current_events)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(events, f, indent=4, ensure_ascii=False)
            self.status_message = "🗑️ Deleted!"
            self.refresh_ui()
            QTimer.singleShot(3000, self.clear_status)

    def clear_status(self):
        self.status_message = ""
        self.refresh_ui()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    file_path = 'dates.json'
    today = datetime.date.today().strftime("%d-%m")
    init_msg = "No events today."

    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                events = json.load(f)
                if today in events:
                    init_msg = "\n".join(events[today]) if isinstance(events[today], list) else events[today]
            except: pass

    ex = UltimateTaskbarApp(init_msg)
    ex.show()
    sys.exit(app.exec_())