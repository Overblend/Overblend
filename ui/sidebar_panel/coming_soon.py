#PySide6 imports-
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QWidget,QGraphicsOpacityEffect
)
#Ui Imports
class ComingSoonPlaceholder(QWidget):
    def __init__(self, theme, user_settings,parent=None):
        super().__init__(parent)
        self.theme = theme
        self.user_settings = user_settings
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        # === Label stylisé
        label = QLabel("COMING SOON")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            QLabel {{
                color: {self.theme['text']['highlight']};
                font-size: 28px;
                font-weight: bold;
                letter-spacing: 2px;
                padding: 40px;
                background-color: rgba(255, 255, 255, 0.02);
                border-radius: 12px;
            }}
        """)

        # === Opacité douce
        effect = QGraphicsOpacityEffect()
        effect.setOpacity(0.8)
        label.setGraphicsEffect(effect)

        layout.addWidget(label, alignment=Qt.AlignCenter)
        layout.addStretch(1)
