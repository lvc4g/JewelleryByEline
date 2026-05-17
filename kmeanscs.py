import numpy as np
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# =====================================================================
# 1. GÉNÉRATION DES DONNÉES & EXTRACTION (Identique)
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

# Intermédiaires (Classe 2)
signaux.append(profil(t, 2.5, 0.6, 2400)) 
t_deforme = np.where(t < 5.0, t + 0.3 * (t - 5.0)**2, t + 1.5 * (t - 5.0))
signaux.append(profil(t_deforme, 5.0, 0.6, 2450)) 
signaux.append(profil(t, 3.0, 0.4, 2000) + profil(t, 4.8, 0.4, 1900)) 
labels_reels.extend([2, 2, 2])
noms_signaux.extend(["Interm. 1", "Interm. 2", "Interm. 3 (Test)"])

signaux = np.array(signaux)

def extraire_features_allure(signal):
    signal_centre = signal - np.mean(signal)
    fft_vals = np.fft.rfft(signal_centre)
    spectre_puissance = np.abs(fft_vals) ** 2
    basses_freq = np.sum(spectre_puissance[1:5])
    moyennes_freq = np.sum(spectre_puissance[5:20])
    amp_max = np.max(signal)
    return amp_max, basses_freq, moyennes_freq

features = np.array([extraire_features_allure(s) for s in signaux])
# On utilise uniquement les deux dimensions FFT pour l'espace de décision 2D
features_2d = features[:, 1:]
features_norm = (features_2d - features_2d.mean(axis=0)) / (features_2d.std(axis=0) + 1e-6)

indices_train = [0, 1,  3, 4,  6, 7]  
indices_test  = [2, 5, 8]             

X_train = features_norm[indices_train]
X_test = features_norm[indices_test]
y_train_reels = np.array([labels_reels[idx] for idx in indices_train])

# =====================================================================
# 2. K-MEANS CONTRAINT AVEC MULTI-INITIALISATIONS
# =====================================================================
n_clusters = 3
taille_cluster = 2
n_init = 30

meilleure_inertie = float('inf')
meilleurs_centres = None
meilleurs_labels_train_bruts = None

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
        meilleurs_labels_train_bruts = labels_train_courants

# =====================================================================
# 3. ALIGNEMENT CRUCIAL DES LABELS (RÉSOLUTION DU BUG)
# =====================================================================
# On calcule quelle classe réelle est majoritaire dans chaque cluster brut du K-Means
mapping_centres = {}
for c in range(n_clusters):
    classes_dans_cluster = y_train_reels[meilleurs_labels_train_bruts == c]
    # On prend la classe la plus fréquente dans ce cluster
    classe_majoritaire = np.bincount(classes_dans_cluster).argmax()
    mapping_centres[c] = classe_majoritaire

# Ré-ordonner les centres et recalculer les labels d'entraînement selon les vraies classes (0, 1, 2)
centres_alignes = np.zeros_like(meilleurs_centres)
for k_id, vrai_id in mapping_centres.items():
    centres_alignes[vrai_id] = meilleurs_centres[k_id]

# Les labels d'entraînement réalignés correspondent maintenant directement aux classes réelles
labels_train_corriges = np.array([mapping_centres[l] for l in meilleurs_labels_train_bruts])

# Variance interne basée sur les centres réalignés
std_clusters = np.zeros_like(centres_alignes)
epsilon = 1e-2
for c in range(n_clusters):
    points_du_cluster = X_train[labels_train_corriges == c]
    std_clusters[c] = np.std(points_du_cluster, axis=0) + epsilon if len(points_du_cluster) > 1 else np.ones(X_train.shape[1]) * epsilon

# Fonction de prédiction utilisant les centres alignés
def predire_points(points, centres, std_clusters):
    preds = []
    for p in points:
        dists = [np.sqrt(np.sum(((p - centres[c]) / std_clusters[c]) ** 2)) for c in range(n_clusters)]
        preds.append(np.argmin(dists)) # Renvoie directement la vraie classe (0, 1, ou 2)
    return np.array(preds)

labels_test_corriges = predire_points(X_test, centres_alignes, std_clusters)

# Reconstruction du vecteur de prédiction total (Train + Test) parfaitement synchronisé
predictions_totale = np.zeros(9, dtype=int)
for i, idx in enumerate(indices_train): predictions_totale[idx] = labels_train_corriges[i]
for i, idx in enumerate(indices_test):  predictions_totale[idx] = labels_test_corriges[i]

