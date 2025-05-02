
import math
from collections.abc import Sequence

# Nouveau TEST_DATA avec vecteurs


# Fonctions easing
def linear_interp(p): return p
def ease_in(p): return p**2
def ease_out(p): return 1 - (1 - p)**2
def ease_in_out(p): return 3 * p**2 - 2 * p**3
def bounce(p): return abs(math.sin(6.28 * p * (1 - p))) * (1 - p)
def elastic(p): return math.sin(13 * math.pi * p) * math.pow(2, -10 * p) + 1 if p < 1 else 1
def step_interp(p): return 0
def bezier_interp(p): return p**3 * (p * (6*p - 15) + 10)

EASING_FUNCTIONS = {
    "linear": linear_interp,
    "ease_in": ease_in,
    "ease_out": ease_out,
    "ease_in_out": ease_in_out,
    "bounce": bounce,
    "elastic": elastic,
    "step": step_interp,
    "bezier": None,  # handled separately
    "cubic": ease_in_out,
}

# Bézier personnalisée
def cubic_bezier(x1, y1, x2, y2, t, epsilon=1e-5, iterations=20):
    def bezier_coord(a1, a2, t):
        return 3 * a1 * (1 - t)**2 * t + 3 * a2 * (1 - t) * t**2 + t**3

    def bezier_derivative(a1, a2, t):
        return 3 * (1 - t)**2 * a1 + 6 * (1 - t) * t * (a2 - a1) + 3 * t**2 * (1 - a2)

    p = t
    for _ in range(iterations):
        x = bezier_coord(x1, x2, p)
        dx = bezier_derivative(x1, x2, p)
        if dx == 0:
            break
        p -= (x - t) / dx
        p = max(0, min(1, p))
    return bezier_coord(y1, y2, p)

# Interpolation générique
def interpolate_value(start, end, percent, mode, bezier_params=None):
    if mode == "bezier" and bezier_params:
        x1, y1, x2, y2 = bezier_params
        easing_val = cubic_bezier(x1, y1, x2, y2, percent)
    else:
        easing = EASING_FUNCTIONS.get(mode, linear_interp)
        easing_val = easing(percent)
    return start + (end - start) * easing_val

def interpolate(data, i, length, t, mode):
    keys = sorted(data.keys())
    k1, k2 = keys[i-1], keys[i]
    t1 = k1 * length / 100
    t2 = k2 * length / 100
    percent = (t - t1) / (t2 - t1)
    percent = max(0, min(1, percent))

    start = data[k1][1]
    end = data[k2][1]
    bezier_params = data[k2][2] if len(data[k2]) > 2 else None

    if isinstance(start, Sequence) and not isinstance(start, str):
        return tuple(
            interpolate_value(s, e, percent, mode, bezier_params)
            for s, e in zip(start, end)
        )
    else:
        return interpolate_value(start, end, percent, mode, bezier_params)

def hold(data, i):
    keys = sorted(data.keys())
    return data[keys[i-1]][1]
def keyframe(t, position, length, data):
    delta = t - position
    if delta < 0 or delta >= length:
        return (0,)  # Toujours un tuple

    data = {int(x): data[x] for x in data}
    keys = sorted(data.keys())
    i = 0
    for timestamp in keys:
        time_in_clip = timestamp * length / 100
        if delta <= time_in_clip:
            mode = data[timestamp][0]
            if mode == "start":
                val = data[timestamp][1]
            elif mode == "hold":
                val = hold(data, i)
            else:
                val = interpolate(data, i, length, delta, mode)
            return val if isinstance(val, tuple) else (val,)
        i += 1

    # Dernière valeur
    val = data[keys[-1]][1]
    return val if isinstance(val, tuple) else (val,)


