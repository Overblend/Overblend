from PySide6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QFileDialog, QScrollArea, QWidget, QButtonGroup, QRadioButton, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import os

class YesNoDialog(QDialog):
    def __init__(self, user_settings, question: str, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = self.user_settings.loaded_theme

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(400, 220)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("fuckingdialog")
        self.setStyleSheet(f"""

            QDialog {{ background-color: {self.theme['background']['panel']};
            border-radius: 12px;}}
            QDialog#fuckingdialog {{
                border: 1px solid {self.theme['container']['border']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_header(layout)
        self.add_separator(layout)
        self.add_body(layout, question)
        self.add_footer(layout)

    def add_header(self, layout):
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(28, 28))
        logo.setFixedSize(28, 28)

        title = QLabel("OVERBLEND")
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignVCenter)

        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

    def add_separator(self, layout):
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self.theme['container']['border']};")
        layout.addWidget(separator)

    def add_body(self, layout, question):
        question_label = QLabel(question)
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setWordWrap(True)
        question_label.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 14px;")
        layout.addWidget(question_label)

    def add_footer(self, layout):
        footer = QHBoxLayout()
        footer.setSpacing(10)

        # Bouton Oui
        yes_btn = QPushButton(self.user_settings.translate("yes"))
        yes_btn.setCursor(Qt.PointingHandCursor)
        yes_btn.setFixedHeight(36)
        yes_btn.setStyleSheet(self.user_settings.get_style("button").format(
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme['button']['default']),
            self.theme['button']['border'],
            self.user_settings.get_color_or_image(self.theme['button']['hover']),
            self.theme['accent']['primary']
        ))
        yes_btn.clicked.connect(self.accept)

        # Bouton Non
        no_btn = QPushButton(self.user_settings.translate("no"))
        no_btn.setCursor(Qt.PointingHandCursor)
        no_btn.setFixedHeight(36)
        no_btn.setStyleSheet(yes_btn.styleSheet())
        no_btn.clicked.connect(self.reject)

        footer.addStretch()
        footer.addWidget(yes_btn)
        footer.addWidget(no_btn)
        footer.addStretch()

        layout.addLayout(footer)

# blendai_actions.py (ajoute ça à la suite)


class MultiChoiceQuestion(QDialog):
    def __init__(self, user_settings, questions: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = self.user_settings.loaded_theme
        self.questions = questions

        self.button_groups = []  # Stocker les groupes de boutons pour chaque question

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(550, 600)
        self.setObjectName("multichoicedialog")
        self.setStyleSheet(f"""
            QDialog#multichoicedialog {{
                background-color: {self.theme['background']['panel']};
                border: 2px solid {self.theme['container']['border']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_header(layout)
        self.add_separator(layout)
        self.add_body(layout)
        self.add_footer(layout)

    def add_header(self, layout):
        header_layout = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(28, 28))
        logo.setFixedSize(28, 28)

        title = QLabel("OVERBLEND")
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignVCenter)

        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

    def add_separator(self, layout):
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self.theme['container']['border']};")
        layout.addWidget(separator)

    def add_body(self, layout):
        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(20)

        for question, options in self.questions.items():
            question_container = QFrame()
            question_container.setObjectName("question_container")
            question_container.setStyleSheet(f"""
                QFrame#question_container {{
                    background-color: {self.theme['background']['secondary']};
                    border: 1px solid {self.theme['container']['border']};
                    border-radius: 10px;
                }}
            """)
            question_layout = QVBoxLayout(question_container)
            question_layout.setContentsMargins(15, 15, 15, 15)
            question_layout.setSpacing(10)

            question_label = QLabel(question)
            question_label.setWordWrap(True)
            question_label.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 15px; font-weight: bold;")
            question_layout.addWidget(question_label)

            group = QButtonGroup(self)
            for opt in options:
                btn = QRadioButton(opt)
                btn.setStyleSheet(f"""
                    QRadioButton {{
                        color: {self.theme['text']['default']};
                        font-size: 13px;
                        padding: 4px;
                    }}
                    QRadioButton:hover {{
                        color: {self.theme['accent']['primary']};
                    }}
                """)
                group.addButton(btn)
                question_layout.addWidget(btn)

            self.button_groups.append(group)
            self.body_layout.addWidget(question_container)

        self.body_layout.addStretch()
        layout.addLayout(self.body_layout)


    def add_footer(self, layout):
        footer = QHBoxLayout()
        footer.setSpacing(10)

        self.confirm_btn = QPushButton(self.user_settings.translate("confirm") or "Confirm")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.setFixedWidth(120)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme['accent']['primary']};
                color: {self.theme['text']['highlight']};
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['accent']['primary_hover']};
            }}
        """)
        self.confirm_btn.clicked.connect(self.check_completion)

        cancel_btn = QPushButton(self.user_settings.translate("cancel") or "Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(40)
        cancel_btn.setFixedWidth(120)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['text']['default']};
                border: 1px solid {self.theme['container']['border']};
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['background']['tertiary']};
                border-color: {self.theme['accent']['primary']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)

        footer.addStretch()
        footer.addWidget(cancel_btn)
        footer.addWidget(self.confirm_btn)

        layout.addLayout(footer)

    def check_completion(self):
        all_selected = all(group.checkedButton() is not None for group in self.button_groups)
        if all_selected:
            self.accept()
        else:
            print("[WARNING] You must answer all questions before confirming!")

    def get_answers(self):
        return [group.checkedButton().text() if group.checkedButton() else None for group in self.button_groups]
class TextInputDialog(QDialog):
    def __init__(self, user_settings, question: str, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = self.user_settings.loaded_theme
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(500, 350)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("textinputdialog")

        self.setStyleSheet(f"""
            QDialog#textinputdialog {{
                background-color: {self.theme['background']['panel']};
                border: 2px solid {self.theme['container']['border']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_header(layout)
        self.add_separator(layout)
        self.add_body(layout, question)
        self.add_footer(layout)

    def add_header(self, layout):
        header_layout = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(28, 28))
        logo.setFixedSize(28, 28)

        title = QLabel("OVERBLEND")
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

    def add_separator(self, layout):
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self.theme['container']['border']};")
        layout.addWidget(separator)

    def add_body(self, layout, question):
        question_label = QLabel(question)
        question_label.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 14px;")
        question_label.setWordWrap(True)
        layout.addWidget(question_label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(self.user_settings.translate("write_here") or "Write your answer here...")
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme['background']['secondary']};
                color: {self.theme['text']['default']};
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.text_edit)

    def add_footer(self, layout):
        footer = QHBoxLayout()
        footer.setSpacing(10)

        cancel_btn = QPushButton(self.user_settings.translate("cancel") or "Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet(self.user_settings.get_style("button").format(
            self.theme["text"]["default"],
            self.user_settings.get_color_or_image(self.theme['button']['default']),
            self.theme['button']['border'],
            self.user_settings.get_color_or_image(self.theme['button']['hover']),
            self.theme['accent']['primary']
        ))
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = QPushButton(self.user_settings.translate("confirm") or "Confirm")
        confirm_btn.setCursor(Qt.PointingHandCursor)
        confirm_btn.setFixedHeight(36)
        confirm_btn.setStyleSheet(cancel_btn.styleSheet())
        confirm_btn.clicked.connect(self.accept)

        footer.addStretch()
        footer.addWidget(cancel_btn)
        footer.addWidget(confirm_btn)

        layout.addLayout(footer)

    def get_text(self):
        return self.text_edit.toPlainText()


