# BanaHealth — reconstruction du site de 2017

Cette reconstruction est un site indépendant en HTML, CSS et JavaScript. Elle
ne démarre ni WordPress, ni PHP, ni base de données, et n'utilise pas Astro à
l'exécution ou à la compilation. La publication principale est préparée séparément ; les anciennes sources restent disponibles pour comparaison.

## Voir le résultat

Depuis la racine de ce dépôt :

```sh
python -m http.server 4317 --directory legacy-2017/site
```

Ouvrir `http://localhost:4317/` pour l'anglais et `/fr/` pour le français.
Les anciennes sélections `?lang=fr` et `?lang=en` sont prises en charge.

## Reconstruire et contrôler

```sh
python -m pip install -r legacy-2017/requirements.txt
python legacy-2017/scripts/build.py
```

Les HTML nettoyés, les ressources archivées et leurs provenances figurent dans
`sources/`. Le build est reproductible depuis ces fichiers, sans requête réseau.
`build-report.json` distingue les captures de 2017, les captures voisines de
2018, les textes juridiques anglais et la page reconstruite depuis les sources
éditoriales. `scripts/recover.py` permet de compléter la récupération des
ressources publiques ; il n'est pas nécessaire au build courant.

Pour les contrôles de navigateur, installer `requirements-review.txt` et
Chromium avec `python -m playwright install chromium`, démarrer le serveur
ci-dessus, puis lancer `python legacy-2017/scripts/verify.py`.
Le résultat est écrit dans `review/verification.json`.

## Fidélité et limites

La composition, les couleurs, les polices, les photos, les textes et la
navigation disponibles dans les archives servent de référence. Les compléments
de 2018 sont identifiés ; ils ne constituent pas des captures certifiées de
2017. Les en-têtes et pieds de page français et anglais sont harmonisés sur
les captures vérifiées de décembre 2017, les pages de juillet étant antérieures
à l'ajout du sélecteur bilingue. La version française de l'hébergement reprend le gabarit anglais et les
textes restaurés dans le dépôt. Les liens juridiques de l'accueil français de
2017 pointaient vers les documents anglais : ces textes sont conservés, sans
introduire les politiques réécrites pendant la migration de 2026.

Les scripts WordPress, les traceurs et les liens parasites de l'ancien thème
ont été retirés. Le menu, les sous-menus, le diaporama et la galerie utilisent
un nouveau script autonome. Une photo d'archive tronquée est remplacée par la
version complète du même cliché récupérée dans une autre capture.

La carte est désormais intégrée par une iframe Google Maps à l’adresse historique, avec un lien d’itinéraire et un panneau de coordonnées repliable. Les contrôles natifs remplacent les commandes de l’ancien thème. Le bouton de retour en haut apparaît après défilement. Le formulaire prépare un courriel dans la
messagerie de la personne ; il n'envoie rien automatiquement et ne stocke rien.
Les affirmations et documents historiques sont conservés, sans actualisation.

## Publication

Depuis le 30 octobre 2026, cette reconstruction est le site principal de
https://banahealth.care/ (français) et https://banahealth.care/en/ (anglais).
Les 36 anciennes adresses de l’aperçu `/historique-2017/` redirigent vers leurs
pages équivalentes. La publication a vérifié les 265 fichiers et les 34 pages.
Une archive privée des 299 fichiers du site précédent est conservée sur OVH,
hors du document root ; les fichiers précédents restent également en place.
La bascule modifie le `.htaccess` racine et les redirections de l’ancien aperçu.

Exécutions de publication :
- https://github.com/xtincell/banahealth/actions/runs/41051052847
- https://github.com/xtincell/banahealth/actions/runs/41053569342


`site/` est le seul dossier à servir. Il est prévu pour la racine d'un hôte
de prévisualisation dédié. Ses chemins absolus ne permettent pas de le déposer
tel quel dans un sous-dossier du site actuel. La configuration Apache fournie
refuse l'indexation et l'exécution de scripts serveur. Le serveur Python de
revue ne lit pas cette configuration Apache.

Pour préparer l'aperçu OVH dans un sous-dossier isolé, utiliser :

```sh
python legacy-2017/scripts/prepare_ovh_preview.py /chemin/prive/lot-neuf
```

Ce script monte les liens, styles et sélecteurs de langue sous
`/historique-2017/`. Il prépare des manifestes, un transfert vers un dossier
temporaire et un renommage final ; il ne se connecte pas et ne publie rien.
Le dossier distant et les règles Apache parentes doivent être vérifiés avant
transfert. Les sélecteurs générés utilisent des liens directs : les anciens
paramètres `lang` peuvent être traités d'abord par les règles de la racine OVH.

L’aperçu historique a été publié le 29 octobre 2026. Le 30 octobre, le propriétaire a demandé son passage sur le domaine principal et la correction des interactions. `scripts/prepare_main.py` prépare les URL françaises existantes à la racine et anglaises sous `/en/`, les redirections, les balises canoniques et le sitemap. `scripts/verify_main.py` teste le résultat avec Apache. La publication principale utilise une version immuable sous `/_banahealth-releases/` et un remplacement atomique du seul `.htaccess` racine. Les fichiers du site précédent restent présents ; une archive privée hors du document root permet également la restauration.

### Client de transfert FTPS

`scripts/ovh_ftps.py` fournit un client de transfert sans dépendance externe,
avec trois commandes : `probe`, `inventory` et `publish`. Il vérifie TLS avant
de demander le mot de passe dans le terminal. Il ne conserve pas ce mot de passe.
Les connexions de données sont chiffrées et passent par le même relais TCP que
la connexion de contrôle. Il utilise exclusivement le relais configuré dans un
environnement géré et s'arrête si ce relais est inaccessible.

```sh
python legacy-2017/scripts/ovh_ftps.py probe
python legacy-2017/scripts/ovh_ftps.py inventory --backup /chemin/prive/inventaire-neuf
python legacy-2017/scripts/ovh_ftps.py publish --release /chemin/prive/lot-neuf --backup /chemin/prive/publication-neuve
python -m unittest discover -s legacy-2017/scripts -p 'test_ovh_ftps.py' -v
```

La publication vérifie le manifeste local, sauvegarde les règles Apache et
l'accueil distants, puis confirme le document root par comparaison avec
l'accueil public. Elle refuse une destination existante, transfère dans un
dossier neuf, relit et vérifie chaque fichier avant le renommage final. Un
échec des contrôles HTTP après renommage entraîne le retrait du seul aperçu.
Les sauvegardes et rapports sont privés. Ce client ne peut pas modifier les
autorisations réseau de l'environnement. Les tests hors ligne ne prouvent
pas une authentification ou une publication distante.
