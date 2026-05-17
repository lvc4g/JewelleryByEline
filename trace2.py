import numpy as np
import matplotlib.pyplot as plt

# Configuration du temps (8 secondes)
feux_hz = 100  # Fréquence d'échantillonnage
t = np.linspace(0, 8, 8 * feux_hz)
f_reference = 100000  # Fréquence de base (100 kHz)

# Fonction pour générer le profil de passage (courants de Foucault)
def profil_passage(t, t_centre, largeur, amplitude):
    return amplitude * np.exp(-((t - t_centre) / largeur) ** 2)

# Création d'une grille de 3 lignes et 3 colonnes (9 graphiques au total)
fig, axs = plt.subplots(3, 3, figsize=(15, 12), sharex=True, sharey=True)
fig.suptitle("Analyse des signatures de fréquence - 9 Traces Distinctes", fontsize=16, fontweight='bold')

# Définition d'un bruit de mesure standard et réaliste pour tous les graphes
def ajouter_bruit(signal):
    return signal + np.random.normal(0, 25, size=len(t))

# =====================================================================
# 1. LIGNE 1 : PETITES PLAQUES (VOITURES)
# Signature : Amplitude modérée, temps de passage court
# =====================================================================
parametres_voitures = [
    {"t_c": 3.0, "larg": 0.35, "amp": 1400},
    {"t_c": 4.5, "larg": 0.40, "amp": 1600},
    {"t_c": 2.0, "larg": 0.38, "amp": 1350}
]

for i, p in enumerate(parametres_voitures):
    ax = axs[0, i]
    f = f_reference + profil_passage(t, p["t_c"], p["larg"], p["amp"])
    ax.plot(t, ajouter_bruit(f), color="tab:blue", label=f"Voiture {i+1}")
    ax.set_title(f"Trace {i+1} : Petite plaque")
    ax.legend(loc="upper right")
    ax.grid(True)

# =====================================================================
# 2. LIGNE 2 : PLAQUES LONGUES (CAMIONS)
# Signature : Forte amplitude, temps de passage étalé (plateau)
# =====================================================================
parametres_camions = [
    {"t_c": 4.0, "larg": 1.3, "amp": 3200},
    {"t_c": 3.5, "larg": 1.1, "amp": 2900},
    {"t_c": 5.0, "larg": 1.4, "amp": 3400}
]

for i, p in enumerate(parametres_camions):
    ax = axs[1, i]
    f = f_reference + profil_passage(t, p["t_c"], p["larg"], p["amp"])
    ax.plot(t, ajouter_bruit(f), color="tab:orange", label=f"Camion {i+1}")
    ax.set_title(f"Trace {i+4} : Plaque longue")
    ax.legend(loc="upper right")
    ax.grid(True)

# =====================================================================
# 3. LIGNE 3 : TRACES AMBIGUËS (ENTRE-DEUX / INCLASSABLES)
# Signature : Formes géométriques réelles mais bâtardes ou superposées
# =====================================================================
ax_ambigu = axs[2, 0]
# Cas 1 : Amplitude d'un camion mais largeur d'une voiture
f_ambigu1 = f_reference + profil_passage(t, 4.0, 0.4, 3100)
ax_ambigu.plot(t, ajouter_bruit(f_ambigu1), color="tab:purple", label="Hybride A")
ax_ambigu.set_title("Trace 7 : Profil hybride")
ax_ambigu.legend(loc="upper right")
ax_ambigu.grid(True)

ax_ambigu = axs[2, 1]
# Cas 2 : Deux petites plaques très rapprochées (Deux voitures ou un camion avec remorque ?)
f_ambigu2 = f_reference + profil_passage(t, 3.2, 0.3, 1500) + profil_passage(t, 4.3, 0.3, 1400)
ax_ambigu.plot(t, ajouter_bruit(f_ambigu2), color="tab:purple", label="Double pic")
ax_ambigu.set_title("Trace 8 : Double passage")
ax_ambigu.legend(loc="upper right")
ax_ambigu.grid(True)

ax_ambigu = axs[2, 2]
# Cas 3 : Une traînée très étalée mais à très faible amplitude (Plaque éloignée ou grand véhicule peu conducteur ?)
f_ambigu3 = f_reference + profil_passage(t, 4.0, 1.8, 1200)
ax_ambigu.plot(t, ajouter_bruit(f_ambigu3), color="tab:purple", label="Hybride B")
ax_ambigu.set_title("Trace 9 : Profil étalé bas")
ax_ambigu.legend(loc="upper right")
ax_ambigu.grid(True)

# Configuration globale des étiquettes des axes
for ax in axs.flat:
    ax.set_xlim(0, 8)

# Ajouter les labels uniquement sur les bords extérieurs pour ne pas surcharger
for ax in axs[2, :]:
    ax.set_xlabel("Temps (s)")
for ax in axs[:, 0]:
    ax.set_ylabel("Fréquence (Hz)")

plt.tight_layout()
plt.savefig('trace_output.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé : trace_output.png")
