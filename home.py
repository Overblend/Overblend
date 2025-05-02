from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt
import os,sys

# Early minimal imports
import tools.updater as updater
from ui.update_popup import UpdatePopup

# ✅ Step 0: Initialize QApplication first!
app = QApplication.instance() or QApplication(sys.argv)

# ✅ Now you can safely import and use graphical elements
from ui.loading import LoadingPopup
from user_settings import UserSettings

# Rest of your loading steps...
user_settings = UserSettings()

# Drapeau pour indiquer si une mise à jour a été démarrée
update_started = False

# === Vérification de mise à jour ===
try:
    if updater.needs_update():
        popup = UpdatePopup(user_settings)
        
        def start_update():
            global update_started
            update_started = True  # Marquer que la mise à jour a été démarrée
            popup.close()
            
            QApplication.processEvents()
            loading = LoadingPopup(user_settings)
            loading.show()
            
            # Désactiver la fermeture de la fenêtre pendant le téléchargement
            loading.setWindowFlag(Qt.WindowCloseButtonHint, False)

            def download_thread():
                try:
                    updater.get_latest_version()
                    QApplication.exit(0)  # Force l'application à se terminer après mise à jour
                except Exception as e:
                    print(f"Download failed: {e}")
                    loading.close()

            import threading
            thread = threading.Thread(target=download_thread, daemon=True)
            thread.start()

            # ➔ Utiliser un QTimer pour surveiller la progression sans bloquer l'UI
            def refresh_progress():
                progress = updater.get_download_progress() or 0
                loading.set_progress(progress, f"Téléchargement de la mise à jour... {progress}%")
                
                # Si le thread est terminé et que nous sommes à 100%, on arrête le timer
                if not thread.is_alive() and progress >= 100:
                    timer.stop()

            timer = QTimer()
            timer.timeout.connect(refresh_progress)
            timer.start(100)  # rafraîchit toutes les 100ms

        popup.no_btn.clicked.connect(popup.close)
        popup.yes_btn.clicked.connect(start_update)

        # Exécuter le dialogue de mise à jour et attendre sa fermeture
        popup.exec()
        
        # Si la mise à jour a été démarrée, on attend la fin du processus et on quitte
        if update_started:
            app.exec()  # Démarrer la boucle d'événements et attendre la fin
            sys.exit(0)  # Sortir complètement une fois la mise à jour terminée

except Exception as e:
    print(f"[WARNING] Update check failed: {e}")
popup = LoadingPopup(user_settings)
popup.show()
QApplication.processEvents()

# === STEP 1: Qt Core & Gui
popup.set_progress(10, "Loading Qt Core & Gui")
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap
QApplication.processEvents()

# === STEP 2: Qt Widgets
popup.set_progress(25, "Loading Qt Widgets")
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QFrame, QGridLayout, QSizePolicy, QMainWindow,
    QComboBox, QFileDialog
)
QApplication.processEvents()

# === STEP 3: Standard Libraries
popup.set_progress(50, "Loading Python Modules")
import subprocess
import platform
import os
import json
from datetime import datetime
from tools.json_utils import safe_load_json 
QApplication.processEvents()

# === STEP 4: Overblend Modules
popup.set_progress(75, "Loading Overblend Modules")
from editor import OverblendEditor, ProjectManager, SettingsManager, VideoEditor
from ui.coming_soon import ComingSoonPopup
QApplication.processEvents()

# === STEP 5: Done
popup.set_progress(100, "Ready!")
QTimer.singleShot(500, popup.close)  # Give time to see 100%

# === Run all steps
# Vérification du premier lancement
first_run_path = os.path.join(os.getenv("APPDATA", ""), "Overblend", "first_run.txt")
if not os.path.exists(first_run_path):
    from PySide6.QtWidgets import QMessageBox
    os.makedirs(os.path.dirname(first_run_path), exist_ok=True)

    message = (
        "Bienvenue sur Overblend.\n\n"
        "Vous utilisez actuellement une version bêta très préliminaire de l'application.\n"
        "À ce stade, de nombreuses fonctionnalités restent à implémenter, et l'expérience utilisateur est en cours d'amélioration continue.\n\n"
        "Nous travaillons activement pour enrichir Overblend avec de nouvelles fonctionnalités, stabiliser les performances et offrir l'outil de montage vidéo le plus fluide et moderne possible.\n\n"
        "Cette version a pour but de vous permettre d'avoir un premier aperçu de l'interface et du concept général.\n\n"
        "Merci de votre patience et de votre soutien.\n"
        "Les mises à jour viendront progressivement au fil des prochaines semaines.\n" 
        "Moaad Barkache."
    )
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("Bienvenue sur Overblend")
    msg.setText(message)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec()

    with open(first_run_path, "w", encoding="utf-8") as f:
        f.write("This file marks the first launch of Overblend.")


