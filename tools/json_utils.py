import json
import os

def safe_load_json(path, default=None):
    if default is None:
        default = []

    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except Exception as e:
        print(f"[ERROR] Failed to load JSON from {path}: {e}")
        return default
