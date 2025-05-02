
import cv2
from decord import VideoReader, cpu
from PIL import Image, ImageDraw, ImageFont
from . import keyframes as kf
from . import visual_effects as ve
import numpy as np

video_lenght_cache =   {}
def safe_overlay(canvas, x1, y1, cropped):
    h, w = cropped.shape[:2]
    if h == 0 or w == 0:
        return
    if cropped.shape[2] == 4:
        alpha = cropped[:, :, 3:] / 255.0
        overlay_rgb = cropped[:, :, :3]
        canvas[y1:y1 + h, x1:x1 + w] = (1 - alpha) * canvas[y1:y1 + h, x1:x1 + w] + alpha * overlay_rgb
    else:
        canvas[y1:y1 + h, x1:x1 + w] = cropped
def hex_to_bgr(hex_color):
    """Convertit une couleur hexadécimale (ex: "#FF0000") en tuple BGR."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (b, g, r)
def get_info(item,project_duration):
    lenght = 0 
    start = 0  
    if "timeline_position" in item:
        start = item.get("timeline_position")
        if item.get("type") == "video":
            timestamps = item.get("timestamps")
            if timestamps and timestamps[1] >= 0:
                    lenght = timestamps[1] - timestamps[0]
            elif timestamps[1] == -1:
                    if item.get("file_path") in video_lenght_cache:
                        lenght = video_lenght_cache[item.get("file_path")] - timestamps[0]
                    else :
                        vr = VideoReader(item["file_path"], ctx=cpu(0))
                        fps = vr.get_avg_fps()
                        full_duration = len(vr) / fps
                        video_lenght_cache[item.get("file_path")] = full_duration*1000
                        lenght = video_lenght_cache[item.get("file_path")]  - timestamps[0]
            elif timestamps[1] == -2:   
                if item.get("file_path") in video_lenght_cache:
                        lenght = video_lenght_cache[item.get("file_path")] - timestamps[0]
                else :
                        vr = VideoReader(item["file_path"], ctx=cpu(0))
                        fps = vr.get_avg_fps()
                        full_duration = len(vr) / fps
                        video_lenght_cache[item.get("file_path")] = full_duration*1000
                        lenght = video_lenght_cache[item.get("file_path")]  - timestamps[0]
                lenght = min((project_duration*1000) - start,lenght)

    elif "timeline_place" in item  :
        
        start = item.get("timeline_place")[0]
        end = item.get("timeline_place")[1]
        if end > 0  :
            lenght = end - start
        elif (end == -1) or (end == -2):
            lenght = (project_duration*1000)-start
    return start,lenght

def generate_frame(t, new_quality, project_duration, container_cache,base_quality,aspect_ratio,elements,get_z_level):
   
    base_w = int(base_quality * (aspect_ratio[0] / aspect_ratio[1]))
    base_h = base_quality
    new_w = int(new_quality * (aspect_ratio[0] / aspect_ratio[1]))
    new_h = new_quality
    scale_x = new_w / base_w
    scale_y = new_h / base_h

    canvas = np.zeros((new_h, new_w, 3), dtype=np.uint8)
    all_items = []
    # --- Collecte des items à afficher ---
    for item in elements:
        if not item.get("is_visible", True):
            continue

        media_type = item.get("type")
        if media_type == "video":
            timeline_pos = item.get("timeline_position", 0) / 1000.0
            timestamps = item.get("timestamps", [])
            if not timestamps:
                continue

            start_offset = timestamps[0] / 1000.0
            t_in_clip = t - timeline_pos  # temps dans la timeline depuis le placement
            if timestamps[1] == -2:
                # Cas spécial : le clip se joue jusqu'à la fin du projet
                effective_duration = project_duration - timeline_pos
            elif timestamps[1] == -1:
                path = item["file_path"]
                try:
                    if path not in container_cache:
                        vr = VideoReader(path, ctx=cpu(0))
                        container_cache[path] = vr
                    else:
                        vr = container_cache[path]
                    fps_video = vr.get_avg_fps()
                    total_duration = len(vr) / fps_video
                except Exception as e:
                    print(f"Erreur decord (durée vidéo) : {e}")
                    continue
                effective_duration = total_duration - start_offset

            else:
                effective_duration = (timestamps[1] - timestamps[0]) / 1000.0

            if 0 <= t_in_clip <= effective_duration:
                target_time = start_offset + t_in_clip
                item["__media_type"] = "video"
                item["__target_time"] = target_time
                all_items.append(item)

                    
        elif media_type in ["image", "text"]:
            timeline_place = item.get("timeline_place", [])
            if not timeline_place:
                continue
            start_time = timeline_place[0] / 1000.0
            end_time = project_duration if timeline_place[1] == -2 else timeline_place[1] / 1000.0
            if start_time <= t <= end_time:
                item["__media_type"] = media_type
                all_items.append(item)
                
    all_items.sort(key=get_z_level)
    # --- Décodage et composition ---
    for item in all_items:
        start, lenght = get_info(item,project_duration)
        # name = item.get("file_path")
        # print(f"{name} ; start : {start}, lenght : {lenght}\n")
     
        # print(f"{name} : {pos_percent} %")
        # pos_percent = item.get("position", [50, 50])
        media_type = item["__media_type"]

        if media_type == "video":
            timeline_pos = item.get("timeline_position", 0) / 1000.0
            # Calcul du temps relatif dans le clip
            t_in_clip = t - timeline_pos
            start_offset = item.get("timestamps", [0])[0] / 1000.0
            # Calcul de la frame cible : on lit à partir du start_offset dans le fichier
            target_time = t_in_clip + start_offset

            path = item["file_path"]
            # Utilisation d'un cache pour éviter de réouvrir la vidéo à chaque appel
            if path not in container_cache:
                try:
                    vr = VideoReader(path, ctx=cpu(0))
                except Exception as e:
                    print("Erreur lors de l'initialisation de VideoReader :", e)
                    continue
                container_cache[path] = vr
            else:
                vr = container_cache[path]

            fps_video = vr.get_avg_fps()
            frame_index = int(target_time * fps_video)

            try:
                frame = vr[frame_index].asnumpy()
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGRA)
            except Exception as e:
                print("Erreur lors du décodage avec decord :", e)
                continue

            image_scaled = cv2.resize(frame, (int(frame.shape[1] * scale_x), int(frame.shape[0] * scale_y)), interpolation=cv2.INTER_AREA)

        elif media_type == "image":
            image = cv2.imread(item["file_path"], cv2.IMREAD_UNCHANGED)
            if image is None:
                continue
            image_scaled = cv2.resize(image, (int(image.shape[1] * scale_x), int(image.shape[0] * scale_y)), interpolation=cv2.INTER_AREA)
            
        elif media_type == "text":
            content = item.get("text", "")
            font_size = int(item.get("font_size", 24) * scale_y)
            color = item.get("color", "white")
            font_path = item.get("file_path", "arial.ttf")
            try:
                font = ImageFont.truetype(font_path, font_size)
            except:
                font = ImageFont.load_default()

            # Mesure du texte avec bbox
            dummy_img = Image.new("RGBA", (1, 1))
            dummy_draw = ImageDraw.Draw(dummy_img)
            bbox = dummy_draw.textbbox((0, 0), content, font=font)

            # === Ajout d'un padding dynamique ===
            padding = int(font_size * 0.2)  # ou fixe: padding = 10
            text_w = (bbox[2] - bbox[0]) + 2 * padding
            text_h = (bbox[3] - bbox[1]) + 2 * padding

            # Création de l'image avec transparence et padding
            text_img = Image.new("RGBA", (text_w, text_h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(text_img)

            # Paramètres de contour
            bd_width = int(item.get("bd_width", 0))
            bd_color = item.get("bd_color", "black")

            # Position du texte avec padding (ajustement ligne de base)
            draw_pos = (padding, padding - bbox[1])

            if bd_width > 0:
                draw.text(draw_pos, content, font=font, fill=color,
                        stroke_width=bd_width, stroke_fill=bd_color)
            else:
                draw.text(draw_pos, content, font=font, fill=color)

            image_scaled = cv2.cvtColor(np.array(text_img), cv2.COLOR_RGBA2BGRA)
        
        pos_percent = kf.keyframe(t*1000,start,lenght,item.get("position"))
        pos_percent = pos_percent if len(pos_percent) >= 2 else pos_percent[0]
        image_scaled,shift = ve.apply_effects(item,image_scaled,t,start,lenght,canvas)
        iw, ih = image_scaled.shape[1], image_scaled.shape[0]
        if pos_percent != 0 :
            cx = int((pos_percent[0] / 100.0) * new_w) + shift[0]
            cy = int((pos_percent[1] / 100.0) * new_h) + shift[1]
            x1 = cx - iw // 2
            y1 = cy - ih // 2
            crop_x1 = max(0, -x1)
            crop_y1 = max(0, -y1)
            crop_x2 = iw - max(0, x1 + iw - new_w)
            crop_y2 = ih - max(0, y1 + ih - new_h)
            x1 = max(0, x1)
            y1 = max(0, y1)
            # Avant de faire le crop :
            if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
                continue  # L'élément est totalement hors de l'écran, on ignore
            
            
            cropped = image_scaled[crop_y1:crop_y2, crop_x1:crop_x2]
            safe_overlay(canvas, x1, y1, cropped)
    return canvas
