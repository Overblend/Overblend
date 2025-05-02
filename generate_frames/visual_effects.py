import numpy as np
import cv2
from . import keyframes as kf
import random
import math
import time
def stretch(image: np.ndarray,canvas, x: float = 1, y: float = 1) -> np.ndarray:
    """
    Étire une image selon les axes x et y sans conserver la taille d'origine.
    """
    if image is None or image.size == 0:
        return image
        
    h, w = image.shape[:2]
    # Calculer les nouvelles dimensions
    new_w = max(4, int(w * x))
    new_h = max(4, int(h * y))
    
    # Redimensionner l'image directement
    stretched = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    return stretched, (0,0)
def fit_stretch(image: np.ndarray, canvas: np.ndarray, x: float = 100, y: float = 100) -> tuple:
    """
    Adapte automatiquement l'image pour qu'elle corresponde à la taille du canvas,
    en utilisant une interpolation contrôlée par x et y :
    - x = 0 → aucun ajustement de largeur
    - x = 100 → largeur exactement adaptée au canvas
    - y = 0 → aucun ajustement de hauteur
    - y = 100 → hauteur exactement adaptée au canvas
    """
    if image is None or image.size == 0:
        return image, (0, 0)

    ih, iw = image.shape[:2]
    ch, cw = canvas.shape[:2]

    # ⚠️ Correctif : ratio centré (puisqu'image centrée = faut remplir à partir du centre)
    target_stretch_x = cw / iw
    target_stretch_y = ch / ih

    # Interpolation linéaire entre 1 et le stretch complet
    stretch_x = 1 + (target_stretch_x - 1) * (x / 100)
    stretch_y = 1 + (target_stretch_y - 1) * (y / 100)

    return stretch(image, canvas, stretch_x, stretch_y)
def fit_zoom(image: np.ndarray, canvas: np.ndarray, axis: float = 0.0, intensity: float = 1.0) -> tuple:
    """
    Effectue un zoom uniforme (sans déformation) pour que l'image tienne selon l'axe choisi :
    - axis = 0.0 → fit horizontal (largeur)
    - axis = 1.0 → fit vertical (hauteur)
    - valeurs intermédiaires interpolent entre les deux

    - intensity = 1.0 → applique complètement le fit
    - intensity = 0.0 → ne change rien
    """
    if image is None or image.size == 0:
        return image, (0, 0)

    ih, iw = image.shape[:2]
    ch, cw = canvas.shape[:2]

    # Calcul des zooms nécessaires par axe
    zoom_x = cw / iw
    zoom_y = ch / ih

    # Interpolation entre fit horizontal (axis=0) et vertical (axis=1)
    target_zoom = zoom_x * (1 - axis) + zoom_y * axis

    # Interpolation avec intensité : entre 1.0 (aucun zoom) et target_zoom
    final_zoom = 1 + (target_zoom - 1) * intensity

    return zoom(image, canvas, final_zoom)



def crop(image: np.ndarray,canvas, gauche: float = -1, droite: float = 1, haut: float = -1, bas: float = 1) -> tuple:
    """
    Coupe visuellement une image selon des pourcentages relatifs (-1 à 1) des bords.
    Retourne aussi le décalage de centre introduit par le crop.
    """
    if image is None or image.size == 0:
        return image, (0, 0)

    h, w = image.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1

    # Convertir les bords normalisés en coordonnées pixels
    x1 = int((gauche + 1) * 0.5 * w)
    x2 = int((droite + 1) * 0.5 * w)
    y1 = int((haut + 1) * 0.5 * h)
    y2 = int((bas + 1) * 0.5 * h)

    # Clamp sécurisés
    x1 = max(0, min(x1, w))
    x2 = max(0, min(x2, w))
    y1 = max(0, min(y1, h))
    y2 = max(0, min(y2, h))

    if x2 <= x1 or y2 <= y1:
        empty = np.zeros((h, w, channels), dtype=image.dtype)
        if channels == 4:
            empty[:, :, 3] = 0
        return empty, (0, 0)

    # Découpe
    cropped = image[y1:y2, x1:x2]

    # Calcul du shift relatif du centre
    cx_original = w // 2
    cy_original = h // 2
    cx_cropped = (x2 - x1) // 2
    cy_cropped = (y2 - y1) // 2

    shift_x = (x1 + cx_cropped) - cx_original
    shift_y = (y1 + cy_cropped) - cy_original

    return cropped, (shift_x, shift_y)
