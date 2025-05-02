import os
import concurrent.futures
from tqdm import tqdm
import cv2
import time

def render_video(filename, length, export_fps, export_quality, aspect_ratio, 
                generate_frame, base_quality, elements, get_z_level, active_section=[0,-1]):
    """
    Version optimisée pour réduire la charge CPU et éviter le freeze du système.
    """
    # 1. Configuration initiale avec vérifications
    if active_section[1] == -1:
        total_frames = int(length * export_fps)
    else:
        total_frames = int(active_section[1] * export_fps / 1000)  # Correction du facteur 1/1000
    start_frame = int(active_section[0] * export_fps / 1000)
    
    print(f"Export: durée = {length:.2f}s, total frames = {total_frames - start_frame}")

    # 2. Préparation du VideoWriter
    new_w = int(export_quality * (aspect_ratio[0] / aspect_ratio[1]))
    new_h = export_quality
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(filename, fourcc, export_fps, (new_w, new_h))
     
    if not out.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir {filename} pour l'écriture")

    # 3. Paramètres d'optimisation
    MAX_WORKERS = min(4, os.cpu_count() or 1)  # Limité à 4 workers maximum
    CHUNK_SIZE = 10  # Nombre de frames à traiter par batch
    THROTTLE_DELAY = 0.01  # Délai entre les batches pour réduire la charge CPU

    def task(t):
        return generate_frame(t, export_quality, length, {}, base_quality, aspect_ratio, elements, get_z_level)

    # 4. Génération et écriture progressive avec contrôle de charge
    try:
        with tqdm(total=total_frames - start_frame, desc="🧠 Génération des frames") as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Découpage en chunks pour mieux contrôler la charge
                times = [i / export_fps for i in range(start_frame, total_frames)]
                
                future_to_time = {
                    executor.submit(task, time): time 
                    for time in times
                }
                
                completed = 0
                for future in concurrent.futures.as_completed(future_to_time):
                    try:
                        frame = future.result()
                        out.write(frame)
                        completed += 1
                        pbar.update(1)
                        
                        # Affichage progressif moins fréquent
                        if completed % 50 == 0:
                            print(f"Export: {completed}/{total_frames - start_frame} frames")
                        
                        # Délai artificiel pour réduire la charge CPU
                        time.sleep(THROTTLE_DELAY)
                            
                    except Exception as e:
                        print(f"Erreur sur la frame: {e}")
                        continue

    except KeyboardInterrupt:
        print("\nExport interrompu par l'utilisateur")
    finally:
        out.release()
        print(f"Export terminé : {filename}")
def render_image(filename, t, export_fps, export_quality, aspect_ratio, 
                generate_frame, base_quality, elements, get_z_level):
    """
    Fonction pour générer une image à un temps spécifique.
    """
    
    # 1. Génération de l'image
    frame = generate_frame(t / 1000, export_quality, 1, {}, base_quality, aspect_ratio, elements, get_z_level)
    
    # 2. Enregistrement de l'image
    cv2.imwrite(filename, frame)
    
    return filename