# if __name__ == "__main__":
    # import matplotlib.pyplot as plt
    # TEST_DATA = {
    #     "0": ["start", (20, 50)],
    #     "10": ["linear", (100, 0)],
    #     "60": ["elastic", (-100, 200)],
    #     "70": ["step", (-100, 0)],
    #     "80": ["bezier", (0, -200), (0.42, -1, 0.58, 1)],
    #     "100": ["hold", (0, 0)]
    # }

    # POSITION = 0
    # # Graphe
    # times = list(range(0, 9000, 100))
    # values = [keyframe(t, POSITION, 5000, TEST_DATA) for t in times]
    # # === GRAPHE TRAJECTOIRE 2D ===
    # # Interprétation de values comme des positions (x, y)
    # positions = [v if len(v) >= 2 else (v[0], 0) for v in values]
    # xs = [pos[0] for pos in positions]
    # ys = [pos[1] for pos in positions]
    # import matplotlib.animation as animation

    # # Préparation de l'animation
    # fig, ax = plt.subplots(figsize=(8, 8))
    # ax.set_title("🧭 Animation en temps réel de la trajectoire (x, y)")
    # ax.set_xlabel("Position X")
    # ax.set_ylabel("Position Y")
    # ax.grid(True)
    # ax.axis("equal")

    # # Dessine la trajectoire en fond (référence)
    # ax.plot(xs, ys, linewidth=1, color='lightblue', label="Trajectoire complète")

    # # Keyframes
    # label_texts = {}  # timestamp → matplotlib Text object

    # for t_str, (mode, pos, *extra) in TEST_DATA.items():
    #     t = int(t_str)
    #     x, y = pos if isinstance(pos, Sequence) and len(pos) == 2 else (pos, 0)
    #     ax.scatter(x, y, s=40, color='black')
    #     text = ax.text(x + 5, y + 5, mode, fontsize=8, color='black')
    #     label_texts[t] = text


    # # Point animé
    # point, = ax.plot([], [], 'ro', markersize=8)

    # # Ligne d'historique
    # trail, = ax.plot([], [], color='blue', linewidth=2)

    # trail_xs = []
    # trail_ys = []

    # def init():
    #     point.set_data([], [])
    #     trail.set_data([], [])
    #     return point, trail

    # def update(frame):
    #     t = frame * 10
    #     pos = keyframe(t, POSITION, 10000, TEST_DATA)
    #     x, y = pos if len(pos) >= 2 else (pos[0], 0)
    #     point.set_data([x], [y])
    #     trail_xs.append(x)
    #     trail_ys.append(y)
    #     trail.set_data(trail_xs, trail_ys)

    #     # === Mise à jour du label actif ===
    #     current_data = {int(k): v for k, v in TEST_DATA.items()}
    #     sorted_keys = sorted(current_data.keys())

    #     active_label = None
    #     for i in range(1, len(sorted_keys)):
    #         start_t = sorted_keys[i - 1] * 100  # en ms
    #         end_t = sorted_keys[i] * 100
    #         if start_t <= t < end_t:
    #             active_label = sorted_keys[i]
    #             break

    #     for key, text in label_texts.items():
    #         text.set_color('red' if key == active_label else 'black')

    #     return point, trail, *label_texts.values()


    # ani = animation.FuncAnimation(fig, update, frames=range(0, 1000), init_func=init,
    #                             interval=10, blit=True, repeat=False)

    # plt.tight_layout()
    # plt.show()
if __name__ == "__main__" : 
    import matplotlib.pyplot as plt
    TEST_DATA = {
    "-50" : ["start", 0],
    "0": ["linear",40],
    "10": ["linear", 30],
    "20": ["ease_in", 50],
    "30": ["ease_out", 70],
    "40": ["ease_in_out", 90],
    "50": ["bounce", 110],
    "60": ["elastic", 130],
    "70": ["step", 150],
    "80": ["bezier", 180, (0.42, 0, 0.58, 1)],  # Bezier personnalisée (ease-in-out standard)
    "100": ["hold", 200]
    }
    POSITION = 5000
    times = list(range(0, 10000, 1))
    values = [keyframe(t, POSITION,1000, TEST_DATA) for t in times]

    plt.figure(figsize=(12, 6))
    plt.plot(times, values, label='keyframe value', linewidth=2)

    # Lignes verticales
    for t, (mode, val, *rest) in sorted({int(k): v for k, v in TEST_DATA.items()}.items()):
        x = t * 100
        plt.axvline(x=x, linestyle='--', alpha=0.5, label=f"{mode} @ {x}ms")

    plt.title("🎬 Interpolations avancées (Bézier paramétrable)")
    plt.xlabel("Temps (ms)")
    plt.ylabel("Valeur")
    plt.grid(True)
    plt.legend(loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.show()
