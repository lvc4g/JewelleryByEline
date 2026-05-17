import numpy as np
import matplotlib.pyplot as plt

# Configuration du temps (8 secondes, 100 Hz)
feux_hz = 100  
t = np.linspace(0, 8, 8 * feux_hz)
f_reference = 100000  # 100 kHz

# Fonction de bruit standard pour le réalisme
def ajouter_bruit(signal):
    return signal + np.random.normal(0, 20, size=len(t))

# Création de la grille 3x6
fig, axs = plt.subplots(3, 6, figsize=(24, 12), sharex=True, sharey=True)
fig.suptitle("Signatures de fréquence : Profils de Véhicules et Cas Ambigus", fontsize=16, fontweight='bold')

# =====================================================================
# 1. LIGNE 1 : PLAQUES COURTES (VOITURES)
# Amplitudes proches des camions, mais durées très brèves
# =====================================================================
parametres_voitures = [
    {"t_c": 3.0, "larg": 0.30, "amp": 2100},
    {"t_c": 4.5, "larg": 0.35, "amp": 2300},
    {"t_c": 2.0, "larg": 0.32, "amp": 2150},
    {"t_c": 3.8, "larg": 0.28, "amp": 2250},
    {"t_c": 5.5, "larg": 0.33, "amp": 2200},
    {"t_c": 2.8, "larg": 0.26, "amp": 2350}
]

for i, p in enumerate(parametres_voitures):
    ax = axs[0, i]
    f = f_reference + p["amp"] * np.exp(-((t - p["t_c"]) / p["larg"]) ** 2)
    ax.plot(t, ajouter_bruit(f), color="tab:blue", label="Plaque courte")
    ax.set_title(f"Trace {i+1} : Voiture")
    ax.legend(loc="upper right")
    ax.grid(True)

# =====================================================================
# 2. LIGNE 2 : PLAQUES LONGUES (CAMIONS)
# Amplitudes similaires aux voitures, mais étalées dans le temps
# =====================================================================
parametres_camions = [
    {"t_c": 4.0, "larg": 1.1, "amp": 2600},
    {"t_c": 3.5, "larg": 0.9, "amp": 2500},
    {"t_c": 5.0, "larg": 1.2, "amp": 2700},
    {"t_c": 2.5, "larg": 1.3, "amp": 2550},
    {"t_c": 6.5, "larg": 0.95, "amp": 2650},
    {"t_c": 4.8, "larg": 1.05, "amp": 2750}
]

for i, p in enumerate(parametres_camions):
    ax = axs[1, i]
    f = f_reference + p["amp"] * np.exp(-((t - p["t_c"]) / p["larg"]) ** 2)
    ax.plot(t, ajouter_bruit(f), color="tab:orange", label="Plaque longue")
    ax.set_title(f"Trace {i+7} : Camion")
    ax.legend(loc="upper right")
    ax.grid(True)

# =====================================================================
# 3. LIGNE 3 : TRACES INTERMÉDIAIRES / AMBIGUËS
# =====================================================================

parametres_ambi = [
    {"type": "hybride", "t_c": 4.0, "larg": 0.6, "amp": 2400},
    {"type": "accel", "t_c": 4.0, "larg": 0.6, "amp": 2450},
    {"type": "double", "t_c": 0.0, "larg": 0.0, "amp": 0.0},
    {"type": "decroissance", "t_c": 4.0, "larg": 0.5, "amp": 2300},
    {"type": "oscillation", "t_c": 4.0, "larg": 0.7, "amp": 2350},
    {"type": "plateau", "t_c": 4.0, "larg": 1.5, "amp": 2250}
]

for i, p in enumerate(parametres_ambi):
    ax = axs[2, i]
    if p["type"] == "hybride":
        f = f_reference + p["amp"] * np.exp(-((t - p["t_c"]) / p["larg"]) ** 2)
        title = "Trace 13 : Hybride"
        color = "tab:purple"
    elif p["type"] == "accel":
        t_passage = p["t_c"]
        t_deforme = np.where(t < t_passage, 
                             t + 0.3 * (t - t_passage)**2,
                             t + 1.5 * (t - t_passage))
        f = f_reference + p["amp"] * np.exp(-((t_deforme - t_passage) / p["larg"]) ** 2)
        title = "Trace 14 : Accélération"
        color = "tab:red"
    elif p["type"] == "double":
        f = f_reference + 2000 * np.exp(-((t - 3.0) / 0.4) ** 2) + 1900 * np.exp(-((t - 4.8) / 0.4) ** 2)
        title = "Trace 15 : Double pic"
        color = "tab:purple"
    elif p["type"] == "decroissance":
        f = f_reference + p["amp"] * np.exp(-((t - 3.5) / 0.5) ** 2) + 1200 * np.exp(-((t - 5.0) / 1.2) ** 2)
        title = "Trace 16 : Décélération"
        color = "tab:purple"
    elif p["type"] == "oscillation":
        f = f_reference + p["amp"] * np.exp(-((t - p["t_c"]) / p["larg"]) ** 2) * (1 + 0.2 * np.sin(5 * t))
        title = "Trace 17 : Oscillation"
        color = "tab:purple"
    else:
        f = f_reference + p["amp"] * np.exp(-((t - p["t_c"]) / p["larg"]) ** 2)
        title = "Trace 18 : Plateau"
        f += 300 * np.exp(-((t - 4.0) / 0.8) ** 2)
        color = "tab:purple"

    ax.plot(t, ajouter_bruit(f), color=color, label=title)
    ax.set_title(title)
    ax.legend(loc="upper right")
    ax.grid(True)

# Configuration et habillage des axes
for ax in axs.flat:
    ax.set_xlim(0, 8)
    ax.set_ylim(99500, 103500)

for ax in axs[2, :]:
    ax.set_xlabel("Temps (s)")
for ax in axs[:, 0]:
    ax.set_ylabel("Fréquence (Hz)")

plt.tight_layout()
plt.savefig('trace_output.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé : trace_output.png")
