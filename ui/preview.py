#Overblend Imports
from .coming_soon import ComingSoonPopup
#PySide6 imports-
from PySide6.QtCore import QSize, Qt,QEvent
from PySide6.QtGui import QIcon, QColor, QPainter
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,QComboBox,QListView,QSlider,QSizePolicy,QStyledItemDelegate)

class AspectRatioDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if index.data() == "---":
            painter.save()
            pen = painter.pen()
            pen.setColor(QColor("#444"))
            painter.setPen(pen)
            y = option.rect.center().y()
            painter.drawLine(option.rect.left() + 10, y, option.rect.right() - 10, y)
            painter.restore()
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        if index.data() == "---":
            return QSize(0, 10)
        return super().sizeHint(option, index)
class ResizeHandle(QWidget):
    def __init__(self, target_widget,parent=None):
        super().__init__(parent)
        self.target_widget = target_widget
        self.resize(16, 16)  # Taille du point de redimensionnement
        self.setCursor(Qt.SizeFDiagCursor)
        self.setMouseTracking(True)
        self.dragging = False
        self.aspect_ratio = 16/9  # Ratio par défaut
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.gray)
        
        # Dessiner trois petits carrés diagonaux pour indiquer le redimensionnement
        for i in range(3):
            painter.drawRect(self.width() - (i+1)*4, self.height() - 4, 3, 3)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.pos()
            self.original_width = self.target_widget.width()
            self.original_height = self.target_widget.height()
            
    def mouseMoveEvent(self, event):
        if self.dragging:
            delta_x = event.x() - self.drag_start_pos.x()
            
            # Calculer la nouvelle taille en maintenant le ratio d'aspect
            new_width = self.original_width + delta_x
            new_height = int(new_width / self.aspect_ratio)
            
            # Limiter à une taille minimale
            if new_width >= 100 and new_height >= 50:
                self.target_widget.setFixedSize(new_width, new_height)
                
                # Notifier le parent que la taille a changé
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        
    def update_aspect_ratio(self, width_ratio, height_ratio):
        self.aspect_ratio = width_ratio / height_ratio
