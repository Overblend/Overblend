#Sys imports
import threading
#Overblend Imports
from BlendAI import BlendAI
#PySide6 imports-
from PySide6.QtCore import Qt,Signal,QTimer
from PySide6.QtGui import QIcon, QColor, QPixmap
from PySide6.QtWidgets import (QGraphicsDropShadowEffect, QHBoxLayout, QLabel,QTextEdit,QPushButton, QVBoxLayout, QWidget,QScrollArea)

#Sys imports
import threading
import time
#Overblend Imports
from BlendAI import BlendAI
#PySide6 imports
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QSize, Property
from PySide6.QtGui import QIcon, QColor, QPixmap, QFontMetrics, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QTextEdit, QPushButton, 
    QVBoxLayout, QWidget, QScrollArea, QSizePolicy, QFrame, QSpacerItem,
    QMenu, QApplication
)

class BubbleLabel(QLabel):
    def __init__(self, text="", is_user=False, user_settings=None, parent=None):
        super().__init__(text, parent)
        self.is_user = is_user
        self.user_settings = user_settings or parent.user_settings
        self.setWordWrap(True)
        
        # Apply appropriate styling
        
        if is_user: 
            style = self.user_settings.get_style("message").format(self.user_settings.get_color_or_image(self.user_settings.loaded_theme["blendai"]["user"]["background"]),
                                                                                    self.user_settings.loaded_theme["blendai"]["user"]["text"])
            self.setStyleSheet(style)
            self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            style = self.user_settings.get_style("message").format(self.user_settings.get_color_or_image(self.user_settings.loaded_theme["blendai"]["assistant"]["background"]),
                                                                                   self.user_settings.loaded_theme["blendai"]["assistant"]["text"])
            self.setStyleSheet(style)
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setOffset(0, 2)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        self.setGraphicsEffect(shadow)

