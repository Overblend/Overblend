from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QApplication
)
from PySide6.QtCore import Qt, QUrl, QObject, QEvent
from PySide6.QtGui import QDesktopServices

class ComingSoonPopup(QDialog):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = self.user_settings.loaded_theme

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setModal(False)
        self.setFixedSize(420, 320)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme['background']['panel']};
                border: 2px solid {self.theme['container']['border']};
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        layout.setAlignment(Qt.AlignCenter)

        self.add_header(layout)
        self.add_separator(layout)
        self.add_body(layout)
        self.add_footer(layout)
        self._install_click_outside_filter()

    def add_header(self, layout):
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(30, 30))
        logo.setFixedSize(30, 30)

        title = QLabel("OVERBLEND")
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignVCenter)

        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

    def add_separator(self, layout):
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self.theme['container']['border']};")
        layout.addWidget(separator)

    def add_body(self, layout):
        message = QLabel(self.user_settings.translate("yet_to_come"))
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet(f"""
            color: {self.theme['text']['highlight']};
            font-size: 20px;
            font-weight: 800;
            padding: 20px;
        """)
        layout.addStretch()
        layout.addWidget(message)
        layout.addStretch()

    def add_footer(self, layout):
        button = QPushButton(self.user_settings.translate("learn_more_features"))
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedHeight(36)
        button.setStyleSheet(self.user_settings.get_style("button").format(
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme['button']['default']),
            self.theme['button']['border'],
            self.user_settings.get_color_or_image(self.theme['button']['hover']),
            self.theme['accent']['primary']
        ))
        button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://overblend.org/features")))

        layout.addWidget(button, alignment=Qt.AlignCenter)

    def _install_click_outside_filter(self):
        class ClickFilter(QObject):
            def __init__(self, parent):
                super().__init__()
                self.parent = parent

            def eventFilter(self, obj, event):
                if event.type() == QEvent.MouseButtonPress:
                    if not self.parent.geometry().contains(event.globalPosition().toPoint()):
                        self.parent.close()
                        return True
                return False

        self._filter_obj = ClickFilter(self)
        app = QApplication.instance()
        app.installEventFilter(self._filter_obj)
        self.finished.connect(lambda: app.removeEventFilter(self._filter_obj))
