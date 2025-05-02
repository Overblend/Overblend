from PySide6.QtCore import Qt, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QMovie, QPixmap
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout,
    QProgressBar, QDialog
)


class LoadingPopup(QDialog):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.setFixedSize(400, 300)
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.user_settings = user_settings
        self.theme = self.user_settings.loaded_theme

        # ✨ Bordure décorative propre au dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.theme['background']['panel']};
                border-radius: 12px;
                border: 2px solid {self.theme['container']['border']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # 🌀 GIF loader
        self.loading_gif = QLabel()
        self.loading_gif.setAlignment(Qt.AlignCenter)
        gif_path = self.user_settings.get_icon("loading", True)

        if gif_path.endswith(".gif"):
            self.movie = QMovie(gif_path)
            self.movie.setScaledSize(QSize(96, 96))  # Taille réduite & propre
            self.movie.setParent(self)
            self.loading_gif.setMovie(self.movie)
            self.movie.start()
        else:
            self.loading_gif.setPixmap(QPixmap(gif_path).scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        layout.addWidget(self.loading_gif)

        # 🧠 Titre
        title = QLabel("OVERBLEND - BETA")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # ➖ Séparateur
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.theme['container']['border']};")
        layout.addWidget(sep)

        # 📊 Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {self.theme['background']['main']};
                border: 1px solid {self.theme['container']['border']};
                border-radius: 6px;
                height: 12px;
            }}
            QProgressBar::chunk {{
                background-color: {self.theme['accent']['primary']};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.progress_bar)

        # 📄 Texte d’état animé
        self.status_text = QLabel("Loading")
        self.status_text.setAlignment(Qt.AlignCenter)
        self.status_text.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 12px;")
        layout.addWidget(self.status_text)

        # ⚙️ Animation de points
        self.dot_count = 0
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.animate_dots)
        self.status_timer.start(500)

        # 🎞️ Animation de progression
        self._current_progress = 0
        self._progress_anim = QPropertyAnimation(self.progress_bar, b"value", self)
        self._progress_anim.setDuration(400)
        self._progress_anim.setEasingCurve(QEasingCurve.InOutCubic)

    def animate_dots(self):
        self.dot_count = (self.dot_count + 1) % 4
        self.status_text.setText("Loading" + "." * self.dot_count)

    def set_progress(self, value, status=None):
        # Smooth animation
        self._progress_anim.stop()
        self._progress_anim.setStartValue(self._current_progress)
        self._progress_anim.setEndValue(value)
        self._progress_anim.start()
        self._current_progress = value

        if status:
            self.status_text.setText(status)