class SelectFileDialog(QDialog):
    def __init__(self, user_settings, files_expected: list, parent=None):
        """
        files_expected = [
            {"type": "Video (.mp4)", "description": "Primary footage"},
            {"type": "Audio (.mp3)", "description": "Background music"},
        ]
        """
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = self.user_settings.loaded_theme
        self.files_expected = files_expected
        self.selected_files = [None] * len(files_expected)
        self.is_dragging = False
        self.confirm_btn = None  

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setFixedSize(650, 500)
        self.setAcceptDrops(True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("selectfiledialog")
        self.setStyleSheet(f"""
            QDialog#selectfiledialog {{
                background-color: {self.theme['background']['panel']};
                border: 2px solid {self.theme['container']['border']};
                border-radius: 12px;
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            
            QScrollBar:vertical {{
                background: {self.theme['background']['secondary']};
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {self.theme['accent']['primary']};
                min-height: 20px;
                border-radius: 5px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.add_header(layout)
        self.add_separator(layout)
        self.add_instructions(layout)
        self.add_file_grid(layout)
        self.add_footer(layout)

    def add_header(self, layout):
        header_layout = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(self.user_settings.get_icon("app_icon").pixmap(28, 28))
        logo.setFixedSize(28, 28)

        title = QLabel("OVERBLEND")
        title.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(logo)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

    def add_separator(self, layout):
        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet(f"background-color: {self.theme['container']['border']};")
        layout.addWidget(separator)

    def add_instructions(self, layout):
        instructions = QLabel(self.user_settings.translate("select_files_instructions") or "Please select the required files below. You can replace files by dragging new ones.")
        instructions.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 13px;")
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

    def add_file_grid(self, layout):
        # Créer un widget de défilement pour les fichiers
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(5, 5, 5, 5)
        
        self.file_widgets = []
        self.drop_labels = []

        for idx, file_info in enumerate(self.files_expected):
            file_container = QFrame()
            file_container.setObjectName(f"file_container_{idx}")
            file_container.setAcceptDrops(True)  # Rendre le conteneur complet acceptant les drops
            file_container.setStyleSheet(f"""
                QFrame#file_container_{idx} {{
                    background-color: {self.theme['background']['secondary']};
                    border-radius: 10px;
                    border: 1px solid {self.theme['container']['border']};
                }}
            """)
            
            # Personnaliser les événements de drag & drop au niveau du conteneur
            file_container.dragEnterEvent = lambda event, idx=idx: self.container_drag_enter(event, idx)
            file_container.dragLeaveEvent = lambda event, idx=idx: self.container_drag_leave(event, idx)
            file_container.dragMoveEvent = lambda event, idx=idx: self.container_drag_move(event, idx)
            file_container.dropEvent = lambda event, idx=idx: self.container_drop_event(event, idx)
            
            container_layout = QVBoxLayout(file_container)
            container_layout.setContentsMargins(15, 15, 15, 15)
            container_layout.setSpacing(10)
            
            header_layout = QHBoxLayout()
            type_label = QLabel(file_info["type"])
            type_label.setStyleSheet(f"color: {self.theme['text']['highlight']}; font-size: 14px; font-weight: bold;")
            
            desc_label = QLabel(file_info["description"])
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {self.theme['text']['sidebar']}; font-size: 11px;")
            desc_label.setAlignment(Qt.AlignLeft)

            header_layout.addWidget(type_label)
            header_layout.addStretch()
            header_layout.addWidget(desc_label)
            
            container_layout.addLayout(header_layout)
            
            drop_area = QLabel()
            drop_area.setObjectName(f"drop_area_{idx}")
            drop_area.setAlignment(Qt.AlignCenter)
            drop_area.setFixedHeight(80)
            self.update_drop_area_style(drop_area, idx, False)
            drop_area.setProperty("index", idx)
            drop_area.mousePressEvent = lambda event, idx=idx: self.select_file(idx)
            
            # Création de l'icône de fichier
            file_icon_label = QLabel()
            file_icon = self.user_settings.get_icon("file")
            if file_icon:
                file_icon_label.setPixmap(file_icon.pixmap(32, 32))
            
            # Création du texte
            drop_text = QLabel(self.user_settings.translate("drop_files_here") or "Drop files here or click to browse")
            drop_text.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 12px;")
            
            # Layout pour l'intérieur de la zone de dépôt
            drop_layout = QVBoxLayout(drop_area)
            drop_layout.setAlignment(Qt.AlignCenter)
            drop_layout.addWidget(file_icon_label, alignment=Qt.AlignCenter)
            drop_layout.addWidget(drop_text, alignment=Qt.AlignCenter)
            
            container_layout.addWidget(drop_area)
            
            # Zone pour afficher le fichier sélectionné
            selected_file_frame = QFrame()
            selected_file_frame.setObjectName(f"selected_file_{idx}")
            selected_file_frame.setVisible(False)
            selected_file_frame.setStyleSheet(f"""
                QFrame#selected_file_{idx} {{
                    background-color: {self.theme['background']['tertiary']};
                    border-radius: 6px;
                }}
            """)
            
            selected_layout = QHBoxLayout(selected_file_frame)
            selected_layout.setContentsMargins(10, 5, 10, 5)
            
            file_icon_selected = QLabel()
            if file_icon:
                file_icon_selected.setPixmap(file_icon.pixmap(16, 16))
            file_icon_selected.setFixedSize(16, 16)
            
            file_name_label = QLabel()
            file_name_label.setObjectName(f"file_name_{idx}")
            file_name_label.setStyleSheet(f"color: {self.theme['text']['default']}; font-size: 12px;")
            
            replace_btn = QPushButton(self.user_settings.translate("replace") or "Replace")
            replace_btn.setObjectName(f"replace_btn_{idx}")
            replace_btn.setCursor(Qt.PointingHandCursor)
            replace_btn.setFixedHeight(24)
            replace_btn.setStyleSheet(f"""
                QPushButton#replace_btn_{idx} {{
                    background-color: transparent;
                    color: {self.theme['accent']['primary']};
                    border: none;
                    font-size: 11px;
                    padding: 0 5px;
                }}
                QPushButton#replace_btn_{idx}:hover {{
                    text-decoration: underline;
                }}
            """)
            replace_btn.clicked.connect(lambda _, idx=idx: self.select_file(idx))
            
            remove_btn = QPushButton()
            remove_btn.setObjectName(f"remove_btn_{idx}")
            remove_btn.setCursor(Qt.PointingHandCursor)
            remove_btn.setFixedSize(24, 24)
            remove_icon = self.user_settings.get_icon("close")
            if remove_icon:
                remove_btn.setIcon(remove_icon)
            remove_btn.setStyleSheet(f"""
                QPushButton#remove_btn_{idx} {{
                    background-color: transparent;
                    border: none;
                }}
                QPushButton#remove_btn_{idx}:hover {{
                    background-color: {self.theme['button']['hover']};
                    border-radius: 12px;
                }}
            """)
            remove_btn.clicked.connect(lambda _, idx=idx: self.remove_file(idx))
            
            selected_layout.addWidget(file_icon_selected)
            selected_layout.addWidget(file_name_label)
            selected_layout.addStretch()
            selected_layout.addWidget(replace_btn)
            selected_layout.addWidget(remove_btn)
            
            container_layout.addWidget(selected_file_frame)
            
            self.drop_labels.append(drop_area)
            self.file_widgets.append({
                "container": file_container,
                "drop_area": drop_area,
                "selected_frame": selected_file_frame,
                "file_name_label": file_name_label,
                "index": idx
            })
            
            scroll_layout.addWidget(file_container)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

    def update_drop_area_style(self, drop_area, idx, is_dragging=False):
        border_style = "dashed" if not self.selected_files[idx] else "solid"
        border_color = self.theme['accent']['primary'] if is_dragging else self.theme['container']['border']
        background = self.theme['background']['tertiary'] if is_dragging else self.theme['background']['secondary']
        
        drop_area.setStyleSheet(f"""
            QLabel#drop_area_{idx} {{
                background-color: {background};
                color: {self.theme['text']['default']};
                border: 2px {border_style} {border_color};
                border-radius: 8px;
            }}
            QLabel#drop_area_{idx}:hover {{
                background-color: {self.theme['background']['tertiary']};
                border-color: {self.theme['accent']['primary']};
            }}
        """)

    def add_footer(self, layout):
        footer = QHBoxLayout()
        footer.setSpacing(15)

        # Indication du nombre de fichiers sélectionnés
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"color: {self.theme['text']['sidebar']}; font-size: 12px;")
        
        self.confirm_btn = QPushButton(self.user_settings.translate("confirm") or "Confirm")
        self.confirm_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.setFixedWidth(120)
        self.confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['text']['sidebar']};
                border: 1px solid {self.theme['container']['border']};
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:enabled {{
                background-color: {self.theme['accent']['primary']};
                color: {self.theme['text']['highlight']};
                border: none;
            }}
            QPushButton:enabled:hover {{
                background-color: {self.theme['accent']['primary']};
                opacity: 0.9;
            }}
            QPushButton:enabled:pressed {{
                background-color: {self.theme['accent']['primary']};
                opacity: 0.8;
            }}
        """)

        self.confirm_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton(self.user_settings.translate("cancel") or "Cancel")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.setFixedHeight(40)
        cancel_btn.setFixedWidth(120)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['text']['default']};
                border: 1px solid {self.theme['container']['border']};
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['background']['tertiary']};
                border-color: {self.theme['accent']['primary']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)

        footer.addWidget(self.status_label)
        footer.addStretch()
        footer.addWidget(cancel_btn)
        footer.addWidget(self.confirm_btn)

        layout.addLayout(footer)
        
        # Update status label after confirm_btn is initialized
        self.update_status_label()
        self.update_confirm_button_state()

    def update_status_label(self):
        selected_count = sum(1 for f in self.selected_files if f is not None)
        total_count = len(self.files_expected)
        self.status_label.setText(f"{selected_count}/{total_count} {self.user_settings.translate('files_selected') or 'files selected'}")
        self.update_confirm_button_state()

    def update_confirm_button_state(self):
        all_filled = all(f is not None for f in self.selected_files)
        self.confirm_btn.setEnabled(all_filled)
        self.confirm_btn.setText(self.user_settings.translate("confirm"))


    def select_file(self, idx):
        allowed_exts = self.files_expected[idx].get("extensions", [])
        if allowed_exts:
            filter_str = "Supported Files (" + " ".join(f"*.{ext}" for ext in allowed_exts) + ")"
        else:
            filter_str = "All Files (*.*)"
        
        filename, _ = QFileDialog.getOpenFileName(self, "Select File", "", filter_str)
        if filename:
            self.set_file(idx, filename)


    def set_file(self, idx, filename):
        if not self.is_valid_extension(filename, idx):
            print(f"[WARNING] Mauvais type de fichier pour {filename}. Ignoré.")
            return
        self.selected_files[idx] = filename
        file_name = os.path.basename(filename)
        
        # Mettre à jour les widgets pour afficher le fichier sélectionné
        self.file_widgets[idx]["drop_area"].setVisible(False)
        self.file_widgets[idx]["selected_frame"].setVisible(True)
        self.file_widgets[idx]["file_name_label"].setText(file_name)
        self.update_status_label()
        
        # Mettre à jour l'apparence du conteneur pour indiquer un fichier sélectionné
        container = self.file_widgets[idx]["container"]
        container.setStyleSheet(f"""
            QFrame#file_container_{idx} {{
                background-color: {self.theme['background']['secondary']};
                border-radius: 10px;
                border: 1px solid {self.theme['accent']['primary']};
            }}
        """)
    def is_valid_extension(self, filename, idx):
        allowed_exts = self.files_expected[idx].get("extensions", [])
        ext = os.path.splitext(filename)[1][1:].lower()
        return ext in allowed_exts

    def remove_file(self, idx):
        self.selected_files[idx] = None
        self.file_widgets[idx]["drop_area"].setVisible(True)
        self.file_widgets[idx]["selected_frame"].setVisible(False)
        self.update_drop_area_style(self.drop_labels[idx], idx)
        self.update_status_label()
        
        # Réinitialiser l'apparence du conteneur
        container = self.file_widgets[idx]["container"]
        container.setStyleSheet(f"""
            QFrame#file_container_{idx} {{
                background-color: {self.theme['background']['secondary']};
                border-radius: 10px;
                border: 1px solid {self.theme['container']['border']};
            }}
        """)

    # Handlers pour le drag & drop au niveau du conteneur
    def container_drag_enter(self, event, idx):
        if event.mimeData().hasUrls():
            event.accept()
            self.highlight_container(idx, True)
    
    def container_drag_leave(self, event, idx):
        self.highlight_container(idx, False)
    
    def container_drag_move(self, event, idx):
        if event.mimeData().hasUrls():
            event.accept()
    
    def container_drop_event(self, event, idx):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            filepath = url.toLocalFile()
            self.set_file(idx, filepath)
            self.highlight_container(idx, False)
    
    def highlight_container(self, idx, highlight):
        border_color = self.theme['accent']['primary'] if highlight else self.theme['container']['border']
        if self.selected_files[idx]:
            border_color = self.theme['accent']['primary']  # Toujours mettre en évidence si un fichier est sélectionné
        
        self.file_widgets[idx]["container"].setStyleSheet(f"""
            QFrame#file_container_{idx} {{
                background-color: {self.theme['background']['secondary']};
                border-radius: 10px;
                border: {2 if highlight else 1}px solid {border_color};
                {f"background-color: {self.theme['background']['tertiary']};" if highlight else ""}
            }}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            self.is_dragging = True
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.is_dragging = False
        # Réinitialiser les styles
        for idx, drop_area in enumerate(self.drop_labels):
            self.update_drop_area_style(drop_area, idx, False)

    def dragMoveEvent(self, event):
        # Trouver le widget de dépôt sous le curseur
        for idx, file_widget in enumerate(self.file_widgets):
            drop_area = file_widget["drop_area"]
            if file_widget["drop_area"].isVisible():
                pos = drop_area.mapFromGlobal(self.mapToGlobal(event.pos()))
                if drop_area.rect().contains(pos):
                    # Mettre en évidence cette zone
                    self.update_drop_area_style(drop_area, idx, True)
                else:
                    # Rétablir le style normal
                    self.update_drop_area_style(drop_area, idx, False)

    def dropEvent(self, event: QDropEvent):
        self.is_dragging = False
        # Réinitialiser les styles
        for idx, drop_area in enumerate(self.drop_labels):
            self.update_drop_area_style(drop_area, idx, False)

        # Trouver la zone de dépôt sous le curseur
        for idx, file_widget in enumerate(self.file_widgets):
            drop_area = file_widget["drop_area"]
            if file_widget["drop_area"].isVisible():
                pos = drop_area.mapFromGlobal(self.mapToGlobal(event.pos()))
                if drop_area.rect().contains(pos) and event.mimeData().hasUrls():
                    url = event.mimeData().urls()[0]
                    filepath = url.toLocalFile()
                    self.set_file(idx, filepath)
                    break