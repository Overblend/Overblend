#Sys Imports
import sys,os,json,shutil,datetime

#Overblend Imports
from preview.preview import FrameProducer
from generate_frames import gen_frame as gf
from client import VideoEditor
from user_settings import UserSettings
from const_vars import BUG_REPORT

#PySide6 imports-
from PySide6.QtCore import Qt,QEvent,Signal,QTimer,QObject, QUrl
from PySide6.QtGui import QIcon,QFont,QFontDatabase, QDesktopServices,QShortcut,QKeySequence
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel,QTextEdit, QDialog, 
    QMainWindow, QPushButton, QVBoxLayout, QWidget,QFileDialog
)
#Ui Imports
from ui.preview import PreviewSection
from ui.sidepanel import DynamicPanel
from ui.resizehandles import VerticalResizeHandle, HorizontalResizeHandle
from ui.timeline import TimelineWidget
from ui.sidebar import Sidebar
from ui.topbuttons import TopButtons

class SettingsManager(QObject):
    settingsChanged = Signal(UserSettings)

    def __init__(self, settings):
        super().__init__()
        self._settings = settings

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, new_settings):
        self._settings = new_settings
        self.settingsChanged.emit(new_settings)
class ProjectManager(QObject):
    projectChanged = Signal(object)

    def __init__(self, project=None):
        super().__init__()
        self._project = project

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, value):
        self._project = value
        self.projectChanged.emit(value)

