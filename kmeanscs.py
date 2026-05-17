import numpy as np
import matplotlib
# Configuration pour l'exécution sans interface graphique (serveur/GitHub Actions)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment

# =====================================================================
# 1. GÉNÉRATION DES DONNÉES (Reprise de la logique précédente)
# =====================================================================
feux_hz = 100  
t = np.linspace(0, 8, 8 * feux_hz)
f_reference = 100000

def profil(t, t_c, larg, amp):
    return amp * np.exp(-((t - t_c) / larg) ** 2)

# On génère les 9 signaux proprement pour l'analyse
signaux = []
labels_reels = [] # 0: Voiture, 1: Camion, 2: Ambi/Intermédiaire

# Voitures (Plaques courtes)
signaux.append(profil(t, 3.0, 0.30, 2100))
signaux.append(profil(t, 4.5, 0.35, 2300))
signaux.append(profil(t, 2.0, 0.32, 2150))
labels_reels.extend([0, 0, 0])

# Camions (Plaques longues)
signaux.append(profil(t, 4.0, 1.1, 2600))
signaux.append(profil(t, 3.5, 0.9, 2500))
signaux.append(profil(t, 5.0, 1.2, 2700))
labels_reels.extend([1, 1, 1])

# Intermédiaires / Ambigus (Trace 7: hybride, Trace 8: accel, Trace 9: traînante)
signaux.append(profil(t, 4.0, 0.6, 2400)) # Trace 7
# Trace 8 (accélération)
t_deforme = np.where(t < 4.0, t + 0.3 * (t - 4.0)**2, t + 1.5 * (t - 4.0))
signaux.append(profil(t_deforme, 4.0, 0.6, 2450)) # Trace 8
# Trace 9
signaux.append(profil(t, 3.5, 0.5, 2300) + profil(t, 5.0, 1.2, 1200)) # Trace 9
labels_reels.extend([2, 2, 2])

signaux = np.array(signaux)

# =====================================================================
# 2. EXTRACTION DE CARACTÉRISTIQUES (FEATURES)
# =====================================================================
def extraire_features(signal, t):
    amp_max = np.max(signal)
    if amp_max == 0: return 0, 0
    indices_dessus = np.where(signal >= amp_max / 2)[0]
    if len(indices_dessus) > 0:
        largeur = t[indices_dessus[-1]] - t[indices_dessus[0]]
    else:
        largeur = 0
    return amp_max, largeur

features = np.array([extraire_features(s, t) for s in signaux])

# Normalisation des caractéristiques
features_norm = (features - features.mean(axis=0)) / features.std(axis=0)

# =====================================================================
# 3. SÉPARATION ENTRAÎNEMENT (2 par classe) / TEST (1 par classe)
# =====================================================================
indices_train = [0, 1,  3, 4,  6, 7]  
indices_test  = [2, 5, 8]             

X_train = features_norm[indices_train]
X_test = features_norm[indices_test]

# =====================================================================
# 4. IMPLÉMENTATION DU K-MEANS CONTRAINT (Contrainte de taille = 2)
# =====================================================================
n_clusters = 3
taille_cluster = 2
n_iterations = 10

np.random.seed(42)
centres = X_train[np.random.choice(len(X_train), n_clusters, replace=False)]

for _ in range(n_iterations):
    centres_étendus = np.repeat(centres, taille_cluster, axis=0)
    matrice_distances = np.linalg.norm(X_train[:, np.newaxis, :] - centres_étendus[np.newaxis, :, :], axis=2)
    indices_points, indices_slots = linear_sum_assignment(matrice_distances)
    labels_train = indices_slots // taille_cluster
    
    nouveaux_centres = np.zeros_like(centres)
    for c in range(n_clusters):
        points_du_cluster = X_train[labels_train == c]
        if len(points_du_cluster) > 0:
            nouveaux_centres[c] = points_du_cluster.mean(axis=0)
    
    if np.allclose(centres, nouveaux_centres):
        break
    centres = nouveaux_centres

# =====================================================================
# 5. INFERENCE / TEST
# =====================================================================
distances_test = np.linalg.norm(X_test[:, np.newaxis, :] - centres[np.newaxis, :, :], axis=2)
labels_test = np.argmin(distances_test, axis=1)

# =====================================================================
# 6. AFFICHAGE DES RÉSULTATS DANS LA CONSOLE GITHUB
# =====================================================================
print("--- RÉSULTATS DE L'ENTRAÎNEMENT CONTRAINT ---")
for i, idx in enumerate(indices_train):
    print(f"Signal {idx+1} (Classe réelle {labels_reels[idx]}) -> Assigné au Cluster {labels_train[i]}")

print("\n--- RÉSULTATS DU TEST ---")
for i, idx in enumerate(indices_test):
    print(f"Signal {idx+1} (Classe réelle {labels_reels[idx]}) -> Classifié dans le Cluster {labels_test[i]}")

# =====================================================================
# 7. CRÉATION ET SAUVEGARDE DU GRAPHIQUE
# =====================================================================
plt.figure(figsize=(10, 6))
Couleurs = ['tab:blue', 'tab:orange', 'tab:purple']

for c in range(n_clusters):
    points = X_train[labels_train == c]
    plt.scatter(points[:, 1], points[:, 0], color=Couleurs[c], marker='o', s=150, label=f'Train Cluster {c} (Bloqué à 2)')

for i, c in enumerate(labels_test):
    plt.scatter(X_test[i, 1], X_test[i, 0], color=Couleurs[c], marker='X', s=200, edgecolors='black', label=f'Test individuel -> Cluster {c}' if i==c else "")

plt.scatter(centres[:, 1], centres[:, 0], color='red', marker='*', s=300, label='Centres finaux')

plt.title("Espace des Features (Normalisé) : Amplitude vs Largeur à mi-hauteur")
plt.ylabel("Amplitude Max (Normalisée)")
plt.xlabel("Largeur du signal (Normalisée)")
plt.grid(True)

handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), loc='lower right')

# Remplacement de plt.show() par la sauvegarde d'image demandée
plt.savefig('trace_output.png', dpi=150, bbox_inches='tight')
print("\nGraphique sauvegardé : trace_output.png")

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# 1. Rassembler tous les labels réels et prédits (Train + Test)
# Pour rappel : indices_train = [0, 1, 3, 4, 6, 7] et indices_test = [2, 5, 8]
y_reels_train = [labels_reels[idx] for idx in indices_train]
y_reels_test  = [labels_reels[idx] for idx in indices_test]

y_true = y_reels_train + y_reels_test
y_pred = list(labels_train) + list(labels_test)

# Noms des classes pour l'affichage
noms_classes = ['Voiture', 'Camion', 'Intermédiaire']

# 2. Calculer la matrice de confusion
cm = confusion_matrix(y_true, y_pred)

# 3. Créer le graphique de la matrice
plt.figure(figsize=(6, 6))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=noms_classes)

# Affichage avec une carte de chaleur (heatmap)
disp.plot(cmap=plt.cm.Blues, ax=plt.gca(), values_format='d')
plt.title("Matrice de Confusion (9 traces)")

# 4. Sauvegarde pour GitHub
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
print("Matrice de confusion sauvegardée : confusion_matrix.png")

# Affichage texte dans la console au cas où
print("\nMatrice de confusion (Format texte) :")
print(cm)