import numpy as np
import matplotlib.pyplot as plt

# Configuration du temps (8 secondes)
feux_hz = 100  # Fréquence d'échantillonnage
t = np.linspace(0, 8, 8 * feux_hz)
f_reference = 100000  # Fréquence de base de l'oscillateur (100 kHz)

# Fonction pour générer une forme de cloche (approche/éloignement)
def profil_passage(t, t_centre, largeur, amplitude):
    return amplitude * np.exp(-((t - t_centre) / largeur) ** 2)

# Configuration des graphiques
fig, axs = plt.subplots(3, 1, figsize=(10, 12), sharex=True, sharey=True)
fig.suptitle("Simulations des traces de fréquence (Oscillateur à résistance négative)", fontsize=14, fontweight='bold')

# --- 1. PETITE PLAQUE (VOITURE) ---
# Transition rapide, impact modéré sur l'inductance
for i, t_c in enumerate([2.5, 4.0, 5.5]):
    amp = 1500 + np.random.normal(0, 50)  # ~1.5 kHz d'augmentation
    larg = 0.4 + np.random.normal(0, 0.05)
    bruit = np.random.normal(0, 30, size=len(t))
    f = f_reference + profil_passage(t, t_c, larg, amp) + bruit
    axs[0].plot(t, f, label=f"Voiture {i+1}")
axs[0].set_title("Petites plaques (Profil type 'Voiture')")
axs[0].legend()
axs[0].grid(True)

# --- 2. PLAQUE PLUS LONGUE (CAMION) ---
# Transition plus longue, impact plus fort et plateau plus large
for i, t_c in enumerate([2.0, 3.5, 5.0]):
    amp = 3000 + np.random.normal(0, 100)  # ~3 kHz d'augmentation
    larg = 1.2 + np.random.normal(0, 0.1)  # Signal plus large dans le temps
    bruit = np.random.normal(0, 40, size=len(t))
    f = f_reference + profil_passage(t, t_c, larg, amp) + bruit
    axs[1].plot(t, f, label=f"Camion {i+1}")
axs[1].set_title("Plaques longues (Profil type 'Camion')")
axs[1].legend()
axs[1].grid(True)

# --- 3. TRACES BRUITÉES / INCATÉGORISABLES ---
# Fort bruit de fond, interférences ou passages multiples/incohérents
for i in range(3):
    bruit_fort = np.random.normal(0, 400, size=len(t))  # Bruit thermique/électromagnétique élevé
    # Profils anarchiques (ex: faux contacts, variations lentes de température ou dérives)
    derive = 500 * np.sin(t * (i + 1)) 
    f = f_reference + derive + bruit_fort
    axs[2].plot(t, f, label=f"Inconnu {i+1}", alpha=0.8)
axs[2].set_title("Traces bruitées (Non catégorisables)")
axs[2].legend()
axs[2].grid(True)

# Habillage des axes
plt.xlabel("Temps (secondes)")
fig.text(0.04, 0.5, "Fréquence de l'oscillateur (Hz)", va='center', rotation='vertical', fontsize=12)

plt.tight_layout()
plt.savefig('trace_output.png', dpi=150, bbox_inches='tight')
print("Graphique sauvegardé : trace_output.png")
plt.show()