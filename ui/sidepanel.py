# === Overblend Imports ===
from .sidebar_panel.blendai_chat import ChatWidget
from .sidebar_panel.coming_soon import ComingSoonPlaceholder
from .sidebar_panel.settings import SettingsPanel
# === PySide6 Imports ===

from PySide6.QtWidgets import (QVBoxLayout, QWidget,
    QStackedWidget
)


# === Panneau dynamique (panel latéral affichant les outils ou placeholders) ===

class DynamicPanel(QWidget):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = user_settings.loaded_theme

        self.setStyleSheet(user_settings.get_color_or_image(self.theme['background']['secondary']))
        self.setVisible(False)

        self.stack = QStackedWidget(self)
        self.pages = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        self.initialized = False

    # === Ajoute toutes les pages (placeholder ou widget fonctionnel) ===
    def add_placeholder_pages(self, buttons):
        for key, _ in buttons:
            if key == "blendai":
                widget = ChatWidget(self.user_settings, self)
            elif key == "settings":
                widget = SettingsPanel(self.user_settings, self)
            else:
                widget = ComingSoonPlaceholder(self.theme,self.user_settings)

            self.add_page(key, widget)

    # === Ajoute une page au panel dynamique
    def add_page(self, key: str, widget: QWidget):
        self.stack.addWidget(widget)
        self.pages[key] = widget

    # === Affiche une page spécifique par sa clé
    def show_page(self, key: str):
        page = self.pages.get(key)
        if page:
            self.stack.setCurrentWidget(page)
            self.setVisible(True)

    # === Change la visibilité du panneau
    def toggle_visibility(self, visible: bool):
        self.setVisible(visible)
