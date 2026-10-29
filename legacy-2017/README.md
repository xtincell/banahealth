# BanaHealth — reconstruction du site de 2017

Cette reconstruction est un site indépendant en HTML, CSS et JavaScript. Elle
ne démarre ni WordPress, ni PHP, ni base de données, et n'utilise pas Astro à
l'exécution ou à la compilation. Le site actuellement publié n'est pas modifié.

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

Le fond cartographique historique n'a pas été récupéré : l'adresse ouvre la
carte dans un onglet séparé. Le formulaire prépare un courriel dans la
messagerie de la personne ; il n'envoie rien automatiquement et ne stocke rien.
Les affirmations et documents historiques sont conservés, sans actualisation.

## Publication

`site/` est le seul dossier à servir. Il est prévu pour la racine d'un hôte
de prévisualisation dédié. Ses chemins absolus ne permettent pas de le déposer
tel quel dans un sous-dossier du site actuel. La configuration Apache fournie
refuse l'indexation et l'exécution de scripts serveur. Le serveur Python de
revue ne lit pas cette configuration Apache.

Ne pas remplacer la production ni son `.htaccess` avec ce résultat sans
préparer une publication distincte et faire valider le rendu. L'accès OVH/SFTP
n'a pas été utilisé dans cette reconstruction.