class MainPanel(QWidget):
    def __init__(self, user_settings: UserSettings, project, parent=None):
        super().__init__(parent)

        # === Selection Active ===
        self.selected_clips = set()
        # === Contextes & Thèmes ===
        self.user_settings = user_settings
        self.project = project
        self.theme = user_settings.loaded_theme
        self.dynamic_panel_initialized = False
        self._project_changed = False
        self.preview_playing = False

        self.setStyleSheet(self.user_settings.get_color_or_image(self.theme["preview"]["background"]))

        # === Setup UI global ===
        self.setup_dynamic_panel()
        self.setup_timeline_and_preview()
        self.setup_layouts()
    # --------------------------------------------------------------------
    # 📦 SETUP DES BLOCS PRINCIPAUX
    # --------------------------------------------------------------------
    def setup_dynamic_panel(self):
        self.dynamic_panel = DynamicPanel(self.user_settings)
        self.dynamic_panel.add_placeholder_pages(self.user_settings.buttons)
    def setup_timeline_and_preview(self):
        self.preview = PreviewSection(self.user_settings, self.project)
        self.timeline = TimelineWidget(self.user_settings, self.project, self)
        self.timeline.play_pause_btn.clicked.connect(self.toggle_preview_playback)

    def setup_layouts(self):
        # === Layout du haut (dynamic_panel + preview)
        self.top_row = QWidget()
        top_row_layout = QHBoxLayout(self.top_row)
        top_row_layout.setContentsMargins(0, 0, 0, 0)
        top_row_layout.setSpacing(0)

        self.vertical_handle = VerticalResizeHandle(self.dynamic_panel, self.preview, self.user_settings)
        self.vertical_handle.setVisible(False)

        top_row_layout.addWidget(self.dynamic_panel)
        top_row_layout.addWidget(self.vertical_handle)
        top_row_layout.addWidget(self.preview, 1)

        # === Handle entre preview et timeline
        self.resize_handle = HorizontalResizeHandle(self.top_row, self.timeline, self.user_settings)

        # === Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.top_row, 4)
        layout.addWidget(self.resize_handle)
        layout.addWidget(self.timeline, 1)

    def toggle_preview_playback(self):
        self.timeline.play_pause_btn.setIcon(QIcon(self.user_settings.get_icon("play" if self.preview_playing else "pause")))
        self.preview_playing = not self.preview_playing
    # --------------------------------------------------------------------
    # 🧠 LOGIQUE UI : SLIDER, RÉSIZER, PANEL
    # --------------------------------------------------------------------

    def update_preview_slider(self):
        precision = self.user_settings.loaded_config["slider"]["preview_slider_precision"]
        percent = self.timeline.playhead_time / self.project.length
        self.preview.preview_slider_overlay.blockSignals(True)
        self.preview.preview_slider_overlay.setValue(int(percent * precision))
        self.preview.preview_slider_overlay.blockSignals(False)

    def on_preview_slider_moved(self, value):
        if not self.project or self.project.length <= 0:
            return
        percent = value / self.user_settings.loaded_config["slider"]["preview_slider_precision"]
        new_time = percent * self.project.length
        self.timeline.set_playhead_time(new_time)

    def resizeEvent(self, event):
        self._cached_pixels_per_second = None
        self.top_row.setFixedHeight(self.height() // 2)
    
        if self.dynamic_panel.isVisible() and self.dynamic_panel_initialized:
            total_width = self.width()
            self.dynamic_panel.setFixedWidth(int(total_width * 0.5) - self.vertical_handle.width())

        super().resizeEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.preview_widget:
            slider = self.preview_slider_overlay
            if hasattr(self, 'resize_handle') and event.type() == QEvent.Resize and obj == self.preview_widget.parent():
                # Positionner le gestionnaire de redimensionnement en bas à droite
                self.resize_handle.move(self.preview_widget.width() - self.resize_handle.width(),
                                    self.preview_widget.height() - self.resize_handle.height())
            elif event.type() == QEvent.Enter:
                slider.show()
            elif event.type() == QEvent.Leave:
                slider.hide()
            elif event.type() == QEvent.Resize:
                # Positionner le slider en bas avec padding
                slider_width = self.preview_widget.width()
                side_padding = 10
                bottom_padding = 10

                slider.setFixedWidth(slider_width - 2 * side_padding)
                slider.move(side_padding, self.preview_widget.height() - 18 - bottom_padding)

                slider.raise_()
        return super().eventFilter(obj, event)
    

    def update_dynamic_panel_width(self):
            total_width = self.width()
            self.dynamic_panel.setFixedWidth(int(total_width * 0.5) - self.vertical_handle.width())

    def toggle_dynamic_panel(self, visible: bool):
        self.dynamic_panel.setVisible(visible)
        self.vertical_handle.setVisible(visible)
        if visible and not self.dynamic_panel_initialized:
            self.update_dynamic_panel_width()
            self.dynamic_panel_initialized = True

    def force_show_preview_slider(self):
        self.preview.preview_slider_overlay.show()

    def force_hide_preview_slider(self):
        self.preview.preview_slider_overlay.hide()


class OverlayMenu(QDialog): 
    def __init__(self, parent: QMainWindow, user_settings, project_manager):
        super().__init__(parent)
        self.user_settings = user_settings
        self.project_manager = project_manager
        self.theme = user_settings.loaded_theme

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setModal(True)
        self.setFixedSize(300, 350)
        self.add_corner_borders()
        self.setStyleSheet(self.user_settings.get_style("menu").format(self.user_settings.get_color_or_image(self.theme["menu"]["background"])))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.add_header(layout)
        self.add_action_buttons(layout)
        self._install_click_outside_filter()
    def add_corner_borders(self):
        # Bord en haut à gauche
        top_left = QFrame(self)
        top_left.setGeometry(0, 0, 80, 4)
        top_left.setStyleSheet(self.user_settings.get_style("top_left_menu_border").format(self.theme["menu"]["border"]))

        left_side = QFrame(self)
        left_side.setGeometry(0, 0, 4, 80)
        left_side.setStyleSheet(self.user_settings.get_style("left_side_menu_border").format(self.theme["menu"]["border"]))

        # Bord en bas à droite
        bottom_right = QFrame(self)
        bottom_right.setGeometry(self.width() - 80, self.height() - 4, 80, 4)
        bottom_right.setStyleSheet(self.user_settings.get_style("bottom_right_menu_border").format(self.theme["menu"]["border"]))
        bottom_right.raise_()

        right_side = QFrame(self)
        right_side.setGeometry(self.width() - 4, self.height() - 80, 4, 80)
        right_side.setStyleSheet(self.user_settings.get_style("right_side_menu_border").format(self.theme["menu"]["border"]))
        right_side.raise_()

        # Pour repositionner si le menu change de taille (sécurité)
        def adjust_positions():
            bottom_right.move(self.width() - 80, self.height() - 4)
            right_side.move(self.width() - 4, self.height() - 80)

        self.resizeEvent = lambda event: adjust_positions()

    def add_header(self, layout):
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(32, 32))
        logo.setFixedSize(32, 32)

        title = QLabel("OVERBLEND")
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-weight: bold; font-size: 18px;")
        title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Bouton "Menu principal"
        menu_btn = QPushButton("Menu")
        menu_btn.setCursor(Qt.PointingHandCursor)
        menu_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['accent']['primary']};
                border: none;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {self.theme['accent']['primary_hover']};
                text-decoration: underline;
            }}
        """)
        menu_btn.clicked.connect(self.return_to_menu)
        header_layout.addWidget(menu_btn)

        layout.addWidget(header)

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self.theme['menu']['separator']};")
        layout.addWidget(separator)
    def return_to_menu(self):
        self.close()
        if self.parent():
            self.parent().close()

            from home import HomeWindow  # 🔁 Import ici pour éviter les boucles
            home = HomeWindow(self.user_settings)
            home.showMaximized()

    def add_action_buttons(self, layout):
        actions = {
            "new": self.create_new_project,
            "open": self.open_project,  # 👈 nouveau
            "save": self.save_project,
            "save_as": self.save_project_as,
            #"change_theme": self.change_theme,
            "report_bug": self.report_bug
        }


        for label, callback in actions.items():
            btn = QPushButton(self.user_settings.translate(label))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(
                self.user_settings.get_style("menu_button").format(
                    self.user_settings.get_color_or_image(self.theme["button"]["default"]),
                    self.theme["text"]["default"],
                    self.user_settings.get_color_or_image(self.theme["button"]["hover"])
                )
            )
            btn.clicked.connect(callback)
            layout.addWidget(btn)
    def show_at_center_of(self, parent: QMainWindow):
        center = parent.geometry().center()
        self.move(center - self.rect().center())
        self.exec()
    def create_new_project(self):
        filename = "untitled.json"
        new_project = VideoEditor(filename)
        self.project_manager.project = new_project
        self.close()
    def open_project(self):
        dialog = QFileDialog(self.parent())
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("JSON Files (*.json)")
        dialog.setWindowTitle("Open Project File")

        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                path = selected_files[0]
                try:
                    project = VideoEditor(path)
                    self.project_manager.project = project
                    print(f"[INFO] Projet chargé depuis : {path}")
                    self.close()
                except Exception as e:
                    print(f"[ERROR] Échec du chargement du projet : {e}")
        else:
            print("[INFO] Open annulé par l'utilisateur.")

    def save_project(self):
        parent = self.parent()

        if os.path.basename(self.project_manager.project.filename) == "untitled.json":
            self.save_project_as()
            return

        success = self.project_manager.project.save()

        if success and isinstance(parent, OverblendEditor):
            parent.show_toast(os.path.basename(self.project_manager.project.filename) + " " + self.user_settings.translate("save_success"))
        
        self.close()


    def save_project_as(self):
        project = self.project_manager.project
        success = project.save()

        if success:
            dialog = QFileDialog(self.parent())
            dialog.setAcceptMode(QFileDialog.AcceptSave)
            dialog.setNameFilter("JSON Files (*.json)")
            dialog.setDefaultSuffix("json")
            dialog.setWindowTitle("Save Project As")
            dialog.setFileMode(QFileDialog.AnyFile)

            if dialog.exec():
                selected_files = dialog.selectedFiles()
                if selected_files:
                    path = selected_files[0]
                    try:
                        project.save()
                        shutil.copy(project.filename, path)
                        project.filename = path
                        project.save()

                        # ✅ Notifie le nouveau chemin
                        self.project_manager.project = project

                        print(f"[INFO] Projet sauvegardé sous : {path}")
                        self.close()
                    except Exception as e:
                        print(f"[ERROR] Save As a échoué : {e}")
            else:
                print("[INFO] Save As annulé par l'utilisateur.")


    def change_theme(self):
        print("TODO: change theme")
        self.close()
    def report_bug(self):
        parent = self.parent()
        if isinstance(parent, OverblendEditor):
            parent.show_toast("Ouverture du formulaire...")

        QDesktopServices.openUrl(QUrl(BUG_REPORT))
        QTimer.singleShot(1000, self.close)



    def _install_click_outside_filter(self):
        def close_if_outside(event):
            if not self.geometry().contains(event.globalPosition().toPoint()):
                self.close()
                QApplication.instance().removeEventFilter(self._filter_obj)

        class ClickFilter(QObject):
            def eventFilter(_, __, event):
                if event.type() == QEvent.MouseButtonPress:
                    close_if_outside(event)
                return False

        self._filter_obj = ClickFilter()
        QApplication.instance().installEventFilter(self._filter_obj)
class UnsavedChangesDialog(QDialog):
    def __init__(self, parent, user_settings, project, on_save, on_discard):
        super().__init__(parent)
        self.user_settings = user_settings
        self.project = project
        self.on_save = on_save
        self.on_discard = on_discard

        self.theme = user_settings.loaded_theme

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 200)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # === Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(28, 28))
        logo.setFixedSize(28, 28)

        title = QLabel("OVERBLEND")
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        # === Séparateur
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {self.theme['menu']['separator']};")
        layout.addWidget(sep)

        # === Message principal
        msg = QLabel(self.user_settings.translate("unsaved_changes").format(os.path.basename(self.project.filename)))
        msg.setStyleSheet(self.user_settings.get_style("unsaved_changes_text").format(self.theme["text"]["highlight"]))
        msg.setWordWrap(True)
        layout.addWidget(msg)

        # === Boutons
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        style = self.user_settings.get_style("button").format(
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme['button']['default']),
            self.theme['button']['border'],
            self.user_settings.get_color_or_image(self.theme['button']['hover']),
            self.theme['accent']['primary']
        )

        save_btn = QPushButton(self.user_settings.translate("save"))
        save_btn.setStyleSheet(style)
        save_btn.clicked.connect(lambda: (self.accept(), self.on_save()))

        discard_btn = QPushButton(self.user_settings.translate("dont_save"))
        discard_btn.setStyleSheet(style)
        discard_btn.clicked.connect(lambda: (self.accept(), self.on_discard()))

        cancel_btn = QPushButton(self.user_settings.translate("cancel"))
        cancel_btn.setStyleSheet(style)
        cancel_btn.clicked.connect(self.reject)
        
        self.add_corner_borders()

        buttons.addWidget(save_btn)
        buttons.addWidget(discard_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        self.setStyleSheet(self.user_settings.get_style("unsaved_changes").format(self.user_settings.get_color_or_image(self.theme["code_viewer"]["background"])))
    def add_corner_borders(self):
        top_left = QFrame(self)
        top_left.setGeometry(0, 0, 80, 4)
        top_left.setStyleSheet("background-color: white; border-top-left-radius: 6px;")

        left_side = QFrame(self)
        left_side.setGeometry(0, 0, 4, 80)
        left_side.setStyleSheet("background-color: white; border-top-left-radius: 6px;")

        bottom_right = QFrame(self)
        bottom_right.setGeometry(self.width() - 80, self.height() - 4, 80, 4)
        bottom_right.setStyleSheet("background-color: white; border-bottom-right-radius: 6px;")
        bottom_right.raise_()

        right_side = QFrame(self)
        right_side.setGeometry(self.width() - 4, self.height() - 80, 4, 80)
        right_side.setStyleSheet("background-color: white; border-bottom-right-radius: 6px;")
        right_side.raise_()

        def adjust():
            bottom_right.move(self.width() - 80, self.height() - 4)
            right_side.move(self.width() - 4, self.height() - 80)

        self.resizeEvent = lambda event: adjust()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
class OverblendEditor(QMainWindow):
    def __init__(self, settings_manager: SettingsManager, project_manager: ProjectManager):
        super().__init__()

        # === Stockage des managers ===
        self.settings_manager = settings_manager
        self.project_manager = project_manager

        # === Données actuelles ===
        self.user_settings = self.settings_manager.settings
        self.project = self.project_manager.project

        # === Fenêtre principale ===
        filename = os.path.basename(self.project.filename or "untitled.json")
        self.setWindowTitle(f"Overblend - {filename}")
        self.setWindowIcon(self.user_settings.get_icon("logo"))
        self.resize(
            self.user_settings.loaded_config["ui"]["window_width"],
            self.user_settings.loaded_config["ui"]["window_height"]
        )

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {self.user_settings.loaded_theme['background']['main']};")
        # === Connexions aux changements dynamiques ===
        self.settings_manager.settingsChanged.connect(self.on_settings_changed)
        self.project_manager.projectChanged.connect(self.on_project_changed)

        # === Initialisation de l'interface ===
        self.setup_autosave()   
        self.update_recent_projects()
        self.setup_ui()
        self.setup_shortcuts()

    # --------------------------------------------------------------------
    # 🔁 RECHARGEMENT UI dynamique
    # --------------------------------------------------------------------
    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.trigger_new_project)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.trigger_open_project)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.trigger_save_project)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self).activated.connect(self.trigger_save_project_as)
    
    def setup_autosave(self):
        try:
            self._autosave_timer.stop()
        except AttributeError:
            from PySide6.QtCore import QTimer
            self._autosave_timer = QTimer()
            self._autosave_timer.timeout.connect(self.trigger_save_project)

        config = self.user_settings.loaded_config.get("autosave", {})
        active = config.get("active", False)
        interval = config.get("interval", 5)  # en minutes

        if active and (os.path.basename(self.project.filename) not in ["untitled.json",""]):
            self._autosave_timer.start(interval * 60 * 1000)
        else:
            self._autosave_timer.stop()


    def trigger_new_project(self):
        new = VideoEditor("untitled.json")
        self.project_manager.project = new

    def trigger_open_project(self):
        menu = OverlayMenu(self, self.user_settings, self.project_manager)
        menu.open_project()

    def trigger_save_project(self):
        filename = os.path.basename(self.project_manager.project.filename or "")
        # Si nom == untitled.json → Save As
        if filename == "untitled.json":
            self.trigger_save_project_as()
            return

        # Sinon sauvegarde normalement
        self.project_manager.project.save()
        self.show_toast(filename + " " + self.user_settings.translate("save_success"))

    def trigger_save_project_as(self):
        menu = OverlayMenu(self, self.user_settings, self.project_manager)
        menu.save_project_as()

    def on_settings_changed(self, new_settings):
        self.user_settings = new_settings
        self.setup_ui()

    def on_project_changed(self, new_project):
        self.project = new_project
        filename = os.path.basename(self.project.filename or "untitled.json")
        self.setWindowTitle(f"Overblend - {filename}")
        self.setup_ui()
        self.update_recent_projects()

    
    def update_recent_projects(self):
        path = self.project.filename
        if not path:
            return
        def get_projects_path():
            appdata = os.getenv('APPDATA')
            if not appdata:
                raise Exception("APPDATA environment variable not found. Are you on Windows?")
            
            overblend_folder = os.path.join(appdata, 'Overblend')
            
            # Créer le dossier si jamais il n'existe pas
            if not os.path.exists(overblend_folder):
                os.makedirs(overblend_folder)
            
            return os.path.join(overblend_folder, 'projects.json')

        projects_path = get_projects_path()
        try:
            from tools.json_utils import safe_load_json
            def get_projects_path():
                appdata = os.getenv('APPDATA')
                if not appdata:
                    raise Exception("APPDATA environment variable not found. Are you on Windows?")
                
                overblend_folder = os.path.join(appdata, 'Overblend')
                
                # Créer le dossier si jamais il n'existe pas
                if not os.path.exists(overblend_folder):
                    os.makedirs(overblend_folder)
                
                return os.path.join(overblend_folder, 'projects.json')

            if os.path.exists(projects_path):
                projects = safe_load_json(get_projects_path())
            else:
                projects = []

            # Chercher un projet avec le même path
            existing = next((p for p in projects if p["path"] == path), None)

            if existing:
                existing["last_opened"] = datetime.datetime.now().isoformat()
            else:
                projects.append({
                    "path": path,
                    "last_opened": datetime.datetime.now().isoformat(),
                    "type": "Video Editor Project"
                })

            # Écrire dans le fichier
            with open(projects_path, "w", encoding="utf-8") as f:
                json.dump(projects, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"[ERROR] Échec lors de l'enregistrement du projet dans projects.json : {e}")
    # --------------------------------------------------------------------
    # 🧠 MISE EN PLACE DE L'INTERFACE
    # --------------------------------------------------------------------
    def setup_ui(self):
        # 🔄 Nettoyer l'ancien contenu
        old_central = self.centralWidget()
        if old_central:
            old_central.setParent(None)
            old_central.deleteLater()

        # 📦 Créer le widget principal
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 📁 Barre latérale
        self.sidebar = Sidebar(self.user_settings,OverlayMenu)
        for button in self.sidebar.buttons:
            button.clicked.connect(lambda checked, b=button: self.set_active_button(b))
        layout.addWidget(self.sidebar)

        # 🧩 Panneau principal
        self.main_panel = MainPanel(self.user_settings, self.project)
        layout.addWidget(self.main_panel, 1)

        # 🔝 Boutons flottants en haut
        self.top_buttons = TopButtons(self.user_settings, self)
        
        

        self.setCentralWidget(central)

        self.top_buttons.setParent(self)
        self.top_buttons.raise_()
        self.top_buttons.show()
        self.top_buttons.move(self.width() - self.top_buttons.width() - 10, 0)

    # --------------------------------------------------------------------
    # 📌 INTERACTIONS UI : Sidebar → DynamicPanel
    # --------------------------------------------------------------------
    def set_active_button(self, active_btn):
        key = next((k for k, b in zip(self.user_settings.buttons, self.sidebar.buttons) if b == active_btn), None)

        already_active = not active_btn.isChecked()

        # Met à jour l’état de tous les boutons
        for btn in self.sidebar.buttons:
            btn.setChecked(False)

        if already_active:
            # Si déjà actif → désactiver le panel
            self.main_panel.dynamic_panel.setVisible(False)
            self.main_panel.vertical_handle.setVisible(False)
        else:
            # Sinon → afficher le bon panel
            active_btn.setChecked(True)
            self.main_panel.dynamic_panel.show_page(key[0])
            self.main_panel.toggle_dynamic_panel(True)


    # --------------------------------------------------------------------
    # 📣 TOAST / NOTIFICATIONS
    # --------------------------------------------------------------------
    def show_toast(self, message: str, duration: int = 2000):
        self._show_colored_toast(message, "rgba(50, 50, 50, 220)", duration)

    def show_warning(self, message: str, duration: int = 2500):
        self._show_colored_toast(message, "#f39c12", duration)

    def _show_colored_toast(self, message: str, bg_color: str, duration: int):
        toast = QLabel(message, self)
        toast.setStyleSheet(f"""
            background-color: {bg_color};
            color: white;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
        """)
        toast.adjustSize()
        toast.move(
            (self.width() - toast.width()) // 2,
            (self.height() - toast.height()) // 2
        )
        toast.show()
        QTimer.singleShot(duration, toast.deleteLater)

    # --------------------------------------------------------------------
    # ❌ DIALOGUE D'ERREUR STYLISÉ
    # --------------------------------------------------------------------
    def show_error(self, title: str, detail: str):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setModal(True)
        dialog.setFixedSize(400, 280)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Header avec logo + titre
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(28, 28))
        logo.setFixedSize(28, 28)

        title_label = QLabel("OVERBLEND")
        title_label.setStyleSheet("color: white; font-size: 17px; font-weight: bold;")
        header_layout.addWidget(logo)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addWidget(header)

        # --- Séparateur
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #555;")
        layout.addWidget(separator)

        # --- Titre de l'erreur
        main_msg = QLabel(title)
        main_msg.setStyleSheet("font-size: 15px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(main_msg)

        # --- Détail technique
        detail_box = QTextEdit()
        detail_box.setText(detail)
        detail_box.setReadOnly(True)
        detail_box.setStyleSheet("""
            background-color: #2f2f2f;
            color: #f1f1f1;
            border-radius: 6px;
            font-size: 13px;
        """)
        layout.addWidget(detail_box)

        # --- Boutons : Send bug + OK
        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        report_btn = QPushButton("Send bug report")
        report_btn.setCursor(Qt.PointingHandCursor)
        report_btn.setStyleSheet("background-color: #3b49fc; color: white; border-radius: 6px; padding: 6px 12px;")
        report_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(BUG_REPORT)))

        ok_btn = QPushButton("OK")
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.setStyleSheet("background-color: #444; color: white; border-radius: 6px; padding: 6px 12px;")
        ok_btn.clicked.connect(dialog.close)

        buttons.addWidget(report_btn)
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        layout.addLayout(buttons)

        dialog.setStyleSheet("background-color: rgba(30, 30, 30, 240); border-radius: 12px;")
        self._add_error_dialog_borders(dialog)
        dialog.exec()

    def _add_error_dialog_borders(self, dialog):
        top_left = QFrame(dialog)
        top_left.setGeometry(0, 0, 80, 4)
        top_left.setStyleSheet("background-color: white; border-top-left-radius: 6px;")

        left_side = QFrame(dialog)
        left_side.setGeometry(0, 0, 4, 80)
        left_side.setStyleSheet("background-color: white; border-top-left-radius: 6px;")

        bottom_right = QFrame(dialog)
        bottom_right.setGeometry(dialog.width() - 80, dialog.height() - 4, 80, 4)
        bottom_right.setStyleSheet("background-color: white; border-bottom-right-radius: 6px;")
        bottom_right.raise_()

        right_side = QFrame(dialog)
        right_side.setGeometry(dialog.width() - 4, dialog.height() - 80, 4, 80)
        right_side.setStyleSheet("background-color: white; border-bottom-right-radius: 6px;")
        right_side.raise_()

        def adjust_positions():
            bottom_right.move(dialog.width() - 80, dialog.height() - 4)
            right_side.move(dialog.width() - 4, dialog.height() - 80)

        dialog.resizeEvent = lambda event: adjust_positions()

    # --------------------------------------------------------------------
    # ❓ OUI / NON Dialog
    # --------------------------------------------------------------------
    def show_yes_or_no(self, message: str, yes_callback, no_callback=None):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        dialog.setModal(True)
        dialog.setFixedSize(300, 150)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        label = QLabel(message)
        label.setStyleSheet("font-size: 14px; color: white;")
        label.setWordWrap(True)
        layout.addWidget(label)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)

        yes_btn = QPushButton("Oui")
        yes_btn.setStyleSheet("background-color: #27ae60; color: white; border-radius: 6px; padding: 6px 12px;")
        yes_btn.clicked.connect(lambda: (dialog.close(), yes_callback()))

        no_btn = QPushButton("Non")
        no_btn.setStyleSheet("background-color: #c0392b; color: white; border-radius: 6px; padding: 6px 12px;")
        no_btn.clicked.connect(lambda: (dialog.close(), no_callback() if no_callback else None))

        buttons.addWidget(yes_btn)
        buttons.addWidget(no_btn)
        layout.addLayout(buttons)

        dialog.setStyleSheet("background-color: #2c2c2c; border-radius: 12px;")
        dialog.exec()

    # --------------------------------------------------------------------
    # 📐 Adaptation de la position des TopButtons
    # --------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.top_buttons.move(self.width() - self.top_buttons.width() - 10, 0)
    #
    def closeEvent(self, event):
        try:
            if not self.project or not self.project.filename or not os.path.exists(self.project.filename):
                return super().closeEvent(event)

            with open(self.project.filename, "r", encoding="utf-8") as f:
                original_data = json.load(f)

            if self.project.project != original_data:
                def save_then_close():
                    self.project.save()
                    event.accept()

                def discard_then_close():
                    event.accept()

                dialog = UnsavedChangesDialog(self, self.user_settings, self.project, save_then_close, discard_then_close)
                if dialog.exec() != QDialog.Accepted:
                    event.ignore()
            else:
                super().closeEvent(event)

        except Exception as e:
            print(f"[ERROR] Échec du check de fermeture : {e}")
            super().closeEvent(event)



if __name__ == "__main__" : 
    app = QApplication(sys.argv)
    
    user_settings = UserSettings()
    settings_manager = SettingsManager(user_settings)

    project = VideoEditor(user_settings.loaded_config["on_start_file"])
    project_manager = ProjectManager(project)

    editor = OverblendEditor(settings_manager, project_manager)
    editor.showMaximized()
    sys.exit(app.exec())
