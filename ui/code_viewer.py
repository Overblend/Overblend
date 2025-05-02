# === Imports ===
import pyperclip
import json

from PySide6.QtCore import Qt, QTimer, QObject, QEvent, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QTextEdit, QDialog,
    QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QTabWidget, QApplication
)

class ProjectCodeViewer(QDialog):
    changesApplied = Signal()  # Optionnel : peut être connecté ailleurs

    def __init__(self, parent: QMainWindow, user_settings, project):
        super().__init__(parent)
        self.user_settings = user_settings
        self.project = project
        self.theme = user_settings.loaded_theme

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setModal(True)
        self.setFixedSize(700, 500)
        self.setStyleSheet(
            self.user_settings.get_style("code_viewer").format(
                self.user_settings.get_color_or_image(self.theme["code_viewer"]["background"])
            )
        )

        self.add_corner_borders()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.add_header(layout)
        self.add_code_view(layout)
        self._install_click_outside_filter()

    # === Header (titre + boutons)
    def add_header(self, layout):
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(32, 32))
        logo.setFixedSize(32, 32)

        title = QLabel("OVERBLEND")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")

        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.add_buttons(header_layout)

        layout.addWidget(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #555;")
        layout.addWidget(sep)

    # === Boutons d'action
    def add_buttons(self, layout):
        # Confirm
        self.check_btn = QPushButton()
        self.check_btn.setIcon(self.user_settings.get_icon("check"))
        self.check_btn.setCursor(Qt.PointingHandCursor)
        self.check_btn.setStyleSheet(self._button_style())
        self.check_btn.hide()
        self.check_btn.clicked.connect(self.apply_edit_mode)
        layout.addWidget(self.check_btn)

        # Edit / Cancel
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(self.user_settings.get_icon("edit"))
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn.setStyleSheet(self._button_style())
        self.edit_btn.clicked.connect(self.toggle_edit_mode)
        layout.addWidget(self.edit_btn)

        # Copy
        self.copy_btn = QPushButton(self.user_settings.translate("copy"))
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setStyleSheet(self._button_style())
        self.copy_btn.clicked.connect(self.copy_project_code)
        layout.addWidget(self.copy_btn)

    def _button_style(self):
        return self.user_settings.get_style("button").format(
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme['button']['default']),
            self.theme['button']['border'],
            self.user_settings.get_color_or_image(self.theme['button']['hover']),
            self.theme['accent']['primary']
        )

    # === Tabs project/prompt
    def add_code_view(self, layout):
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            self.user_settings.get_style("code_viewer_tab_widget").format(
                self.user_settings.get_color_or_image(self.theme['code_viewer']['tab_bar_disabled']),
                self.theme['text']['default'],
                self.theme['button']['border'],
                self.user_settings.get_color_or_image(self.theme['code_viewer']['code_background']),
                self.theme['text']['highlight'],
                self.user_settings.get_color_or_image(self.theme['background']['panel']),
                self.theme['button']['border']
            )
        )

        self.project_text = QTextEdit()
        self.project_text.setReadOnly(True)
        self.project_text.setStyleSheet(self.user_settings.get_style("project_code").format(
            self.user_settings.get_color_or_image(self.theme['code_viewer']['code_background']),
            self.theme['code_viewer']['text_color']
        ))
        self.project_text.setPlainText(self.load_project_code())
        self.tab_widget.addTab(self.project_text, self.user_settings.translate("project"))

        self.prompt_text = QTextEdit()
        self.prompt_text.setReadOnly(True)
        self.prompt_text.setStyleSheet(self.project_text.styleSheet())
        self.prompt_text.setPlainText(self.load_prompt_code())
        self.tab_widget.addTab(self.prompt_text, self.user_settings.translate("prompt"))

        layout.addWidget(self.tab_widget)

        self.original_project = self.project_text.toPlainText()
        self.original_prompt = self.prompt_text.toPlainText()

    def load_project_code(self):
        try:
            return json.dumps(self.project.project, indent=4, ensure_ascii=False)
        except Exception as e:
            return f"Error loading project: {e}"

    def load_prompt_code(self):
        try:
            return json.dumps(self.user_settings.loaded_config.get("prompt", {}), indent=4, ensure_ascii=False)
        except Exception as e:
            return f"Error loading prompt: {e}"

    # === Copier l'onglet actif
    def copy_project_code(self):
        index = self.tab_widget.currentIndex()
        code = self.project_text.toPlainText() if index == 0 else self.prompt_text.toPlainText()
        pyperclip.copy(code)

        self.copy_btn.setText(self.user_settings.translate("copied"))
        QTimer.singleShot(1500, lambda: self.copy_btn.setText(self.user_settings.translate("copy")))

    # === Toggle : entrer ou sortir du mode édition
    def toggle_edit_mode(self):
        editor = self._get_active_editor()
        if not editor.isReadOnly():
            self.cancel_edit_mode()
        else:
            self.enter_edit_mode()

    def enter_edit_mode(self):
        editor = self._get_active_editor()
        editor.setReadOnly(False)
        self.check_btn.show()
        self.edit_btn.setIcon(self.user_settings.get_icon("discard"))

    def cancel_edit_mode(self):
        index = self.tab_widget.currentIndex()
        editor = self._get_active_editor()
        content = self.original_project if index == 0 else self.original_prompt
        editor.setPlainText(content)
        editor.setReadOnly(True)
        self.check_btn.hide()
        self.edit_btn.setIcon(self.user_settings.get_icon("edit"))

    # === Appliquer les modifications
    def apply_edit_mode(self):
        index = self.tab_widget.currentIndex()
        editor = self._get_active_editor()
        editor.setReadOnly(True)
        self.check_btn.hide()
        self.edit_btn.setIcon(self.user_settings.get_icon("edit"))

        try:
            if index == 0:
                parsed = json.loads(editor.toPlainText())
                self.project.project = parsed
                if isinstance(self.parent(), QMainWindow) and hasattr(self.parent(), "project_manager"):
                    self.parent().project_manager.project = self.project
            else:
                prompt = editor.toPlainText()
                prompt = prompt[1:-1] if prompt.startswith('"') else prompt
                self.user_settings.loaded_config["prompt"] = prompt
                with open(self.user_settings.settings_path, "w", encoding="utf-8") as f:
                    json.dump(self.user_settings.loaded_config, f, indent=4, ensure_ascii=False)

            self.changesApplied.emit()

        except Exception as e:
            print(f"[ERROR] Mauvais format JSON : {e}")

    def _get_active_editor(self):
        return self.project_text if self.tab_widget.currentIndex() == 0 else self.prompt_text

    # === Bordures custom
    def add_corner_borders(self):
        def create_corner(x, y, w, h, radius, corner="top-left"):
            corner_frame = QFrame(self)
            corner_frame.setGeometry(x, y, w, h)
            style = "background-color: white;"
            if corner == "top-left":
                style += "border-top-left-radius: 6px;"
            elif corner == "bottom-right":
                style += "border-bottom-right-radius: 6px;"
            corner_frame.setStyleSheet(style)
            return corner_frame

        create_corner(0, 0, 80, 4, 6, "top-left")
        create_corner(0, 0, 4, 80, 6, "top-left")
        create_corner(self.width() - 80, self.height() - 4, 80, 4, 6, "bottom-right").raise_()
        create_corner(self.width() - 4, self.height() - 80, 4, 80, 6, "bottom-right").raise_()

        self.resizeEvent = lambda event: [
            create_corner(self.width() - 80, self.height() - 4, 80, 4, 6, "bottom-right").move(self.width() - 80, self.height() - 4),
            create_corner(self.width() - 4, self.height() - 80, 4, 80, 6, "bottom-right").move(self.width() - 4, self.height() - 80)
        ]

    # === Fermer en cliquant à l’extérieur
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
