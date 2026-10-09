# Recomposition des quatre familles — 9 octobre 2026

État : intégré et inspecté localement. Pas de publication, commit ou push.
Preview compilé : http://127.0.0.1:4321/ ; développement : http://127.0.0.1:4322/.

## Décisions et critiques

Question → le gabarit unique sépare images et descriptions, et donne aux huit pages FR/EN une lecture indifférenciée → **réviser** les compositions, sans retoucher le corpus.

- Services : trois chapitres photographiques, onze services ouvrables nativement ; le premier est ouvert. L'infographie originale demeure dans « Original presentation » / « Présentation originale », pas supprimée ni traduite.
- Medical care : quatre entrées photographiques avec titre sur image, définition et lien vers la spécialité. Les détails français restent intégralement disponibles ; les deux sections d'accompagnement anglaises restent visibles sous l'index. Les corpus différents ne sont pas artificiellement harmonisés.
- South Africa : photographie du Cap à l'ouverture ; les quatre autres images sont associées à leur raison. Les cinq photos et légendes d'origine figurent une seule fois chacune. Tous les paragraphes, chiffres et affirmations historiques sont conservés, non validés médicalement ni actualisés.
- Network : identité officielle, fiche complète et lien institutionnel réunis par établissement. Pas d'image générée présentée comme photographie d'un hôpital réel.

Premier rendu → cadrage FIV trop serré et logos réduits par leur marge blanche → **réviser** le positionnement photographique et la présentation CSS des fichiers logos, sans modifier ces fichiers.

Tablette 768 px → le centrage d'une photo à côté d'une liste longue laisse un grand vide en haut → **réviser** Services et les raisons South Africa en composition empilée sous 1000 px ; rendu réinspecté.

Clavier mobile → le contour de focus intérieur recouvre le début d'un intitulé → **réviser** le décalage du contour ; les 23 ouvertures testées ont ensuite un focus visible.

Verdict → **poursuivre vers validation visuelle utilisateur**, pas reconnaissance extérieure ni validation auprès de patients.

## Conservation et vérifications statiques

Le composant reçoit le HTML produit par le compilateur Markdown Astro, puis répartit les nœuds h2 existants. Aucun autre compilateur, traitement éditorial ou script navigateur n'est ajouté. Chaque fragment source est marqué `data-editorial` ; le contrôle compare leur texte concaténé, dans l'ordre, au corps antérieur intégral. Les textes des cartes et légendes sont contrôlés séparément.

`npm run build` : succès, 69 sorties avec la 404 et les 34 rendus Legacy indépendants.

Commande de comparaison :

```sh
BANA_PREVIEW_ORIGIN=http://127.0.0.1:4321 node scripts/check-presence.mjs /tmp/banahealth-before-update.w8DoGJ
```

Résultat : 68 pages, 542 contrôles de contenu, 37 fichiers éditoriaux inchangés par hash, 6 fichiers de signature inchangés, 68 cibles de navigation et 122 variantes d'images, aucune erreur. Titres, descriptions, langues, canoniques, alternates et exclusions du sitemap vérifiés. Le composant Legacy et global.css sont aussi identiques au snapshot de début de cette intervention.

Snapshot additionnel des composants, styles, textes et validateur : `/tmp/banahealth-before-interiors.dO8qGL` (temporaire, pas une sauvegarde de production).

## Observations navigateur

- Les huit pages à 390, 768 et 1440 px : 24 contrôles finaux, un h1 par page, aucun débordement horizontal et aucune image chargée cassée. Les images différées non encore chargées ne sont pas couvertes par ce dernier constat ; leurs URL sont contrôlées en HTTP.
- 23 ouvertures au clavier : 12 sur Services EN, 7 sur Network EN et 4 sur Soins médicaux FR. Chaque touche Entrée change effectivement l'état et laisse le focus visible. Pas de débordement après ouverture.
- Le lien photographique FIV atteint bien la page de spécialité anglaise.
- Les quatre changements EN → FR et allers-retours FR moderne → Legacy → moderne préservent la bonne page.
- Avec JavaScript réellement désactivé : un devis se déplie et l'aller-retour Services EN moderne/Legacy fonctionne. JavaScript réactivé après test.
- Aucun avertissement ou erreur dans le journal navigateur interrogé après les parcours compilés.
- Captures inspectées : `design/preview/our-services-final.jpg`, `medical-care-final.jpg`, `why-south-africa-final.jpg`, `our-network-final.jpg` (1440 × 1000).

Les règles de mouvement réduit préexistantes couvrent les transitions ajoutées ; cette intervention n'ajoute aucune animation automatique. Pas de nouvelle mesure de performance, de contraste pixel sur photographie, de test lecteur d'écran, de Safari/Firefox ou de zoom navigateur natif 200 %. Une inspection experte ne vaut pas test avec des utilisateurs.

## Édition et dépendances

Les sources Markdown/YAML restent éditables. Les deux nouveaux libellés se trouvent dans `src/textes/presentation.yaml`. Les photographies des trois volets restent configurées dans `src/textes/photographies.yaml` ; les illustrations existantes conservent leur mention de personnages fictifs. Aucun CMS, nouvelle langue ou changement de framework.

`ultrahtml` 1.7.0 et `entities` 4.5.0, déjà installés indirectement, sont désormais déclarés directement, avec lockfile synchronisé. Aucune montée de version de ces paquets.

L'audit npm effectué signale **4 vulnérabilités transitives (3 high, 1 moderate)** : http-cache-semantics, sharp, smol-toml et source-map-js. Elles ne sont pas corrigées dans cette intervention UI ; à traiter et vérifier avant publication. Cette alerte ne démontre pas une exploitation du site statique.
