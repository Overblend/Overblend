#Sys Imports
import random,os,math,cv2

#Overblend Imports

#PySide6 imports-
from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QPixmap, QImage, QPainter
from PySide6.QtWidgets import (
    QFrame,QHBoxLayout, QLabel,
     QVBoxLayout, QWidget,QSizePolicy
)

def extract_frame_at_time(file_path, time_s):
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        print(f"Erreur : Impossible d'ouvrir la vidéo {file_path}")
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        print(f"Erreur : FPS invalide pour {file_path}")
        cap.release()
        return None

    frame_index = int(time_s * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        print(f"Erreur : Impossible de lire la frame à {time_s}s dans {file_path}")
        return None

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = frame_rgb.shape
    bytes_per_line = ch * w
    qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)

class BaseElementStyle:
    def __init__(self, item):
        self.item = item
    def render(self):
        # Container principal
        container = QWidget()
        container.setObjectName("containerWallah")
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(0)

        # Titre du fichier (en haut à gauche)
        name = self.item.get("file_path", "untitled").split("/")[-1]
        title = QLabel(name)
        title.setStyleSheet("color: white; font-size: 11px; font-weight: bold;")
        title.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(title)
        # Fond par défaut, sera surchargé
        container.setStyleSheet("background: #444; border-radius: 4px;")
        return container
class VideoElement(BaseElementStyle):
    def render(self, pixels_per_second=100):
        container = super().render()
        container.setObjectName("containerWallah")
        container.setStyleSheet("QWidget#containerWallah { background: #000000; border: 2px solid white; border-radius: 4px;}")
        return container
class AudioElement(BaseElementStyle):
    def render(self):
        container = super().render()
        container.setObjectName("containerWallah")
        container.setStyleSheet("QWidget#containerWallah { background: rgba(0,0,0,0.3); border: 2px solid white; border-radius: 4px;}")
        
        # Obtenir le layout existant qui contient déjà le titre
        main_layout = container.layout()
        
        # Créer un widget pour contenir les barres audio avec une classe optimisée
        bars_container = EfficientAudioBarsWidget()
        
        # Ajouter le conteneur de barres au layout principal (sous le titre)
        main_layout.addWidget(bars_container)
        
        return container
class EfficientAudioBarsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bars = []
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.setMinimumHeight(40)
        
        # Timer pour limiter les mises à jour
        self.resize_timer = QTimer(self)
        self.resize_timer.setSingleShot(True)
        self.resize_timer.setInterval(300)  # 300ms delay
        self.resize_timer.timeout.connect(self.updateBarsLayout)
        
        # Pool de barres précrées
        self.bar_pool = []
        self.createBarPool(50)  # Créer un pool initial
    
    def createBarPool(self, count):
        for i in range(count):
            bar = QFrame()
            bar.setFixedWidth(2)
            bar.setStyleSheet("background: white; border-radius: 1px;")
            bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            bar.hide()  # Masquer jusqu'à utilisation
            self.bar_pool.append(bar)
    
    def resizeEvent(self, event):
        # Lancer le timer au lieu de mettre à jour immédiatement
        self.resize_timer.start()
        super().resizeEvent(event)
    
    def updateBarsLayout(self):
        width = self.width()
        bar_width = 2
        spacing = 2
        num_bars = max(10, int(width / (bar_width + spacing)))
        
        # Masquer toutes les barres actuellement visibles
        for bar in self.bars:
            self.layout.removeWidget(bar)
            bar.hide()
        
        # S'assurer que nous avons assez de barres dans notre pool
        if len(self.bar_pool) < num_bars:
            self.createBarPool(num_bars - len(self.bar_pool))
        
        # Réinitialiser la liste des barres actives
        self.bars = []
        
        # Utiliser les barres du pool
        for i in range(num_bars):
            bar = self.bar_pool[i]
            height = random.randint(10, 30)
            bar.setFixedHeight(height)
            self.layout.addWidget(bar, 0, Qt.AlignBottom)
            bar.show()
            self.bars.append(bar)
        
        # Ajouter un spacer à la fin si besoin
        if self.layout.count() > num_bars:
            spacer = self.layout.itemAt(num_bars)
            if not spacer or not spacer.spacerItem():
                self.layout.addStretch(1)
class TextElement(BaseElementStyle):
    def render(self):
        container = super().render()
        container.setStyleSheet("background: #27ae60; border-radius: 4px;")
        return container
class ImageElement(BaseElementStyle):
    def render(self):
        container = super().render()
        container.setStyleSheet("background: transparent; border-radius: 4px;")

        image_path = self.item.get("file_path") 
        if not os.path.isfile(image_path):
            return container

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return container

        repeated_label = QLabel(container)
        repeated_label.setStyleSheet("background: transparent; border: 2px solid white;")
        repeated_label.lower()

        def update_diapo():
            container_width = container.width()
            container_height = container.height()

            target_width = 100
            scaled_pixmap = pixmap.scaledToWidth(target_width, Qt.SmoothTransformation)
            scaled_height = scaled_pixmap.height()

            y_offset = max(0, (container_height - scaled_height) // 2)

            # Préparer un QPixmap vide à la taille du container
            tiled = QPixmap(container_width, container_height)
            tiled.fill(Qt.transparent)

            painter = QPainter(tiled)
            x = 0
            while x < container_width:
                painter.drawPixmap(x, y_offset, scaled_pixmap)
                x += target_width
            painter.end()

            repeated_label.setPixmap(tiled)
            repeated_label.resize(container_width, container_height)

        container.resizeEvent = lambda event: update_diapo()
        update_diapo()

        return container
class GifElement(BaseElementStyle):
    def render(self):
        container = super().render()
        container.setStyleSheet("background: #d35400; border-radius: 4px;")
        return container