import numpy as np
import matplotlib.pyplot as plt

# Configuration du temps (8 secondes, 100 Hz)
feux_hz = 100  
t = np.linspace(0, 8, 8 * feux_hz)
f_reference = 100000  # 100 kHz

# Fonction de bruit standard pour le réalisme
def ajouter_bruit(signal):
    return signal + np.random.normal(0, 20, size=len(t))

# Création de la grille 3x3
fig, axs = plt.subplots(3, 3, figsize=(15, 12), sharex=True, sharey=True)
fig.suptitle("Signatures de fréquence : Profils de Véhicules et Cas Ambigus", fontsize=16, fontweight='bold')

# =====================================================================
# 1. LIGNE 1 : PLAQUES COURTES (VOITURES)
# Amplitudes proches des camions, mais durées très brèves
# =====================================================================
parametres_voitures = [
    {"t_c": 3.0, "larg": 0.30, "amp": 2100},
    {"t_c": 4.5, "larg": 0.35, "amp": 2300},
    {"t_c": 2.0, "larg": 0.32, "amp": 2150}
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
    {"t_c": 5.0, "larg": 1.2, "amp": 2700}
]

for i, p in enumerate(parametres_camions):
    ax = axs[1, i]
    f = f_reference + p["amp"] * np.exp(-((t - p["t_c"]) / p["larg"]) ** 2)
    ax.plot(t, ajouter_bruit(f), color="tab:orange", label="Plaque longue")
    ax.set_title(f"Trace {i+4} : Camion")
    ax.legend(loc="upper right")
    ax.grid(True)

# =====================================================================
# 3. LIGNE 3 : TRACES INTERMÉDIAIRES / AMBIGUËS
# =====================================================================

# --- TRACE 7 : Durée intermédiaire + Amplitude hybride ---
# Pile entre la longueur d'une voiture lente et d'un camion rapide
ax_ambigu1 = axs[2, 0]
f_ambigu1 = f_reference + 2400 * np.exp(-((t - 4.0) / 0.6) ** 2)
ax_ambigu1.plot(t, ajouter_bruit(f_ambigu1), color="tab:purple", label="Hybride")
ax_ambigu1.set_title("Trace 7 : Taille/Vitesse indéterminée")
ax_ambigu1.legend(loc="upper right")
ax_ambigu1.grid(True)


# --- TRACE 8 : ACCÉLÉRATION NON NULLE (Asymétrie forte) ---
# Le véhicule entre lentement (pente douce) et repart très vite (pente raide)
ax_accel = axs[2, 1]
t_passage = 4.0
f_accel = np.zeros_like(t)

# On applique une distorsion du temps pour simuler l'accélération
# t_deforme ralentit avant 4s et accélère après 4s
t_deforme = np.where(t < t_passage, 
                     t + 0.3 * (t - t_passage)**2,  # Approche ralentie
                     t + 1.5 * (t - t_passage))     # Éloignement rapide

f_accel = f_reference + 2450 * np.exp(-((t_deforme - t_passage) / 0.6) ** 2)
ax_accel.plot(t, ajouter_bruit(f_accel), color="tab:red", label="Accélération")
ax_accel.set_title("Trace 8 : Passage avec accélération")
ax_accel.legend(loc="upper right")
ax_accel.grid(True)


# --- TRACE 9 : Décélération puis arrêt / faux plat ---
# Le véhicule ralentit brusquement au-dessus du capteur puis repart
ax_ambigu3 = axs[2, 2]
f_ambigu3 = f_reference + 2300 * np.exp(-((t - 3.5) / 0.5) ** 2) + 1200 * np.exp(-((t - 5.0) / 1.2) ** 2)
ax_ambigu3.plot(t, ajouter_bruit(f_ambigu3), color="tab:purple", label="Profil asymétrique")
ax_ambigu3.set_title("Trace 9 : Vitesse variable / Traînante")
ax_ambigu3.legend(loc="upper right")
ax_ambigu3.grid(True)

# Configuration et habillage des axes
for ax in axs.flat:
    ax.set_xlim(0, 8)
    ax.set_ylim(99500, 103500) # Fixe la même échelle de fréquence partout

for ax in axs[2, :]:
    ax.set_xlabel("Temps (s)")
for ax in axs[:, 0]:
    ax.set_ylabel("Fréquence (Hz)")

plt.tight_layout()
plt.savefig('trace_output.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé : trace_output.png")
