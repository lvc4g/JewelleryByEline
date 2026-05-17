import numpy as np
import matplotlib
# Configuration pour l'exécution sans interface graphique (serveur/GitHub Actions)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# =====================================================================
# 1. GÉNÉRATION DES DONNÉES (9 traces avec retards et formes complexes)
# =====================================================================
feux_hz = 100  
t = np.linspace(0, 8, 8 * feux_hz)
f_reference = 100000

def profil(t, t_c, larg, amp):
    return amp * np.exp(-((t - t_c) / larg) ** 2)

signaux = []
labels_reels = []
noms_signaux = []

# Voitures (Classe 0)
signaux.append(profil(t, 1.5, 0.30, 2100))
signaux.append(profil(t, 6.0, 0.35, 2300))
signaux.append(profil(t, 3.5, 0.32, 2150))
labels_reels.extend([0, 0, 0])
noms_signaux.extend(["Voiture 1", "Voiture 2", "Voiture 3 (Test)"])

# Camions (Classe 1)
signaux.append(profil(t, 5.5, 1.1, 2600))
signaux.append(profil(t, 2.0, 0.9, 2500))
signaux.append(profil(t, 4.0, 1.2, 2700))
labels_reels.extend([1, 1, 1])
noms_signaux.extend(["Camion 1", "Camion 2", "Camion 3 (Test)"])

# Intermédiaires / Indéterminés (Classe 2)
signaux.append(profil(t, 2.5, 0.6, 2400)) # Hybride
t_deforme = np.where(t < 5.0, t + 0.3 * (t - 5.0)**2, t + 1.5 * (t - 5.0))
signaux.append(profil(t_deforme, 5.0, 0.6, 2450)) # Accélération
signaux.append(profil(t, 3.0, 0.4, 2000) + profil(t, 4.8, 0.4, 1900)) # Double pic
labels_reels.extend([2, 2, 2])
noms_signaux.extend(["Interm. 1 (Taille)", "Interm. 2 (Accel)", "Interm. 3 (Double Pic - Test)"])

signaux = np.array(signaux)

# =====================================================================
# 2. EXTRACTION DES FEATURES (FFT) & NORMALISATION
# =====================================================================
def extraire_features_allure(signal):
    signal_centre = signal - np.mean(signal)
    fft_vals = np.fft.rfft(signal_centre)
    spectre_puissance = np.abs(fft_vals) ** 2
    basses_freq = np.sum(spectre_puissance[1:5])
    moyennes_freq = np.sum(spectre_puissance[5:20])
    amp_max = np.max(signal)
    return amp_max, basses_freq, moyennes_freq

features = np.array([extraire_features_allure(s) for s in signaux])
features_norm = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-6)

indices_train = [0, 1,  3, 4,  6, 7]  
indices_test  = [2, 5, 8]             

X_train = features_norm[indices_train]
X_test = features_norm[indices_test]

# =====================================================================
# 3. K-MEANS CONTRAINT (Multi-initialisations n_init = 30)
# =====================================================================
n_clusters = 3
taille_cluster = 2
n_init = 30

meilleure_inertie = float('inf')
meilleurs_centres = None
meilleurs_labels_train = None

np.random.seed(24) 

for init in range(n_init):
    centres_courants = X_train[np.random.choice(len(X_train), n_clusters, replace=False)]
    for _ in range(20):
        centres_étendus = np.repeat(centres_courants, taille_cluster, axis=0)
        matrice_distances = np.linalg.norm(X_train[:, np.newaxis, :] - centres_étendus[np.newaxis, :, :], axis=2)
        _, indices_slots = linear_sum_assignment(matrice_distances)
        labels_train_courants = indices_slots // taille_cluster
        
        nouveaux_centres = np.zeros_like(centres_courants)
        for c in range(n_clusters):
            points_du_cluster = X_train[labels_train_courants == c]
            if len(points_du_cluster) > 0: nouveaux_centres[c] = points_du_cluster.mean(axis=0)
        if np.allclose(centres_courants, nouveaux_centres): break
        centres_courants = nouveaux_centres
        
    inertie_courante = sum(np.sum(np.linalg.norm(X_train[labels_train_courants == c] - centres_courants[c], axis=1)**2) for c in range(n_clusters))
    if inertie_courante < meilleure_inertie:
        meilleure_inertie = inertie_courante
        meilleurs_centres = centres_courants
        meilleurs_labels_train = labels_train_courants

centres = meilleurs_centres
labels_train = meilleurs_labels_train

# Variance interne des clusters pour la pondération
std_clusters = np.zeros_like(centres)
epsilon = 1e-2
for c in range(n_clusters):
    points_du_cluster = X_train[labels_train == c]
    std_clusters[c] = np.std(points_du_cluster, axis=0) + epsilon if len(points_du_cluster) > 1 else np.ones(X_train.shape[1]) * epsilon

# Fonction de prédiction pondérée (Mahalanobis diagonale) pour un point ou une grille
def predire_points(points, centres, std_clusters):
    preds = []
    for p in points:
        dists = [np.sqrt(np.sum(((p - centres[c]) / std_clusters[c]) ** 2)) for c in range(n_clusters)]
        preds.append(np.argmin(dists))
    return np.array(preds)

labels_test = predire_points(X_test, centres, std_clusters)

# Reconstruction de l'ordre total des prédictions pour les graphiques
predictions_totale = np.zeros(9, dtype=int)
for i, idx in enumerate(indices_train): predictions_totale[idx] = labels_train[i]
for i, idx in enumerate(indices_test):  predictions_totale[idx] = labels_test[i]