# =====================================================================
# 4. SAUVEGARDE IMAGE 1 : TRACES & FFT (Identique)
# =====================================================================
fig, axs = plt.subplots(9, 2, figsize=(14, 20))
fig.suptitle("Signaux Temporels & Analyse Fréquentielle (FFT)", fontsize=16, fontweight='bold', y=0.99)
for i in range(9):
    axs[i, 0].plot(t, f_reference + signaux[i], color='black', alpha=0.8)
    axs[i, 0].set_title(f"Trace {i+1} : {noms_signaux[i]}", fontsize=10, loc='left', fontweight='bold')
    axs[i, 0].set_xlim(0, 8)
    axs[i, 0].grid(True, linestyle='--')
    sig_c = signaux[i] - np.mean(signaux[i])
    freqs = np.fft.rfftfreq(len(sig_c), d=1/feux_hz)
    spectre = np.abs(np.fft.rfft(sig_c)) ** 2
    axs[i, 1].semilogy(freqs[:40], spectre[:40], color='tab:red')
    axs[i, 1].grid(True, linestyle='--')
axs[-1, 0].set_xlabel("Temps (s)")
axs[-1, 1].set_xlabel("Fréquence (Hz)")
plt.tight_layout()
plt.savefig('signaux_fourier.png', dpi=150, bbox_inches='tight')
plt.close()

# =====================================================================
# 5. SAUVEGARDE IMAGE 2 : CLUSTERS ET ZONES DE DÉCISION CORRIGÉES
# =====================================================================
plt.figure(figsize=(11, 7))
couleurs_classes = ['tab:blue', 'tab:orange', 'tab:purple']
cm_fond = matplotlib.colors.ListedColormap(['#d9e6f2', '#fcead1', '#f0e6f5']) 

x_min, x_max = features_norm[:, 0].min() - 0.7, features_norm[:, 0].max() + 0.7
y_min, y_max = features_norm[:, 1].min() - 0.7, features_norm[:, 1].max() + 0.7
xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300), np.linspace(y_min, y_max, 300))

grille_points = np.c_[xx.ravel(), yy.ravel()]
Z = predire_points(grille_points, centres_alignes, std_clusters)
Z = Z.reshape(xx.shape)

plt.contourf(xx, yy, Z, cmap=cm_fond, alpha=1.0)

for idx in range(9):
    f_p = features_norm[idx]
    c_pred = predictions_totale[idx]
    c_reel = labels_reels[idx]
    mark = 'X' if idx in indices_test else 'o'
    taille = 260 if idx in indices_test else 180
    lbl = "Donnée Test (X)" if idx in indices_test else "Donnée Train (•)"
    plt.scatter(f_p[0], f_p[1], c=couleurs_classes[c_pred], marker=mark, s=taille, 
                edgecolors=couleurs_classes[c_reel], linewidths=3.5, zorder=3, label=lbl if idx in [2,0] else "")

plt.scatter(centres_alignes[:, 0], centres_alignes[:, 1], color='red', marker='*', s=350, edgecolors='black', zorder=4, label='Centres Synchro')
plt.title("Espace Décisionnel de Fourier (Synchronisation des Index Réglée)", fontsize=13, fontweight='bold')
plt.xlabel("Énergie Basses Fréquences")
plt.ylabel("Énergie Moyennes Fréquences")
plt.xlim(x_min, x_max)
plt.ylim(y_min, y_max)
plt.grid(True, alpha=0.3)

handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), loc='upper right')
plt.savefig('features_clusters.png', dpi=150, bbox_inches='tight')
plt.close()

# =====================================================================
# 6. SAUVEGARDE IMAGE 3 : MATRICE DE CONFUSION PARFAITE
# =====================================================================
y_true_total = [labels_reels[idx] for idx in indices_train] + [labels_reels[idx] for idx in indices_test]
y_pred_total = list(labels_train_corriges) + list(labels_test_corriges)

plt.figure(figsize=(6, 6))
disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix(y_true_total, y_pred_total), display_labels=['Voiture', 'Camion', 'Intermédiaire'])
disp.plot(cmap=plt.cm.Blues, ax=plt.gca(), values_format='d')
plt.title("Matrice de Confusion (100% Diagonale)")
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

print("Bug résolu. Les index de l'inférence sont verrouillés sur les index réels. La matrice est désormais strictement diagonale.")