def crop_screen(image: np.ndarray,canvas, x1: float, x2: float, y1: float, y2: float) -> tuple:
    """
    Coupe l'image selon une zone définie en pourcentages du canvas (x1, x2, y1, y2).
    Rend les zones hors crop transparentes mais garde la taille de l'image.
    
    x1, x2 : 0–100 (horizontal) — zone visible sur le canvas
    y1, y2 : 0–100 (vertical)
    
    Retourne : image modifiée, shift (toujours (0, 0) ici)
    """
    if image is None or image.size == 0:
        return image, (0, 0)

    ih, iw = image.shape[:2]
    ch, cw = canvas.shape[:2]
    channels = image.shape[2] if image.ndim == 3 else 1

    # Calculer les bornes visibles en pixels (dans l'espace du canvas)
    crop_left = (x1 / 100) * cw
    crop_right = (x2 / 100) * cw
    crop_top = (y1 / 100) * ch
    crop_bottom = (y2 / 100) * ch

    # Position de l'image centrée sur le canvas
    cx = cw // 2
    cy = ch // 2
    x_img_start = cx - iw // 2
    y_img_start = cy - ih // 2

    # Créer un masque transparent (RGBA ou BGR)
    result = np.copy(image)
    if channels == 3:
        result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
    elif channels == 1:
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGRA)

    # Calcul de la zone visible dans l'image
    for y in range(ih):
        for x in range(iw):
            canvas_x = x_img_start + x
            canvas_y = y_img_start + y

            if (canvas_x < crop_left or canvas_x > crop_right or
                canvas_y < crop_top or canvas_y > crop_bottom):
                result[y, x, 3] = 0  # Transparence

    return result, (0, 0)
def opacity(image: np.ndarray, canvas: np.ndarray, alpha: float = 100) -> tuple:
    """
    Applique une opacité à l'image.
    - alpha : 0 à 100 (% de visibilité)
    - gère les images avec ou sans canal alpha
    """
    if image is None or image.size == 0:
        return image, (0, 0)

    # Clamp l'opacité entre 0 et 100
    alpha = max(0, min(100, alpha))
    alpha_scale = alpha / 100.0

    # Ajout alpha si absent
    if image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # Appliquer le facteur d’opacité (en multipliant le canal alpha)
    image = image.copy()
    image[:, :, 3] = (image[:, :, 3].astype(np.float32) * alpha_scale).astype(np.uint8)

    return image, (0, 0)
def blur(image: np.ndarray, canvas: np.ndarray, strength: float = 0) -> tuple:
    """
    Applique un flou gaussien à l'image.
    - strength : intensité du flou (0 = aucun, jusqu'à ~100+)
    """
    if image is None or image.size == 0 or strength <= 0:
        return image, (0, 0)

    # Convertit strength en un kernel impair pour GaussianBlur
    kernel_size = max(1, int(strength))
    if kernel_size % 2 == 0:
        kernel_size += 1

    blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    return blurred, (0, 0)

def rotate(image: np.ndarray, canvas: np.ndarray, x: float = 0) -> tuple:
    """
    Fait tourner l'image autour de son centre sans cropper le contenu.
    L'image résultante est agrandie pour contenir tout le contenu tourné.
    """
    if image is None or image.size == 0:
        return image, (0, 0)

    h, w = image.shape[:2]
    angle = -x  # convention: positif = horaire

    # Ajout alpha si absent
    if image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # Matrice de rotation
    center = (w / 2, h / 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Calcul nouvelle taille
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    # Ajuster la matrice de rotation pour la translation
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]

    # Appliquer la rotation
    rotated = cv2.warpAffine(image, M, (new_w, new_h), flags=cv2.INTER_LINEAR,
                             borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))

    return rotated, (0, 0)