class AvatarLabel(QLabel):
    """Circular avatar label"""
    def __init__(self, image_path, size=40, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.image_path = image_path
        self.setScaledContents(True)
        self.update_avatar(image_path, size)
        
    def update_avatar(self, image_path, size=40):
        # Load image and create circular mask
        pixmap = QPixmap(image_path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Create circular mask
        rounded = QPixmap(size, size)
        rounded.fill(Qt.transparent)
        
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.white)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        self.setPixmap(rounded)

class MessageWidget(QWidget):
    """Widget that contains a single message"""
    def __init__(self, message, is_user=False, show_avatar=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.message = message
        
        # Set up layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(12)
        
        # Create message bubble
        self.bubble = BubbleLabel(message, is_user, user_settings=parent.user_settings)
        self.bubble.setMaximumWidth(600)  # Largeur max fixe
        
        # Create timestamp (hidden initially)
        self.timestamp = QLabel()
        self.timestamp.setStyleSheet("color: #888; font-size: 11px;")
        self.timestamp.setVisible(False)
        
        # Create message container with timestamp
        msg_container = QVBoxLayout()
        msg_container.setSpacing(2)
        msg_container.addWidget(self.bubble)
        msg_container.addWidget(self.timestamp, 0, Qt.AlignRight if is_user else Qt.AlignLeft)
        
        # Add avatar if needed
        if show_avatar and not is_user:
            path = self.parent().user_settings.get_icon("assistant",True)
            avatar = AvatarLabel(path)
            main_layout.addWidget(avatar, 0, Qt.AlignTop)
            main_layout.addLayout(msg_container, 1)
            main_layout.addStretch()
        else:
            if is_user:
                main_layout.addStretch()
                main_layout.addLayout(msg_container)
            else:
                # Indentation for AI messages without avatar
                main_layout.addSpacerItem(QSpacerItem(40, 1))
                main_layout.addLayout(msg_container, 1)
                main_layout.addStretch()
        
        # Set up context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, pos):
        menu = QMenu(self)
        copy_action = menu.addAction("Copy Message")
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(self.message))
        
        # Add timestamp toggle
        if self.timestamp.isVisible():
            time_action = menu.addAction("Hide Timestamp")
            time_action.triggered.connect(lambda: self.timestamp.setVisible(False))
        else:
            time_action = menu.addAction("Show Timestamp")
            time_action.triggered.connect(self.show_timestamp)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def show_timestamp(self):
        self.timestamp.setText(time.strftime("%H:%M"))
        self.timestamp.setVisible(True)

class ThinkingAnimation(QWidget):
    """Compact inline animated thinking indicator"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 5, 15, 5)
        self.layout.setSpacing(6)

        # Avatar
        path = self.parent().user_settings.get_icon("assistant", True)
        self.avatar = AvatarLabel(path,size=28)
        self.layout.addWidget(self.avatar)

        # Bubble with thinking + dots
        self.bubble = QWidget()
        bubble_layout = QHBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(12, 8, 12, 8)
        bubble_layout.setSpacing(6)

        self.label = QLabel(f"{self.parent().user_settings.loaded_theme['assistant']['name']} is thinking")
        self.label.setStyleSheet(self.parent().user_settings.get_style("thinking_text").format(self.parent().user_settings.loaded_theme['blendai']['thinking_text']))
        bubble_layout.addWidget(self.label)

        self.dots = []
        for _ in range(3):
            dot = QLabel("•")
            dot.setStyleSheet("color: #aaa; font-size: 16px;")
            self.dots.append(dot)
            bubble_layout.addWidget(dot)
        self.bubble.setStyleSheet(self.parent().user_settings.get_style("thinking_bubble").format(self.parent().user_settings.get_color_or_image(self.parent().user_settings.loaded_theme["blendai"]["thinking_bubble"])))
        self.bubble.setGraphicsEffect(self._shadow_effect())
        self.layout.addWidget(self.bubble)
        self.layout.addStretch()

        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.animation_step = 0

    def _shadow_effect(self):
        effect = QGraphicsDropShadowEffect()
        effect.setOffset(0, 2)
        effect.setBlurRadius(10)
        effect.setColor(QColor(0, 0, 0, 50))
        return effect

    def update_animation(self):
        self.animation_step += 1
        for i, dot in enumerate(self.dots):
            phase = (self.animation_step + i * 2) % 12
            opacity = 1.0 if phase < 3 else 0.3
            dot.setStyleSheet(f"color: rgba(170, 170, 170, {int(opacity * 255)}); font-size: 16px;")

    def start_animation(self):
        self.animation_step = 0
        self.timer.start(150)

    def stop_animation(self):
        self.timer.stop()

class FancyTextEdit(QTextEdit):
    """Enhanced input field with animation and adaptive sizing"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Type a message…")
        self.setAcceptRichText(False)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        _ = self.parent().user_settings
        theme = _.loaded_theme['blendai']['input']

        style = _.get_style("blendai_input").format(_.get_color_or_image(theme["active_background"]),
                                                                        theme["text"],
                                                                        theme["inactive_border"],
                                                                        theme["hover_border"],
                                                                        theme["active_border"],
                                                                        _.get_color_or_image(theme["disabled_background"]),
                                                                        theme["disabled_text"],
                                                                        theme["disabled_border"])
        self.setStyleSheet(style)
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setOffset(0, 2)
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
        
        # Initial height
        self.setFixedHeight(41)
        self.setMaximumHeight(100)
        
        # Focus animation
        self.focus_animation = QPropertyAnimation(self, b"border_color", self)
        self.focus_animation.setDuration(200)
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.focus_animation.setStartValue(QColor("#444"))
        self.focus_animation.setEndValue(QColor("#4d5bce"))
        self.focus_animation.start()
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_animation.setStartValue(QColor("#4d5bce"))
        self.focus_animation.setEndValue(QColor("#444"))
        self.focus_animation.start()
        
    def get_border_color(self):
        return self.palette().color(self.backgroundRole())
    
    def set_border_color(self, color):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), color)
        self.setPalette(palette)
    
    border_color = Property(QColor, get_border_color, set_border_color)

