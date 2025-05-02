import json,os
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox,
    QPushButton, QCheckBox, QSlider, QTabWidget, QScrollArea,
    QFrame, QSpinBox, QGroupBox, QGridLayout
)
from PySide6.QtGui import QPixmap, QColor
from PySide6.QtCore import Qt, QSize, QRect, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QMainWindow, QGraphicsDropShadowEffect

class SettingsPanel(QWidget):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = self.user_settings.loaded_theme
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet(f"background-color: {self.theme['background']['panel']}")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel(self.user_settings.translate("settings"))
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 20px; font-weight: bold;")
        
     
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {self.theme['container']['border']};
                background-color: {self.theme['background']['panel']};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
            QTabBar::tab {{
                background-color: {self.theme['background']['sidebar']};
                color: {self.theme['text']['sidebar']};
                border: 1px solid {self.theme['container']['border']};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {self.theme['background']['panel']};
                color: {self.theme['text']['highlight']};
            }}
        """)
        
        # Create tabs
        self.general_tab = self.create_general_tab()
        self.appearance_tab = self.create_appearance_tab()
        # self.audio_tab = self.create_audio_tab() #TO BE ADDED IN NEXT UPDATE
        # self.export_tab = self.create_export_tab() #TO BE ADDED IN NEXT UDPATE
        # self.advanced_tab = self.create_advanced_tab() #TO BE ADDED IN NEXT UPDATE
        
        # Add tabs to widget
        self.tabs.addTab(self.general_tab, "General")
        self.tabs.addTab(self.appearance_tab, "Appearance")
        # self.tabs.addTab(self.audio_tab, "Audio")  #TO BE ADDED IN NEXT UPDATE
        # self.tabs.addTab(self.export_tab, "Export")  #TO BE ADDED IN NEXT UPDATE
        # self.tabs.addTab(self.advanced_tab, "Advanced")  #TO BE ADDED IN NEXT UPDATE
        
        main_layout.addWidget(self.tabs)
        
        
    def create_tab_scroll_area(self):
        # Create a scroll area for tab content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {self.theme['background']['panel']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.theme['background']['tertiary']};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme['accent']['primary']};
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        scroll.setWidget(content)
        return scroll, content, layout
    
    def create_general_tab(self):
        scroll, content, layout = self.create_tab_scroll_area()
        
        # Language group
        lang_group = self.create_group_box("Language & Region")
        lang_layout = QVBoxLayout(lang_group)
        
        lang_layout.addLayout(self._build_combo_row("Interface Language", self.user_settings.available_langs))
        # Project settings group
        project_group = self.create_group_box("Project Settings")
        project_layout = QVBoxLayout(project_group)
        
        # Enable Auto-Save checkbox
        checkbox_layout = self._build_checkbox_row("Enable Auto-Save")
        checkbox = checkbox_layout.itemAt(0).widget()
        checkbox.setChecked(self.user_settings.loaded_config.get("autosave", {}).get("active", False))
        checkbox.stateChanged.connect(lambda state: self._update_autosave_setting("active", bool(state)))
        project_layout.addLayout(checkbox_layout)

        # Auto-Save interval spinner
        spin_layout = self._build_spin_row("Auto-Save Interval (minutes)", 5, 1, 60)
        spinbox = spin_layout.itemAt(2).widget()
        spinbox.setValue(self.user_settings.loaded_config.get("autosave", {}).get("interval", 5))
        spinbox.valueChanged.connect(lambda val: self._update_autosave_setting("interval", val))
        project_layout.addLayout(spin_layout)

        
        # Add groups to layout
        layout.addWidget(lang_group)
        layout.addWidget(project_group)
        layout.addStretch()
        
        return scroll
    def create_appearance_tab(self):
        scroll, content, layout = self.create_tab_scroll_area()

        # Charger les thèmes depuis le fichier JSON
        themes_path = os.path.join("settings", "themes.json")
        if not os.path.exists(themes_path):
            return scroll

        with open(themes_path, "r", encoding="utf-8") as f:
            try:
                themes_data = json.load(f)
            except:
                themes_data = {}

        # Titre de section
        title_label = QLabel("Thèmes")
        title_label.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        layout.addSpacing(20)

        # Identifier le thème actuel
        current_theme = self.parent().user_settings.loaded_config["theme"]
        
        # Grille avec grands aperçus (2 colonnes seulement)
        theme_grid = QGridLayout()
        theme_grid.setSpacing(30)  # Grand espacement entre les prévisualisations
        
        # Ajouter les prévisualisations de thèmes à la grille
        for i, theme_name in enumerate(themes_data.keys()):
            is_current = theme_name == current_theme
            theme_widget = self.create_large_theme_preview(theme_name, is_current)
            row = i // 2  # 2 thèmes par ligne
            col = i % 2
            theme_grid.addWidget(theme_widget, row, col, Qt.AlignCenter)

        layout.addLayout(theme_grid)
        layout.addStretch()
        return scroll

    def create_large_theme_preview(self, theme_name, is_current=False):
        # Conteneur principal
        container = QFrame()
        container.setCursor(Qt.PointingHandCursor)
        container.setFixedSize(310, int(310*(9/16) + 100))  # Taille beaucoup plus grande
        
        # Style du conteneur
        border_color = self.theme['accent']['primary'] if is_current else self.theme['container']['border']
        container.setObjectName("caca")
        container.setStyleSheet(f"""
            QFrame#caca {{
                background-color: {self.theme['background']['tertiary']};
                border: 2px solid {border_color};
                border-radius: 12px;
            }}
            QFrame:hover#caca {{
                border: 2px solid {self.theme['accent']['primary_hover']};
            }}
        """)
        
        # Ajouter un effet d'ombre pour la profondeur
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 70))
        shadow.setOffset(0, 4)
        container.setGraphicsEffect(shadow)

        # Layout principal
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 16)
        layout.setSpacing(12)

        # Grand aperçu de l'image
        preview_container = QFrame()
        preview_container.setStyleSheet(f"""
            border-radius: 8px;
        """)
        preview_container.setMinimumHeight(200)  # Hauteur importante pour l'aperçu
        
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(4, 4, 4, 4)
        
        preview_img = QLabel()
        img_path = os.path.join("theme_files", f"{theme_name}.png")
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(
                QSize(300, int(300*(9/16))),  # Taille beaucoup plus grande
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            preview_img.setPixmap(pixmap)
            preview_img.setAlignment(Qt.AlignCenter)
        else:
            preview_img.setText("Aperçu non disponible")
            preview_img.setStyleSheet(f"color: {self.theme['text']['secondary']}; font-size: 14px; font-style: italic;")
            preview_img.setAlignment(Qt.AlignCenter)
        preview_img.setStyleSheet(f"border: 1px solid white")
        preview_layout.addWidget(preview_img)
        layout.addWidget(preview_container)

        # Barre d'informations en bas
        info_layout = QHBoxLayout()
        
        # Nom du thème
        name_label = QLabel(theme_name.capitalize())
        name_label.setStyleSheet(f"""
            color: {self.theme['text']['highlight']}; 
            background: none;
            font-size: 16px; 
            font-weight: bold;
        """)
        info_layout.addWidget(name_label)
        
        # Indicateur si c'est le thème actuel
        if is_current:
            current_badge = QLabel("• Actif")
            current_badge.setStyleSheet(f"""
                color: {self.theme['accent']['primary']}; 
                background: none;
                font-size: 14px;
            """)
            info_layout.addWidget(current_badge)
        else:
            apply_btn = QPushButton("Appliquer")
            apply_btn.setCursor(Qt.PointingHandCursor)
            apply_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.theme['accent']['primary']};
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {self.theme['accent']['primary_hover']};
                }}
            """)
            apply_btn.clicked.connect(lambda: self.apply_theme(theme_name))
            info_layout.addWidget(apply_btn)
        
        layout.addLayout(info_layout)
        
        # Événement de clic sur tout le conteneur pour appliquer le thème
        container.mousePressEvent = lambda event: self.apply_theme(theme_name)
        
        return container

    def apply_theme(self, theme_name):
        # Met à jour le fichier settings_path
        config_path = self.user_settings.settings_path
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        config["theme"] = theme_name  # ⬅️ MAJ la valeur du thème
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        # Recharge user_settings
        self.user_settings.load_config()
        self.user_settings.load_theme(theme_name)

        # Recharge l'UI principale
        parent = self.parent()
        while not isinstance(parent, QMainWindow):
            parent = parent.parent()
        if parent and hasattr(parent, "setup_ui"):
            parent.setup_ui()

    def create_theme_preview(self, theme_name, is_current=False):

        # Créer un widget conteneur avec effet d'ombre
        container = QFrame()
        
        # Style de base du conteneur
        container_style = f"""
            QFrame {{
                background-color: {self.theme['background']['tertiary']};
                border: 2px solid {self.theme['container']['border']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 2px solid {self.theme['accent']['primary']};
                background-color: {self.theme['background']['secondary']};
            }}
        """
        
        # Ajouter un style spécial si c'est le thème actuel
        if is_current:
            container_style += f"""
                QFrame {{
                    border: 2px solid {self.theme['accent']['primary']};
                    background-color: {self.theme['background']['secondary']};
                }}
            """
        
        container.setStyleSheet(container_style)
        container.setCursor(Qt.PointingHandCursor)
        container.setFixedSize(190, 170)  # Taille augmentée pour plus d'espace
        
        # Créer un effet d'ombre
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 3)
        container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Prévisualisation PNG avec un cadre
        preview_frame = QFrame()
        preview_frame.setStyleSheet(f"background-color: {self.theme['background']['main']}; border-radius: 8px;")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(2, 2, 2, 2)
        
        preview_img = QLabel()
        img_path = os.path.join("theme_files", f"{theme_name}.png")
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path).scaled(QSize(170, 100), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            preview_img.setPixmap(pixmap)
        else:
            preview_img.setText("Aucun aperçu")
            preview_img.setStyleSheet(f"color: {self.theme['text']['secondary']}; font-style: italic;")
            preview_img.setAlignment(Qt.AlignCenter)
        
        preview_layout.addWidget(preview_img, alignment=Qt.AlignCenter)
        layout.addWidget(preview_frame)

        # Nom du thème avec style amélioré
        label = QLabel(theme_name.capitalize())
        label.setStyleSheet(f"""
            color: {self.theme['text']['highlight']}; 
            font-size: 14px; 
            font-weight: bold;
        """)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # Indicateur de thème actuel
        if is_current:
            current_label = QLabel("Actuel")
            current_label.setStyleSheet(f"""
                color: {self.theme['accent']['primary']}; 
                font-size: 12px; 
                font-style: italic;
            """)
            current_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(current_label)

        # Animation au survol
        def enterEvent(event):
            animation = QPropertyAnimation(container, b"geometry")
            animation.setDuration(150)
            geometry = container.geometry()
            animation.setStartValue(geometry)
            animation.setEndValue(QRect(geometry.x(), geometry.y() - 5, geometry.width(), geometry.height()))
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()
            
        def leaveEvent(event):
            animation = QPropertyAnimation(container, b"geometry")
            animation.setDuration(150)
            geometry = container.geometry()
            animation.setStartValue(geometry)
            animation.setEndValue(QRect(geometry.x(), geometry.y() + 5, geometry.width(), geometry.height()))
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()
            
        container.enterEvent = enterEvent
        container.leaveEvent = leaveEvent

        # Appliquer le thème au clic avec effet visuel
        def apply_theme():
            # Effet visuel lors du clic
            click_anim = QPropertyAnimation(container, b"geometry")
            click_anim.setDuration(100)
            geometry = container.geometry()
            click_anim.setStartValue(geometry)
            click_anim.setEndValue(QRect(geometry.x(), geometry.y() + 3, geometry.width(), geometry.height()))
            click_anim.setEasingCurve(QEasingCurve.OutCubic)
            click_anim.start()
            
            # Récupérer la fenêtre principale et appliquer le thème
            parent = self.parent()
            while not isinstance(parent, QMainWindow):
                parent = parent.parent()
            parent.user_settings.load_theme(theme_name)
            parent.setup_ui()

        container.mousePressEvent = lambda event: apply_theme()

        return container

    def create_audio_tab(self):
        scroll, content, layout = self.create_tab_scroll_area()
        
        # Playback group
        playback_group = self.create_group_box("Playback")
        playback_layout = QVBoxLayout(playback_group)
        
        playback_layout.addLayout(self._build_slider_row("Default Volume", 75, "%"))
        playback_layout.addLayout(self._build_checkbox_row("Mute Audio When Editing"))
        playback_layout.addLayout(self._build_checkbox_row("Play Sound Effects for UI Actions"))
        
        # Audio processing group
        processing_group = self.create_group_box("Audio Processing")
        processing_layout = QVBoxLayout(processing_group)
        
        processing_layout.addLayout(self._build_combo_row("Audio Quality", ["Low", "Medium", "High"]))
        processing_layout.addLayout(self._build_checkbox_row("Auto Noise Reduction"))
        processing_layout.addLayout(self._build_slider_row("Noise Reduction Level", 50, "%"))
        processing_layout.addLayout(self._build_checkbox_row("Auto Normalize Audio"))
        
        # Add groups to layout
        layout.addWidget(playback_group)
        layout.addWidget(processing_group)
        layout.addStretch()
        
        return scroll
    
    def create_export_tab(self):
        scroll, content, layout = self.create_tab_scroll_area()
        
        # Video export group
        video_group = self.create_group_box("Video Export")
        video_layout = QVBoxLayout(video_group)
        
        video_layout.addLayout(self._build_combo_row("Default Export Format", ["MP4", "MOV", "AVI", "WebM"]))
        video_layout.addLayout(self._build_combo_row("Default Resolution", ["Original", "4K (3840×2160)", "1080p", "720p"]))
        video_layout.addLayout(self._build_combo_row("Encoding Quality", ["Low", "Medium", "High", "Maximum"]))
        video_layout.addLayout(self._build_spin_row("Frame Rate (FPS)", 30, 15, 120))
        
        # Output settings group
        output_group = self.create_group_box("Output Settings")
        output_layout = QVBoxLayout(output_group)
        
        output_layout.addLayout(self._build_file_path_row("Default Export Location"))
        output_layout.addLayout(self._build_checkbox_row("Add Date to Filename"))
        output_layout.addLayout(self._build_checkbox_row("Remember Last Export Settings"))
        output_layout.addLayout(self._build_checkbox_row("Open After Export"))
        
        # Add groups to layout
        layout.addWidget(video_group)
        layout.addWidget(output_group)
        layout.addStretch()
        
        return scroll
    
    def create_advanced_tab(self):
        scroll, content, layout = self.create_tab_scroll_area()
        
        # Performance group
        performance_group = self.create_group_box("Performance")
        performance_layout = QVBoxLayout(performance_group)
        
        performance_layout.addLayout(self._build_combo_row("Playback Quality", ["Low", "Medium", "High", "Original"]))
        performance_layout.addLayout(self._build_spin_row("Maximum Timeline Tracks", 20, 5, 100))
        performance_layout.addLayout(self._build_spin_row("RAM Usage Limit (GB)", 4, 1, 32))
        performance_layout.addLayout(self._build_checkbox_row("Use GPU Acceleration"))
        
        # BlendAI group
        blendai_group = self.create_group_box("BlendAI Assistant")
        blendai_layout = QVBoxLayout(blendai_group)
        
        blendai_layout.addLayout(self._build_checkbox_row("Enable BlendAI Assistant"))
        blendai_layout.addLayout(self._build_checkbox_row("Remember Conversation History"))
        blendai_layout.addLayout(self._build_slider_row("Response Length", 50, ""))
        blendai_layout.addLayout(self._build_checkbox_row("Allow Internet Access for BlendAI"))
        
        # Developer group
        dev_group = self.create_group_box("Developer")
        dev_layout = QVBoxLayout(dev_group)
        
        dev_layout.addLayout(self._build_checkbox_row("Enable Developer Tools"))
        dev_layout.addLayout(self._build_checkbox_row("Show Debug Information"))
        dev_layout.addLayout(self._build_file_path_row("Log File Location"))
        
        # Add groups to layout
        layout.addWidget(performance_group)
        layout.addWidget(blendai_group)
        layout.addWidget(dev_group)
        layout.addStretch()
        
        return scroll
    
    def create_group_box(self, title):
        group = QGroupBox(title)
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {self.theme['container']['border']};
                border-radius: 8px;
                margin-top: 16px;
                background-color: {self.theme['background']['secondary']};
                color: {self.theme['text']['highlight']};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        return group
    
    def _update_autosave_setting(self, key, value):
        config_path = self.user_settings.settings_path
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        if "autosave" not in config:
            config["autosave"] = {}

        config["autosave"][key] = value

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        self.user_settings.load_config()

        # 🔄 Relancer autosave si disponible
        parent = self.parent()
        while parent and not hasattr(parent, "setup_autosave"):
            parent = parent.parent()
        if parent:
            parent.setup_autosave()

    def _build_combo_row(self, label_text, items):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 14px;")
        
        combo = QComboBox()
        combo.addItems(items)
        combo.setStyleSheet(self.user_settings.get_style("aspect_ratio_dropdown").format(
            self.user_settings.get_color_or_image(self.theme["dropdown"]["background"]),
            self.theme["text"]["default"],
            self.theme["dropdown"]["separator"],
            self.user_settings.get_color_or_image(self.theme["dropdown"]["hover"]),
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme["dropdown"]["list_background"]),
            self.theme["dropdown"]["selected_background"]
        ))
        combo.setMinimumWidth(200)
        if label_text.lower() == "interface language":
            current_lang = self.user_settings.loaded_config.get("lang", "en")
            combo.setCurrentText(current_lang)

            def on_lang_change(new_lang):
                config_path = self.user_settings.settings_path
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                config["lang"] = new_lang
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)

                self.user_settings.load_config()
                self.user_settings.load_language(new_lang)

                # Recharger la fenêtre principale
                parent = self.parent()
                while not isinstance(parent, QMainWindow):
                    parent = parent.parent()
                    
                if parent and hasattr(parent, "setup_ui"):
                    parent.setup_ui()

            combo.currentTextChanged.connect(on_lang_change)
        
        row.addWidget(label)
        row.addStretch()
        row.addWidget(combo)
        return row
    
    def _build_checkbox_row(self, label_text):
        row = QHBoxLayout()
        checkbox = QCheckBox(label_text)
        checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {self.theme['text']['default']};
                font-size: 14px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 1px solid {self.theme['button']['border']};
                border-radius: 3px;
                background: {self.theme['button']['default']};
            }}
            QCheckBox::indicator:checked {{
                background: {self.theme['button']['checked_bg']};
                border: 1px solid {self.theme['button']['checked_border']};
                image: url({self.user_settings.get_icon('check',True)});
            }}
        """)
        row.addWidget(checkbox)
        row.addStretch()
        return row
    
    def _build_slider_row(self, label_text, default_value, unit=""):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 14px;")
        
        slider = QSlider(Qt.Horizontal)
        slider.setValue(default_value)
        slider.setRange(0, 100)
        slider.setMinimumWidth(150)
        slider.setStyleSheet(self.user_settings.get_style("preview_slider").format(
            self.user_settings.get_color_or_image(self.theme['slider']['groove']),
            self.user_settings.get_color_or_image(self.theme['slider']['handle']),
            self.user_settings.get_color_or_image(self.theme['slider']['subpage']),
            self.user_settings.get_color_or_image(self.theme['slider']['addpage'])
        ))
        
        value_label = QLabel(f"{default_value}{unit}")
        value_label.setMinimumWidth(40)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 14px;")
        
        row.addWidget(label)
        row.addStretch()
        row.addWidget(slider)
        row.addWidget(value_label)
        return row
    
    def _build_spin_row(self, label_text, default_value, min_value, max_value):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 14px;")
        
        spin = QSpinBox()
        spin.setRange(min_value, max_value)
        spin.setValue(default_value)
        spin.setMinimumWidth(70)
        spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {self.theme['background']['tertiary']};
                color: {self.theme['text']['default']};
                border: 1px solid {self.theme['button']['border']};
                border-radius: 4px;
                padding: 2px 4px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 16px;
                border: none;
                background: {self.theme['button']['default']};
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background: {self.theme['button']['hover']};
            }}
        """)
        
        row.addWidget(label)
        row.addStretch()
        row.addWidget(spin)
        return row
    
    def _build_color_picker_row(self, label_text):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 14px;")
        
        color_preview = QPushButton()
        color_preview.setFixedSize(30, 30)
        color_preview.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']['primary']};
                border: 1px solid {self.theme['button']['border']};
                border-radius: 4px;
            }}
        """)
        
        choose_btn = QPushButton("Choose...")
        choose_btn.setStyleSheet(self.user_settings.get_style("button").format(
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme["button"]["default"]),
            self.theme["button"]["border"],
            self.user_settings.get_color_or_image(self.theme["button"]["hover"]),
            self.theme["accent"]["primary"]
        ))
        
        row.addWidget(label)
        row.addStretch()
        row.addWidget(color_preview)
        row.addWidget(choose_btn)
        return row
    
    def _build_file_path_row(self, label_text):
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 14px;")
        
        path_display = QLabel("/Users/username/Documents")
        path_display.setStyleSheet(f"""
            color: {self.theme['text']['sidebar']};
            font-size: 13px;
            background-color: {self.theme['background']['tertiary']};
            border: 1px solid {self.theme['button']['border']};
            border-radius: 4px;
            padding: 4px 8px;
        """)
        path_display.setMinimumWidth(150)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet(self.user_settings.get_style("button").format(
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme["button"]["default"]),
            self.theme["button"]["border"],
            self.user_settings.get_color_or_image(self.theme["button"]["hover"]),
            self.theme["accent"]["primary"]
        ))
        
        row.addWidget(label)
        row.addStretch()
        row.addWidget(path_display)
        row.addWidget(browse_btn)
        return row