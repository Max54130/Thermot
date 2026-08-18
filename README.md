# Thermot

Jeu de mots par proximité de sens, en français, entièrement hors ligne.
Le mot caché se devine par le sens, pas par l'orthographe : chaque proposition
reçoit une température calculée sur l'appareil.

Version 4.3.0 · six variantes · minSdk 21 · targetSdk 34

**Nouveautés 4.0.1** : le titre de l'en-tête reprend la lettre du logo. Il était
composé en JetBrains Mono, une chasse fixe, alors que le mot-symbole utilise une
police proportionnelle : les avances y varient d'une lettre à l'autre. Le mot du
logo a été mesuré sur l'image, hauteur des lettres 95 px et largeur 703 px, soit
un rapport de 7,40. Space Grotesk demi-gras à 0,165 em d'espacement donne 7,49,
c'est le meilleur accord parmi les polices embarquées. L'écran de démarrage n'a
pas été touché.

**Nouveautés 4.0.0** : le corpus est lu jusqu'au rang 1 000 000 au lieu de
500 000, et l'application est livrée en six APK. Chaque variante monolingue
n'embarque que son lexique et va donc beaucoup plus loin dans le vocabulaire.
Elles portent des identifiants distincts (`fr.thermot.jeu.fr`, `.en`, etc.) et
cohabitent sur le même téléphone.

| Variante | Mots jouables | Taille | Chargement | Analyse d'une partie | Mémoire |
|---|---|---|---|---|---|
| Multilingue | 110 000 par langue | 169 Mo | 1,5 s | 129 ms | 61 Mo |
| Français | 184 517 | 56 Mo | 1,7 s | 222 ms | 92 Mo |
| Anglais | 176 758 | 54 Mo | 1,1 s | 207 ms | 75 Mo |
| Espagnol | 258 776 | 79 Mo | 1,3 s | 270 ms | 114 Mo |
| Italien | 254 231 | 77 Mo | 1,2 s | 268 ms | 107 Mo |
| Allemand | 400 034 | 124 Mo | 3,3 s | 448 ms | 242 Mo |

Mesures prises sur les APK eux-mêmes, pas sur les sources : le contenu de
chaque archive est extrait puis servi tel quel au navigateur de test.

L'allemand atteint le plafond de 400 000 mots fixé dans la chaîne, ses composés
étant sans fin. C'est aussi la variante la plus lourde à l'exécution : 242 Mo de
mémoire, à surveiller sur un téléphone d'entrée de gamme.

`construire_variantes.sh` produit les six APK. `outils/tronquer_lexique.py`
dérive les lexiques allégés de la variante multilingue sans relire le corpus,
les mots étant rangés par fréquence décroissante dans le fichier binaire.

Version 3.5.0

**Nouveautés 3.5.0** :

- Filtre de contenu. Les mots crus et à caractère sexuel sont masqués par
  défaut : ils ne peuvent être ni proposés, ni figurer parmi les mots les plus
  proches, ni tomber comme mot du jour. Une option « Mots crus » dans le menu
  les rend jouables, elle est désactivée à l'installation. Un joueur qui tape un
  mot masqué reçoit un message explicite, et non un « mot inconnu » trompeur.
- Les listes sont construites par `outils/build_sensibles.py` : amorces
  explicites, extension par voisinage vectoriel au-delà de 0,40 de proximité,
  puis retrait des faux positifs relus. Entre 288 et 672 mots par langue, soit
  moins de 1 % du vocabulaire.
- Correction : le bouton « Changer de thème » du menu ne faisait rien. Son
  action n'était pas branchée dans l'aiguillage, depuis la version 1.4.0. Le
  bouton de l'en-tête, lui, a toujours fonctionné.

Version 3.4.0

**Nouveautés 3.4.0** : le vocabulaire acceptable double. Les corpus sont
désormais lus jusqu'à la 320 000ᵉ ligne au lieu de la 120 000ᵉ, et les plafonds
passent de 40 000 à 78 000 mots en français, de 24 000 à 48 000 dans les autres
langues. Des mots rares mais parfaitement usuels comme « esperluette »,
rang 184 240 du corpus, deviennent jouables.

