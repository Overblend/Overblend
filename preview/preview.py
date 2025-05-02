import cv2
from PIL import Image, ImageDraw, ImageFont
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QVBoxLayout,
                               QWidget)

import queue
import threading
import time
import sys
def resize_for_preview(canvas, preview_label):
    display = cv2.resize(canvas, preview_label.size().toTuple(), interpolation=cv2.INTER_LINEAR)
    qimg = QImage(display.data, display.shape[1], display.shape[0], display.shape[1] * 3, QImage.Format.Format_BGR888)
    return QPixmap.fromImage(qimg)
class FrameProducer(threading.Thread):
    def __init__(self, preview_label,  get_project, generate_frame, getter):
        super().__init__(daemon=True)
        self.project_func = get_project
        self.project = None
        self.getter = getter
        self.start_time = getter()
        self.initial_time = getter()  # Garder une référence au temps initial
        self.preview_label = preview_label
        self.generate_frame = generate_frame
        self.queue = queue.Queue(maxsize=120)
        self.running = True
        self.container_cache = {}
        self.current_elements_id = None
        self.real_start_time = time.perf_counter()  # Temps de démarrage réel de la génération

    def reset_start_time(self, new_time: float):
        """Met à jour la position de lecture en supprimant les frames en attente."""
        self.start_time = new_time
        self.initial_time = new_time  # Mettre à jour le temps initial
        self.real_start_time = time.perf_counter()  # Réinitialiser le temps réel
        with self.queue.mutex:
            self.queue.queue.clear()

    def run(self):
        while self.running:
            # Récupérer les éléments actuels
            self.project = self.project_func()
            current_elements = self.project.elements
            current_id = id(current_elements)
            
            # Vérifier si les éléments ont changé
            if self.current_elements_id != current_id:
                #print(f"Éléments changés (ID précédent: {self.current_elements_id}, ID actuel: {current_id}), réinitialisation de la queue")
                self.current_elements_id = current_id
                current_time = self.getter()
                self.reset_start_time(current_time)  # Utiliser reset_start_time pour tout réinitialiser correctement
                
            # Calculer où nous devrions être en fonction du temps écoulé
            elapsed_real = time.perf_counter() - self.real_start_time
            target_frame_time = self.initial_time + elapsed_real
            
            # Si le temps cible est trop en avance par rapport à notre position actuelle,
            # nous devons sauter des frames
            if target_frame_time > self.start_time + (1.0 / self.project.preview_fps):
                frames_to_skip = int((target_frame_time - self.start_time) * self.project.preview_fps)
                if frames_to_skip > 0:
                    #print(f"⚠️ En retard de {target_frame_time - self.start_time:.3f}s, saut de {frames_to_skip} frame(s)")
                    self.start_time += frames_to_skip * (1.0 / self.project.preview_fps)
            
            t = self.start_time
            frame_start = time.perf_counter()
            
            # Générer la frame
            frame = self.generate_frame(t, self.project.preview_quality, self.project.length, self.container_cache, 
                                      self.project.base_quality, self.project.aspect_ratio, current_elements, self.project.get_z_level)
            
            frame_time = time.perf_counter() - frame_start
            
            # Mettre à jour le temps pour la prochaine frame
            self.start_time += 1.0 / self.project.preview_fps
            
            # Adapter et ajouter la frame à la queue
            pixmap = resize_for_preview(frame, self.preview_label)
            self.queue.put((t, pixmap))
            
            # Si nous avons été très rapides, attendre un peu pour ne pas surcharger le CPU
            time_remaining = (1.0 / self.project.preview_fps) - frame_time
            if time_remaining > 0:
                time.sleep(time_remaining * 0.8)  # Laisser un peu de marge
class OverblendWindow(QMainWindow):
    def __init__(self,aspect_ratio,preview_fps,base_quality,preview_quality,lenght,generate_frame,elements,get_z_level):
        super().__init__()
        self.setWindowTitle("Overblend Preview")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_width = 300
        self.preview_fps = preview_fps
        self.base_quality = base_quality
        self.preview_quality = preview_quality
        self.lenght = lenght
        self.generate_frame = generate_frame
        self.aspect_ratio = aspect_ratio
        self.get_elements = elements  # éléments dynamiques via fonction

        self.get_z_level = get_z_level
        preview_height = int(self.preview_width * aspect_ratio[1] / aspect_ratio[0])

        self.preview_label = QLabel(self)
        self.preview_label.setFixedSize(self.preview_width, preview_height)
        self.preview_label.setStyleSheet("background-color: black;")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_label)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        self.frames = []
        self.start_frame_thread()
        self.start_preview()


    def start_frame_thread(self):
        self.producer = FrameProducer(self.preview_label,
                                      self.preview_fps,
                                      self.base_quality,
                                      self.preview_quality,
                                      self.lenght,
                                      self.generate_frame,
                                      self.aspect_ratio,
                                      self.elements,
                                      self.get_z_level)
        self.producer.start()


    def start_preview(self):
        self.timer.start(int((1/self.preview_fps) * 1000))
    def update_frame(self):
        if not self.producer.queue.empty():
            t, pixmap = self.producer.queue.get()
            self.preview_label.setPixmap(pixmap)
        elif not self.producer.running:
            self.timer.stop()
            print("🛑 Preview complete.")
def preview(*args):
    app = QApplication(sys.argv)
    window = OverblendWindow(*args)
    window.show()
    sys.exit(app.exec())
    