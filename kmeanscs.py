import numpy as np
import matplotlib
# Configuration pour l'exécution sans interface graphique (serveur/GitHub Actions)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# =====================================================================
# 1. GÉNÉRATION DES DONNÉES (Avec retards volontaires pour piéger l'algo)
# =====================================================================
feux_hz = 100  
t = np.linspace(0, 8, 8 * feux_hz)
f_reference = 100000

def profil(t, t_c, larg, amp):
    return amp * np.exp(-((t - t_c) / larg) ** 2)

signaux = []
labels_reels = []

# Voitures (Passages à des moments très différents : 1.5s, 6.0s, 3.5s)
signaux.append(profil(t, 1.5, 0.30, 2100))
signaux.append(profil(t, 6.0, 0.35, 2300))
signaux.append(profil(t, 3.5, 0.32, 2150))
labels_reels.extend([0, 0, 0])

# Camions (Passages à 5.5s, 2.0s, 4.0s)
signaux.append(profil(t, 5.5, 1.1, 2600))
signaux.append(profil(t, 2.0, 0.9, 2500))
signaux.append(profil(t, 4.0, 1.2, 2700))
labels_reels.extend([1, 1, 1])

# Intermédiaires / Ambigus (Moments variables)
signaux.append(profil(t, 2.5, 0.6, 2400)) 
t_deforme = np.where(t < 5.0, t + 0.3 * (t - 5.0)**2, t + 1.5 * (t - 5.0))
signaux.append(profil(t_deforme, 5.0, 0.6, 2450)) # Accélération centrée à 5s
signaux.append(profil(t, 3.0, 0.5, 2300) + profil(t, 4.5, 1.2, 1200)) 
labels_reels.extend([2, 2, 2])

signaux = np.array(signaux)

# =====================================================================
# 2. EXTRACTION DE FEATURES INVARIANTES AU RETARD (Moments Centrés)
# =====================================================================
def extraire_features_invariantes(signal, t):
    amp_max = np.max(signal)
    if amp_max == 0: return 0, 0, 0
    
    # On normalise le signal comme une distribution de probabilité temporelle
    aire = np.sum(signal)
    prob_t = signal / aire
    
    # 1. Temps moyen du passage (Le centre de gravité, qu'on va utiliser pour centrer)
    t_moyen = np.sum(t * prob_t)
    
    # 2. Variance temporelle (Indépendante de t_moyen -> invariance au retard)
    variance_t = np.sum(((t - t_moyen) ** 2) * prob_t)
    largeur_temporelle = np.sqrt(variance_t)
    
    # 3. Asymétrie (Skewness) temporelle : utile pour détecter l'accélération (Trace 8)
    skewness_t = np.sum(((t - t_moyen) ** 3) * prob_t) / (variance_t ** 1.5 + 1e-6)
    
    return amp_max, largeur_temporelle, skewness_t

features = np.array([extraire_features_invariantes(s, t) for s in signaux])

# Normalisation (Z-score)
features_norm = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-6)

indices_train = [0, 1,  3, 4,  6, 7]  
indices_test  = [2, 5, 8]             

X_train = features_norm[indices_train]
X_test = features_norm[indices_test]

# =====================================================================
# 3. K-MEANS CONTRAINT AVEC MULTI-INITIALISATIONS (n_init = 20)
# =====================================================================
n_clusters = 3
taille_cluster = 2
n_iterations_max = 15
n_init = 20  # Nombre de relances pour trouver l'optimum global

meilleure_inertie = float('inf')
meilleurs_centres = None
meilleurs_labels_train = None

np.random.seed(42) # Pour la reproductibilité globale, mais les sous-tirages varient

for init in range(n_init):
    # Sélection aléatoire de 3 centres de départ parmi les données d'entraînement
    centres_init = X_train[np.random.choice(len(X_train), n_clusters, replace=False)]
    centres_courants = centres_init.copy()
    
    for _ in range(n_iterations_max):
        centres_étendus = np.repeat(centres_courants, taille_cluster, axis=0)
        matrice_distances = np.linalg.norm(X_train[:, np.newaxis, :] - centres_étendus[np.newaxis, :, :], axis=2)
        
        # Assignation optimale (contrainte de taille)
        _, indices_slots = linear_sum_assignment(matrice_distances)
        labels_train_courants = indices_slots // taille_cluster
        
        # Recalcul des centres
        nouveaux_centres = np.zeros_like(centres_courants)
        for c in range(n_clusters):
            points_du_cluster = X_train[labels_train_courants == c]
            if len(points_du_cluster) > 0:
                nouveaux_centres[c] = points_du_cluster.mean(axis=0)
                
        if np.allclose(centres_courants, nouveaux_centres):
            break
        centres_courants = nouveaux_centres
        
    # Calcul de l'inertie de cette tentative (somme des distances au carré)
    inertie_courante = 0
    for c in range(n_clusters):
        points_du_cluster = X_train[labels_train_courants == c]
        if len(points_du_cluster) > 0:
            inertie_courante += np.sum(np.linalg.norm(points_du_cluster - centres_courants[c], axis=1) ** 2)
            
    # On garde la meilleure exécution
    if inertie_courante < meilleure_inertie:
        meilleure_inertie = inertie_courante
        meilleurs_centres = centres_courants
        meilleurs_labels_train = labels_train_courants

centres = meilleurs_centres
labels_train = meilleurs_labels_train

print(f"Meilleure inertie trouvée après {n_init} relances : {meilleure_inertie:.4f}")

# =====================================================================
# 4. CALCUL DE LA VARIANCE DES CLUSTERS ET INFERENCE TEST PONDÉRÉE
# =====================================================================
std_clusters = np.zeros_like(centres)
epsilon = 1e-3 # Légèrement augmenté pour stabiliser les dimensions à faible variance

for c in range(n_clusters):
    points_du_cluster = X_train[labels_train == c]
    if len(points_du_cluster) > 1:
        std_clusters[c] = np.std(points_du_cluster, axis=0) + epsilon
    else:
        std_clusters[c] = np.ones(X_train.shape[1]) * epsilon

labels_test = []
for point_test in X_test:
    distances_ponderees = []
    for c in range(n_clusters):
        # Distance de Mahalanobis diagonale (pondérée par l'écart-type du cluster)
        dist_normalisee = np.sqrt(np.sum(((point_test - centres[c]) / std_clusters[c]) ** 2))
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

# Graphique 1 : Visualisation 2D des deux features principales (Amplitude vs Largeur temporelle)
plt.figure(figsize=(10, 6))
Couleurs = ['tab:blue', 'tab:orange', 'tab:purple']
for c in range(n_clusters):
    points = X_train[labels_train == c]
    plt.scatter(points[:, 1], points[:, 0], color=Couleurs[c], marker='o', s=150, label=f'Train Cluster {c}')
for i, c in enumerate(labels_test):
    plt.scatter(X_test[i, 1], X_test[i, 0], color=Couleurs[c], marker='X', s=200, edgecolors='black', label=f'Test -> Cluster {c}' if i==c else "")
plt.scatter(centres[:, 1], centres[:, 0], color='red', marker='*', s=300, label='Centres Optimaux')
plt.title("Classification Robuste au Retard Temporel (Multi-initialisé)")
plt.ylabel("Amplitude Max (Normalisée)")
plt.xlabel("Étalement Temporel Invariant (Normalisé)")
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
plt.title("Matrice de Confusion (Insensible au Retard)")
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

print("Graphiques mis à jour. L'impact du déphasage temporel est désormais neutralisé.")
