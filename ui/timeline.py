import math,os
import numpy as np

#PySide6 imports-
from PySide6.QtCore import QSize, Qt,QEvent,Signal,QPoint,QTimer,QRect
from PySide6.QtGui import QIcon, QColor, QPainter,QFont,QPolygon
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,QSlider,QScrollArea
)
from .elements import VideoElement,ImageElement,GifElement,AudioElement,TextElement

class TimelineBody(QWidget):
    def __init__(self, user_settings, project, timeline_ruler, parent=None):
        super().__init__(parent)
        self.main_panel = parent.parent()
        self.user_settings = user_settings
        self.project = project
        self.timeline_ruler = timeline_ruler
        self.theme = self.user_settings.loaded_theme
        self._block = None
        self._selection_rect = None
        self._selection_start = None

        self.magnet = 5
        self.setAcceptDrops(True)
        self._previous_scroll_offset = 0
        self.track_widgets = {}

        self.setObjectName("timelineBody")
        self.setStyleSheet(self.user_settings.get_color_or_image(self.theme["timeline"]["body"]))
        self.setFocusPolicy(Qt.StrongFocus)

        # Scroll container
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setFocusPolicy(Qt.NoFocus)
        self.scroll.setStyleSheet("QScrollArea { border: none; }")

        self.scroll_timer = QTimer(self)
        self.scroll_timer.setInterval(20)
        self.scroll_timer.timeout.connect(self._scroll_if_needed)
        self._scroll_direction = 0  # -1 = haut, 1 = bas, 0 = rien
        self.track_y_map = None
        # Track container inside scroll
        self.container = QWidget()
        self.track_layout = QVBoxLayout(self.container)
        self.track_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll.setWidget(self.container)

        # Layout global
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.scroll)

        self.refresh_tracks()
        self.scroll.verticalScrollBar().valueChanged.connect(self.update_elements)

    def clear_all(self):
        # Supprimer tous les widgets de track
        for i in reversed(range(self.track_layout.count())):
            item = self.track_layout.itemAt(i)
            if widget := item.widget():
                widget.setParent(None)
                widget.deleteLater()

        self.track_widgets.clear()

        # Supprimer tous les widgets d'éléments
        if hasattr(self, "_element_widgets"):
            for block in self._element_widgets.values():
                block.setParent(None)
                block.deleteLater()
            self._element_widgets.clear()

    def create_add_button(self, z):
        plus_btn = QPushButton("+")
        plus_btn.setFixedHeight(20)
        plus_btn.setFixedWidth(self.user_settings.loaded_config["ui"]["timeline_left_padding"])
        plus_btn.setCursor(Qt.PointingHandCursor)
        plus_btn.setStyleSheet("""
            QPushButton {
                background: #222;
                color: #aaa;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #fff;
            }
        """)
        plus_btn.clicked.connect(lambda _, b=plus_btn: self.open_track_type_selector(z, b))

        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(plus_btn, alignment=Qt.AlignLeft)
        return container
    def open_track_type_selector(self, z, button):
        popup = QWidget(self.window())
        popup.setWindowFlags(Qt.Popup)
        theme = self.theme

        popup.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background']['panel']};
                border: 1px solid {theme['button']['border']};
                border-radius: 8px;
            }}
            QPushButton {{
                background-color: {theme['button']['default']};
                color: {self.theme["text"]["default"]};
                padding: 6px 12px;
                border: none;
                text-align: left;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {theme['button']['hover']};
            }}
        """)


        layout = QVBoxLayout(popup)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Add New Track")
        title.setStyleSheet("color: white; font-size: 14px; font-weight: bold; border: none")

        layout.addWidget(title)

        track_types = [("video", "video"), ("audio", "audio_fix"), ("text", "text")]

        for track_type, icon_key in track_types:
            icon = self.user_settings.get_icon(icon_key)
            btn = QPushButton(f"  {track_type.capitalize()}")
            btn.setIcon(QIcon(icon))
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _, t=track_type: self.add_new_track(t, z))
            layout.addWidget(btn)

        popup.adjustSize()

        # ↓ Position intelligente : si dépasse l’écran, le popup s’ouvre vers le haut
        global_pos = button.mapToGlobal(QPoint(0, 0))
        screen_rect = QApplication.primaryScreen().availableGeometry()

        if global_pos.y() + popup.height() > screen_rect.bottom():
            popup.move(global_pos.x() + button.width(), global_pos.y() - popup.height())
        else:
            popup.move(global_pos.x() + button.width(), global_pos.y() + button.height())

        popup.show()
        self._track_popup = popup

    def add_new_track(self, type, z):
        if hasattr(self.project, "add_track"):
            self.project.add_track(type, z)
            self.clear_all()
            self.refresh_tracks()
            QTimer.singleShot(0, self.update_elements)
        if hasattr(self, "_track_popup") and self._track_popup:
            self._track_popup.close()
            self._track_popup = None
    def force_track_geometry_update(self):
        self.container.updateGeometry()
        self.container.repaint()
        QApplication.processEvents()

    def refresh_tracks(self):
        # Clean old tracks
        for i in reversed(range(self.track_layout.count())):
            item = self.track_layout.itemAt(i)
            if widget := item.widget():
                widget.deleteLater()

        self.track_widgets.clear()

        if not self.project or not hasattr(self.project, "tracks"):
            return
        self.track_layout.setSpacing(0)
        sorted_tracks = sorted(self.project.tracks, key=lambda t: t.get("z", 0), reverse=True)
        self.track_layout.addWidget(self.create_add_button(100))
        for track in sorted_tracks:
            widget = self.create_track_widget(track)
            self.track_layout.addWidget(widget)
            # === BOUTON +
            self.track_layout.addWidget(self.create_add_button(track["z"]))
        
        self.track_layout.addStretch()
        QTimer.singleShot(0, self.update_elements)
    def _scroll_if_needed(self):
        vbar = self.scroll.verticalScrollBar()
        pixels_per_second = self.timeline_ruler._calculate_pixels_per_second()  # ou _calculate_pixels_per_second()

        px_step = 20  # décalage visuel en pixels à chaque tick
        time_step = px_step / pixels_per_second

        if self._scroll_direction == -1:
            vbar.setValue(vbar.value() - px_step)
        elif self._scroll_direction == 1:
            vbar.setValue(vbar.value() + px_step)
        elif self._scroll_direction == 2:
            self.timeline_ruler.start_time += time_step
            self.timeline_ruler.update()
            self.update_elements()
        elif self._scroll_direction == -2:
            self.timeline_ruler.start_time = max(0, self.timeline_ruler.start_time - time_step)
            self.timeline_ruler.update()
            self.update_elements()
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._phantom = None
            self._dragged_file = event.mimeData().urls()[0].toLocalFile()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if hasattr(self, "_dragged_file") and self._dragged_file:
            event.acceptProposedAction()
            self._update_phantom(event.pos())

    def dropEvent(self, event):
        file_path = self._dragged_file
        if not os.path.isfile(file_path):
            self._cancel_drag("Type de fichier non supporté")
            return

        file_type = self._guess_file_type(file_path)
        if not file_type or file_type not in self.project.supported_types:
            self._cancel_drag("Type de fichier non supporté")
            return

        pos = event.pos()
        x = pos.x()
        padding = self.user_settings.loaded_config["ui"]["timeline_left_padding"]
        t = self.timeline_ruler.get_time_for_x(x - padding)
        track_id = self._find_closest_track(pos.y(), file_type)

        if not track_id:
            self._cancel_drag("Type de fichier non supporté")
            return

        self.project.add_file(file_type, file_path, track_id, int(t * 1000))
        self._phantom.deleteLater()
        self._phantom = None
        self._dragged_file = None
        self.update_elements()
    def _map_file_type_to_track_type(self, file_type):
        if file_type in ["image", "gif", "video"]:
            return "video"
        if file_type == "audio":
            return "audio"
        if file_type == "text":
            return "text"
        return None

    def _find_closest_track(self, y, file_type=None):
        target_track_type = self._map_file_type_to_track_type(file_type) if file_type else None

        compatible = [
            tid for tid in self.track_y_map
            if file_type is None or self.project.get_track_type(tid) == target_track_type
        ]
        if not compatible:
            return None
        return min(compatible, key=lambda tid: abs(self.track_y_map[tid] - y))

    def _cancel_drag(self, reason=""):
        if self._phantom:
            self._phantom.deleteLater()
            self._phantom = None
        self._dragged_file = None
        self.parent().parent().parent().parent().show_warning(reason)

 
    def _guess_file_type(self, file_path):
        ext = file_path.lower().split(".")[-1]
        if ext in ["mp4", "mov", "mkv"]: return "video"
        if ext in ["mp3", "wav"]: return "audio"
        if ext in ["jpg", "jpeg", "png"]: return "image"
        if ext in ["gif"]: return "gif"
        if ext in ["txt", "srt"]: return "text"
        return None  


    def _update_phantom(self, pos):
        # Nettoie les anciens phantoms zombies
        for child in self.findChildren(QLabel, "phantom_preview"):
            if child != getattr(self, "_phantom", None):
                child.deleteLater()

        if getattr(self, "_phantom", None) is None or not self._phantom.isVisible():
            self._phantom = QLabel(self)
            self._phantom.setObjectName("phantom_preview")
            self._phantom.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); border: 1px dashed #ccc;")
            self._phantom.setFixedSize(80, self.user_settings.loaded_config["ui"]["track_height"])
            self._phantom.show()

        track_y = self._find_closest_track(pos.y())
        x = max(pos.x(), self.user_settings.loaded_config["ui"]["timeline_left_padding"])
        self._phantom.move(x, self.track_y_map[track_y])
    
    def update_elements(self):
        self._element_widgets = getattr(self, "_element_widgets", {})
        used_ids = set()
        # Mapping entre track_id et sa position Y
        self.track_y_map = {}
        track_height = self.user_settings.loaded_config["ui"]["track_height"]
        
        for track_id, (_, _, track_widget) in self.track_widgets.items():
             # Position du track dans TimelineBody
            track_pos = track_widget.mapTo(self, QPoint(0, 0))
            self.track_y_map[track_id] = track_pos.y()
       
        timeline_top_y = self.mapTo(self.window(), QPoint(0, 0)).y()
        for item in self.project.elements:
            if not item.get("is_visible", True):
                continue

            track_id = item.get("channel")
            if track_id not in self.track_y_map:
                continue
            
            element_id = item["id"]
            used_ids.add(element_id)

            # Calcul du temps en secondes
            start = self.project.get_timeline_start(element_id) / 1000.0
            end = start + self.project.get_instance_length(element_id) / 1000.0
            
            # Position
            x1 = max(self.timeline_ruler.get_x_for_time(start),self.user_settings.loaded_config["ui"]["timeline_left_padding"] )
            x2 = min(max(self.timeline_ruler.get_x_for_time(end),x1),self.window().width()) 

            
            width = max(1, x2 - x1)
            
            y = self.track_y_map[track_id]   # petit padding vertical
            
            if width <= 1:
                if element_id in self._element_widgets:
                    self._element_widgets[element_id].hide()
                continue

            if element_id in self._element_widgets:
                block = self._element_widgets[element_id]
                block.setFixedWidth(width)
                for child in block.children():
                    child.resize(block.size())
                block.setStyleSheet("""
                    #track_element {
                    background: transparent;
                    border: 1px solid white;
                    border-radius: 4px;
                }""")
                #print(self.main_panel.selected_clips)
                if element_id in self.main_panel.selected_clips:
                    
                    block.setStyleSheet("""
                        #track_element {
                            border: 2px solid orange;
                            border-radius: 4px;
                        }
                    """)
            else:
                block = QWidget(self.window())  # sans layout parent
                
            
                block.setObjectName("track_element")
                block.setStyleSheet("""
                    #track_element {
                    background: transparent;
                    border: 1px solid white;
                    border-radius: 4px;
                }""")
                #print(self.main_panel.selected_clips)
                if element_id in self.main_panel.selected_clips:
                    
                    block.setStyleSheet("""
                        #track_element {
                            border: 2px solid orange;
                            border-radius: 4px;
                        }
                    """)

                block.setCursor(Qt.PointingHandCursor)
                item_type = item.get("type", "video")
                
                style_class = {
                    "video": VideoElement,
                    "audio": AudioElement,
                    "text": TextElement,
                    "image": ImageElement,
                    "gif": GifElement,
                }.get(item_type, VideoElement)
                pixels_per_second = self.timeline_ruler._calculate_pixels_per_second()
                if item_type == "video":
                    design = style_class(item).render(pixels_per_second)
                else : 
                    design = style_class(item).render()
                design.setParent(block)
                design.move(0, 0)
                
                block.setFixedWidth(width)

                block.setFixedHeight(track_height)
                block._drag_start = None
                block._resize_mode = None  # "left", "right" ou None
                block._original_width = None
                block._original_x = None

                design.resize(block.size())
                design.lower()  # pour ne pas bloquer les events
                def apply_block_style(block, is_selected):
                    if is_selected:
                        block.setStyleSheet("""
                            #track_element {
                                border: 2px solid orange;
                                border-radius: 4px;
                            }
                        """)
                    else:
                        block.setStyleSheet("""
                            #track_element {
                                background: transparent;
                                border: 1px solid white;
                                border-radius: 4px;
                            }
                        """)

                def on_press(event, blk=block, itm=item):
                    if event.button() == Qt.LeftButton:
                        pos_x = event.pos().x()
                        margin = 5
                        if pos_x <= margin:
                            blk._resize_mode = "left"
                        elif pos_x >= blk.width() - margin:
                            blk._resize_mode = "right"
                        else:
                            blk._resize_mode = None  # Drag normal

                        blk._drag_start = event.pos()
                        blk._original_width = blk.width()
                        blk._original_x = blk.x()
                        blk.setCursor(Qt.SizeHorCursor if blk._resize_mode else Qt.ClosedHandCursor)
                        blk.grabMouse()
                    if QApplication.keyboardModifiers() & Qt.ControlModifier:
                        # Toggle selection
                        if item["id"] in self.main_panel.selected_clips:
                            self.main_panel.selected_clips.remove(item["id"])
                        else:
                            self.main_panel.selected_clips.add(item["id"])
                    else:
                        # Simple click : clear and add current
                        self.main_panel.selected_clips.clear()
                        self.main_panel.selected_clips.add(item["id"])

                    self.update_elements()



                def on_move(event, blk=block, item=item):
                    if blk._resize_mode == "left":
                        global_mouse_x = event.globalPosition().toPoint().x()
                        block_right = blk._original_x + blk._original_width
                        new_width = block_right - global_mouse_x

                        if new_width > 20:
                            blk.setFixedWidth(new_width)
                            blk.move(global_mouse_x, blk.y())
                        return

                    elif blk._resize_mode == "right":
                        delta_x = event.globalPosition().toPoint().x() - blk.mapToGlobal(QPoint(0, 0)).x() 
                        new_width = blk._original_width + delta_x
                        if new_width > 20:
                            blk.setFixedWidth(new_width)
                        return
                    if blk._drag_start and event.buttons() & Qt.LeftButton:
                        global_mouse = event.globalPosition().toPoint()
                        self._block = blk
                        cursor_pos = self.mapFromGlobal(global_mouse)
                        margin = 20
                        sidebar_width = self.parent().sidebar.width() if hasattr(self.parent(), 'sidebar') else 80
                        left_panel_width = self.user_settings.loaded_config["ui"]["timeline_left_padding"]
                        if cursor_pos.y() < margin:
                            self._scroll_direction = -1
                            self.scroll_timer.start()
                        elif cursor_pos.y() > self.height() - margin:
                            self._scroll_direction = 1
                            self.scroll_timer.start()
                        elif cursor_pos.x() < margin + sidebar_width + left_panel_width:
                            self._scroll_direction = -2
                            self.scroll_timer.start()
                        elif cursor_pos.x() > self.width() - margin:
                            self._scroll_direction = 2
                            self.scroll_timer.start()
                        else:
                            self._scroll_direction = 0
                            self.scroll_timer.stop()


                        
                        # Coords locales dans TimelineBody
                        local_mouse = self.mapFromGlobal(global_mouse)

                        new_x = local_mouse.x() - blk._drag_start.x() + self.user_settings.loaded_config["ui"]["timeline_left_padding"]
                        

                        element_type = item.get("type", "video")

                        # Types incompatibles
                        incompatible = {
                            "audio": {"video", "image", "gif"},
                            "video": {"audio"},
                            "image": {"audio"},
                            "gif": {"audio"},
                            "text": set()
                        }

                        # Filtre des pistes compatibles uniquement
                        compatible_track_y_map = {
                            tid: y for tid, y in self.track_y_map.items()
                            if self.get_track_type(tid) not in incompatible.get(element_type, set())
                        }

                        # S'assurer qu’il reste des pistes compatibles
                        if compatible_track_y_map:
                            closest_track_id, closest_y = min(
                                compatible_track_y_map.items(),
                                key=lambda pair: abs(pair[1] - local_mouse.y() + blk.height()//2)
                            )
                        else:
                            # fallback : pas de snap, garder piste actuelle
                            closest_track_id = item.get("channel")
                            closest_y = self.track_y_map.get(closest_track_id, 0)

                        
                        # Position globale
                        timeline_top_y = self.mapTo(self.window(), QPoint(0, 0)).y()
                        window_pos = self.mapTo(self.window(), QPoint(0,closest_y))
                       
                        # Clamp hauteur et décalage
                        delta = max(timeline_top_y - window_pos.y() + 2 , 0)
                        height = max(min(self.user_settings.loaded_config["ui"]["track_height"] - delta,
                                        self.user_settings.loaded_config["ui"]["track_height"]), 0)
                        blk.setFixedHeight(height)
                        # Calcul du scroll offset actuel et delta
                        
                        

                        blk.move(new_x, window_pos.y() + delta)
                        blk.raise_()
                        blk.show()
                        blk._hovered_track_id = closest_track_id  # utile pour on_release
                        # ➤ Mode magnétique (snap horizontal à d'autres éléments)
                        
                        target_blocks = [
                            other_block for eid, other_block in self._element_widgets.items()
                            if eid != item["id"]
                        ]


                        # Calcule la position X du bloc actuel
                        dragged_left = new_x
                        dragged_right = new_x + blk.width()

                        # Initialiser la meilleure distance trouvée
                        closest_snap_dx = 0
                        min_snap_dist = self.magnet + 1
                        # for child in block.children():
                        #     child.resize(block.size())

                        for other in target_blocks:
                            other_left = other.x()
                            other_right = other.x() + other.width()

                            # Positions du bloc en mouvement
                            dragged_left = new_x
                            dragged_right = new_x + blk.width()

                            # LEFT ↔ RIGHT (déjà implémenté)
                            dist = abs(dragged_left - other_right)
                            if dist < min_snap_dist:
                                closest_snap_dx = other_right - dragged_left
                                min_snap_dist = dist

                            dist = abs(dragged_right - other_left)
                            if dist < min_snap_dist:
                                closest_snap_dx = other_left - dragged_right
                                min_snap_dist = dist

                            # NEW: LEFT ↔ LEFT
                            dist = abs(dragged_left - other_left)
                            if dist < min_snap_dist:
                                closest_snap_dx = other_left - dragged_left
                                min_snap_dist = dist

                            # NEW: RIGHT ↔ RIGHT
                            dist = abs(dragged_right - other_right)
                            if dist < min_snap_dist:
                                closest_snap_dx = other_right - dragged_right
                                min_snap_dist = dist

                        # Appliquer le meilleur snap trouvé
                        if abs(closest_snap_dx) <= self.magnet:
                            new_x += closest_snap_dx

                        blk.move(new_x, blk.y())



                        


                def on_release(event, blk=block, item=item):
                    blk.releaseMouse() 
                    if blk._resize_mode:
                        # Calculer le nouveau start/end
                        global_pos = blk.mapToGlobal(QPoint(0, 0))
                        local_pos = self.timeline_ruler.mapFromGlobal(global_pos)
                        new_start_time = self.timeline_ruler.get_time_for_x(local_pos.x())
                        new_duration = blk.width() / self.timeline_ruler._calculate_pixels_per_second()

                        if blk._resize_mode == "left":
                            item["timestamps"][0] = int(new_start_time * 1000)
                            item["timestamps"][1] = int((new_start_time + new_duration) * 1000)
                            print(item["timestamps"])
                            #self.project.update_timeline_placement(item["id"], int(new_start_time * 1000))

                        elif blk._resize_mode == "right":
                            item["timestamps"][1] = int((new_start_time + new_duration) * 1000)

                        blk._resize_mode = None
                        self.update_elements()
                        return
                    blk.setCursor(Qt.PointingHandCursor)
                    if self.scroll_timer.isActive():
                        self.scroll_timer.stop()
                        self._scroll_direction = 0
                    blk._drag_start = None
                    self._block = None
                    # ➤ Nouvelle position temporelle
                    global_pos = blk.mapToGlobal(QPoint(0, 0))
                    local_pos = self.timeline_ruler.mapFromGlobal(global_pos)
                    new_time = self.timeline_ruler.get_time_for_x(local_pos.x())
                    new_track_id = getattr(blk, "_hovered_track_id", None)
                    new_start_ms = int(new_time * 1000)
                    duration = self.project.get_instance_length(item["id"])
                    new_end_ms = new_start_ms + duration

                    # ➤ Vérifie les collisions dans la même piste
                    best_start = new_start_ms
                    min_distance = None

                    for eid, _ in self._element_widgets.items():
                        if eid == item["id"]:
                            continue

                        other = next((el for el in self.project.elements if el["id"] == eid), None)
                        if not other or other.get("channel") != new_track_id:
                            continue

                        other_start = self.project.get_timeline_start(eid)
                        other_end = other_start + self.project.get_instance_length(eid)

                        # Vérifie l’overlap
                        if not (new_end_ms <= other_start or new_start_ms >= other_end):
                            # Overlap détecté
                            # Tente d’aligner à gauche ou à droite du bloc
                            distance_left = abs(new_start_ms - other_end)
                            distance_right = abs(new_end_ms - other_start)

                            if min_distance is None or distance_left < min_distance:
                                best_start = other_end
                                min_distance = distance_left

                            if distance_right < min_distance:
                                best_start = other_start - duration
                                min_distance = distance_right

                    # Appliquer la nouvelle position (modifiée si collision)
                    self.project.update_timeline_placement(item["id"], max(0, best_start))
                    # Recalcul de la durée du projet
                    self.project.length = self.project.compute_project_duration()
                    self.timeline_ruler.project.length = self.project.length

                    # Forcer la mise à jour du zoom et des timestamps
                    self.timeline_ruler.update()
                    self.main_panel.timeline.update_playhead_position()

                    # Recalcul du zoom min pour s’adapter à la nouvelle durée
                    #self.main_panel.timeline.fit_to_project()

                    if new_track_id and item.get("channel") != new_track_id:                                                                                                        
                        item["channel"] = new_track_id  # déplace dans la bonne piste

                    self.update_elements()


                
                block.mousePressEvent = lambda e, func=on_press: func(e)
                block.mouseMoveEvent = on_move
                block.mouseReleaseEvent = on_release

                self._element_widgets[element_id] = block
                if self.scroll_timer.isActive():
                    self.scroll_timer.stop()
                    self._scroll_direction = 0
            
                # Update position / taille
            if self._block != block :

                local_pos = QPoint(x1, y)
                window_pos = self.mapTo(self.window(), local_pos)

                delta = max(timeline_top_y - window_pos.y() + 2, 0)
                height = max(min(track_height - delta, track_height), 0)

                block.setFixedHeight(height)
                block.move(window_pos.x(), window_pos.y() + delta)
                #print(f"Old width : {width} , placement width : {block.width()}")

                block.show()
            
        # Nettoyer les éléments supprimés
        for old_id, block in list(self._element_widgets.items()):
            if old_id not in used_ids:
                block.hide() 
    def create_track_widget(self, track):
        track_widget = QWidget()
        track_widget.setFixedHeight(self.user_settings.loaded_config["ui"]["track_height"])

        layout = QHBoxLayout(track_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left panel
        left_panel = QWidget()
        left_panel.setFixedWidth(self.user_settings.loaded_config["ui"]["timeline_left_padding"])
        left_panel.setStyleSheet("background: rgba(0, 0, 0, 1);")
        layout.addWidget(left_panel)

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(6)
        left_layout.setAlignment(Qt.AlignTop)

        # Top icon (track type)
        track_type = track.get("type", "media")
        icon_map = {"audio": "audio_fix", "video": "video", "media": "video", "text": "text"}
        icon_name = icon_map.get(track_type, "video")
        icon = self.user_settings.get_icon(icon_name)
        top_icon = QLabel()
        top_icon.setPixmap(icon.pixmap(15, 15))
        left_layout.addWidget(top_icon, alignment=Qt.AlignLeft)

        # Spacer and bottom icons
        left_layout.addStretch()
        bottom_container = QWidget()
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(2)

        volume_icon = QLabel()
        volume_icon.setPixmap(self.user_settings.get_icon("volume").pixmap(15, 15))
        bottom_layout.addWidget(volume_icon)

        movedown_icon = QLabel()
        movedown_icon.setPixmap(self.user_settings.get_icon("move_down").pixmap(15, 15))
        bottom_layout.addWidget(movedown_icon)

        moveup_icon = QLabel()
        moveup_icon.setPixmap(self.user_settings.get_icon("move_up").pixmap(15, 15))
        bottom_layout.addWidget(moveup_icon)

        left_layout.addWidget(bottom_container)
        

        # Right panel (will hold elements later)
        right_panel = QWidget()
        right_panel.setStyleSheet("background: rgba(0, 0, 0, 0.2);")

        layout.addWidget(right_panel, 1)

        # Save reference
        self.track_widgets[track["id"]] = (left_panel, right_panel, track_widget)

        return track_widget
    def add_track(self):
        print("track added !")
    def get_track_type(self, track_id):
        for track in self.project.tracks:
            if track["id"] == track_id:
                return track.get("type", "")
        return ""
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._selection_start = event.pos()
            self._selection_rect = QLabel(self)
            self._selection_rect.setStyleSheet("border: 1px dashed orange; background: rgba(255,165,0,30);")
            self._selection_rect.setGeometry(QRect(self._selection_start, QSize()))
            self._selection_rect.show()

    # mouseMoveEvent
    def mouseMoveEvent(self, event):
        if self._selection_rect:
            rect = QRect(self._selection_start, event.pos()).normalized()
            self._selection_rect.setGeometry(rect)

    # mouseReleaseEvent
    def mouseReleaseEvent(self, event):
        if self._selection_rect:
            selected_ids = []
            selection_box = self._selection_rect.geometry()
            self._selection_rect.deleteLater()
            self._selection_rect = None

            for eid, block in self._element_widgets.items():
                if selection_box.intersects(block.geometry()):
                    selected_ids.append(eid)

            if QApplication.keyboardModifiers() & Qt.ControlModifier:
                for eid in selected_ids:
                    if eid in self.main_panel.selected_clips:
                        self.main_panel.selected_clips.remove(eid)
                    else:
                        self.main_panel.selected_clips.add(eid)
            else:
                self.main_panel.selected_clips = set(selected_ids)

            self.update_elements()

class TimelineWidget(QWidget):
    def __init__(self, user_settings,project, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.project = project
        self.theme = user_settings.loaded_theme

        self.setFixedHeight(400)
        self.setMinimumHeight(100)
        self.setMaximumHeight(600)
        self.setObjectName("timelineWidget")
        self.setStyleSheet(self.user_settings.get_color_or_image(self.theme["timeline"]["background"]))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === Header
        self.timeline_header = QWidget()
        self.timeline_header.setFixedHeight(120)
        header_layout = QVBoxLayout(self.timeline_header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        # === timeline_header_top
        self.timeline_header_top = QWidget()
        self.timeline_header_top.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(self.timeline_header_top)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(10)
        # === timeline_header_bottom
        self.timeline_header_bottom = QWidget()
        self.timeline_header_bottom.setStyleSheet(self.user_settings.get_color_or_image(self.theme["timeline"]["ruler"]))
        self.timeline_ruler = TimelineRulerWidget(user_settings,project)
        self.timeline_ruler.setFixedHeight(35)
        self.timeline_ruler.project = project  
        ruler_layout = QHBoxLayout(self.timeline_header_bottom)
        self.left_padding = self.user_settings.loaded_config["ui"]["timeline_left_padding"]
        ruler_layout.setContentsMargins(self.left_padding, 0, self.user_settings.loaded_config["ui"]["timeline_right_padding"], 0)
        ruler_layout.addWidget(self.timeline_ruler)
        # == triangle playhead
        self.playhead_time = 0.0
        self.playhead_triangle = PlayheadTriangle(self.user_settings, self.timeline_header_bottom)
        self.playhead_line = PlayheadLine(self.user_settings, self)
        self.playhead_line.setFixedHeight(self.height())
        self.playhead_line.show()


        # ➤ LEFT actions
        actions_container = QWidget()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(6)
        
        def make_btn(text, icon_key):
            btn = QPushButton(text)
            btn.setIcon(QIcon(self.user_settings.get_icon(icon_key)))
            btn.setStyleSheet(self.user_settings.get_style("button").format(self.theme["text"]["default"],
                                                                            self.user_settings.get_color_or_image(self.theme['button']['default']),
                                                                            self.theme['button']['border'],
                                                                            self.user_settings.get_color_or_image(self.theme['button']['hover']),
                                                                            self.theme['accent']['primary']))
            btn.setCursor(Qt.PointingHandCursor)
            return btn

        translate = self.user_settings.translate

        for key, icon_key in [
            ("split", "cut"),
            ("autocut", "video"),
            ("fix_audio", "audio_fix"),
            ("add_subtitle", "subtitles"),
            ("ask_ai", "blendai")
        ]:
            actions_layout.addWidget(make_btn(translate(key), icon_key))


        top_layout.addWidget(actions_container,alignment=Qt.AlignLeft)

        # ➤ CENTER: lecture controls
        center = QWidget()
        self.controls_layout = QHBoxLayout(center)
        self.controls_layout.setContentsMargins(0, 0, 0, 0)
        self.controls_layout.setSpacing(10)

        def icon_btn(icon_key, size=36):
            btn = QPushButton()
            btn.setIcon(QIcon(self.user_settings.get_icon(icon_key)))
            btn.setFixedSize(size, size)
            # For play: always 24x24, for others: auto-scale
            if icon_key == "play":
                btn.setIconSize(QSize(24, 24))
            else:
                btn.setIconSize(QSize(size - 16, size - 16))

            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.theme['button']['play']};
                    border-radius: {size // 2}px;
                    border: 1px solid {self.theme['button']['border']};
                }}
                QPushButton:hover {{
                    background-color: {self.theme['button']['play_hover']};
                }}
            """)
            return btn

        self.rewind_btn = icon_btn("rewind")
        self.play_pause_btn = icon_btn("play", 48)
        self.controls_layout.addWidget(self.rewind_btn)
        self.controls_layout.addWidget(self.play_pause_btn)

        self.controls_layout.addWidget(icon_btn("fastforward"))

        # Timestamp
        self.timestamp = QLabel("00:00.0 / 01:00.0")
        self.timestamp.setFixedHeight(36)
        self.timestamp.setAlignment(Qt.AlignCenter)
        self.timestamp.setStyleSheet(f"""
            QLabel {{
                color: {self.theme['text']['default']};
                background-color: {self.theme['button']['play']};
                border-radius: 6px;
                padding: 6px 12px;
                border: 1px solid {self.theme['button']['border']};
                font-family: monospace;
                font-size: 12px;
            }}
        """)
        self.controls_layout.addWidget(self.timestamp)

        # Volume
        mute_icon = QLabel()
        mute_icon.setPixmap(self.user_settings.get_icon("mute").pixmap(20, 20))

        volume_slider = QSlider(Qt.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setFixedWidth(100)
        volume_slider.setFixedHeight(30)
        volume_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: {self.theme['slider']['groove']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {self.theme['slider']['handle']};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.theme['slider']['subpage']};
            }}
            QSlider::add-page:horizontal {{
                background: {self.theme['slider']['addpage']};
            }}
        """)
        max_icon = QLabel()
        max_icon.setPixmap(self.user_settings.get_icon("volume").pixmap(20, 20))

        volume_container = QWidget()
        volume_container.setObjectName("volumeContainer")
        volume_container.setStyleSheet(f"""
            QWidget#volumeContainer {{
                background-color: {self.theme['container']['background']};
                border: 1px solid {self.theme['container']['border']};
                border-radius: 8px;
                                       }}
        """)
        volume_container.setFixedHeight(30)
        volume_layout = QHBoxLayout(volume_container)
        volume_layout.setContentsMargins(6, 0, 6, 0)
        volume_layout.setSpacing(6)

        volume_layout.addWidget(mute_icon)
        volume_layout.addWidget(volume_slider)
        volume_layout.addWidget(max_icon)

        self.controls_layout.addWidget(volume_container)


        top_layout.addWidget(center, 1,alignment=Qt.AlignCenter)

        # ➤ RIGHT: zoom + fit
        right = QWidget()
        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.setAlignment(Qt.AlignRight)
        right_layout.addStretch()

        zoomout = QLabel()
        zoomout.setPixmap(self.user_settings.get_icon("zoom_out").pixmap(20, 20))
        self.zoom_slider = QSlider(Qt.Horizontal)

        self.zoom_slider_precision = self.user_settings.loaded_config["ui"].get("zoom_slider_precision", 100)
        self.zoom_slider.setRange(0, self.zoom_slider_precision)    

        self.zoom_slider.setFixedWidth(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
        self.zoom_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: {self.theme['slider']['groove']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {self.theme['slider']['handle']};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            QSlider::sub-page:horizontal {{
                background: {self.theme['slider']['subpage']};
            }}
            QSlider::add-page:horizontal {{
                background: {self.theme['slider']['addpage']};
            }}
        """)

        zoomin = QLabel()
        zoomin.setPixmap(self.user_settings.get_icon("zoom_in").pixmap(20, 20))

        fit_btn = QPushButton("Fit")
        fit_btn.setFixedSize(60, 30)
        fit_btn.clicked.connect(self.fit_to_project)
        fit_btn.setCursor(Qt.PointingHandCursor)
        fit_btn.setStyleSheet(self.user_settings.get_style("fit_button").format(self.theme['text']['highlight'],
                                                                                self.user_settings.get_color_or_image(self.theme['accent']['primary']),
                                                                                self.theme['accent']['primary_hover'],
                                                                                self.user_settings.get_color_or_image(self.theme['accent']['primary_hover']),
                                                                                self.theme['accent']['primary']
                                                                                ))


        zoom_container = QWidget()
        zoom_container.setObjectName("zoomContainer")
        zoom_container.setStyleSheet(f"""
            QWidget#zoomContainer {{
                background-color: {self.theme['container']['background']};
                border: 1px solid {self.theme['container']['border']};
                border-radius: 8px;
            }}
        """)
        zoom_container.setFixedHeight(30)
        zoom_layout = QHBoxLayout(zoom_container)
        zoom_layout.setContentsMargins(6, 0, 6, 0)
        zoom_layout.setSpacing(6)

        zoom_layout.addWidget(zoomout)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_layout.addWidget(zoomin)
        
        right_layout.addWidget(zoom_container)

        right_layout.addSpacing(10)
        
        right_layout.addWidget(fit_btn)
        

        top_layout.addWidget(right,alignment=Qt.AlignRight)
        top_layout.addStretch()

        # Assemble header
        header_layout.addWidget(self.timeline_header_top,3)
        header_layout.addWidget(self.timeline_header_bottom,1)
        main_layout.addWidget(self.timeline_header, alignment=Qt.AlignTop)
        # === Timeline body area
        self.timeline_body = TimelineBody(user_settings,self.project,self.timeline_ruler,self)
        main_layout.addWidget(self.timeline_body, 4)
        
        self.timeline_header_top.installEventFilter(self)
        self.timeline_ruler.playhead_callback = self.update_playhead_position
        self.timeline_ruler.marker_callback = self.timeline_body.update_elements
        self.timeline_ruler.timeClicked.connect(self.user_timeline_click)
        self.timeline_ruler.playheadGrab.connect(self.parent().force_show_preview_slider)
        self.timeline_ruler.playheadRelease.connect(self.parent().force_hide_preview_slider)
    def eventFilter(self, obj, event):
        if obj == self.timeline_header_top and event.type() == QEvent.Resize:
            self.update_controls_padding()
        return super().eventFilter(obj, event)
    def user_timeline_click(self, t: float):
            self.parent().timer.stop()
            if hasattr(self.parent(),"producer") : 
                self.parent().producer.reset_start_time(t)
            self.set_playhead_time(t)
            if hasattr(self.parent(),"producer") : 
                self.parent().start_preview()
    def set_playhead_time(self, t: float):
            self.playhead_time = t
            self.update_playhead_position()
            self.saved_playhead_x = self.timeline_ruler.get_x_for_time(t)
            
            
    def update_playhead_position(self):
        x = self.timeline_ruler.get_x_for_time(self.playhead_time)
        if x >= self.left_padding  :
            self.playhead_triangle.show()
            self.playhead_triangle.move(x -6  ,self.timeline_ruler.height()-11)
            self.playhead_line.move(x - 1, self.timeline_header.height())
            self.playhead_line.setFixedHeight(self.timeline_body.height())
            self.playhead_line.raise_()
            self.playhead_triangle.raise_()
            self.timestamp.setText(f"{self.format_time(self.playhead_time)} / {self.format_time(self.timeline_ruler.project.length)}")
        else : 
            self.playhead_triangle.hide()
        self.parent().update_preview_slider()
    def format_time(self, t):
        h = int(t) // 3600
        m = (int(t) // 60) % 60
        s = int(t) % 60
        ms = int((t - int(t)) * 1000)  # une seule décimale pour les ms (ex: .3)

        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}.{ms}"
        else:
            return f"{m:02d}:{s:02d}.{ms}"
    def update_controls_padding(self):
        total_width = self.timeline_header_top.width()
        left_group_width = self.timeline_header_top.children()[1].width()
        rewind_width = self.rewind_btn.width()
        play_width = self.play_pause_btn.width()

        ideal_center = total_width // 2
        real_play_center = left_group_width + rewind_width + (play_width // 2)

        offset = ideal_center - real_play_center - 119  # ajustable si besoin
        self.controls_layout.setContentsMargins(max(0, offset), 0, 0, 0)
    def on_zoom_slider_changed(self, value):
        t = self.playhead_time
        padding = self.user_settings.loaded_config["ui"]["timeline_left_padding"]

        # Avant le zoom : position du playhead
        p_old = self.timeline_ruler._calculate_pixels_per_second()
        x_before = (t - self.timeline_ruler.start_time) * p_old + padding

        # Conversion slider → zoom logarithmique
        slider_min, slider_max = 0, self.zoom_slider_precision
        zoom_min, zoom_max = 1, 100
        normalized = (value - slider_min) / (slider_max - slider_min)
        zoom = zoom_min * ((zoom_max / zoom_min) ** normalized)
        zoom = int(zoom)

        # Appliquer zoom
        self.timeline_ruler.set_zoom(zoom)
        QApplication.processEvents()

        # Après le zoom : recalcul start_time pour conserver x
        p_new = self.timeline_ruler._calculate_pixels_per_second()
        self.timeline_ruler.start_time = t - (x_before - padding) / p_new
        self.timeline_ruler.start_time = max(0.0, self.timeline_ruler.start_time)

        # Update
        self.timeline_ruler.update()
        self.update_playhead_position()
        self.saved_playhead_x = self.timeline_ruler.get_x_for_time(t)


    def fit_to_project(self):
        self.on_zoom_slider_changed(0)
        duration = getattr(self.timeline_ruler.project, "length", 60)
        if duration <= 0:
            return

        fit_margin_ratio = self.timeline_ruler.fit_margin_ratio
        width = self.timeline_ruler.width()
        pixels_per_second = width / (duration * fit_margin_ratio)
        max_ = self.user_settings.loaded_config["ui"]["pixels_per_second_max"]
        base = max(0.01, min(width / (duration * fit_margin_ratio), max_ - 1))

        zoom_factor = (pixels_per_second - base) / (max_ - base)
        zoom_factor = max(0.0, min(zoom_factor, 1.0))
        best_zoom = int((zoom_factor ** (1 / 3)) * 100)

        # Appliquer zoom + reset du scroll horizontal
        slider_value = int(best_zoom * self.zoom_slider_precision / 100)
        self.zoom_slider.setValue(slider_value)

        self.timeline_ruler.start_time = 0
        self.timeline_ruler.update()
class TimelineRulerWidget(QWidget):
    timeClicked = Signal(float)
    playheadGrab = Signal()
    playheadRelease = Signal()
    def __init__(self, user_settings,project, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.theme = user_settings.loaded_theme
        self.left_padding = self.user_settings.loaded_config["ui"]["timeline_left_padding"]
        self.right_padding = self.user_settings.loaded_config["ui"]["timeline_right_padding"]
        self.project = project  # ← sera injecté par le parent

            
        self.marker_callback = None
        self.playhead_callback = None
        self._dragging_playhead = False

        self.zoom_level = 2
        self.tick_positions = {}
        self.start_time = 0
        self.fit_margin_ratio = 2

        self._cached_pixels_per_second = None
        self._cached_width = None
        self._cached_zoom_level = None

    def set_zoom(self, zoom):
        self._cached_pixels_per_second = None
        max_visible_duration = self.project.length * self.fit_margin_ratio
        base = self.width() / max_visible_duration
        max_ = self.user_settings.loaded_config["ui"]["pixels_per_second_max"]
        base = max(0.01, min(base, max_ - 1))
        pixels_needed = self.width() / max_visible_duration

        zoom_factor = (pixels_needed - base) / (max_ - base)
        zoom_factor = max(0.0, min(zoom_factor, 1.0))
        min_zoom = int((zoom_factor ** (1 / 3)) * 100)
        self.zoom_level = max(min_zoom, min(zoom, 100))
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.position().x()
            t = self.get_time_for_x(x)
            self.timeClicked.emit(t)
            self.playheadGrab.emit()

            self._dragging_playhead = True
            self.setCursor(Qt.SizeHorCursor)

    def mouseMoveEvent(self, event):
        if self._dragging_playhead:
            x = event.position().x()
            t = self.get_time_for_x(x)
            self.timeClicked.emit(t)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.playheadRelease.emit()
            self._dragging_playhead = False
            self.unsetCursor()

    def get_time_for_x(self, x):
        pixels_per_second = self._calculate_pixels_per_second()
        precision = 1000  # 1000 = précision à la ms, 100 = 10ms, etc.
        return max(0,round((x / pixels_per_second + self.start_time) * precision) / precision)


    def get_x_for_time(self, t):
        pixels_per_second = self._calculate_pixels_per_second()
        return round((t - self.start_time) * pixels_per_second + self.left_padding)


    def wheelEvent(self, event):
        delta = event.angleDelta().x() or event.angleDelta().y()
        scroll_amount = delta / 120
        visible_duration = self.width() / self._calculate_pixels_per_second()
        scroll_seconds = scroll_amount * visible_duration * 0.05
        self.start_time = max(0, self.start_time - scroll_seconds)
        self.update()

    def _calculate_pixels_per_second(self):
        width = self.width()
        zoom = self.zoom_level

        if (
            self._cached_pixels_per_second is not None and
            self._cached_width == width and
            self._cached_zoom_level == zoom
        ):
            return self._cached_pixels_per_second

        max_ = self.user_settings.loaded_config["ui"]["pixels_per_second_max"]
        duration = getattr(self.project, "length", 60)
        if duration <= 0:
            return 100

        ideal_base = width / (duration * self.fit_margin_ratio)
        min_base = width / 100000
        dynamic_base = max(min_base, min(ideal_base, max_))

        zoom_factor = (zoom / 100) ** 3
        result = round(dynamic_base + (max_ - dynamic_base) * zoom_factor, 10)

        self._cached_pixels_per_second = result
        self._cached_width = width
        self._cached_zoom_level = zoom
        
        return result


    
    def update_project_length(self):
        self.update()
    def paintEvent(self, event):
        self.tick_positions = {}  # Réinitialise à chaque draw
        painter = QPainter(self)
        width = self.width() - self.user_settings.loaded_config["ui"]["timeline_right_padding"]
        height = self.height()

        pixels_per_second = self._calculate_pixels_per_second()
        visible_duration = width / pixels_per_second
        start_time = self.start_time
        end_time = start_time + visible_duration
        font_name = getattr(self.user_settings, "loaded_font_family", None)
        if font_name:
            font = QFont(font_name)
            font.setPixelSize(10)  # ← ajuste ici selon test
            painter.setFont(font)



        # Style
        minor_color = QColor(self.theme["tick"]["minor"])
        major_color = QColor(self.theme["tick"]["major"])
        text_color = QColor(self.theme["text"]["tick"] )


        # Graduation dynamique
        nice_steps = [
            0.001, 0.002, 0.005,
            0.01, 0.02, 0.05,
            0.1, 0.2, 0.5,
            1, 2, 5, 10, 30, 60, 120, 300, 600, 1800, 3600
        ]

        target_px_spacing = self.user_settings.loaded_config["target_ruler_spacing"]
        best_step = min(nice_steps, key=lambda s: abs(pixels_per_second * s - target_px_spacing))
        
        # Ticks via np.arange
        # Décalage visuel doux : évite les sauts quand on scroll
        # On aligne les ticks sur un temps absolu régulier
        first_tick = math.floor(start_time / best_step) * best_step
        last_tick = math.ceil(end_time / best_step) * best_step
        ticks = np.arange(first_tick, last_tick + best_step, best_step)
        if self.parent() and hasattr(self.parent(), "update_test_marker"):
            self.parent().update_test_marker()

        # Tick rouge toutes les N secondes (ici : 2 * best_step)
        major_every = 2 * best_step
        for tick in ticks:
            x = int((tick - start_time) * pixels_per_second) 
            self.tick_positions[round(tick, 5)] = x
            # Tolérance dynamique en fonction du step actuel
            tolerance = best_step * 0.01  # 1% du step (par ex. 0.01s si step = 1s)
            is_major = abs((tick % major_every)) < tolerance or abs((major_every - (tick % major_every))) < tolerance




            # Draw tick
            painter.setPen(major_color if is_major else minor_color)
            painter.drawLine(x, height, x, height - (14 if is_major else 6))

            # Draw label
            if is_major:
                h = int(tick) // 3600
                m = (int(tick) // 60) % 60
                s = int(tick) % 60
                ms = int((tick - int(tick)) * 1000)

                # Affiche les ms seulement si on voit moins de 10 secondes à l'écran
                if visible_duration < 10:

                # Zoom très précis → afficher toujours les ms avec le contexte complet
                    label = f"{h:02d}h:{m:02d}m:{s:02d}s:{ms:03d}ms" if h > 0 else (
                            f"{m:02d}m:{s:02d}s:{ms:03d}ms" if m > 0 else (f"{s:02d}s:{ms:03d}ms" if s > 0 else f"{ms:03d}ms"))
                else:
                    # Moins de précision → pas besoin des ms
                    if h > 0:
                        label = f"{h:02d}h:{m:02d}m:{s:02d}s"
                    elif m > 0:
                        label = f"{m:02d}m:{s:02d}s"
                    else:
                        label = f"{s:02d}s"


                text_rect = painter.boundingRect(0, 0, 100, 20, Qt.AlignLeft, label)
                painter.setPen(text_color)
                painter.drawText(x - text_rect.width() // 2, self.height()-18, label)
        # Affiche des ticks intermédiaires si le step est grand
        #if best_step >= 1:
        for tick in ticks:
            if tick not in ticks:
                continue  # sécurité

            # Position des ticks intermédiaires
            quarter_tick = tick + best_step * 0.25
            half_tick = tick + best_step * 0.5
            three_quarters_tick = tick + best_step * 0.75

            for subtick, size, color in [
                (quarter_tick, 4, QColor("#444")),
                (half_tick, 8, QColor("#666")),
                (three_quarters_tick, 4, QColor("#444")),
            ]:
                if start_time <= subtick <= end_time:
                    x = int((subtick - start_time) * pixels_per_second) 
                    painter.setPen(color)
                    painter.drawLine(x, height, x, height - size)

        if self.marker_callback:
            self.marker_callback()
        if self.playhead_callback:
            self.playhead_callback()
        painter.end()
class PlayheadTriangle(QWidget):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 10)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.theme = user_settings.loaded_theme
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        triangle_color = QColor(self.theme["playhead"]["triangle"])
        painter.setBrush(triangle_color)
        painter.setPen(Qt.NoPen)

        w, h = self.width(), self.height()
        triangle = QPolygon([
            QPoint(0, 0),
            QPoint(w, 0),
            QPoint(w // 2, h),
        ])
        painter.drawPolygon(triangle)
        painter.end()
class PlayheadLine(QWidget):
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.setFixedWidth(2)
        self.setStyleSheet("background: transparent;")
        self.theme = user_settings.loaded_theme
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = QColor(self.theme["playhead"]["bar"])
        painter.setPen(color)
        painter.drawLine(self.width() // 2, 0, self.width() // 2, self.height())
        painter.end()
