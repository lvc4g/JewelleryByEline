import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

# =====================================================================
# 1. GÉNÉRATION DES DONNÉES & EXTRACTION
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
voitures = [
    {"t_c": 1.5, "larg": 0.30, "amp": 2100},
    {"t_c": 6.0, "larg": 0.35, "amp": 2300},
    {"t_c": 3.5, "larg": 0.32, "amp": 2150},
    {"t_c": 2.8, "larg": 0.28, "amp": 2250},
    {"t_c": 5.2, "larg": 0.34, "amp": 2180},
    {"t_c": 4.1, "larg": 0.26, "amp": 2330}
]
for i, p in enumerate(voitures):
    signaux.append(profil(t, p["t_c"], p["larg"], p["amp"]))
    labels_reels.append(0)
    noms_signaux.append(f"Voiture {i+1}{' (Test)' if i >= 4 else ''}")

# Camions (Classe 1)
camions = [
    {"t_c": 5.5, "larg": 1.10, "amp": 2600},
    {"t_c": 2.0, "larg": 0.90, "amp": 2500},
    {"t_c": 4.0, "larg": 1.20, "amp": 2700},
    {"t_c": 3.0, "larg": 1.30, "amp": 2550},
    {"t_c": 6.5, "larg": 0.95, "amp": 2650},
    {"t_c": 4.8, "larg": 1.05, "amp": 2750}
]
for i, p in enumerate(camions):
    signaux.append(profil(t, p["t_c"], p["larg"], p["amp"]))
    labels_reels.append(1)
    noms_signaux.append(f"Camion {i+1}{' (Test)' if i >= 4 else ''}")

# Intermédiaires (Classe 2)
interms = [
    {"type": "hybride", "t_c": 4.0, "larg": 0.60, "amp": 2400},
    {"type": "accel", "t_c": 5.0, "larg": 0.60, "amp": 2450},
    {"type": "double", "t_c": 0.0, "larg": 0.00, "amp": 0.00},
    {"type": "decroissance", "t_c": 3.5, "larg": 0.50, "amp": 2300},
    {"type": "oscillation", "t_c": 4.0, "larg": 0.70, "amp": 2350},
    {"type": "plateau", "t_c": 4.0, "larg": 1.50, "amp": 2250}
]
for i, p in enumerate(interms):
    if p["type"] == "hybride":
        s = profil(t, p["t_c"], p["larg"], p["amp"]) + 0.0
        title = "Interm. 1"
    elif p["type"] == "accel":
        t_deforme = np.where(t < p["t_c"],
                             t + 0.3 * (t - p["t_c"])**2,
                             t + 1.5 * (t - p["t_c"]))
        s = profil(t_deforme, p["t_c"], p["larg"], p["amp"])
        title = "Interm. 2"
    elif p["type"] == "double":
        s = profil(t, 3.0, 0.40, 2000) + profil(t, 4.8, 0.40, 1900)
        title = "Interm. 3"
    elif p["type"] == "decroissance":
        s = profil(t, p["t_c"], p["larg"], p["amp"]) + 1200 * np.exp(-((t - 5.0) / 1.20) ** 2)
        title = "Interm. 4"
    elif p["type"] == "oscillation":
        s = profil(t, p["t_c"], p["larg"], p["amp"]) * (1 + 0.2 * np.sin(5 * t))
        title = "Interm. 5"
    else:
        s = profil(t, p["t_c"], p["larg"], p["amp"]) + 300 * np.exp(-((t - 4.0) / 0.80) ** 2)
        title = "Interm. 6"
    signaux.append(s)
    labels_reels.append(2)
    noms_signaux.append(f"{title}{' (Test)' if i >= 4 else ''}")

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

indices_train = [0, 1, 2, 3, 6, 7, 8, 9, 12, 13, 14, 15]
indices_test = [4, 5, 10, 11, 16, 17]

X_train = features_norm[indices_train]
X_test = features_norm[indices_test]
y_train_reels = np.array([labels_reels[idx] for idx in indices_train])

# =====================================================================
# 2. K-MEANS CONTRAINT AVEC MULTI-INITIALISATIONS
# =====================================================================
n_clusters = 3
# Déterminer dynamiquement le nombre de slots par centre pour
# garantir au moins autant de slots que d'échantillons d'entraînement.
taille_cluster = int(np.ceil(len(X_train) / n_clusters))
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
            if len(points_du_cluster) > 0:
                nouveaux_centres[c] = points_du_cluster.mean(axis=0)
        if np.allclose(centres_courants, nouveaux_centres):
            break
        centres_courants = nouveaux_centres

    inertie_courante = sum(np.sum(np.linalg.norm(X_train[labels_train_courants == c] - centres_courants[c], axis=1)**2) for c in range(n_clusters))
    if inertie_courante < meilleure_inertie:
        meilleure_inertie = inertie_courante
        meilleurs_centres = centres_courants
        meilleurs_labels_train_bruts = labels_train_courants

# =====================================================================
# 3. ALIGNEMENT CRUCIAL DES LABELS (RÉSOLUTION DU BUG)
# =====================================================================
mapping_centres = {}
for c in range(n_clusters):
    classes_dans_cluster = y_train_reels[meilleurs_labels_train_bruts == c]
    classe_majoritaire = np.bincount(classes_dans_cluster).argmax()
    mapping_centres[c] = classe_majoritaire

