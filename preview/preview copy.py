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
    def __init__(self, preview_label,preview_fps, base_quality, preview_quality,lenght,generate_frame,aspect_ratio,elements,get_z_level):
        super().__init__(daemon=True)
        self.fps = preview_fps
        self.base_quality = base_quality
        self.new_quality = preview_quality
        self.preview_label = preview_label
        self.aspect_ratio = aspect_ratio
        self.elements = elements
        self.get_z_level =get_z_level
        self.generate_frame = generate_frame
        self.queue = queue.Queue(maxsize=120)
        self.running = True
        self.project_duration = lenght  # CHANGED: precalc duration
        self.container_cache = {}  # 🔁 Un cache par fichier vidéo


    def run(self):
        total_frames = int(self.project_duration* self.fps)
        predicted_time = 0.0
        avg_gen_time = 1.0 / self.fps  # init à 1 frame

        alpha = 0.1 # pour smooth la moyenne glissante

        for i in range(total_frames):
            if not self.running:
                break

            start_time = time.perf_counter()

            # 🔮 On prédit le temps théorique de la frame à générer
            # 🧠 Skip frames si on a trop de retard pour suivre le framerate
            if avg_gen_time > (1.0 / self.fps):
                skip = int(avg_gen_time * self.fps)
                predicted_time += skip * (1.0 / self.fps)
                print(f"⚠️ Skipping {skip} frame(s) to catch up")

            t = predicted_time

            frame_start = time.perf_counter()
            frame = self.generate_frame(t, self.new_quality, self.project_duration, self.container_cache,self.base_quality,self.aspect_ratio,self.elements,self.get_z_level)
            frame_time = time.perf_counter() - frame_start

            # 🎯 Moyenne glissante sur le temps de génération
            avg_gen_time = (1 - alpha) * avg_gen_time + alpha * frame_time

            # ⏭️ Temps suivant estimé pour garder un rythme fluide
            predicted_time += 1.0 / self.fps

            resize_start = time.perf_counter()
            pixmap = resize_for_preview(frame, self.preview_label)
            resize_time = time.perf_counter() - resize_start

            self.queue.put((t, pixmap))
            total_time = time.perf_counter() - start_time
            
            print(f"[{i}/{total_frames}] Frame @ {t:.2f}s | gen: {frame_time:.3f}s | resize: {resize_time:.3f}s | total: {total_time:.3f}s | avg_gen: {avg_gen_time:.3f}s")
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
        self.elements = elements
        self.get_z_level = get_z_level
        preview_height = int(self.preview_width * aspect_ratio[1] / aspect_ratio[0])

        self.preview_label = QLabel(self)
        self.preview_label.setFixedSize(self.preview_width, preview_height)
        self.preview_label.setStyleSheet("background-color: black;")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_label)
        self
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.current_time = 0.0

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
        self.current_time = 0.0
        self.timer.start(int((1/self.preview_fps) * 1000))

    def update_frame(self):
        if not self.producer.queue.empty():
            t, pixmap = self.producer.queue.get()
            self.preview_label.setPixmap(pixmap)
            self.current_time = t
        elif not self.producer.running:
            self.timer.stop()
            print("🛑 Preview complete.")
def preview(*args):
    app = QApplication(sys.argv)
    window = OverblendWindow(*args)
    window.show()
    sys.exit(app.exec())
if __name__ == "__main__" : 
    preview()