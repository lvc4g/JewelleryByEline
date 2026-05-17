import numpy as np
import matplotlib
# Configuration pour l'exécution sans interface graphique (serveur/GitHub Actions)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# =====================================================================
# 1. GÉNÉRATION DES DONNÉES ET EXTRACTION DES FEATURES (Identique)
# =====================================================================
feux_hz = 100  
t = np.linspace(0, 8, 8 * feux_hz)
f_reference = 100000

def profil(t, t_c, larg, amp):
    return amp * np.exp(-((t - t_c) / larg) ** 2)

signaux = []
labels_reels = []

# Voitures (Regroupées, faible variance)
signaux.append(profil(t, 3.0, 0.30, 2100))
signaux.append(profil(t, 4.5, 0.35, 2300))
signaux.append(profil(t, 2.0, 0.32, 2150))
labels_reels.extend([0, 0, 0])

# Camions (Plus étalés, forte variance)
signaux.append(profil(t, 4.0, 1.1, 2600))
signaux.append(profil(t, 3.5, 0.9, 2500))
signaux.append(profil(t, 5.0, 1.2, 2700))
labels_reels.extend([1, 1, 1])

# Intermédiaires / Ambigus
signaux.append(profil(t, 4.0, 0.6, 2400)) 
t_deforme = np.where(t < 4.0, t + 0.3 * (t - 4.0)**2, t + 1.5 * (t - 4.0))
signaux.append(profil(t_deforme, 4.0, 0.6, 2450)) 
signaux.append(profil(t, 3.5, 0.5, 2300) + profil(t, 5.0, 1.2, 1200)) 
labels_reels.extend([2, 2, 2])

signaux = np.array(signaux)

def extraire_features(signal, t):
    amp_max = np.max(signal)
    if amp_max == 0: return 0, 0
    indices_dessus = np.where(signal >= amp_max / 2)[0]
    largeur = t[indices_dessus[-1]] - t[indices_dessus[0]] if len(indices_dessus) > 0 else 0
    return amp_max, largeur

features = np.array([extraire_features(s, t) for s in signaux])
features_norm = (features - features.mean(axis=0)) / features.std(axis=0)

indices_train = [0, 1,  3, 4,  6, 7]  
indices_test  = [2, 5, 8]             

X_train = features_norm[indices_train]
X_test = features_norm[indices_test]

# =====================================================================
# 2. ENTRAÎNEMENT DU K-MEANS CONTRAINT
# =====================================================================
n_clusters = 3
taille_cluster = 2
n_iterations = 10

np.random.seed(42)
centres = X_train[np.random.choice(len(X_train), n_clusters, replace=False)]

for _ in range(n_iterations):
    centres_étendus = np.repeat(centres, taille_cluster, axis=0)
    matrice_distances = np.linalg.norm(X_train[:, np.newaxis, :] - centres_étendus[np.newaxis, :, :], axis=2)
    _, indices_slots = linear_sum_assignment(matrice_distances)
    labels_train = indices_slots // taille_cluster
    
    nouveaux_centres = np.zeros_like(centres)
    for c in range(n_clusters):
        points_du_cluster = X_train[labels_train == c]
        if len(points_du_cluster) > 0:
            nouveaux_centres[c] = points_du_cluster.mean(axis=0)
    if np.allclose(centres, nouveaux_centres): break
    centres = nouveaux_centres

# =====================================================================
# 3. CALCUL DE LA LARGEUR (DISPERSION) DE CHAQUE CLUSTER
# =====================================================================
# Pour chaque dimension (Amplitude et Largeur), on calcule l'écart-type interne du cluster.
# On ajoute une petite valeur epsilon (1e-6) pour éviter une division par zéro si un cluster est ultra-serré.
std_clusters = np.zeros_like(centres)
epsilon = 1e-6

for c in range(n_clusters):
    points_du_cluster = X_train[labels_train == c]
    if len(points_du_cluster) > 1:
        std_clusters[c] = np.std(points_du_cluster, axis=0) + epsilon
    else:
        std_clusters[c] = np.ones(X_train.shape[1]) * epsilon

# =====================================================================
# 4. INFERENCE / TEST PONDÉRÉE PAR LA LARGEUR DES CLUSTERS
# =====================================================================
labels_test = []
for point_test in X_test:
    distances_ponderees = []
    for c in range(n_clusters):
        centre = centres[c]
        std = std_clusters[c]
        
        # Distance Euclidienne normalisée par l'écart-type de chaque coordonnée
        # Formule : racine( somme( ((x_i - centre_i) / std_i)^2 ) )
        dist_normalisee = np.sqrt(np.sum(((point_test - centre) / std) ** 2))
        distances_ponderees.append(dist_normalisee)
        
    labels_test.append(np.argmin(distances_ponderees))
labels_test = np.array(labels_test)

# =====================================================================
# 5. MATRICE DE CONFUSION ET SAUVEGARDE
# =====================================================================
y_reels_train = [labels_reels[idx] for idx in indices_train]
y_reels_test  = [labels_reels[idx] for idx in indices_test]

y_true = y_reels_train + y_reels_test
y_pred = list(labels_train) + list(labels_test)

noms_classes = ['Voiture', 'Camion', 'Intermédiaire']
cm = confusion_matrix(y_true, y_pred)

# Graphique 1 : Espace des features
plt.figure(figsize=(10, 6))
Couleurs = ['tab:blue', 'tab:orange', 'tab:purple']
for c in range(n_clusters):
    points = X_train[labels_train == c]
    plt.scatter(points[:, 1], points[:, 0], color=Couleurs[c], marker='o', s=150, label=f'Train Cluster {c}')
for i, c in enumerate(labels_test):
    plt.scatter(X_test[i, 1], X_test[i, 0], color=Couleurs[c], marker='X', s=200, edgecolors='black', label=f'Test -> Cluster {c}' if i==c else "")
plt.scatter(centres[:, 1], centres[:, 0], color='red', marker='*', s=300, label='Centres')
plt.title("Classification avec Distance Pondérée par la Variance des Clusters")
plt.ylabel("Amplitude Max (Normalisée)")
plt.xlabel("Largeur du signal (Normalisée)")
plt.grid(True)
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), loc='lower right')
plt.savefig('trace_output.png', dpi=150, bbox_inches='tight')
plt.close()

# Graphique 2 : Matrice de confusion
plt.figure(figsize=(6, 6))
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=noms_classes)
disp.plot(cmap=plt.cm.Blues, ax=plt.gca(), values_format='d')
plt.title("Matrice de Confusion Pondérée")
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

print("Graphiques 'trace_output.png' et 'confusion_matrix.png' mis à jour et sauvegardés.")
