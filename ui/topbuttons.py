
#PySide6 imports-
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout, QPushButton, QWidget,
)
from .code_viewer import ProjectCodeViewer
class TopButtons(QWidget):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.translate = self.user_settings.translate
        self.theme = user_settings.loaded_theme
        self.setParent(parent)

        self.setup_ui()
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Ajout des boutons
        self.buttons = {
            "save": self.create_button(" " + self.translate("save"), "save", self.on_save_clicked),
            "code": self.create_button(self.translate("project_code"), "code", self.on_open_code),
            #"files": self.create_button(self.translate("project_files"), "file") #TO ADD IN FUTURE UPDATE
        }
        for btn in self.buttons.values():
            layout.addWidget(btn)

        self.adjustSize()
    def create_button(self, label, icon_key, callback=None):
        btn = QPushButton(label)
        btn.setIcon(QIcon(self.user_settings.get_icon(icon_key)))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self.user_settings.get_style("top_buttons").format(self.theme['text']['default'],
                                                                             self.user_settings.get_color_or_image(self.theme['button']['default']),
                                                                             self.theme['button']['border'],
                                                                             self.user_settings.get_color_or_image(self.theme['button']['hover']),
                                                                             self.theme['accent']['primary']))
        if callback:
            btn.clicked.connect(callback)
        return btn
    def on_save_clicked(self):
        parent = self.parent()
        if hasattr(parent, "trigger_save_project"):
            parent.trigger_save_project()
    def on_open_code(self):
        parent = self.parent()
        if hasattr(parent, "project_manager"):
            viewer = ProjectCodeViewer(parent, self.user_settings, parent.project_manager.project)
            viewer.exec()


