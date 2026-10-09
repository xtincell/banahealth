# BanaHealth — présentation locale du 9 octobre 2026

## Contrat

Une seule proposition locale : photographies dominantes, interface discrète,
textes intégraux, Mulish et logo conservés. Le hero diaporama est obligatoire :
trois slides, hauteur constante, titres sur l'image, textes, auteurs et liens
d'origine. Une doctrine de design ne peut pas supprimer une fonctionnalité
demandée. Aucun push ni déploiement avant validation client.

## Système visuel

Encre #103e39, vert lisible #08685f, texte secondaire #49615b, papier #f6f7f2,
filets #cbd8d1, orange de marque #f1592f en accent non textuel. Mulish 400 pour
le corps, 600 pour les titres, 800 pour les actions. Corps 17 px / 1,65,
16 px sur mobile. Gouttière clamp(1.25rem, 4.5vw, 5rem). Grille souple à deux
colonnes, repli mobile et lecture Markdown bornée. Focus de 3 px.
Contrastes calculés : encre/blanc 11,86:1 ; vert/blanc 6,65:1 ;
texte secondaire/papier 6,20:1. Pas de petit texte orange.

Le hero est un cadre photographique unique, pas une galerie avec légendes.
Sa hauteur ne dépend pas du message. Sur ordinateur : titres à droite de la
première photo, à gauche des deux suivantes, pour préserver les sujets.
Sur mobile : titre superposé dans la zone inférieure de la photo, fond
progressivement éclairci pour lire les mots sans masquer les yeux.
Aucune nouvelle formulation marketing. Commandes de 44 px minimum,
rotation à 6,5 s, pause explicite, suspension au survol/focus et en arrière-plan.
Mouvement réduit : pas de rotation automatique ni de transition.
Sans JavaScript : les trois messages restent lisibles successivement.

Les trois domaines de service utilisent des dépliants HTML natifs, avec une
photo associée à celui ouvert et accès aux pages de soins. Contact : pictogrammes
petits, coordonnées dès l'introduction. Articles : photos sans cadre décoratif,
logos non recadrés, tous les paragraphes, étapes et légendes conservés.
La fondatrice se lit sur une largeur complète en format tablette.
Menu mobile natif, liens FR/EN vers les équivalents, bouton Legacy.

## Photographies

Deux photographies d'illustration générées avec des personnages africains
matures et âgés en contexte sud-africain remplacent les doublons sur les
services accompagnement/voyage. Mention explicite de personnages fictifs.
Photos et mentions éditables dans src/textes/photographies.yaml ; prompts
et provenance dans design/PHOTO-PROMPTS.md.
Les photos documentaires — fondatrice, hébergements, établissements —
ne sont pas remplacées par des images synthétiques. Pas de personnes
générées associées à un témoignage, une équipe réelle ou un résultat médical.

## Legacy et validation

34 routes Legacy indépendantes partagent les sources éditoriales, pas le DOM
moderne. Styles modernes isolés ; navigation et changement de langue restent
sous /legacy/. Retour vers la page moderne équivalente, noindex et canonical
moderne, exclusion du sitemap. Aucun changement des signatures email.
Les anciens liens d'atelier redirigent vers la présentation moderne unique
en développement.

Intégration locale, pas direction validée par le client. La suppression
initiale du hero et les titres placés sous la photo ont été explicitement
rejetés et corrigés. La critique repose maintenant sur le navigateur réel,
sans prétendre à un résultat Awwwards. Voir design/LOCAL-UPDATE-QA.md.

## Déclinaisons intérieures — 9 octobre 2026

Services, Medical care, South Africa et Network ont des compositions indépendantes du gabarit d'article : chapitres photo et détails natifs, index de spécialités photographique, raisons illustrées, puis répertoire des institutions. Le corpus Markdown est rendu par Astro et réparti sans réécriture. Sur tablette, les longs textes passent sous les photos plutôt que de laisser un vide au-dessus. Le bilan, les critiques et les limites de preuve sont dans `design/INTERIOR-UPDATE-QA.md`. Legacy reste indépendant et inchangé.

## Publication d'essai autorisée — 9 octobre 2026

Le site réellement en ligne reste la présentation principale, à ses URL habituelles.
La nouvelle présentation est montée sous `/nouveau/`, FR et EN, avec retour vers
la page actuelle équivalente. Les deux accueils actuels reçoivent uniquement un
lien de découverte. `noindex` et canoniques racine empêchent une indexation
concurrente. Aucun changement des signatures ni inversion des présentations.
La procédure et les preuves de publication sont dans `design/PREVIEW-PUBLICATION.md`.