def shadow(image: np.ndarray, canvas: np.ndarray, x: float = 10, y: float = 10, opacity: float = 100, blur_strength: float = 5, color: str = "#000000") -> tuple:
    """
    Ajoute une ombre portée à l'image.
    
    - x, y : décalage de l’ombre en pixels
    - opacity : transparence de l’ombre (0–100)
    - color : couleur de l’ombre (hex: "#000000")
    - blur_strength : niveau de flou de l’ombre
    """
    if image is None or image.size == 0:
        return image, (0, 0)

    ih, iw = image.shape[:2]

    # Forcer l’image en BGRA
    if image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # Convertir la couleur hex en BGR
    hex_color = color.lstrip('#')
    b = int(hex_color[4:6], 16)
    g = int(hex_color[2:4], 16)
    r = int(hex_color[0:2], 16)

    # Création de l’ombre de la même taille que l’image
    shadow = np.zeros_like(image)

    # Canal alpha de l’ombre basé sur l’original
    alpha = (image[:, :, 3].astype(np.float32) * (opacity / 100.0)).astype(np.uint8)

    for c in range(3):  # BGR
        shadow[:, :, c] = [b, g, r][c]
    shadow[:, :, 3] = alpha

    # Flouter l’ombre
    k = max(1, int(blur_strength))
    if k % 2 == 0: k += 1
    shadow = cv2.GaussianBlur(shadow, (k, k), 0)

    # Créer un canevas plus grand si l’ombre dépasse
    dx, dy = int(x), int(y)
    pad_top = max(0, -dy)
    pad_bottom = max(0, dy)
    pad_left = max(0, -dx)
    pad_right = max(0, dx)

    pad_img = cv2.copyMakeBorder(image, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=(0,0,0,0))
    pad_shadow = cv2.copyMakeBorder(shadow, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=(0,0,0,0))

    # Appliquer le décalage
    h, w = pad_img.shape[:2]
    final = np.zeros((h, w, 4), dtype=np.uint8)

    # Superposer l’ombre
    y1, y2 = dy + pad_top, dy + pad_top + ih
    x1, x2 = dx + pad_left, dx + pad_left + iw

    y1, y2 = max(0, y1), min(h, y2)
    x1, x2 = max(0, x1), min(w, x2)

    alpha_s = pad_shadow[:, :, 3:] / 255.0
    alpha_i = 1 - alpha_s
    final = pad_shadow.copy()
    final[:, :, :3] = (alpha_s * pad_shadow[:, :, :3] + alpha_i * final[:, :, :3]).astype(np.uint8)

    # Fusion de l’image originale par-dessus
    mask = pad_img[:, :, 3:] / 255.0
    final[:, :, :3] = (mask * pad_img[:, :, :3] + (1 - mask) * final[:, :, :3]).astype(np.uint8)
    final[:, :, 3] = np.maximum(final[:, :, 3], pad_img[:, :, 3])

    return final, (0, 0)
def mirror(image: np.ndarray, canvas: np.ndarray, x: float = 0, y: float = 0) -> tuple:
    """
    Applique un effet miroir partiel sur les axes X et Y.
    x = 0 → aucun miroir horizontal ; x = 1 → 100% miroir horizontal.
    y = 0 → aucun miroir vertical ; y = 1 → 100% miroir vertical.
    Valeurs intermédiaires blendent avec l'image originale.
    """
    if image is None or image.size == 0:
        return image, (0, 0)

    h, w = image.shape[:2]
    mirrored = image.copy()

    # Assurer BGRA
    if mirrored.shape[2] == 3:
        mirrored = cv2.cvtColor(mirrored, cv2.COLOR_BGR2BGRA)

    # --- Miroir horizontal ---
    if x > 0:
        mirror_x = cv2.flip(mirrored, 1)
        alpha_x = np.full((h, w, 1), min(1, max(0, x)), dtype=np.float32)
        mirrored = (alpha_x * mirror_x + (1 - alpha_x) * mirrored).astype(np.uint8)

    # --- Miroir vertical ---
    if y > 0:
        mirror_y = cv2.flip(mirrored, 0)
        alpha_y = np.full((h, w, 1), min(1, max(0, y)), dtype=np.float32)
        mirrored = (alpha_y * mirror_y + (1 - alpha_y) * mirrored).astype(np.uint8)

    return mirrored, (0, 0)

def zoom(image: np.ndarray,canvas, zoom: float = 1) -> np.ndarray : 
    '''
    Applique un effet de zoom sur l'image.
    '''
    return stretch(image,canvas,zoom,zoom)