Deux régressions corrigées au passage : le filtre de téléchargement raisonnait
en octets et perdait tous les mots allemands commençant par une voyelle
infléchie, et la règle de flexion allemande fusionnait « Kirsche », le fruit,
avec « Kirsch », l'alcool.

Version 3.3.0

**Nouveautés 3.3.0**, issues d'un audit complet :

- Les 100 degrés sont réservés au mot trouvé. Le voisin de rang 1 atteignait
  par construction le plafond de l'échelle et affichait lui aussi 100,0°, ce qui
  laissait croire à une seconde bonne réponse. Il vaut désormais 99,0° au plus.
- Huit mots vulgaires retirés des cibles, dans trois langues. Ils pouvaient
  tomber comme mot du jour.
- Cinquante définitions abstraites réécrites en formulations concrètes :
  « Action de », « Fait de » et « Caractère de ce qui » n'apprenaient rien au
  joueur.

Version 3.2.0

**Nouveautés 3.2.0** : 5 778 mots cibles, tous pourvus d'une définition
rédigée. Les 2 527 mots ajoutés à la version précédente ont reçu la leur.
52 mots ont été retirés des cibles : noms propres, abréviations et fautes
d'orthographe repérés à la relecture.

**Nouveautés 3.1.0** : le vivier de mots passe de 3 303 à 5 830 cibles. Les
nouvelles cibles proviennent d'une liste externe, triée par une régression
logistique entraînée sur les cibles déjà curées (justesse 94 à 97 %) pour ne
garder que les noms communs. Les indices fournis avec cette liste ont été
écartés : ils citaient les voisins vectoriels du mot caché, ce qui donnait la
réponse au lieu d'orienter.

Version 3.0.0

**Nouveautés 3.0.0** : les cinq langues sont complètes. 3 303 définitions
rédigées, une pour chaque mot cible, dans les cinq langues. Deux formes
fautives ont été retirées des cibles allemandes au passage : « Nagel », que la
règle de flexion avait fusionné avec son pluriel, et « Not », réduit à sa forme
minuscule.

**Réserve sur l'allemand** : ces 471 définitions sont écrites avec sérieux et
passent le contrôle de fuite, mais l'allemand est la langue la moins sûre de
l'auteur du lot. Certaines tournures peuvent sonner traduites. Une relecture
par un germanophone est conseillée avant toute diffusion.

**Nouveautés 2.8.0** : l'italien est terminé.

**Nouveautés 2.7.0** : l'espagnol est terminé. 499 définitions pour 499 mots
cibles. Les ancres de la catégorie « partie du corps » ont été enrichies dans
les cinq langues : « diente » se voyait classé comme animal, il est maintenant
rangé au bon endroit.

**Nouveautés 2.6.0** : l'anglais est terminé à son tour. 616 définitions pour
616 mots cibles. Français et anglais sont désormais complets sur les trois
formes d'indice.

**Nouveautés 2.5.0** : le français est terminé. Les 1 204 mots cibles ont leur
définition rédigée, sans exception. Au passage, « week », reste tronqué de
« week-end », a été retiré de la liste des cibles.

**Nouveautés 2.4.0** : troisième lot de définitions françaises.

**Nouveautés 2.3.0** : deuxième lot de définitions françaises.

**Nouveautés 2.2.0** : troisième forme d'indice, la définition rédigée. Premier
lot de définitions françaises, écrites dans l'ordre du tirage quotidien pour
couvrir les mots qui tombent en premier. Un contrôle automatique refuse toute
définition qui laisserait filtrer son propre mot ou un dérivé évident.

**Nouveautés 2.1.0** : les indices orientent au lieu de donner. Ils sont tirés
au hasard parmi ceux qui restent pour le mot du jour, sous deux formes, la
catégorie et une phrase d'usage où le mot est masqué. Quand il n'y en a plus,
l'appli le dit et ne joue plus de coup à ta place. Sur la bande thermique, le
mot que porte l'aiguille n'a plus de marque fixe : sa position n'est donc plus
annoncée avant l'arrivée de l'aiguille.