class SendButton(QPushButton):
    """Enhanced send button with hover effects"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setIcon(QIcon(parent.parent().user_settings.get_icon("send")))
        self.setFixedSize(41, 41)
        us = self.parent().user_settings
        theme = us.loaded_theme["blendai"]["send_message"]
        g = us.get_color_or_image
        self.setStyleSheet(us.get_style("send_message").format(g(theme["inactive"]),
                                                               g(theme["hover"]),
                                                               g(theme["pressed"]),
                                                               g(theme["disabled"])))
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setOffset(0, 2)
        shadow.setBlurRadius(5)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(shadow)
        
        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"icon_size", self)
        self.hover_animation.setDuration(100)
        
    def enterEvent(self, event):
        self.hover_animation.setStartValue(QSize(16, 16))
        self.hover_animation.setEndValue(QSize(18, 18))
        self.hover_animation.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.hover_animation.setStartValue(QSize(18, 18))
        self.hover_animation.setEndValue(QSize(16, 16))
        self.hover_animation.start()
        super().leaveEvent(event)
        
    def get_icon_size(self):
        return self.iconSize()
    
    def set_icon_size(self, size):
        self.setIconSize(size)
    
    icon_size = Property(QSize, get_icon_size, set_icon_size)

class ChatWidget(QWidget):
    response_ready = Signal(dict)
    
    def __init__(self, user_settings, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self.blendai = BlendAI(user_settings.loaded_config["prompt"])
        self.message_count = 0
        self.thinking_animation = None
        
        # Set up main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 5, 15, 5)
        
        # Add BlendAI avatar to header
        path = self.parent().user_settings.get_icon("assistant", True)
        blendai_avatar = AvatarLabel(path,size=32)
        header_layout.addWidget(blendai_avatar)
        
        # Add title
        title = QLabel(f"{self.user_settings.loaded_theme['assistant']['name']} - {self.user_settings.loaded_theme['assistant']['description']}")
        title.setStyleSheet(self.user_settings.get_style("chat_title").format(self.user_settings.loaded_theme["text"]["default"]))
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Add to main layout
        layout.addWidget(header)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background: {self.user_settings.loaded_theme['blendai']['separator']};")
        layout.addWidget(separator)
        
        # Create scroll area with improved styling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        us = self.user_settings
        theme = us.loaded_theme["blendai"]["scroll"]
        g = us.get_color_or_image
        style = us.get_style("chat_scroll").format(g(theme["background"]), g(theme["handle"]))
        self.scroll_area.setStyleSheet(style)
        # Content inside scroll
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setContentsMargins(0, 10, 0, 10)
        self.scroll_layout.setSpacing(15)
        
        # Add welcome message
        self.add_ai_message(self.user_settings.loaded_theme['assistant']['entry_message'])
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, 1)
        
        # Input area
        input_area = QWidget()
        input_area.setObjectName("inputArea")
        theme = self.user_settings.get_color_or_image(self.user_settings.loaded_theme["blendai"]["input"]["area"])
        input_area.setStyleSheet(self.user_settings.get_style("chat_input_area").format(theme))
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(5, 5, 5, 5)
        input_layout.setSpacing(10)
        
        # Enhanced text input
        self.input = FancyTextEdit(self)
        self.input.textChanged.connect(self.adjust_input_height)
        input_layout.addWidget(self.input)
        
        # Enhanced send button
        self.send_btn = SendButton(self)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        # Add shadow to input area
        input_shadow = QGraphicsDropShadowEffect()
        input_shadow.setOffset(0, 4)
        input_shadow.setBlurRadius(15)
        input_shadow.setColor(QColor(0, 0, 0, 60))
        input_area.setGraphicsEffect(input_shadow)
        
        layout.addWidget(input_area)
        
        # Set up signals
        self.response_ready.connect(self.finalize_ai_response)
        
    def adjust_input_height(self):
        # Calculate required height based on content
        document_size = self.input.document().size().toSize()
        margins = self.input.contentsMargins()
        padding = 20  # Account for padding
        
        required_height = document_size.height() + margins.top() + margins.bottom() + padding
        required_height = max(41, min(required_height, 100))
        
        # Only animate if there's an actual change
        if required_height != self.input.height():
            animation = QPropertyAnimation(self.input, b"maximumHeight")
            animation.setDuration(100)
            animation.setStartValue(self.input.height())
            animation.setEndValue(required_height)
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()
            
            # Match send button height
            send_animation = QPropertyAnimation(self.send_btn, b"maximumHeight")
            send_animation.setDuration(100)
            send_animation.setStartValue(self.send_btn.height())
            send_animation.setEndValue(required_height)
            send_animation.setEasingCurve(QEasingCurve.OutCubic)
            send_animation.start()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            modifiers = event.modifiers()
            if modifiers == Qt.ShiftModifier:
                # Insert newline with Shift+Enter
                cursor = self.input.textCursor()
                cursor.insertText("\n")
            elif modifiers == Qt.NoModifier:
                # Send message with plain Enter
                self.send_message()
                event.accept()
                return
        super().keyPressEvent(event)
        
    def send_message(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
            
        # Add user message
        self.add_user_message(text)
        self.input.clear()
        self.input.setFocus()
        
        # Show thinking animation
        self.start_thinking_animation()
        
        # Get project data
        main_panel = self.parent()
        while main_panel and not hasattr(main_panel, "timeline"):
            main_panel = main_panel.parent()
            
        if main_panel:
            current_project_data = main_panel.project.project
            # Start AI response in separate thread
            threading.Thread(
                target=self.fetch_ai_reply,
                args=(text, current_project_data),
                daemon=True
            ).start()
            
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
        
    def fetch_ai_reply(self, user_input, project):
        response = self.blendai.summon_god(user_input, project)
        self.response_ready.emit(response)
        
    def start_thinking_animation(self):
        # Disable input while thinking
        self.input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # Create and start animation
        self.thinking_animation = ThinkingAnimation(self)
        self.scroll_layout.addWidget(self.thinking_animation)
        self.thinking_animation.start_animation()
        
        # Scroll to bottom
        self.scroll_to_bottom()
        
    def add_user_message(self, message):
        # Create message with user styling
        msg_widget = MessageWidget(message, is_user=True, parent=self)
        self.scroll_layout.addWidget(msg_widget)
        self.message_count += 1
        
        # Add spacer after every 2 messages for visual grouping
        if self.message_count % 2 == 0:
            spacer = QWidget()
            spacer.setFixedHeight(10)
            self.scroll_layout.addWidget(spacer)
            
        # Scroll to bottom
        self.scroll_to_bottom()
        
    def add_ai_message(self, message, animate=True):
        """Add AI message with typing animation effect"""
        # Create the message widget first with empty text
        msg_widget = MessageWidget("", is_user=False, parent=self)
        self.scroll_layout.addWidget(msg_widget)
        self.message_count += 1
        
        # Add spacer for visual grouping
        if self.message_count % 2 == 0:
            spacer = QWidget()
            spacer.setFixedHeight(10)
            self.scroll_layout.addWidget(spacer)
        
        # Scroll to bottom immediately to show typing is starting
        self.scroll_to_bottom()
        
        if animate:
            # Typing effect - gradually reveal message
            full_message = message
            current_text = ""
            
            # Define a function to update the text gradually
            def update_text():
                nonlocal current_text
                if not msg_widget.bubble:  # Safety check in case widget was destroyed
                    return
                    
                # Get next character(s) to add
                if len(current_text) < len(full_message):
                    # Calculate characters to add in this step
                    # Use a variable typing speed - faster for punctuation, slower for new sentences
                    if len(current_text) > 0 and full_message[len(current_text)-1] in ['.', '!', '?', '\n']:
                        # Add fewer characters after sentence end (pause effect)
                        chars_to_add = min(2, len(full_message) - len(current_text))
                    else:
                        # Normal typing speed - add 2-5 characters at once
                        chars_to_add = min(3 + (len(current_text) // 100), len(full_message) - len(current_text))
                    
                    # Add the next character(s)
                    current_text = full_message[:len(current_text) + chars_to_add]
                    
                    # Update bubble text
                    msg_widget.bubble.setText(current_text)
                    
                    # Scroll to follow typing
                    self.scroll_to_bottom()
                    
                    # Schedule next update
                    interval = 30  # Base typing speed in ms
                    if current_text and current_text[-1] in ['.', '!', '?']:
                        interval = 200  # Pause longer after sentences
                    elif current_text and current_text[-1] in [',', ';', ':']:
                        interval = 100  # Pause briefly after punctuation
                    
                    QTimer.singleShot(interval, update_text)
                else:
                    # Typing complete
                    pass
            
            # Start the typing animation
            QTimer.singleShot(10, update_text)
        else:
            # No animation, show full message immediately
            msg_widget.bubble.setText(message)
            self.scroll_to_bottom()

    # Modify finalize_ai_response to use the animation
    def finalize_ai_response(self, response):
        # Stop and remove thinking animation
        if self.thinking_animation:
            self.thinking_animation.stop_animation()
            self.thinking_animation.setParent(None)
            self.thinking_animation = None
            
        # Re-enable input
        self.input.setEnabled(True)
        self.send_btn.setEnabled(True)
        
        # Update project if needed
        try:
            if isinstance(response, dict) and "project" in response:
                new_data = response["project"]
                # Find main panel
                main_panel = self.parent()
                while main_panel and not hasattr(main_panel, "timeline"):
                    main_panel = main_panel.parent()
                    
                if main_panel and hasattr(main_panel.project, "load_from_dict"):
                    # Update project
                    main_panel.project.load_from_dict(new_data)
                    timeline = main_panel.timeline.timeline_body
                    timeline.project = main_panel.project
                    timeline.clear_all()
                    timeline.refresh_tracks()
                    timeline.update_elements()
                    
                    # Add success indicator
                    self.add_system_message("✅ Project updated successfully")
        except Exception as e:
            print(f"⚠️ Error processing AI response: {e}")
            self.add_system_message(f"⚠️ Error updating project: {str(e)}")
            
        # Add AI response with typing animation
        ai_response = response.get("response", "❓ No response found.")
        self.add_ai_message(ai_response, animate=True)
    def add_system_message(self, message):
        """Add small system notification"""
        notification = QLabel(message)
        notification.setAlignment(Qt.AlignCenter)
        notification.setStyleSheet(self.user_settings.get_style("system_notification").format(self.user_settings.get_color_or_image(self.user_settings.loaded_theme["blendai"]["system_notification"]),
                                                                         self.user_settings.loaded_theme["text"]["highlight"]))
        
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.addStretch()
        layout.addWidget(notification)
        layout.addStretch()
        
        self.scroll_layout.addWidget(container)
        self.scroll_to_bottom()
        
    def scroll_to_bottom(self):
        """Scroll to bottom of chat after layout is updated"""
        def do_scroll():
            scrollbar = self.scroll_area.verticalScrollBar()
            animation = QPropertyAnimation(scrollbar, b"value", self)
            animation.setDuration(300)
            animation.setStartValue(scrollbar.value())
            animation.setEndValue(scrollbar.maximum())
            animation.setEasingCurve(QEasingCurve.OutCubic)
            animation.start()

        QTimer.singleShot(0, do_scroll)

