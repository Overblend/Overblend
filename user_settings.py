import json, os
from PySide6.QtGui import QIcon, QFont, QFontDatabase

class UserSettings:
    DEFAULT_CONFIG = {
        "theme": "default",
        "lang": "en",
        "on_start_file": "untitled.json",
        "ui": {
            "window_width": 1000,
            "window_height": 500,
            "sidebar_width": 100,
            "preview_height": 315,
            "track_height": 60,
            "timeline_left_padding": 100,
            "timeline_right_padding": 0,
            "pixels_per_second_max": 200000,
            "maximize_on_start": True
        },
        "slider": {
            "preview_slider_precision": 1000
        },
        "autosave": {
            "active": True,
            "interval": 5
        },
        "target_ruler_spacing": 50,
        "prompt": "Sois un assistant agréable",
        "token": "token-example"
    }
    def __init__(self, theme_path="settings/themes.json", lang_path="settings/lang.json"):
        #Path Settings
        self.settings_path = self.get_or_create_settings_path()
        self.theme_path = theme_path
        self.lang_path = lang_path
        self.base_path = os.getcwd()

        self.default_theme = None
        self.available_langs = None
        #User Choices    
        self.loaded_config = None
        self.loaded_theme = None
        self.loaded_lang = None
        #Initial Load 
        self.load_config()
        self.load_default_theme()
        self.load_theme(self.loaded_config["theme"])
        self.load_language(self.loaded_config["lang"])
        #Sidebar Buttons 
        self.buttons = [
            ("toolkits", self.get_icon("toolkits")),
            ("blendai", self.get_icon("blendai")),
            ("video", self.get_icon("video")),
            ("audio_fix", self.get_icon("audio_fix")),
            ("subtitles", self.get_icon("subtitles")),
            ("text", self.get_icon("text")),
            ("elements", self.get_icon("elements")),
            ("settings", self.get_icon("settings")),
        ]
    def get_or_create_settings_path(self):
        appdata = os.getenv('APPDATA')
        if not appdata:
            raise Exception("APPDATA environment variable not found. Are you on Windows?")
        
        overblend_folder = os.path.join(appdata, 'Overblend')
        if not os.path.exists(overblend_folder):
            os.makedirs(overblend_folder)

        config_path = os.path.join(overblend_folder, 'config.json')
        
        if not os.path.exists(config_path):
            # Créer un fichier config par défaut
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        
        return config_path
    def load_config(self):
        with open(self.settings_path, "r") as f:
            self.loaded_config = json.load(f)
    def load_default_theme(self):
        with open(self.theme_path, "r") as f:
            themes = json.load(f)
        self.default_theme = themes.get("default",{})
    def load_theme(self,name):
        with open(self.theme_path, "r") as f:
            themes = json.load(f)
        self.loaded_theme = themes.get(name,{})
    def load_language(self,language):
        with open(self.lang_path, "r", encoding="utf-8") as f:
            langs = json.load(f)
        self.loaded_lang = langs.get(language, {})
        self.available_langs = list(langs.keys())

    def get_icon(self, name: str,only_path = False) -> QIcon:
        path = self.loaded_theme.get("icons",{}).get(name,False)
        if not path:
            # fallback to default theme
            path = self.default_theme.get("icons", {}).get(name)
            if not path:
                if only_path :
                    return ""
                return QIcon()
        if only_path :
            return path
        return QIcon(path)
    def get_style(self,name: str) -> str:
        style = self.loaded_theme.get("styles",{}).get(name,False)
        if not style : 
            return self.default_theme["styles"].get(name)
        return style
    def get_color_or_image(self, result, parent=None):
        if not result:
            return ""

        # Cas 1 – Couleur HEX ou rgb()
        if isinstance(result, str) and (result.strip().startswith("#") or result.strip().lower().startswith("rgb")):
            return f"background: {result};"

        # Cas 2 – Image ou gif : retourne une ligne QSS
        if isinstance(result, str) and os.path.isfile(result):
            return f"""
                background-image: url({result});
                background-position: center;
                background-repeat: no-repeat;
            """

        return ""

    def translate(self, key: str) -> str:
        return self.loaded_lang.get(key.lower(), key)
    
    def apply_global_font(self, app):
        font_info = self.loaded_theme["font"]
        if font_info == "default": # Default Font
            return
        if font_info.endswith(".ttf") or font_info.endswith(".otf"): #File Font
            font_id = QFontDatabase.addApplicationFont(font_info)
            if font_id != -1:
                loaded_families = QFontDatabase.applicationFontFamilies(font_id)
                if loaded_families:
                    font_family = loaded_families[0]
                    self.loaded_font_family = font_family
                    font = QFont(font_family)
                    app.setFont(font)
        else: #System Fonts
            font = QFont(font_info)
            app.setFont(font)