**Nouveautés 2.0.0** : cinq langues, français, anglais, espagnol, italien et
allemand. Chacune embarque son propre lexique, sa liste de mots cibles, ses
tolérances de saisie, son mot du jour et ses statistiques. Interface entièrement
traduite. La langue se choisit dans l'en-tête, le premier lancement suit celle
du système.

**Nouveautés 1.5.0** : la bande thermique porte une aiguille. À chaque mot
proposé, elle part du bord glacial, file jusqu'à la température du mot, la
dépasse légèrement puis revient s'y poser. La durée du trajet suit la distance
parcourue, donc un mot brûlant met plus longtemps à arriver qu'un mot tiède, et
le résultat se lit avant même le chiffre. Le mouvement est désactivé si le
système demande de réduire les animations.

**Nouveautés 1.4.0** : nouvelle icône, déclinée en icônes héritées (coins
découpés) et en icône adaptative Android 8+ (contenu détouré, ramené dans la
zone sûre, sur un aplat de marque) ; l'écran de démarrage reprend le logo, sa
bande graduée servant de jauge de chargement ; le titre de l'appli est composé
dans la même lettre monospace que le logo ; les trois boutons de l'en-tête sont
des pictogrammes dessinés au lieu de caractères typographiques, le bouton des
statistiques est un histogramme ; le panneau des statistiques est reformulé avec
des libellés explicites.

**Nouveautés 1.3.0** : bouton « Effacer la partie en cours » qui vide l'écran et
remet les essais à zéro sans changer le mot caché ni toucher aux statistiques,
avec confirmation dès qu'il y a des essais à perdre ; quand la partie est
terminée, une note explique pourquoi la révélation n'est plus proposée ; les
actions passent en tête du menu, elles étaient sous le pli et donc invisibles
sans faire défiler le panneau.