class PreviewSection(QWidget):
    def __init__(self, user_settings, project, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.project = project
        self.theme = self.user_settings.loaded_theme
        self.resizing_preview = False
        self.setup_ui()
        
    def setup_ui(self):
        # Configurer le widget principal
        self.setObjectName("preview_section")
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Créer la section de prévisualisation
        preview_container = self.create_preview_container()
        main_layout.addWidget(preview_container, alignment=Qt.AlignCenter)
        
        # Barre de contrôle
        control_bar = self.create_control_bar()
        main_layout.addWidget(control_bar)

    def create_preview_container(self):
        # Conteneur pour le widget de prévisualisation
        preview_container = QWidget()
        container_layout = QVBoxLayout(preview_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Widget de prévisualisation
        self.preview_widget = QLabel()
        self.preview_widget.setObjectName("preview_widget")
        self.preview_widget.setMinimumHeight(100)
        self.preview_widget.setMaximumHeight(800)
        self.preview_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_widget.setFixedHeight(int(self.user_settings.loaded_config["ui"]["preview_height"]))
        self.preview_widget.setFixedWidth(int(self.user_settings.loaded_config["ui"]["preview_height"] * (16 / 9)))
        self.preview_widget.setStyleSheet(self.user_settings.get_style("preview_widget").format(self.theme['preview']['border']))
        # Slider de prévisualisation (overlay)
        self.preview_slider_overlay = QSlider(Qt.Horizontal, self.preview_widget)
        self.preview_slider_overlay.setRange(0, self.user_settings.loaded_config["slider"]["preview_slider_precision"])
        self.preview_slider_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.preview_slider_overlay.hide()
        self.preview_slider_overlay.valueChanged.connect(self.on_preview_slider_moved)
        self.preview_slider_overlay.setStyleSheet(self.user_settings.get_style("preview_slider").format(self.user_settings.get_color_or_image(self.theme['slider']['groove']),
                                                                                                        self.user_settings.get_color_or_image(self.theme['slider']['handle']),
                                                                                                        self.user_settings.get_color_or_image(self.theme['slider']['subpage']),
                                                                                                        self.user_settings.get_color_or_image(self.theme['slider']['addpage'])))
        self.preview_slider_overlay.setGeometry(
                10,
                self.preview_widget.height() - 20,
                self.preview_widget.width() - 20,
                10
            )
        
        container_layout.addWidget(self.preview_widget)
        
        # Gestionnaire de redimensionnement
        self.resize_preview = ResizeHandle(self.preview_widget, preview_container)
        self.resize_preview.update_aspect_ratio(self.project.aspect_ratio[0], self.project.aspect_ratio[1])
        
        # Configuration des événements
        self.preview_widget.installEventFilter(self)
        self.preview_widget.setMouseTracking(True)
        preview_container.installEventFilter(self)
        
        return preview_container

    def create_control_bar(self):
        translate = self.user_settings.translate
        control_bar = QWidget()
        control_bar.setAttribute(Qt.WA_StyledBackground, True)
        control_bar.setStyleSheet("background-color: transparent;")
        control_bar.setFixedWidth(self.preview_widget.width())
        
        control_layout = QHBoxLayout(control_bar)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # Bloc de contrôles gauche
        left_controls = self.create_left_controls(translate)
        
        # Bloc de contrôles droit
        right_controls = self.create_right_controls()
        
        control_layout.addWidget(left_controls, alignment=Qt.AlignLeft)
        control_layout.addStretch()
        control_layout.addWidget(right_controls, alignment=Qt.AlignRight)
        
        return control_bar
        
    def create_left_controls(self, translate):
        left_controls = QWidget()
        left_layout = QHBoxLayout(left_controls)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Dropdown pour le ratio d'aspect
        self.create_aspect_ratio_dropdown(translate)
        
        # Dropdown pour la qualité
        self.create_quality_dropdown(translate)
        
        # Bouton d'export
        export_btn = QPushButton(translate("export"))
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(lambda: ComingSoonPopup(self.user_settings).exec())

        export_btn.setFixedHeight(36)
        g = self.user_settings.get_color_or_image
        style = self.user_settings.get_style("export_button").format(self.theme['text']['highlight'],
                                                                     g(self.theme['accent']['primary']),
                                                                     self.theme['accent']['primary_hover'],
                                                                     g(self.theme['accent']['primary_hover']),
                                                                     self.theme['accent']['primary'])
        export_btn.setStyleSheet(style)
        left_layout.addWidget(self.aspect_ratio_dropdown)
        left_layout.addWidget(self.quality_dropdown)
        left_layout.addWidget(export_btn)
        left_controls.setStyleSheet("background: transparent;")
        
        return left_controls
    
    def create_aspect_ratio_dropdown(self, translate):
        self.aspect_ratio_dropdown = QComboBox()
        self.aspect_ratio_dropdown.setItemDelegate(AspectRatioDelegate())
        self.aspect_ratio_dropdown.setFixedHeight(36)
        us = self.user_settings
        g = us.get_color_or_image
        style = us.get_style("aspect_ratio_dropdown").format(g(self.theme['dropdown']['background']),
                                                             self.theme['text']['default'],
                                                             self.theme['dropdown']['separator'],
                                                             g(self.theme['dropdown']['hover']),
                                                             self.theme['text']['default'],
                                                             g(self.theme['dropdown']['list_background']),
                                                             self.theme['dropdown']['selected_background'])
        self.aspect_ratio_dropdown.setStyleSheet(style)
        # Initialiser la map des ratios d'aspect
        self.aspect_ratio_map = {
            "aspect_ratio_tiktok": [9, 16],
            "aspect_ratio_youtube_shorts": [9, 16],
            "aspect_ratio_instagram_story": [9, 16],
            "aspect_ratio_instagram_reel": [9, 16],
            "aspect_ratio_youtube": [16, 9],
            "aspect_ratio_instagram_post": [4, 5],
            "aspect_ratio_twitter": [1, 1],
            "aspect_ratio_portrait": [3, 4],
            "aspect_ratio_square": [1, 1],
            "aspect_ratio_landscape": [4, 3],
            "aspect_ratio_wide": [21, 9],
        }
        
        # Ajouter les options avec icônes
        icons = self.user_settings.get_icon("aspect_ratios",True) 
        self.aspect_ratio_dropdown.addItem(QIcon(icons["tiktok"]), translate("aspect_ratio_tiktok"))
        self.aspect_ratio_dropdown.addItem(QIcon(icons["youtube"]), translate("aspect_ratio_youtube_shorts"))
        self.aspect_ratio_dropdown.addItem(QIcon(icons["instagram"]), translate("aspect_ratio_instagram_story"))
        self.aspect_ratio_dropdown.addItem(QIcon(icons["instagram"]), translate("aspect_ratio_instagram_reel"))
        self.aspect_ratio_dropdown.addItem("---")
        self.aspect_ratio_dropdown.addItem(QIcon(icons["youtube"]), translate("aspect_ratio_youtube"))
        self.aspect_ratio_dropdown.addItem("---")
        self.aspect_ratio_dropdown.addItem(QIcon(icons["instagram"]), translate("aspect_ratio_instagram_post"))
        self.aspect_ratio_dropdown.addItem(QIcon(icons["twitter"]), translate("aspect_ratio_twitter"))
        self.aspect_ratio_dropdown.addItem("---")
        self.aspect_ratio_dropdown.addItem(QIcon(icons["portrait"]), translate("aspect_ratio_portrait"))
        self.aspect_ratio_dropdown.addItem(QIcon(icons["square"]), translate("aspect_ratio_square"))
        self.aspect_ratio_dropdown.addItem(QIcon(icons["landscape"]), translate("aspect_ratio_landscape"))
        self.aspect_ratio_dropdown.addItem(QIcon(icons["wide"]), translate("aspect_ratio_wide"))
        
        # Connecter le signal de changement
        self.aspect_ratio_dropdown.currentIndexChanged.connect(self.on_aspect_ratio_changed)
        
        # Définir la sélection actuelle
        current_ratio = self.project.aspect_ratio
        for i in range(self.aspect_ratio_dropdown.count()):
            label = self.aspect_ratio_dropdown.itemText(i)
            for key, ratio in self.aspect_ratio_map.items():
                if ratio == current_ratio and translate(key) == label:
                    self.aspect_ratio_dropdown.setCurrentIndex(i)
                    break
        
    
    def create_quality_dropdown(self, translate):
        self.quality_dropdown  = QComboBox()
        self.quality_dropdown.setFixedHeight(36)
        us = self.user_settings
        g = us.get_color_or_image
        style = us.get_style("quality_dropdown").format(g(self.theme['dropdown']['background']),
                                                        self.theme['text']['default'],
                                                        self.theme['dropdown']['separator'],
                                                        g(self.theme['dropdown']['hover']),
                                                        g(self.theme['dropdown']['list_background']),
                                                        self.theme['text']['default'],
                                                        self.theme['dropdown']['selected_background'])
        self.quality_dropdown.setStyleSheet(style)
        self.quality_dropdown.setView(QListView())  # Pour éviter les bugs visuels
        
        # Initialiser la map des qualités
        self.quality_map = {
            "quality_144p": 144,
            "quality_240p": 240,
            "quality_360p": 360,
            "quality_480p": 480,
            "quality_720p": 720,
            "quality_1080p": 1080,
        }
        
        # Ajouter les options avec icônes
        self.quality_dropdown.addItem(QIcon(self.user_settings.get_icon("144p")), translate("quality_144p"))
        self.quality_dropdown.addItem(QIcon(self.user_settings.get_icon("240p")), translate("quality_240p"))
        self.quality_dropdown.addItem(QIcon(self.user_settings.get_icon("360p")), translate("quality_360p"))
        self.quality_dropdown.addItem(QIcon(self.user_settings.get_icon("480p")), translate("quality_480p"))
        self.quality_dropdown.addItem(QIcon(self.user_settings.get_icon("720p")), translate("quality_720p"))
        self.quality_dropdown.addItem(QIcon(self.user_settings.get_icon("1080p")), translate("quality_1080p"))
        
        # Connecter le signal de changement
        self.quality_dropdown.currentIndexChanged.connect(self.on_quality_changed)
        
    
    def create_right_controls(self):
        right_controls = QWidget()
        right_layout = QHBoxLayout(right_controls)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        for icon_key in ["revert", "revert_back", "fullscreen"]:
            btn = QPushButton()
            btn.clicked.connect(lambda: ComingSoonPopup(self.user_settings).exec())
            btn.setIcon(QIcon(self.user_settings.get_icon(icon_key)))
            btn.setFixedSize(36, 36)
            btn.setCursor(Qt.PointingHandCursor)
            g = self.user_settings.get_color_or_image
            style = self.user_settings.get_style("preview_button").format(g(self.theme['button']['play']),
                                                                          self.theme['button']['border'],
                                                                          g(self.theme['button']['play_hover']))
            btn.setStyleSheet(style)
            right_layout.addWidget(btn)
        
        right_controls.setStyleSheet("background: transparent;")
        return right_controls
    
    def on_preview_slider_moved(self, value):
        if not self.project or self.project.length <= 0:
            return
        percent = value / self.user_settings.loaded_config["slider"]["preview_slider_precision"]
        new_time = percent * self.project.length
        self.parent().parent().timeline.set_playhead_time(new_time)
    def on_aspect_ratio_changed(self, index):
        # Récupérer le texte de l'élément sélectionné
        selected_text = self.aspect_ratio_dropdown.itemText(index)
        
        # Trouver le ratio correspondant
        for key, ratio in self.aspect_ratio_map.items():
            if self.user_settings.translate(key) == selected_text:
                # Mettre à jour le ratio d'aspect du projet
                self.project.aspect_ratio = ratio
                # Mettre à jour la prévisualisation
                self.resize_preview.update_aspect_ratio(ratio[0], ratio[1])
                new_width = int(self.preview_widget.height() * ratio[0] / ratio[1])
                self.preview_widget.setFixedWidth(new_width)
                self.preview_slider_overlay.setGeometry(
                    10,
                    self.preview_widget.height() - 20,
                    self.preview_widget.width() - 20,
                    10
                )
                break
    
    def on_quality_changed(self, index):
        # Récupérer le texte de l'élément sélectionné
        selected_text = self.quality_dropdown.itemText(index)
        
        # Trouver la qualité correspondante
        for key, quality in self.quality_map.items():
            if self.user_settings.translate(key) == selected_text:
                # Mettre à jour la qualité du projet
                self.project.preview_quality = quality
                break
    
    def eventFilter(self, obj, event):
        # Gérer les événements pour l'affichage du slider, etc.
        if obj == self.preview_widget:
            if event.type() == QEvent.Enter:
                self.preview_slider_overlay.show()
                # Positionner le slider en bas de preview_widget
                self.preview_slider_overlay.setGeometry(
                    10,
                    self.preview_widget.height() - 20,
                    self.preview_widget.width() - 20,
                    10
                )
            elif event.type() == QEvent.Leave:
                if not self.preview_slider_overlay.isSliderDown():
                    self.preview_slider_overlay.hide()
        
        return super(PreviewSection, self).eventFilter(obj, event)