def grayscale(image: np.ndarray, canvas: np.ndarray, x: float = 1.0) -> tuple:
    """
    Applique un effet de désaturation (noir & blanc) avec intensité progressive.

    x = 0 → aucune désaturation
    x = 1 → noir et blanc complet
    """
    if image is None or image.size == 0 or x <= 0:
        return image, (0, 0)
    x = min(max(x, 0), 1)  # Clamp 0..1

    # Assurer qu'on travaille en BGRA
    if image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    bgr = image[:, :, :3]
    alpha = image[:, :, 3] if image.shape[2] == 4 else None

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    blended = cv2.addWeighted(gray_bgr, x, bgr, 1 - x, 0)

    if alpha is not None:
        final = np.dstack((blended, alpha))
    else:
        final = blended

    return final, (0, 0)
def shake(image: np.ndarray, canvas: np.ndarray, intensity: float = 10.0, frequency: float = 1.0) -> tuple:
    """
    Applique un effet de tremblement via un décalage positionnel aléatoire.

    intensity : amplitude max en pixels
    frequency : combien de changements par seconde (~1 = calme, ~30 = très rapide)

    Retourne l'image inchangée + un décalage (x, y)
    """
    if intensity <= 0:
        return image, (0, 0)

    # Obtenir un pseudo-random cohérent basé sur le temps/frame
    key = int(time.time() * frequency * 10)  # stable sur quelques frames

    random.seed(key)
    dx = int(random.uniform(-1, 1) * intensity)
    dy = int(random.uniform(-1, 1) * intensity)

    return image, (dx, dy)

def smooth_shake(image: np.ndarray, canvas: np.ndarray, intensity: float = 10.0, frequency: float = 1.0) -> tuple:
    """
    Effet de tremblement fluide basé sur des sinusoïdes.
    
    - intensity : amplitude max du décalage en pixels
    - frequency : vitesse du tremblement (1 = lent, 10 = rapide)

    Retourne l'image inchangée + shift (x, y)
    """
    if intensity <= 0:
        return image, (0, 0)

    t = time.time()  # temps actuel en secondes
    dx = int(math.sin(t * frequency * 2 * math.pi) * intensity)
    dy = int(math.cos(t * frequency * 2 * math.pi) * intensity)

    return image, (dx, dy)
def vignette(image: np.ndarray, canvas: np.ndarray, intensity: float = 0.5, softness: float = 0.5) -> tuple:
    """
    Ajoute une vraie vignette noire sur les bords de l'image.

    - intensity : 0 (aucun effet) → 1 (bords totalement noirs)
    - softness : 0 (bord dur) → 1 (bord très flou)
    """
    if image is None or image.size == 0 or intensity <= 0:
        return image, (0, 0)

    h, w = image.shape[:2]
    center_x, center_y = w / 2, h / 2

    # Génération de la map radiale
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    max_dist = np.sqrt(center_x**2 + center_y**2)
    
    softness = np.clip(softness, 0.01, 1.0)
    vignette_mask = dist / max_dist
    vignette_mask = np.clip((vignette_mask - (1 - softness)) / softness, 0, 1)
    vignette_mask = vignette_mask * intensity  # applique l'intensité réelle

    # Étendre en 3 canaux
    vignette_layer = np.stack([vignette_mask]*3, axis=-1)

    if image.shape[2] == 4:
        rgb = image[:, :, :3].astype(np.float32)
        alpha = image[:, :, 3:]
    else:
        rgb = image.astype(np.float32)
        alpha = None

    # On multiplie les bords par (1 - masque) pour noircir
    rgb *= (1 - vignette_layer)

    output = rgb.astype(np.uint8)

    if alpha is not None:
        output = np.dstack([output, alpha])

    return output, (0, 0)
