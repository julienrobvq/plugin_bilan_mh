# Bilan milieu humide

Cette extension permet de calculer les valeurs des associées aux bilans dans le formulaire milieux humides de Géofluence.

## Étapes d'utilisation

1. Ouvrir la table attributaire du formulaire milieux humides et sélectionner les entités pour lesquelles vous souhaitez générer un bilan. Cette étape est optionnelle, si vous ne sélectionnez rien, le bilan sera calculé pour toutes les entités de la couche. Il est toutefois à noter que le temps de calcul augmente en fonction du nombre d'entités sélectionnées. 
2. Si vous souhaitez exécuter le calcul uniquement sur votre sélection, cocher l'option "Appliquer seulemetn aux milieux humides sélectionnés".
3. Lancer le calcul du bilan.
4. Un message vous indique le calcul s'est exécuté avec succès. En cliquant sur le bouton des détails, vous pouvez consulter une synthèse des valeurs calculées et insérer dans le formulaire milieux humides.

## Fonctionnement de l'extension

### Hydrologie

- La section hydrologie est calculée à l'aide d'un compteur sur les indicateurs hydrologiques primaires et secondaires.
- Pour qu'un milieu ait une hydrologie typique des milieux humides, il doit y avoir au moins 1 indicateur primaire ou 2 indicateurs secondaires comptabilisés. 

### Sol

- Le nombre d'horizons minérales est calculé avec un compteur qui compile les horizons de type "Minéral" ou "Sol perturbé (organique et minéral)"
- Le nombre d'horizons organique est calculé avec un compteur qui compile les horizons de type "Fibrisol, mésisol, humisol"
- Le bilan indique un sol hydromorphe si au moins une horizon organique est compilée ou si la classe de drainage du sol est de 5 ou de 6 et si au moins une horizon minérale a été compilée.

### Végétation

Pour le bilan de végétation, des valeurs sont calculées dans deux couches.

#### Formulaire espèces végétales

1. Calcul du recouvrement relatif des espèces en fonction de leur strate et du recouvrement absolu noté sur le terrain.
2. À partir des recouvrement absolu, on détermine si l'espèce est dominante dans sa strate : 

    - Classement des valeurs de recouvrement relatif en ordre décroissant. 
    - Les espèces qui ont un recouvrement relatif égal ou supérieur à 20 sont directement notées comme dominantes.
    - Celles qui contribuent à atteindre 50% du recouvrement relatif de la strate le sont également. 
    - Lorsque plusieurs espèces ont le même recouvrement relatif et qu'au moins une d'entre elles permet d'atteindre le seuil de 50%, toutes les espèces sont identifiées comme dominantes. Cela permet de tenir compte du caractère aléatoire du classement initial lorsque plusieurs enregistrements ont la même valeur de recouvrement relatif.
    - Finalement, lorsque les recouvrements absolus totaux d'une strate sont inférieurs à 10%, les espèces qui la composent ne peuvent jamais considérées comme dominantes.

#### Formulaire milieux humides

- Le nombre d'espèces indicatrices des milieux humides est calculé avec un compteur qui compile les espèces dominantes d'un milieu ayant un statut hydrique "obligatoire" ou "facultatif".
- Le nombre d'espèces non indicatrices des milieux humides est calculé avec un compteur qui compile les espèces dominantes d'un milieu ayant un statut hydrique "non indicatrice". Les espèces n'ayant pas de statut hydrique sont également comprises dans ce calcul.
- Le bilan de végétation indique une végétation typique des milieux humides si le nombre d'essences hygrophiles est supérieur au nombre d'essences non hygrophiles.

### Bilan final

- Le bilan indique la présence d'un milieu humide lorsqu'un sol hydromorphe a été identifié et qu'aucune perturbation anthropique majeure et irréversible n'a été signalée, ou lorsque la végétation est dominée par essences hygrophiles.