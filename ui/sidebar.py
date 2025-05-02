#PySide6 imports-
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
     QLabel,QMainWindow, QPushButton, QVBoxLayout, QWidget,QScrollArea
)
class Sidebar(QWidget):
    def __init__(self, user_settings, menu):
        super().__init__()
        self.user_settings = user_settings
        self.theme = user_settings.loaded_theme
        self.menu = menu
        self.buttons = []

        self.init_ui()

    def init_ui(self):
        # === Scroll principal
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(self.user_settings.loaded_config["ui"]["sidebar_width"])
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            self.user_settings.get_color_or_image(self.theme["background"]["sidebar"], scroll)
        )

        # === Conteneur dans le scroll
        container = QWidget()
        container.setContentsMargins(10, 6, 10, 6)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 20, 0, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        # === Logo bouton
        logo_button = self.create_logo_button()
        logo_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(logo_button, alignment=Qt.AlignHCenter)
        layout.addSpacing(20)

        # === Boutons principaux
        self.build_sidebar_buttons(layout)

        layout.addStretch()
        scroll.setWidget(container)

        # === Layout principal de la Sidebar
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def create_logo_button(self):
        icon = self.user_settings.get_icon("app_icon")
        btn = QPushButton()
        btn.setIcon(icon)
        btn.clicked.connect(self.open_overlay_menu)
        btn.setIconSize(QSize(40, 40))
        btn.setFixedSize(60, 60)

        bg_style = self.user_settings.get_color_or_image(self.theme["button"]["default"])
        qss = self.user_settings.get_style("logo_button").format(bg_style)
        btn.setStyleSheet(qss)

        return btn
    def open_overlay_menu(self):
        parent_window = self.window()
        if isinstance(parent_window, QMainWindow):
            menu = self.menu(parent_window, self.user_settings, parent_window.project_manager)
            menu.show_at_center_of(parent_window)
            

    def build_sidebar_buttons(self, layout):
        keys = [x[0] for x in self.user_settings.buttons]
        for key in keys:
            icon = self.user_settings.get_icon(key)
            label = self.user_settings.translate(key)
            button = SidebarButton(icon, label, self.theme, self.user_settings)

            block = QWidget()
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(5)
            block_layout.addWidget(button, alignment=Qt.AlignHCenter)
            block_layout.addWidget(button.text_label, alignment=Qt.AlignHCenter)

            layout.addWidget(block, alignment=Qt.AlignHCenter)
            self.buttons.append(button)
#----------------------------
class SidebarButton(QPushButton):
    def __init__(self, icon: QIcon, label: str, theme: dict,user_settings):
        super().__init__()
        self.setIcon(icon)
        self.setIconSize(QSize(24, 24))
        self.setFixedSize(50, 50)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)

        self.theme = theme
        self.user_settings = user_settings
        self.setStyleSheet(self.build_stylesheet())

        self.text_label = QLabel(label)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet(self.user_settings.get_style("sidebar_text").format(self.theme['text']['sidebar']))
    def build_stylesheet(self):
        bg = self.user_settings.get_color_or_image(self.theme["button"]["default"])
        hover = self.user_settings.get_color_or_image(self.theme["button"]["hover"])
        checked =self.user_settings.get_color_or_image(self.theme["button"]["checked_bg"])
        border = self.theme["button"]["border"]
        checked_border = self.theme["button"]["checked_border"]
        return self.user_settings.get_style("sidebar_button").format(bg,border,hover,checked,checked_border)