class HomeWindow(QMainWindow):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.setWindowIcon(user_settings.get_icon("logo"))
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.user_settings = user_settings
        self.theme = self.user_settings.loaded_theme
        

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"background-color: {self.theme['background']['main']};")
        # Create all sections
        self.setup_header()
        self.setup_main_content()
        self.setup_footer()
        
        # Add sections to main layout
        main_layout.addWidget(self.header)
        main_layout.addWidget(self.main_content, 1)
        main_layout.addWidget(self.footer)


    def open_main_editor(self, project_path=None):
        popup = LoadingPopup(self.user_settings)
        popup.show()
        popup.raise_()
        QApplication.processEvents()

        def step1():
            popup.set_progress(10, "Loading project...")
            QApplication.processEvents()
            QTimer.singleShot(700, step2)

        def step2():
            if project_path:
                project = VideoEditor(project_path)
            else:
                project = VideoEditor()
            self.project = project
            popup.set_progress(40, "Project loaded.")
            QApplication.processEvents()
            QTimer.singleShot(700, step3)

        def step3():
            popup.set_progress(60, "Launching editor...")
            self.close()
            QApplication.processEvents()
            QTimer.singleShot(700, step4)

        def step4():
            project_manager = ProjectManager(self.project)
            settings_manager = SettingsManager(self.user_settings)
            self.editor = OverblendEditor(settings_manager, project_manager)
            popup.set_progress(90, "Almost done...")
            QApplication.processEvents()
            QTimer.singleShot(700, finalize)

        def finalize():
            self.editor.showMaximized()
            popup.set_progress(100, "Done")
            popup.close()

        step1()

    def handle_open_project(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("JSON Files (*.json)")
        dialog.setWindowTitle("Open Project File")

        if dialog.exec():
            selected_files = dialog.selectedFiles()
            if selected_files:
                self.open_main_editor(selected_files[0])
    


    def sanitize_recent_projects(self):
        def get_projects_path():
            appdata = os.getenv('APPDATA')
            if not appdata:
                raise Exception("APPDATA environment variable not found. Are you on Windows?")
            
            overblend_folder = os.path.join(appdata, 'Overblend')
            
            # Créer le dossier si jamais il n'existe pas
            if not os.path.exists(overblend_folder):
                os.makedirs(overblend_folder)
            
            return os.path.join(overblend_folder, 'projects.json')
        path = get_projects_path()
        if not os.path.exists(path):
            return

        try:
            
            projects = safe_load_json(path)

            updated_projects = []
            for p in projects:
                if os.path.exists(p.get("path", "")):
                    updated_projects.append(p)

            if len(updated_projects) != len(projects) and len(projects) != 0 :
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(updated_projects, f, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"[ERROR] Failed to sanitize recent projects: {e}")
    def delete_project_file(self, path):
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"[INFO] Deleted: {path}")
            self.sanitize_recent_projects()
            self.refresh_ui()
        except Exception as e:
            print(f"[ERROR] Failed to delete project: {e}")

    #  UI SETUP OF MAIN SECTIONS   
    def setup_header(self):
        # Header section with logo and welcome text
        self.header = QWidget()
        self.header.setFixedHeight(100)
        self.header.setObjectName("header")
        self.header.setStyleSheet(f"""QWidget#header{{ 
            background-color: {self.theme['background']['panel']};
            border-bottom: 1px solid white ;
        }}""")
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(40, 20, 40, 20)
        header_layout.setSpacing(10)
        
        # Logo and app name
        logo_layout = QHBoxLayout()
        
        logo = QLabel()
        logo_pixmap = QPixmap(self.user_settings.get_icon("logo", True))
        logo.setPixmap(logo_pixmap.scaled(QSize(40, 40), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        app_name = QLabel("OVERBLEND")
        app_name.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 24px; font-weight: bold;")
        
        logo_layout.addWidget(logo)
        logo_layout.addWidget(app_name)
        logo_layout.addStretch()
        
        self.lang_selector = QComboBox()
        self.lang_selector.addItems(self.user_settings.available_langs)
        self.lang_selector.setCurrentText(self.user_settings.loaded_config.get("lang", "en"))
        self.lang_selector.setFixedWidth(80)
        self.lang_selector.setStyleSheet(f"""
            QComboBox {{
                background-color: {self.theme['background']['hover']};
                color: {self.theme['text']['default']};
                font-size: 13px;
                padding: 4px 8px;
                border: 1px solid {self.theme['container']['border']};
                border-radius: 6px;
            }}
            QComboBox:hover {{
                background-color: {self.theme['background']['tertiary']};
            }}
        """)

        self.lang_selector.currentTextChanged.connect(self.change_language)

        header_layout.addLayout(logo_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.lang_selector)
        
    def setup_main_content(self):
        # Main content area with split layout
        
        self.main_content = QWidget()
        self.main_content.setStyleSheet(f"background-color: {self.theme['background']['secondary']}")
        
        main_layout = QHBoxLayout(self.main_content)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)
        
        # Left side (Projects)
        left_panel = QWidget()
        left_panel.setObjectName("projects")
        left_panel.setStyleSheet(f""" QWidget#projects {{ 
            background-color: {self.theme['background']['panel']};
            border-radius: 12px;
            border: 1px solid {self.theme['container']['border']};
        }} """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(25, 25, 25, 25)
        left_layout.setSpacing(20)
        
        # Projects header
        projects_header = QHBoxLayout()
        projects_title = QLabel(self.user_settings.translate("recent_projects"))
        projects_title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 18px; font-weight: bold;")
        projects_header.addWidget(projects_title)
        projects_header.addStretch()
        
        # Projects separator
        projects_separator = QFrame()
        projects_separator.setFrameShape(QFrame.HLine)
        projects_separator.setStyleSheet(f"background-color: {self.theme['container']['border']}; max-height: 1px;")
        
        # Projects grid
        self.setup_projects_grid(left_layout)
        
        # Projects actions
        projects_actions = QHBoxLayout()
        projects_actions.setSpacing(10)
        
        open_btn = self.create_action_button(self.user_settings.translate("open_project"))
        new_btn = self.create_action_button(self.user_settings.translate("new_project"))
        
        open_btn.clicked.connect(self.handle_open_project)
        new_btn.clicked.connect(lambda: self.open_main_editor(None))

        projects_actions.addWidget(open_btn)
        projects_actions.addWidget(new_btn)
        
        left_layout.insertLayout(0, projects_header)
        left_layout.insertWidget(1, projects_separator)
        left_layout.addLayout(projects_actions)
        
        
        # Automation section
        automation_card = self.create_automation_card()

        # Toolkits card (en haut maintenant)
        toolkits_card = self.create_section_card("Toolkits")
        self.setup_toolkits_section(toolkits_card)


        
        # Add panels to main layout
        center_container = QWidget()
        center_layout = QHBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(12)  

        center_layout.addWidget(left_panel, 1)
        center_layout.addWidget(automation_card, 1)
        center_layout.addWidget(toolkits_card, 1)

        
        main_layout.addWidget(center_container)

    def setup_toolkits_section(self, card):
        content_layout = QVBoxLayout()
        card.layout().addLayout(content_layout)
        
        # Description de la section
        description = QLabel(self.user_settings.translate("browse_toolkit_desc"))
        description.setStyleSheet(f"""
            color: {self.theme['text']['sidebar']};
            background: transparent;
            font-size: 13px;
            margin-bottom: 10px;
        """)

        description.setWordWrap(True)
        content_layout.addWidget(description)
        content_layout.addSpacing(5)
        
        # Toolkits grid avec un design moderne
        toolkits = [
            {
                "name": self.user_settings.translate("video_effects"), 
                "count": "0 items", 
                "description": self.user_settings.translate("video_effects_desc")
            },
            {
                "name": self.user_settings.translate("text_animations"),
                "count": "0 items", 
                "description": self.user_settings.translate("text_animations_desc")
            },
            {
                "name": self.user_settings.translate("color_grading"), 
                "count": "0 presets", 
                "description": self.user_settings.translate("color_grading_desc")
            },
            {
                "name": self.user_settings.translate("sound_fx"),
                "count": "0 items", 
                "description": self.user_settings.translate("sound_fx_desc")
            }
        ]
        
        # Container pour les cartes de toolkit
        toolkit_container = QFrame()
        toolkit_container.setObjectName("toolkitCardsContainer")
        toolkit_container.setStyleSheet(f"""
            QFrame#toolkitCardsContainer {{
                background: transparent;
                border: none;
            }}
        """)
        
        toolkit_layout = QGridLayout(toolkit_container)
        toolkit_layout.setContentsMargins(0, 0, 0, 0)
        toolkit_layout.setSpacing(12)
        
        # Créer une grille 2x2 de cartes
        row, col = 0, 0
        for i, toolkit in enumerate(toolkits):
            toolkit_widget = self.create_toolkit_card(toolkit)
            toolkit_layout.addWidget(toolkit_widget, row, col)
            
            # Passer à la colonne/ligne suivante
            col += 1
            if col > 1:  # 2 colonnes maximum
                col = 0
                row += 1
        
        content_layout.addWidget(toolkit_container)
        content_layout.addSpacing(10)
        
        # Boutons d'action en bas
        action_buttons = QHBoxLayout()
        action_buttons.setSpacing(10)
        
        # Bouton principal
        explore_btn = QPushButton(self.user_settings.translate("browse_toolkits"))
        explore_btn.setCursor(Qt.PointingHandCursor)
        explore_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']['primary']};
                color: {self.theme['text']['highlight']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent']['primary_hover']};
            }}
        """)
        
        # Bouton secondaire
        store_btn = QPushButton(self.user_settings.translate("visit_store"))
        store_btn.setCursor(Qt.PointingHandCursor)
        store_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['accent']['primary']};
                border: 1px solid {self.theme['accent']['primary']};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['background']['hover']};
            }}
        """)
        
        explore_btn.clicked.connect(lambda: ComingSoonPopup(self.user_settings).exec())
        store_btn.clicked.connect(lambda: ComingSoonPopup(self.user_settings).exec())

        action_buttons.addWidget(explore_btn)
        action_buttons.addWidget(store_btn)
        content_layout.addLayout(action_buttons)
  
    def setup_projects_grid(self, layout):

        def format_time_diff(ts_str):
            try:
                dt = datetime.fromisoformat(ts_str)
            except Exception:
                return "Unknown"

            now = datetime.now()
            diff = now - dt

            minutes = diff.total_seconds() // 60
            hours = minutes // 60
            days = diff.days

            if minutes < 1:
                return "Just now"
            elif minutes < 60:
                return f"{int(minutes)} min ago"
            elif hours < 24:
                return f"{int(hours)} hours ago"
            elif days == 1:
                return f"Yesterday at {dt.strftime('%H:%M')}"
            elif days <= 7:
                return f"{dt.strftime('%A')} at {dt.strftime('%H:%M')}"
            elif days <= 30:
                return f"{int(days)} days ago"
            else:
                return dt.strftime("on %d %b %Y")

        def get_projects_path():
            appdata = os.getenv('APPDATA')
            if not appdata:
                raise Exception("APPDATA environment variable not found. Are you on Windows?")
            
            overblend_folder = os.path.join(appdata, 'Overblend')
            
            # Créer le dossier si jamais il n'existe pas
            if not os.path.exists(overblend_folder):
                os.makedirs(overblend_folder)
            
            return os.path.join(overblend_folder, 'projects.json')

        # Charger les projets
        self.sanitize_recent_projects()
        project_data = safe_load_json(get_projects_path())
        
        project_data = project_data[::-1] if isinstance(project_data,list) else [project_data]
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("border-radius: 20px;")
        scroll_layout = QVBoxLayout(container)
        scroll_layout.setAlignment(Qt.AlignTop)
        scroll_layout.setContentsMargins(10,10, 10, 0)
        scroll_layout.setSpacing(10)

        for proj in project_data:
            project = {
                "name": os.path.basename(proj["path"]),
                "date": format_time_diff(proj["last_opened"]),
                "type": proj.get("type", "Unknown"),
                "path": proj["path"]
            }
            scroll_layout.addWidget(self.create_project_item(project))

        scroll_area.setWidget(container)
        layout.addWidget(scroll_area, 1)

    def setup_footer(self):
        self.footer = QFrame()
        self.footer.setFixedHeight(120)
        self.footer.setStyleSheet(f"""
            background-color: {self.theme['background']['panel']};
            border-top: 1px solid {self.theme['container']['border']};
        """)

        layout = QHBoxLayout(self.footer)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(0)  # on gère le spacing avec les QSpacerItem
        
        layout.addLayout(self.create_footer_section(self.user_settings.translate("blendai_tips"),
                                                     self.user_settings.translate("blendai_tip_desc"),
                                                      self.user_settings.translate("blendai_tip_btn"),
                                                       lambda: ComingSoonPopup(self.user_settings).exec()))
        layout.addStretch()
        layout.addLayout(self.create_footer_section(self.user_settings.translate("whats_new"),
                                                     self.user_settings.translate("whats_new_desc"),
                                                       self.user_settings.translate("whats_new_btn"),
                                                       lambda: ComingSoonPopup(self.user_settings).exec()))
        layout.addStretch()
        layout.addLayout(self.create_footer_section(self.user_settings.translate("footer_settings"),
                                                     self.user_settings.translate("footer_settings_desc"),
                                                       self.user_settings.translate("video_effects_btn"),
                                                         lambda: ComingSoonPopup(self.user_settings).exec()))

    # SECTION CREATION
    def create_footer_section(self, title, description, button_text, button_action):
        layout = QVBoxLayout()
        layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"""
            color: {self.theme['text']['highlight']};
            border: none;
            font-size: 16px;
            font-weight: bold;
        """)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(f"""
            color: {self.theme['text']['default']};
            border: none;
            font-size: 13px;
        """)

        action_btn = QPushButton(button_text)
        action_btn.setCursor(Qt.PointingHandCursor)
        action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['accent']['primary']};
                font-size: 13px;
                font-weight: bold;
                border: none;
                padding: 0;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {self.theme['accent']['primary_hover']};
                text-decoration: underline;
            }}
        """)
        action_btn.clicked.connect(button_action)

        layout.addWidget(title_lbl)
        layout.addWidget(desc_lbl)
        layout.addWidget(action_btn)
        layout.addStretch()

        return layout


    def create_automation_card(self):
        card = QFrame()
        card.setObjectName("automation_card")
        card.setStyleSheet(f"""
            QFrame#automation_card {{
                background-color: {self.theme['background']['panel']};
                border-radius: 12px;
                border: 1px solid {self.theme['accent']['primary']};
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 22, 25, 22)
        card_layout.setSpacing(18)
        
        # Header with title and icon - More modern layout
        header_layout = QHBoxLayout()
        
        # Ajout d'un conteneur pour l'icône avec fond
        icon_container = QFrame()
        icon_container.setObjectName("iconContainer")
        icon_container.setFixedSize(40, 40)
        icon_container.setStyleSheet(f"""
            QFrame#iconContainer {{
                background-color: {self.theme['accent']['primary']};
                border-radius: 20px;
            }}
        """)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(self.user_settings.get_icon("automation",True)).scaled(QSize(30, 30), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 18px;
            background: transparent;
            color: {self.theme['accent']['primary']};
        """)
        
        icon_layout.addWidget(icon_label)
        
        # Titre avec police plus grande et style plus visible
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        
        title_label = QLabel(self.user_settings.translate("automate_pipeline"))
        title_label.setStyleSheet(f"""
            color: {self.theme['text']['highlight']};
            background: transparent;
            font-size: 20px;
            font-weight: bold;
        """)
        
        subtitle = QLabel(self.user_settings.translate("automate_subtitle"))
        subtitle.setStyleSheet(f"""
            color: {self.theme['text']['sidebar']};
            background: transparent;
            font-size: 13px;
        """)
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(icon_container)
        header_layout.addSpacing(12)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Separator line with gradient
        separator = QFrame()
        separator.setObjectName("gradientSeparator")
        separator.setFixedHeight(2)
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"""
            QFrame#gradientSeparator {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 {self.theme['accent']['primary']}, 
                                        stop:1 {self.theme['background']['panel']});
                margin-top: 5px;
                margin-bottom: 5px;
            }}
        """)
        
        # Description with better formatting
        description = QLabel(self.user_settings.translate("automate_description"))
        description.setWordWrap(True)
        description.setStyleSheet(f"""
            color: {self.theme['text']['default']};
            background: transparent;
            font-size: 14px;
            line-height: 1.5;
            margin-bottom: 8px;
        """)
        
        # Automation options with improved layout
        automation_options = QHBoxLayout()
        automation_options.setSpacing(15)
        automation_options.setContentsMargins(0, 8, 0, 8)
        
        # Option 1: Quick Templates
        quick_templates = self.create_automation_option(
            self.user_settings.translate("quick_templates"),  
            self.user_settings.translate("quick_templates_desc"),
            "pipeline"
        )
        
        # Option 2: Custom Workflow
        custom_workflow = self.create_automation_option(
            self.user_settings.translate("custom_workflow"),
            self.user_settings.translate("custom_workflow_desc"),
            "workflow"
        )
        
        # Option 3: AI Assistant
        ai_assistant = self.create_automation_option(
            self.user_settings.translate("ai_assistant"), 
            self.user_settings.translate("ai_assistant_desc"),
            "blendai"
        )
        
        automation_options.addWidget(quick_templates)
        automation_options.addWidget(custom_workflow)
        automation_options.addWidget(ai_assistant)
        
        # Action buttons with improved layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        # Main Get Started button
        get_started_btn = QPushButton(self.user_settings.translate("get_started_automation"))
        get_started_btn.setCursor(Qt.PointingHandCursor)
        get_started_btn.clicked.connect(lambda: ComingSoonPopup(self.user_settings).exec())

        get_started_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']['primary']};
                color: {self.theme['text']['highlight']};
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent']['primary_hover']};
            }}
        """)
        
        # Secondary button
        learn_more_btn = QPushButton(self.user_settings.translate("learn_more"))
        learn_more_btn.setCursor(Qt.PointingHandCursor)
        learn_more_btn.clicked.connect(lambda: ComingSoonPopup(self.user_settings).exec())
        learn_more_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['text']['default']};
                border: 1px solid {self.theme['container']['border']};
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['background']['hover']};
                border-color: {self.theme['accent']['primary']};
                color: {self.theme['text']['highlight']};
            }}
        """)
        
        buttons_layout.addWidget(get_started_btn)
        buttons_layout.addWidget(learn_more_btn)
        
        # Add all elements to card layout
        card_layout.addLayout(header_layout)
        card_layout.addWidget(separator)
        card_layout.addWidget(description)
        card_layout.addLayout(automation_options)
        card_layout.addStretch(1)
        card_layout.addLayout(buttons_layout)
        
        return card
    
    def create_automation_option(self, title, description, icon):
        option = QFrame()
        option.mousePressEvent = lambda event: ComingSoonPopup(self.user_settings).exec()
        option.setObjectName("automationOption")
        option.setCursor(Qt.PointingHandCursor)
        option.setFixedWidth(180)
        option.setStyleSheet(f"""
            QFrame#automationOption {{
                background-color: {self.theme['background']['tertiary']};
                border-radius: 10px;
                border: 1px solid {self.theme['container']['border']};
                padding: 5px;
            }}
            QFrame#automationOption:hover {{
                border-color: {self.theme['accent']['primary']};
                background-color: {self.theme['background']['hover']};
            }}
        """)
        
        layout = QVBoxLayout(option)
        layout.setContentsMargins(12, 15, 12, 15)
        layout.setSpacing(12)
        
        # Icon with better styling
        icon_container = QFrame()
        icon_container.setObjectName("iconBg")
        icon_container.setFixedSize(46, 46)
        icon_container.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-radius: 23px;
            }}
        """)

        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_label = QLabel()
        icon_label.setPixmap(QPixmap(self.user_settings.get_icon(icon,True)).scaled(QSize(30, 30), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 20px;")
        icon_layout.addWidget(icon_label)
        
        # Title with better styling
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {self.theme['text']['highlight']};
            background: transparent;
            font-size: 14px;
            font-weight: bold;
            padding-top: 5px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        
        # Description with better styling
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet(f"""
            color: {self.theme['text']['sidebar']};
            background: transparent;
            font-size: 12px;
            line-height: 1.3;
        """)
        
        # Progress indicator or status icon (petit point pour montrer que c'est sélectionnable)
        status_container = QHBoxLayout()
        status_container.setContentsMargins(0, 5, 0, 0)
        
        status_dot = QLabel("•")
        status_dot.setStyleSheet(f"""
            color: {self.theme['accent']['primary']};
            background: transparent;
            font-size: 20px;
            opacity: 0.7;
        """)
        status_dot.setAlignment(Qt.AlignCenter)
        
        status_container.addStretch()
        status_container.addWidget(status_dot)
        status_container.addStretch()
        
        layout.addWidget(icon_container, 0, Qt.AlignCenter)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        layout.addLayout(status_container)
        
        return option
    
    def create_section_card(self, title):
        card = QFrame()
        card.setObjectName("section_card")
        card.setStyleSheet(f"""
            QFrame#section_card {{
                background-color: {self.theme['background']['panel']};
                border-radius: 12px;
                border: 1px solid {self.theme['container']['border']};
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # Card header with icon and title
        header_layout = QHBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {self.theme['text']['highlight']}; background: transparent;font-size: 20px; font-weight: bold;")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        card_layout.addLayout(header_layout)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background-color: {self.theme['container']['border']}; max-height: 1px;")
        
        card_layout.addWidget(separator)
        
        return card

    def create_project_item(self, project):
        item = QFrame()
        item.setObjectName("projectItem")
        item.setCursor(Qt.PointingHandCursor)
        item.setStyleSheet(f"""
            QFrame#projectItem {{
                background-color: {self.theme['background']['tertiary']};
                border-radius: 10px;
                border: 1px solid {self.theme['container']['border']};
            }}
            QFrame#projectItem:hover {{
                background-color: {self.theme['background']['hover']};
                border: 1px solid {self.theme['accent']['primary']};
            }}
        """)
        item.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        item.setFixedHeight(70)  # Légèrement plus petit puisqu'on retire la miniature
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(14)
        
        # Project info with more organized layout
        info_container = QFrame()
        info_container.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        # Project name with better styling - Using file format (project.json)
        filename = project["name"].lower().replace(" ", "_") 
        name = QLabel(filename)
        name.setStyleSheet(f"""
            color: {self.theme['text']['highlight']};
            font-weight: bold;
            font-size: 14px;
        """)
        
        # Metadata container
        metadata_container = QFrame()
        metadata_container.setStyleSheet("background: transparent;")
        metadata_layout = QHBoxLayout(metadata_container)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(12)
        
        # Date
        date = QLabel(project["date"])
        date.setStyleSheet(f"""
            color: {self.theme['text']['sidebar']};
            font-size: 11px;
        """)
        
        # Type with icon - Changed to "Audio" type
        type_container = QHBoxLayout()
        type_container.setSpacing(4)
        project_type = QLabel(project["type"])
        project_type.setStyleSheet(f"""
            color: {self.theme['text']['sidebar']};
            font-size: 11px;
        """)
        type_container.addWidget(project_type)
        
        # Add all metadata widgets
        metadata_layout.addWidget(date)
        metadata_layout.addLayout(type_container)
        metadata_layout.addStretch()
        
        # Add project info to layout
        info_layout.addWidget(name)
        info_layout.addWidget(metadata_container)
        
        # Actions container with menu and shortcut buttons
        actions_container = QHBoxLayout()
        actions_container.setSpacing(6)
        
        # Edit button
        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon(self.user_settings.get_icon("file", True) or ""))
        def reveal_in_explorer(path):
            if platform.system() == "Windows":
                subprocess.run(f'explorer /select,"{os.path.normpath(path)}"', shell=True)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", "-R", path])
            else:  # Linux (Nautilus, Dolphin, etc.)
                folder = os.path.dirname(path)
                subprocess.run(["xdg-open", folder])
        edit_btn.clicked.connect(lambda _, p=project["path"]: reveal_in_explorer(p))
        if not self.user_settings.get_icon("edit", True):
            edit_btn.setText("✏️")
        edit_btn.setObjectName("actionButton")
        edit_btn.setFixedSize(28, 28)
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet(f"""
            QPushButton#actionButton {{
                background-color: transparent;
                color: {self.theme['text']['sidebar']};
                border: none;
                border-radius: 5px;
                font-size: 14px;
            }}
            QPushButton#actionButton:hover {{
                background-color: {self.theme['button']['hover']};
                color: {self.theme['text']['highlight']};
            }}
        """)
        
        # Menu button
        menu_btn = QPushButton()
        menu_btn.setIcon(QIcon(self.user_settings.get_icon("trash", True)))
        menu_btn.setObjectName("menuButton")
        menu_btn.setFixedSize(28, 28)
        menu_btn.setCursor(Qt.PointingHandCursor)
        menu_btn.setStyleSheet(f"""
            QPushButton#menuButton {{
                background-color: transparent;
                color: {self.theme['text']['sidebar']};
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#menuButton:hover {{
                background-color: {self.theme['button']['hover']};
                color: {self.theme['text']['highlight']};
            }}
        """)
        menu_btn.clicked.connect(lambda _, p=project["path"]: self.delete_project_file(p))
        actions_container.addWidget(edit_btn)
        actions_container.addWidget(menu_btn)
        
        # Assembler tous les éléments - sans thumbnail_container
        layout.addWidget(info_container, 1)  # Le 1 donne plus d'espace aux infos
        layout.addLayout(actions_container)
        def on_click_event(event):
            self.open_main_editor(project["path"])

        item.mousePressEvent = on_click_event
        return item
    
    def create_theme_item(self, theme):
        item = QFrame()
        item.setCursor(Qt.PointingHandCursor)
        item.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['background']['tertiary']};
                border-radius: 6px;
                padding: 6px;
            }}
            QFrame:hover {{
                background-color: {self.theme['background']['hover']};
            }}
        """)
        
        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)
        
        # Theme color preview (3 color circles)
        preview = QHBoxLayout()
        preview.setSpacing(4)
        
        for color in [self.theme['background']['main'], 
                     self.theme['accent']['primary'], 
                     self.theme['button']['default']]:
            circle = QLabel()
            circle.setFixedSize(16, 16)
            circle.setStyleSheet(f"""
                background-color: {color};
                border-radius: 8px;
                border: 1px solid {self.theme['container']['border']};
            """)
            preview.addWidget(circle)
        
        # Theme name and status
        name = QLabel(theme["name"])
        name.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-weight: bold; font-size: 13px;")
        
        status = QLabel()
        if theme["active"]:
            status.setText("●")
            status.setStyleSheet(f"color: {self.theme['accent']['primary']}; font-size: 14px;")
        
        layout.addLayout(preview)
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(status)
        
        return item
  
    def create_toolkit_card(self, toolkit):
        # Création d'une carte toolkit simplifiée et compacte
        card = QFrame()
        card.setObjectName("toolkitCard")
        card.setCursor(Qt.PointingHandCursor)
        card.setStyleSheet(f"""
            QFrame#toolkitCard {{
                background-color: {self.theme['background']['tertiary']};
                border-radius: 8px;
                border: 1px solid {self.theme['container']['border']};
            }}
            QFrame#toolkitCard:hover {{
                border-color: {self.theme['accent']['primary']};
                background-color: {self.theme['background']['hover']};
            }}
        """)
        
        # Réduire la taille globale de la carte
        card.setFixedHeight(120)  # Hauteur réduite
        card.setMaximumWidth(150)  # ou 200 pour plus compact
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)  # Marges intérieures réduites
        layout.setSpacing(4)  # Espacement réduit entre les éléments
        
        # En-tête avec nom et compteur
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        
        # Nom du toolkit
        name = QLabel(toolkit["name"])
        name.setWordWrap(True)
        name.setStyleSheet(f"""
            color: {self.theme['text']['highlight']};
            background: transparent;
            font-weight: bold;
            font-size: 13px;  /* Taille de police réduite */
        """)
        
        # Compteur avec style discret
        counter = QLabel(toolkit["count"])
        counter.setStyleSheet(f"""
            color: {self.theme['text']['sidebar']};
            background: transparent;
            font-size: 11px;
        """)
        
        header_layout.addWidget(name)
        header_layout.addStretch()
        header_layout.addWidget(counter)
        
        # Description simplifiée
        description = QLabel(toolkit["description"])
        description.setWordWrap(True)
        description.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        description.setStyleSheet(f"""
            color: {self.theme['text']['sidebar']};
            background: transparent;
            font-size: 11px;  /* Taille de police réduite */
        """)
        
        # Bouton d'action discret
        action_btn = QPushButton("Open →")
        action_btn.setObjectName("subtleButton")
        action_btn.setCursor(Qt.PointingHandCursor)
        action_btn.clicked.connect(lambda: ComingSoonPopup(self.user_settings).exec())
        action_btn.setStyleSheet(f"""
            QPushButton#subtleButton {{
                background-color: transparent;
                background: transparent;
                color: {self.theme['accent']['primary']};
                border: none;
                padding: 2px 0px;
                font-size: 11px;
                font-weight: bold;
                text-align: left;
            }}
            QPushButton#subtleButton:hover {{
                color: {self.theme['accent']['primary_hover']};
                text-decoration: underline;
            }}
        """)
        
        # Ajouter tous les éléments à la carte
        layout.addLayout(header_layout)
        layout.addWidget(description)
        layout.addStretch()
        layout.addWidget(action_btn, 0, Qt.AlignLeft)
        
        card.mousePressEvent = lambda event: ComingSoonPopup(self.user_settings).exec()

        return card
    
    def create_action_button(self, text):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['button']['default']};
                color: {self.theme['text']['default']};
                border: 1px solid {self.theme['button']['border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self.theme['button']['hover']};
                border-color: {self.theme['accent']['primary']};
            }}
        """)
        return button
    
    def create_compact_button(self, text, icon):
        button = QPushButton(f"{icon} {text}")
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['accent']['primary']};
                border: none;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {self.theme['accent']['primary_hover']};
                text-decoration: underline;
            }}
        """)
        return button
    
    #UI FUNCS
    def change_language(self, new_lang):
        config_path = self.user_settings.settings_path
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        config["lang"] = new_lang
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        # Recharge la langue et l'UI
        self.user_settings.load_config()
        self.user_settings.load_language(new_lang)
        self.refresh_ui()

    def refresh_ui(self):
        # Supprimer anciens widgets
        self.centralWidget().layout().removeWidget(self.header)
        self.centralWidget().layout().removeWidget(self.main_content)
        self.centralWidget().layout().removeWidget(self.footer)

        self.header.deleteLater()
        self.main_content.deleteLater()
        self.footer.deleteLater()

        # Recharger le thème (si besoin) et l'interface
        self.theme = self.user_settings.loaded_theme
        self.setup_header()
        self.setup_main_content()
        self.setup_footer()

        self.centralWidget().layout().addWidget(self.header)
        self.centralWidget().layout().addWidget(self.main_content, 1)
        self.centralWidget().layout().addWidget(self.footer)

        self.lang_selector.setCurrentText(self.user_settings.loaded_config.get("lang", "en"))

    


if __name__ == "__main__":
    app = QApplication.instance()
    user_settings = UserSettings()  # charge tes paramètres comme d'habitude

    window = HomeWindow(user_settings)
    window.setWindowTitle("Overblend Home")
    window.resize(1280, 800)
    window.showMaximized()
    sys.exit(app.exec())