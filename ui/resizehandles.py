#PySide6 imports-
from PySide6.QtCore import Qt
from PySide6.QtGui import  QColor, QPainter
from PySide6.QtWidgets import QWidget
class HorizontalResizeHandle(QWidget):
    def __init__(self, top_widget, bottom_widget,user_settings, parent=None):
        super().__init__(parent)
        self.top_widget = top_widget
        self.user_settings = user_settings 
        self.bottom_widget = bottom_widget
        self.setFixedHeight(4)
        self.setCursor(Qt.SizeVerCursor)
        self.setStyleSheet(f"background-color: {user_settings.loaded_theme['resize_handle']['default']};")

        self._press_pos = None
        self._original_height = None
    def enterEvent(self, event):
        self.setCursor(Qt.SizeVerCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPos()
            self._original_height = self.top_widget.height()

    def mouseMoveEvent(self, event):
        if self._press_pos:
            delta = event.globalPos().y() - self._press_pos.y()
            new_height = self._original_height + delta

            total_height = self.parent().height()
            min_h = total_height * 0.2
            max_h = total_height * 0.8
            new_height = max(min_h, min(max_h, new_height))

            self.top_widget.setFixedHeight(int(new_height))

    def mouseReleaseEvent(self, event):
        self._press_pos = None
        self._original_height = None
        self.unsetCursor()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color = QColor(self.user_settings.loaded_theme["resize_handle"]["default"])

        # 🔁 Peindre tout le fond
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRect(self.rect())

        # ➕ Grip central (optionnel)
        w, h = self.width(), self.height()
        grip_width = 60
        grip_height = 4
        x = (w - grip_width) // 2
        y = (h - grip_height) // 2
        grip_color = QColor(self.user_settings.loaded_theme["resize_handle"]["grip"])  # légèrement plus clair, transparent
        painter.setBrush(grip_color)
        painter.drawRoundedRect(x, y, grip_width, grip_height, 2, 2)

class VerticalResizeHandle(QWidget):
    def __init__(self, left_widget, right_widget, user_settings, parent=None):
        super().__init__(parent)
        self.left_widget = left_widget
        self.right_widget = right_widget
        self.user_settings = user_settings
        self.setFixedWidth(6)
        self.setCursor(Qt.SizeHorCursor)
        self.setStyleSheet(f"background: white;")

        self._press_pos = None
        self._original_width = None

    def enterEvent(self, event):
        self.setCursor(Qt.SizeHorCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.unsetCursor()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPos()
            self._original_width = self.left_widget.width()

    def mouseMoveEvent(self, event):
        if self._press_pos:
            delta = event.globalPos().x() - self._press_pos.x()
            new_width = self._original_width + delta

            # Contraintes visuelles
            total_width = self.parent().width()
            min_w = total_width * 0.1
            max_w = total_width * 0.5
            new_width = max(min_w, min(max_w, new_width))

            self.left_widget.setFixedWidth(int(new_width))

    def mouseReleaseEvent(self, event):
        self._press_pos = None
        self._original_width = None
        self.unsetCursor()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        color = QColor(self.user_settings.loaded_theme["resize_handle"]["default"])

        # 🔁 Peindre tout le fond
        painter.setPen(Qt.NoPen)
        painter.setBrush(color)
        painter.drawRect(self.rect())

        # ➕ Grip central (optionnel)
        w, h = self.width(), self.height()
        grip_width = 4
        grip_height = 60
        x = (w - grip_width) // 2
        y = (h - grip_height) // 2
        grip_color = QColor(self.user_settings.loaded_theme["resize_handle"]["grip"])  # légèrement plus clair, transparent
        painter.setBrush(grip_color)
        painter.drawRoundedRect(x, y, grip_width, grip_height , 2, 2)