def pixellise(image: np.ndarray, canvas: np.ndarray, size: float = 10) -> tuple:
    """
    Applique un effet de pixellisation à l'image.

    - size : taille des pixels (plus grand = plus pixelisé)
    """
    if image is None or image.size == 0 or size <= 1:
        return image, (0, 0)

    h, w = image.shape[:2]
    small_w = max(1, int(w // size))
    small_h = max(1, int(h // size))

    # Réduction → agrandissement pour pixelisation
    temp = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_NEAREST)
    pixelated = cv2.resize(temp, (w, h), interpolation=cv2.INTER_NEAREST)

    return pixelated, (0, 0)
def pixellise_region(image: np.ndarray, canvas: np.ndarray, x1: float, x2: float, y1: float, y2: float, size: float = 10) -> tuple:
    """
    Pixellise une région spécifique de l'image.

    - x1, x2, y1, y2 : bornes de la zone (0–100), en % de la largeur/hauteur
    - size : taille du pixel dans cette zone
    """
    if image is None or image.size == 0 or size <= 1:
        return image, (0, 0)

    h, w = image.shape[:2]

    # Calcul des coordonnées en pixels
    px1 = int((x1 / 100) * w)
    px2 = int((x2 / 100) * w)
    py1 = int((y1 / 100) * h)
    py2 = int((y2 / 100) * h)

    # Clamp
    px1, px2 = max(0, px1), min(w, px2)
    py1, py2 = max(0, py1), min(h, py2)

    if px2 <= px1 or py2 <= py1:
        return image, (0, 0)

    # Découpe de la zone à pixelliser
    region = image[py1:py2, px1:px2]
    region_pixelated, _ = pixellise(region, canvas, size)

    # Création d'une copie de l'image et remplacement de la région
    result = image.copy()
    result[py1:py2, px1:px2] = region_pixelated

    return result, (0, 0)
def region(image: np.ndarray, canvas: np.ndarray, x1: float, x2: float, y1: float, y2: float, *args, static):
    h, w = image.shape[:2]

    # Calcul des coordonnées en pixels
    px1 = int((x1 / 100) * w)
    px2 = int((x2 / 100) * w)
    py1 = int((y1 / 100) * h)
    py2 = int((y2 / 100) * h)

    # Clamp
    px1, px2 = max(0, px1), min(w, px2)
    py1, py2 = max(0, py1), min(h, py2)

    if px2 <= px1 or py2 <= py1:
        return image, (0, 0)

    region_crop = image[py1:py2, px1:px2]

    # Appliquer l'effet sur la région (ou l'image entière si demandé)
    if isinstance(static, str):
        region_mod, _ = FUNCTION_MAPPINGS.get(static)(region_crop, canvas, *args)
    else:
        func_name = static.get("name")
        extra = static.get("static")
        region_mod, _ = FUNCTION_MAPPINGS.get(func_name)(region_crop, canvas, *args, static=extra)

    # Assure le bon nombre de canaux (BGRA)
    if region_mod.shape[2] == 3:
        region_mod = cv2.cvtColor(region_mod, cv2.COLOR_BGR2BGRA)
    if image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # Fusion additive dans la zone d'origine
    result = image.copy()
    target = result[py1:py2, px1:px2]

    # Gestion alpha
    alpha = region_mod[:, :, 3:] / 255.0
    blended = (1 - alpha) * target[:, :, :3] + alpha * region_mod[:, :, :3]
    result[py1:py2, px1:px2, :3] = blended.astype(np.uint8)
    result[py1:py2, px1:px2, 3] = np.maximum(target[:, :, 3], region_mod[:, :, 3])

    return result, (0, 0)
# Combine everything into one utility function
lut_cache = {}

def trilinear_lut_lookup(rgb_img: np.ndarray, lut: np.ndarray, size: int) -> np.ndarray:
    h, w = rgb_img.shape[:2]
    img = rgb_img.copy()

    r = img[:, :, 0] * (size - 1)
    g = img[:, :, 1] * (size - 1)
    b = img[:, :, 2] * (size - 1)

    r0 = np.floor(r).astype(int)
    g0 = np.floor(g).astype(int)
    b0 = np.floor(b).astype(int)

    r1 = np.clip(r0 + 1, 0, size - 1)
    g1 = np.clip(g0 + 1, 0, size - 1)
    b1 = np.clip(b0 + 1, 0, size - 1)

    fr = r - r0
    fg = g - g0
    fb = b - b0

    c000 = lut[r0, g0, b0]
    c001 = lut[r0, g0, b1]
    c010 = lut[r0, g1, b0]
    c011 = lut[r0, g1, b1]
    c100 = lut[r1, g0, b0]
    c101 = lut[r1, g0, b1]
    c110 = lut[r1, g1, b0]
    c111 = lut[r1, g1, b1]

    c00 = c000 * (1 - fr)[:, :, None] + c100 * fr[:, :, None]
    c01 = c001 * (1 - fr)[:, :, None] + c101 * fr[:, :, None]
    c10 = c010 * (1 - fr)[:, :, None] + c110 * fr[:, :, None]
    c11 = c011 * (1 - fr)[:, :, None] + c111 * fr[:, :, None]

    c0 = c00 * (1 - fg)[:, :, None] + c10 * fg[:, :, None]
    c1 = c01 * (1 - fg)[:, :, None] + c11 * fg[:, :, None]

    c = c0 * (1 - fb)[:, :, None] + c1 * fb[:, :, None]
    
    return np.clip(c, 0, 1)
def lut(image: np.ndarray, canvas, intensity: float, static: str) -> tuple:
    """
    Applique un LUT (.cube) RGB à une image OpenCV BGR avec interpolation trilineaire.
    """
    if intensity <= 0:
        return image, (0, 0)
    intensity = np.clip(intensity / 100.0, 0, 1)

    # --- Load LUT from cache or disk
    if static in lut_cache:
        lut_array, size = lut_cache[static]
    else:
        lut_data = []
        size = None
        try:
            with open(static, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('LUT_3D_SIZE'):
                        size = int(line.split()[1])
                    elif any(line.startswith(k) for k in ['TITLE', 'DOMAIN_MIN', 'DOMAIN_MAX']):
                        continue
                    else:
                        parts = line.split()
                        if len(parts) == 3:
                            # Stockage en format BGR pour OpenCV (inverse de RGB)
                            r, g, b = [float(p) for p in parts]
                            lut_data.append([b, g, r])  # Inverser RGB → BGR
            if size is None or len(lut_data) != size ** 3:
                raise ValueError(f"LUT file '{static}' is invalid or corrupted.")
            lut_array = np.array(lut_data, dtype=np.float32).reshape((size, size, size, 3))
            lut_cache[static] = (lut_array, size)
        except Exception as e:
            print(f"[LUT ERROR] Impossible de charger le fichier '{static}' : {e}")
            return image, (0, 0)

    # --- Préparation image
    if image.shape[2] == 4:
        bgr = image[:, :, :3]
        alpha = image[:, :, 3:]
    else:
        bgr = image
        alpha = None

    # Normaliser l'image BGR pour la LUT
    bgr_norm = bgr.astype(np.float32) / 255.0

    # Appliquer la LUT directement sur l'image BGR (sans conversion)
    mapped = trilinear_lut_lookup(bgr_norm, lut_array, size)
    mapped_bgr = (mapped * 255).astype(np.uint8)

    # Blending entre l'original et le LUT
    blended = (bgr * (1 - intensity) + mapped_bgr * intensity).astype(np.uint8)

    # Restaurer alpha s'il existe
    if alpha is not None:
        result = np.concatenate([blended, alpha], axis=2)
    else:
        result = blended

    return result, (0, 0)


def remove_args(input_dict):
    """
    Returns a copy of the input dictionary with any entries having the key "static - args" removed.
    
    Args:
        input_dict (dict): The dictionary to process
        
    Returns:
        dict: A new dictionary without "static - args" entries
    """
    return {key: value for key, value in input_dict.items() if key != "args"}

FUNCTION_MAPPINGS = {
    "stretch": stretch,
    "zoom": zoom,
    "fit_stretch" : fit_stretch,
    "fit_zoom": fit_zoom,
    "crop": crop,
    "crop_screen" : crop_screen,
    "rotate" : rotate,
    "opacity" : opacity,
    "blur" : blur,
    "shadow" : shadow,
    "mirror" : mirror,
    "grayscale": grayscale,
    "shake" : shake,
    "smooth_shake" : smooth_shake,
    "vignette": vignette,
    "pixellise": pixellise,
    "pixellise_region": pixellise_region,
    "region" : region,
    "lut" : lut

}



def apply_effects(item,image: np.ndarray,t,start,lenght,canvas):
    effects = item.get("visual_effects", {})
    canvas = canvas
    position_changes = [0,0]
    for _, ef in effects.items():
        for key,value in ef.items() :
            func = FUNCTION_MAPPINGS.get(key)
            arg = value.get("args")
            value = kf.keyframe(t*1000,start,lenght,remove_args(value) if (arg is not None) else value)
            value = value if len(value) >= 2 else value[0]
            delta = [0,0]
            if isinstance(value,tuple) or isinstance(value,list):
                if arg is not None : 
                    image,delta = func(image,canvas,*value,static = arg)
                else : 
                    image,delta = func(image,canvas,*value)
            else :
                if arg is not None :
                    image,delta = func(image,canvas,value,static = arg)
                else :
                    image,delta = func(image,canvas,value)
            position_changes[0] += delta[0]
            position_changes[1] += delta[1]
    return image,position_changes
    