centres_alignes = np.zeros_like(meilleurs_centres)
for k_id, vrai_id in mapping_centres.items():
    centres_alignes[vrai_id] = meilleurs_centres[k_id]

labels_train_corriges = np.array([mapping_centres[l] for l in meilleurs_labels_train_bruts])

std_clusters = np.zeros_like(centres_alignes)
epsilon = 1e-2
for c in range(n_clusters):
    points_du_cluster = X_train[labels_train_corriges == c]
    std_clusters[c] = np.std(points_du_cluster, axis=0) + epsilon if len(points_du_cluster) > 1 else np.ones(X_train.shape[1]) * epsilon


def predire_points(points, centres, std_clusters):
    preds = []
    for p in points:
        dists = [np.sqrt(np.sum(((p - centres[c]) / std_clusters[c]) ** 2)) for c in range(n_clusters)]
        preds.append(np.argmin(dists))
    return np.array(preds)

labels_test_corriges = predire_points(X_test, centres_alignes, std_clusters)

predictions_totale = np.zeros(18, dtype=int)
for i, idx in enumerate(indices_train):
    predictions_totale[idx] = labels_train_corriges[i]
for i, idx in enumerate(indices_test):
    predictions_totale[idx] = labels_test_corriges[i]

# =====================================================================
# 4. SAUVEGARDE IMAGE 1 : TRACES & FFT
# =====================================================================
fig, axs = plt.subplots(18, 2, figsize=(14, 36))
fig.suptitle("Signaux Temporels & Analyse Fréquentielle (FFT)", fontsize=16, fontweight='bold', y=0.99)
for i in range(18):
    axs[i, 0].plot(t, f_reference + signaux[i], color='black', alpha=0.8)
    axs[i, 0].set_title(f"Trace {i+1} : {noms_signaux[i]}", fontsize=10, loc='left', fontweight='bold')
    axs[i, 0].set_xlim(0, 8)
    axs[i, 0].grid(True, linestyle='--')
    sig_c = signaux[i] - np.mean(signaux[i])
    freqs = np.fft.rfftfreq(len(sig_c), d=1/feux_hz)
    spectre = np.abs(np.fft.rfft(sig_c)) ** 2
    axs[i, 1].semilogy(freqs[:40], spectre[:40], color='tab:red')
    axs[i, 1].grid(True, linestyle='--')
# Étiquettes d'axes avec unités : colonnes gauche/droite
axs[0, 0].set_ylabel("Amplitude")
axs[0, 1].set_ylabel("Puissance spectrale")
axs[-1, 0].set_xlabel("Temps (s)")
axs[-1, 1].set_xlabel("Fréquence (Hz)")
plt.tight_layout()
plt.savefig('signaux_fourier.png', dpi=150, bbox_inches='tight')
plt.close()

# =====================================================================
# 5. SAUVEGARDE IMAGE 2 : CLUSTERS ET ZONES DE DÉCISION
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

# Tracer explicitement les points par classe pour s'assurer que toutes les
# données (4 entraînement + 2 test par classe) sont affichées clairement.
for c in range(n_clusters):
    # indices d'entraînement et de test pour la classe réelle c
    train_idxs = [i for i in indices_train if labels_reels[i] == c]
    test_idxs = [i for i in indices_test if labels_reels[i] == c]

    # Points d'entraînement
    if train_idxs:
        xs = features_norm[train_idxs, 0]
        ys = features_norm[train_idxs, 1]
        preds = [predictions_totale[i] for i in train_idxs]
        plt.scatter(xs, ys, c=[couleurs_classes[p] for p in preds], marker='o', s=100,
                    edgecolors=couleurs_classes[c], linewidths=0.5, zorder=3,
                    label=f'Classe {c} Train')

    # Points de test
    if test_idxs:
        xs = features_norm[test_idxs, 0]
        ys = features_norm[test_idxs, 1]
        preds = [predictions_totale[i] for i in test_idxs]
        plt.scatter(xs, ys, c=[couleurs_classes[p] for p in preds], marker='X', s=180,
                    edgecolors=couleurs_classes[c], linewidths=0.5, zorder=3,
                    label=f'Classe {c} Test')

plt.scatter(centres_alignes[:, 0], centres_alignes[:, 1], color='red', marker='*', s=300, edgecolors='black', zorder=4, label='Centres Synchro')
plt.title("Espace Décisionnel de Fourier (Synchronisation des Index Réglée)", fontsize=13, fontweight='bold')
# Les features ont été normalisées => unités en z-score
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
# 6. SAUVEGARDE IMAGE 3 : MATRICE DE CONFUSION
# =====================================================================
y_true_total = [labels_reels[idx] for idx in indices_train] + [labels_reels[idx] for idx in indices_test]
y_pred_total = list(labels_train_corriges) + list(labels_test_corriges)

plt.figure(figsize=(6, 6))
disp = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix(y_true_total, y_pred_total), display_labels=['Voiture', 'Camion', 'Intermédiaire'])
disp.plot(cmap=plt.cm.Blues, ax=plt.gca(), values_format='d')
# Indiquer une unité pour la matrice (comptage d'exemples)
plt.xlabel("Prédictions")
plt.ylabel("Vraies classes")
plt.title("Matrice de Confusion")
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()

print("Execution terminée. Les fichiers signaux_fourier.png, features_clusters.png et confusion_matrix.png ont été sauvegardés.")