# =====================================================================
# 4. SAUVEGARDE IMAGE 1 : TRACES TEMPORELLES ET SPECTRES FFT
# =====================================================================
fig, axs = plt.subplots(9, 2, figsize=(14, 20))
fig.suptitle("Signaux Temporels (Fréquence vs Temps) & Analyse Fréquentielle (FFT)", fontsize=16, fontweight='bold', y=0.99)

for i in range(9):
    # Colonne 1 : Temps
    axs[i, 0].plot(t, f_reference + signaux[i], color='black', alpha=0.8)
    axs[i, 0].set_title(f"Trace {i+1} : {noms_signaux[i]}", fontsize=10, loc='left', fontweight='bold')
    axs[i, 0].set_xlim(0, 8)
    axs[i, 0].grid(True, linestyle='--')
    
    # Colonne 2 : FFT
    sig_c = signaux[i] - np.mean(signaux[i])
    freqs = np.fft.rfftfreq(len(sig_c), d=1/feux_hz)
    spectre = np.abs(np.fft.rfft(sig_c)) ** 2
    
    axs[i, 1].semilogy(freqs[:40], spectre[:40], color='tab:red') # On zoome sur les 40 premières composantes
    axs[i, 1].set_title("Spectre de Puissance FFT", fontsize=9, loc='right', color='dimgray')
    axs[i, 1].grid(True, linestyle='--')

axs[-1, 0].set_xlabel("Temps (secondes)")
axs[-1, 1].set_xlabel("Fréquence de modulation (Hz)")
plt.tight_layout()
plt.savefig('signaux_fourier.png', dpi=150, bbox_inches='tight')
plt.close()

# =====================================================================
# 5. SAUVEGARDE IMAGE 2 : CLUSTERS AVEC FOND COLORÉ ET CONTOURS RÉELS
# =====================================================================
plt.figure(figsize=(11, 7))
couleurs_classes = ['tab:blue', 'tab:orange', 'tab:purple']
cm_fond = matplotlib.colors.ListedColormap(['#d9e6f2', '#fcead1', '#f0e6f5']) # Couleurs douces pour le fond

# Génération de la grille pour colorer les zones de décision (sur les axes Feature 1 et 2)
x_min, x_max = features_norm[:, 1].min() - 0.7, features_norm[:, 1].max() + 0.7
y_min, y_max = features_norm[:, 2].min() - 0.7, features_norm[:, 2].max() + 0.7
xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300), np.linspace(y_min, y_max, 300))

# Pour chaque point de la grille, on simule une feature 3 (amplitude max) fixe à la moyenne (0) pour projeter en 2D
grille_points = np.c_[np.zeros(xx.ravel().shape), xx.ravel(), yy.ravel()]
Z = predire_points(grille_points, centres, std_clusters)
Z = Z.reshape(xx.shape)

# Coloration des zones de décision arrière-plan
plt.contourf(xx, yy, Z, cmap=cm_fond, alpha=1.0)

# Tracé des points (Train + Test mélangés pour affichage global)
for idx in range(9):
    f_p = features_norm[idx]
    c_pred = predictions_totale[idx]
    c_reel = labels_reels[idx]
    mark = 'X' if idx in indices_test else 'o'
    taille = 260 if idx in indices_test else 180
    lbl = "Donnée Test (X)" if idx in indices_test else "Donnée Train (•)"
    
    # Dessin du point : Couleur intérieure = Cluster Prédit, Couleur contour (edgecolor) = Classe Réelle
    plt.scatter(f_p[1], f_p[2], c=couleurs_classes[c_pred], marker=mark, s=taille, 
                edgecolors=couleurs_classes[c_reel], linewidths=3.5, zorder=3, label=lbl if idx in [2,0] else "")

# Tracé des centres optimaux
plt.scatter(centres[:, 1], centres[:, 2], color='red', marker='*', s=350, edgecolors='black', zorder=4, label='Centres de décision')

plt.title("Espace Décisionnel de Fourier (Zones colorées par Cluster)", fontsize=13, fontweight='bold')
plt.xlabel("Énergie Basses Fréquences (Étalement Global)")
plt.ylabel("Énergie Moyennes Fréquences (Rugosité / Multi-pics)")
plt.xlim(x_min, x_max)
plt.ylim(y_min, y_max)
plt.grid(True, alpha=0.3)

# Gestion propre des légendes sans doublons
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), loc='lower left', framealpha=0.9)

# Note explicative sur le graphique
plt.text(x_min+0.1, y_max-0.3, "• Couleur intérieure = Cluster attribué\n• Couleur contour = Classe réelle", 
         bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'), fontsize=9)

plt.savefig('features_clusters.png', dpi=150, bbox_inches='tight')
plt.close()

# =====================================================================
# 6. SAUVEGARDE IMAGE 3 : MATRICE DE CONFUSION
# =====================================================================
y_true = [labels_reels[idx] for idx in indices_train] + [labels_reels[idx] for idx in indices_test]
y_pred = list(labels_train) + list(labels_test)

plt.figure(figsize=(6, 6))
disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix(y_true, y_pred), display_labels=['Voiture', 'Camion', 'Intermédiaire'])
disp.plot(cmap=plt.cm.Blues, ax=plt.gca(), values_format='d')
plt.title("Matrice de Confusion Finale")
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

print("--- EXÉCUTION TERMINÉE SUR GITHUB ---")
print("Fichiers d'analyse exportés avec succès :")
print("1. signaux_fourier.png  -> Visualisation temporelle et fréquentielle des 9 traces.")
print("2. features_clusters.png -> Cartographie des zones d'influence des clusters avec marqueurs bi-colorés.")
print("3. confusion_matrix.png  -> Matrice de performance de la classification.")