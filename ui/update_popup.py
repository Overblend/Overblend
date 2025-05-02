from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QApplication
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QIcon

class UpdatePopup(QDialog):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = user_settings.loaded_theme

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 250)
        self.setStyleSheet(f"background-color: {self.theme['background']['panel']}; border-radius: 12px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_header(layout)
        self.add_separator(layout)
        self.add_body(layout)
        self.add_footer(layout)

    def add_header(self, layout):
        header = QHBoxLayout()
        header.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(28, 28))
        logo.setFixedSize(28, 28)

        title = QLabel("OVERBLEND")
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 18px; font-weight: bold;")

        header.addWidget(logo)
        header.addWidget(title)
        header.addStretch()

        layout.addLayout(header)

    def add_separator(self, layout):
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.theme['container']['border']};")
        layout.addWidget(sep)

    def add_body(self, layout):
        self.body_text = QLabel("A new update is available!\nWould you like to install it now?")
        self.body_text.setAlignment(Qt.AlignCenter)
        self.body_text.setWordWrap(True)
        self.body_text.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 14px; padding: 20px;")
        layout.addWidget(self.body_text)

    def add_footer(self, layout):
        footer = QHBoxLayout()
        footer.setSpacing(15)

        self.no_btn = QPushButton("No")
        self.no_btn.setCursor(Qt.PointingHandCursor)
        self.no_btn.setStyleSheet(self.user_settings.get_style("button").format(
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme['button']['default']),
            self.theme['button']['border'],
            self.user_settings.get_color_or_image(self.theme['button']['hover']),
            self.theme['accent']['primary']
        ))

        self.yes_btn = QPushButton("Yes")
        self.yes_btn.setCursor(Qt.PointingHandCursor)
        self.yes_btn.setStyleSheet(self.no_btn.styleSheet())

        footer.addStretch()
        footer.addWidget(self.no_btn)
        footer.addWidget(self.yes_btn)
        footer.addStretch()

        layout.addLayout(footer)
