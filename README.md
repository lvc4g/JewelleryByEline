# JewelleryByEline
###### site NSI créé par 
### C'est un projet de boutique en ligne de bagues pour la marque Jewellery By Eline. 
#### Le site contient 5 pages toutes différentes :
- Acceuil :
Page d'acceuil et page principale.
- Femme :
Page comportant des bijoux pour les femmes.
- Homme : 
Page comportant des bijoux pour les hommes.
- Soldes :
Page comportant toutes les soldes.
- Nous découvrir :
Page comportant des informations sur la marque avec notemment toute son histoire.

### Le site contient aussi plusieurs effets écrits en Javascript :
#### - Un carrousel : 
(ou type de module de site Web qui fait la rotation du contenu d'une manière similaire à celle d'un diaporama, soit par une commande de l'utilisateur ou par des transitions temporisées.)

Il est utilisé pour prévisualiser l'ambiance du site et certains bijoux choisis. On trouve ci-dessous le début de l'html du carrousel :


```html
<div id="carrousel">
	<div id="container">
	</div>
	<img src="bouton.png" class="bouton" id="d" />
	<img src="bouton.png" class="bouton" id="g"/>
</div>
```


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
Cet effet permet à l'utilisateur de s'amuser à déssiner avec sa souris la bague de ses rêves (ou ce qu'il veut). Unique et ludique, cette fonctionnalité contribue à la relation client que souhaient avoir les deux créatrices. À terme, il serait amélioré pour permettre de stocker les différents dessins et de réaliser des concours dans lesquels chaque utilisateur pourrait donner son avis afin d'élir le plus beau dessin. Ces concours permettraient de créer une réelle proximité avec les clients.

#### - La carte du produit le plus tendance :
Cette carte attractive permet de mettre en avant le produit le plus commandé du mois et donc d'inciter les utilisateurs à commander pour être tendance.


#### - POP UP ! :
Cet effet informe l'utilisateur qu'il a de belles soldes à ne pas manquer. Les soldes sont en réalité essentiellement constituées de produits invendus. Il permet donc encore d'inciter à la consommation mais cible les uitilisateurs moins fortunés. Une partie du css du pop est affichée ci-dessous :

```css
.popup{
	position: fixed;
	top: 50%;
	left: 50%;
	transform: trasnlate(-50%, -50%);
	display : none;
}
```