**Nouveautés 1.2.0** : la révélation du mot passe par un écran de confirmation
et son bouton est rouge ; une partie terminée ne peut plus être révélée une
seconde fois (l'ancienne version ajoutait un doublon dans la liste) ; l'en-tête
et le pied sont pleins et reprennent exactement la couleur des barres système,
qui ne savent pas être translucides, ce qui supprime le liseré visible en haut
et en bas. Le verre dépoli reste sur les lignes d'essais et les panneaux.

**Nouveautés 1.1.0** : thème clair, thème sombre ou suivi du système (bouton
dans l'en-tête, choix mémorisé) ; surfaces en verre dépoli avec repli automatique
si la WebView ne gère pas `backdrop-filter` ; écran de démarrage, natif puis
animé ; texte et contrastes revus pour la lisibilité.

---

## Ce que c'est, et ce que ce n'est pas

C'est une implémentation originale du genre « jeu sémantique », écrite de zéro.
Aucun code, aucune donnée, aucun élément graphique ne provient d'un jeu existant.
Le moteur, la liste de mots cibles, l'échelle de température et l'interface sont
propres à ce projet.

L'appli ne demande **aucune permission** dans son manifeste, pas même l'accès
réseau. Elle ne peut donc techniquement rien envoyer ni recevoir. Les parties et
les statistiques restent dans le stockage local de la WebView.

---

## Architecture

Même schéma que les autres applis : une coquille Android minimale, tout le reste
en HTML/CSS/JS embarqué.

```
app/src/main/
  java/fr/thermot/jeu/MainActivity.java   coquille WebView, ~130 lignes, zéro dépendance
  assets/www/
    index.html      structure, écran de démarrage
    style.css       thèmes clair et sombre, verre dépoli, mise en page
    moteur.js       chargement du lexique, cosinus, classement
    jeu.js          logique de partie, thème, affichage, sauvegarde locale
    langues.js      textes de l'interface dans les cinq langues
    lexiques/
      lexique-XX.bin  vecteurs int8 par langue
      alias-XX.txt    formes tolérées à la saisie
      cibles-XX.txt   noms communs tirés comme mot du jour
    polices/        Space Grotesk et JetBrains Mono, sous-ensemble latin
  res/
    mipmap-*/                icônes héritées et premier plan adaptatif
    mipmap-anydpi-v26/       déclaration de l'icône adaptative
    drawable/                fond de l'écran de lancement natif
    values/                  thème, couleurs, chaînes
```

### Thème et barres système

Le thème se choisit dans l'en-tête et tourne entre trois états : suivi du
système, clair, sombre. Le choix est mémorisé localement. La page prévient la
partie native par un pont minimal (`Pont.theme(clair)`), qui accorde la barre
d'état et la barre de navigation à l'ambiance choisie. C'est le seul point de
contact entre la page et le système, et rien d'extérieur ne peut l'appeler
puisque tout le contenu est embarqué.

### Écran de démarrage

Deux couches. La première est native : `res/drawable/fond_lancement.xml` sert de
`windowBackground`, donc le fond de marque s'affiche avant même que la WebView
existe, ce qui supprime le flash blanc. La seconde est dans la page : disque
thermique animé, jauge de chargement réelle, puis fondu. Elle reste affichée au
minimum 900 ms même si le lexique se charge plus vite, pour éviter le
clignotement.

### Verre dépoli

Les surfaces utilisent `backdrop-filter: blur(22px) saturate(150%)` sur un fond
de trois halos thermiques. Un bloc `@supports not (backdrop-filter: blur(2px))`
retombe sur des surfaces opaques pour les WebView anciennes, sans perte de
lisibilité.

Les fichiers de `assets/www` sont servis sous une origine virtuelle
`https://thermot.local` interceptée dans `shouldInterceptRequest`. Cela donne
accès à `fetch()` et à `localStorage` sans qu'aucune requête ne sorte de
l'appareil. Toute requête vers un autre hôte reçoit une réponse vide.

## Les langues

| Langue | Mots du lexique | Mots cibles | Taille |
|---|---|---|---|
| Français | 78 011 | 1 867 | 24,5 Mo |
| Anglais | 48 000 | 957 | 15,0 Mo |
| Espagnol | 48 021 | 839 | 15,1 Mo |
| Italien | 48 021 | 878 | 15,1 Mo |
| Allemand | 48 087 | 1 235 | 15,1 Mo |

Le français garde un vocabulaire plus large parce que c'est la langue de
référence du projet. Une seule langue est chargée en mémoire à la fois, le
changement recharge le lexique en moins d'une seconde.

Chaque langue a ses propres règles de tolérance à la saisie, écrites dans
`outils/build_lexiques.py` :

- **français** : pluriels en -s et -x, accents facultatifs ;
- **anglais** : pluriels en -s et -es ;
- **espagnol** : pluriels en -s et -es, accents facultatifs ;
- **italien** : pluriels par changement de voyelle finale, libro/libri,
  casa/case, formaggio/formaggi ;
- **allemand** : déclinaisons et pluriels (Berg, Berges, Berge, Bergen),
  démutation des umlauts (Bücher ramené à Buch), majuscule des noms communs
  conservée, et saisie tolérée en ae, oe, ue, ss.

Une forme fléchie n'est fusionnée avec sa forme de base que si celle-ci est plus
fréquente et que le cosinus dépasse 0,55. La fréquence tranche mieux qu'une
règle absolue : sans ce garde-fou, « corps » se faisait ramener à « corp ».

Les mots cibles sont toujours inclus dans le lexique, même s'ils tombent
au-delà du plafond de vocabulaire : un mot du jour absent du lexique n'aurait
aucun sens.

## Les indices

Deux sources, toutes deux vérifiables, produites par
`outils/build_indices.py` dans `lexiques/indices-XX.json` :

- **La catégorie**, déduite du lexique lui-même. Chaque catégorie est définie
  par cinq mots d'ancrage, la cible reçoit celle dont le centre est le plus
  proche. Deux garde-fous : un seuil de similarité de 0,28 et une marge de
  0,035 sur la deuxième catégorie. Sans cette marge, un mot sans catégorie
  évidente récoltait une étiquette au hasard, ce qui égare au lieu d'aider.
  C'est pourquoi seuls 60 à 75 % des mots ont une catégorie : le silence vaut
  mieux qu'une fausse piste.
- **Une phrase d'usage** où le mot est masqué, tirée du corpus Tatoeba. La
  phrase n'est retenue que si elle contient un seul mot cible, entre 35 et 110
  caractères, et si le mot masqué ne réapparaît nulle part ailleurs dedans.

| Langue | Cibles | Définitions | Catégories | Phrases |
|---|---|---|---|---|
| Français | 1 866 | 1 866 | 1 258 | 1 664 |
| Anglais | 956 | 956 | 694 | 927 |
| Espagnol | 839 | 839 | 642 | 798 |
| Italien | 875 | 875 | 633 | 784 |
| Allemand | 1 234 | 1 234 | 887 | 1 118 |

- **Une définition rédigée**, dans `outils/definitions/XX.json`. Écrites pour
  le jeu, pas recopiées d'un dictionnaire. Elles sont ajoutées par lots, dans
  l'ordre réel du tirage quotidien plutôt qu'en ordre alphabétique, pour que
  les mots qui tombent en premier soient couverts en premier. Un contrôle
  automatique refuse celles qui contiennent leur propre entrée ou un dérivé
  évident : `sortie` définie avec « sortir » est rejetée, il faut la réécrire.

État des définitions : les cinq langues sont complètes, 5 770 définitions au
total, une pour chaque mot cible. Toutes sont écrites pour le jeu, aucune n'est reprise d'un dictionnaire. C'est un travail par lots, à
poursuivre.

Longueur moyenne d'une définition : 57 caractères. Elles sont volontairement
courtes et concrètes : une définition de dictionnaire est souvent trop
technique ou trop circulaire pour servir d'indice.

Le format `indices-XX.json` accepte n'importe quel type supplémentaire : une
entrée est un objet `{"t": "type", "x": "texte"}`, il suffit d'en ajouter et de
prévoir son étiquette dans `langues.js`.

La piste du Wiktionnaire reste écartée : l'extraction disponible pour le
français donne des gloses en anglais, donc inutilisables telles quelles.

## Le moteur

Les 300 dimensions d'origine sont conservées. Une analyse en composantes
principales à 160 dimensions aurait divisé la taille par deux, mais la mesure
donne 84 % de recouvrement des 50 plus proches voisins contre 98 % avec la
seule quantification : le jeu serait devenu sensiblement moins juste. La taille
se règle donc sur le nombre de mots, pas sur les dimensions.

Le lexique est une matrice de vecteurs de mots quantifiés en int8 :

```
"MOTX" | uint32 nMots | uint16 dim | uint32 tailleBlocMots
       | mots UTF-8 séparés par \n
       | nMots * dim int8       (vecteurs, normalisés puis × 127)
       | nMots float32          (normes, pré-calculées)
```

La proximité entre deux mots est le cosinus de leurs vecteurs. Au lancement
d'une partie, le moteur calcule la similarité de la cible avec les 41 678 mots
(environ 50 ms), en déduit les 1 000 plus proches et la similarité médiane.

L'affichage ne montre pas le cosinus brut : deux mots français sans rapport
tournent autour de 0,13, ce qui donnerait l'impression que tout est tiède.
La température affichée est recalée pour chaque mot caché :

```
température = 100 × (cosinus − médiane) / (cosinus du mot le plus proche − médiane)
```

Donc 0° = un mot pris au hasard, 100° = le mot le plus proche de la cible,
et les valeurs négatives existent pour les mots franchement éloignés.

## Le mot du jour

Tiré de `cibles.txt` mélangé par un générateur pseudo-aléatoire à graine fixe
(`0x7A1C05`), indexé par le nombre de jours écoulés depuis le 1er janvier 2026.
Le tirage est donc identique sur tous les appareils, sans le moindre serveur.

---

## Construire

### Avec Android Studio

Ouvrir le dossier et lancer `Run`. Gradle 8.9, AGP 8.7.3, Java 17.

### En ligne de commande, sans Gradle

`construire.sh` refait exactement ce qui a produit l'APK livré :
aapt2, javac, d8, zipalign, apksigner. Il faut un SDK Android (platform 34 et
build-tools 34.0.0) et un JDK.

```bash
ANDROID_HOME=/chemin/vers/sdk ./construire.sh
```

### Signature

Le dépôt ne contient pas de clé de signature : `construire.sh` en génère une
de test à la volée (`cle-thermot.jks`, mot de passe `thermot2026`) si aucune
n'est présente à côté du script, pour permettre une compilation locale
immédiate. Cette clé est exclue du dépôt par `.gitignore` : ne jamais en
committer une, et conserver précieusement celle qui sert à signer de vraies
publications, ailleurs que dans ce dépôt.

### Lexiques

Le dépôt ne contient pas non plus les `lexiques/lexique-*.bin` (vecteurs
fastText quantifiés, plusieurs dizaines de Mo par langue) : sans eux
l'application se lance mais ne peut pas jouer. Pour les régénérer, voir
« Régénérer le lexique » plus bas — il faut les vecteurs `cc.XX.300.vec`
de fastText, téléchargés séparément.

---

## Régénérer le lexique

Les scripts de préparation ne sont pas nécessaires pour construire l'appli,
ils servent si tu veux changer la taille du vocabulaire ou les mots cibles.

1. Récupérer les vecteurs voulus, en deux tranches :
   `... | zcat | head -n 120000 > data/pt_head.vec` pour le vocabulaire courant,
   puis `... | zcat | sed -n '120001,500000p' > data/pt_tail.vec` pour les mots
   rares. La seconde tranche pèse environ 800 Mo au téléchargement et peut être
   supprimée une fois le lexique construit.
2. Ajouter la langue dans le dictionnaire `LANGUES` de
   `outils/build_lexiques.py` : alphabet, taille, règles de flexion.
3. Déposer la liste des mots cibles dans `outils/cibles/pt.txt`.
4. Lancer `python3 outils/build_lexiques.py pt`, puis ajouter les textes
   d'interface dans `assets/www/langues.js` et le code dans `CODES_LANGUE`.
3. `outils/faire_icones.py` régénère tout le jeu d'icônes à partir d'un logo
   carré unique, à placer en entrée du script.

Augmenter `MAX_KEEP` élargit le vocabulaire accepté, au prix de la taille de
l'APK : environ 300 octets par mot.

---

## Sources et licences

- **Vecteurs de mots** : fastText `cc.fr.300`, entraînés sur Common Crawl et
  Wikipédia par Facebook AI Research.
  https://fasttext.cc/docs/en/crawl-vectors.html
  Distribués sous **Creative Commons Attribution-ShareAlike 3.0**.
  Le fichier `lexique.bin` en est une œuvre dérivée : il doit rester sous la
  même licence s'il est redistribué, avec mention de la source.
  Les cinq lexiques dérivent des modèles `cc.fr`, `cc.en`, `cc.es`, `cc.it` et
  `cc.de`.
  Référence : E. Grave, P. Bojanowski, P. Gupta, A. Joulin, T. Mikolov,
  *Learning Word Vectors for 157 Languages*, LREC 2018.
- **Phrases d'exemple** : corpus Tatoeba, https://tatoeba.org, contributions
  sous **licence CC BY 2.0 FR**. Seules les phrases contenant un mot cible sont
  embarquées, le mot y étant masqué.
- **Space Grotesk** (Florian Karsten) et **JetBrains Mono** (JetBrains) :
  **SIL Open Font License 1.1**, redistribution autorisée avec la licence.
- Le reste (code, interface, icônes, liste de mots cibles) est original.

La mention de ces sources figure aussi dans le menu de l'appli.
