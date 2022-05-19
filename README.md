# JewelleryByEline
###### site NSI créé par 
### C'est un projet de boutique en ligne de bagues pour la marque Jewellery By Eline. 
#### Le site contient 5 pages toutes différentes :
- Acceuil :
sert à....
- Femme :
- Homme : 
- Soldes :
- Nous découvrir :

### Le site contient aussi plusieurs effets écrits en Javascript :
#### - Un carrousel :
##### ou type de module de site Web qui fait la rotation du contenu d'une manière similaire à celle d'un diaporama, soit par une commande de l'utilisateur ou par des transitions temporisées.
Il est utilisé pour prévisualiser l'ambiance du site et certains bijoux choisis.

#### - Une barre de recherche avec saisie semi-automatique :
Cette barre de recherche est incomplète, en effet les différents articles n'ont pas de pages attitrées et la barre de recherche ne peut donc pas mener vers ces dernières. La barre de recherche peut cependant proposer les mots ou groupes de mots choisis dans js/suggestions.js comme ci-dessous :

```js
 let suggestions = [
    "Soldes",
 ];
```

#### - L'affichage des tailles sur les bagues :
Cet effet permet d'afficher les différentes tailles proposées (S/M/L). Il se produit lorsque la souris passe sur l'image d'un article. Lorsque cela arrive, l'image se grise et les tailles disponibles de l'article sont indiquées. Cela permet à l'utilisateur de voir directemnt si la taille qu'il porte est disponible.

#### - Le tableau "à craie" :
Cet effet permet à l'utilisateur de s'amuser à déssiner avec sa souris la bague de ses rêves (ou ce qu'il veut). Unique et ludique, cette fonctionnalité contribue à la relation client que souhaient avoir les deux créatrices. 

```js
<div class="fadebox">
  <div class="title text">Taille en stock : S / M / L </div>
</div>
```
