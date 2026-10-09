# Mise à jour locale — preuves du 9 octobre 2026

Skill `concevoir-ui-ux` v4 : lu avec ses trois références. L'instruction de
produire une seule proposition prime sur la recherche de variantes. Le skill
`imagegen` sert aux photographies, pas à une maquette UI générée.

## Corrections après observation

- Suppression du diaporama : rejetée par l'utilisateur et corrigée. Trois
  slides, auteurs et destinations d'origine. Aucun message déplacé dans un
  dépliant. Titres superposés, hauteur indépendante de la longueur du texte.
- Première composition photo puis légende : rejetée, remplacée par un hero
  photographique avec superposition lisible et cadrages par sujet.
- Contact mobile : pictogrammes initialement trop grands ; réduits à 48/64 px,
  téléphone/courriel placés dès l'introduction.
- Fondatrice sur tablette : texte trop étroit ; récit sous le duo titre/photo.
- Services : deux photos générées distinctes remplacent les doublons du hero
  et du visa. Photos documentaires conservées. Format 3:2 sur mobile pour ne
  pas découper les visages. Mention de fiction, pas de fausse preuve médicale.

## Contenus et production statique

Commande :

`BANA_PREVIEW_ORIGIN=http://127.0.0.1:4321 node scripts/check-presence.mjs /tmp/banahealth-before-update.w8DoGJ`

Résultat : 68 pages modernes/Legacy, 542 comparaisons de contenu, 37 fichiers
éditoriaux inchangés, six fichiers de signature inchangés par SHA-256,
68 destinations de navigation et 87 cibles d'image HTTP 200 ; zéro échec.
Corps Markdown comparés au rendu sauvegardé avant modification, pas à un rendu
après coup. Titres, descriptions, hreflang et canonical vérifiés.
Legacy noindex, canonical moderne, navigation confinée à Legacy,
hors sitemap ; atelier hors build et anciens liens redirigés en développement.
Compilation : 69 pages, dont la 404. Legacy : 34 rendus indépendants.
Le validateur exige désormais les trois slides et leurs commandes.

## Navigateur réel

Les 34 pages modernes compilées ont été ouvertes à 390, 768 et 1440 px,
avec attente du chargement de page : 102 contrôles, zéro débordement horizontal
du document, pas d'image chargée cassée, une h1 par page. Les images encore
différées ne sont pas prétendues toutes inspectées visuellement.

Captures inspectées : accueil ordinateur/mobile, deuxième/troisième slide,
soins, fondatrice/tablette, contact/mobile, photo générée voyage.
Les trois slides mesurent chacune 832 px à 1440 × 1000, 764 px à 390 × 844.
Précédent, suivant, puces (dont Entrée clavier), pause et rotation réelle
vérifiés. Inactives inert et masquées à l'accessibilité ; hauteur stable.
Mouvement réduit émulé : transition 0 s, pas de rotation automatique,
bouton de pause masqué ; retour au réglage normal après le contrôle.

Menu mobile ouvert par Tab/Entrée. Version compilée, JavaScript désactivé :
menu et navigation vers Contact vérifiés. Les trois messages restent lisibles
successivement sans JavaScript, pas de rotation automatique dans ce mode.
Coordonnées de Contact visibles avant 540 px à 390 × 844.
Contraste statique : encre/blanc 11,86:1, vert/blanc 6,65:1,
texte secondaire/papier 6,20:1. Photos générées optimisées à 62 et 104 ko
pour les versions WebP de 1400 px (pas une mesure de performance terrain).

## Limites

Pas de zoom natif 200 %, Safari/Firefox ou lecteur d'écran validé.
Pas de Lighthouse, LCP ou résultat d'essai utilisateur revendiqué.
Contrôles de focus et navigation ciblés, pas certification WCAG exhaustive.
Les affirmations historiques restent intactes mais non authentifiées.
Aucune qualité Awwwards garantie ; validation visuelle client encore attendue.

## Livraison

Source intégrée localement, aucun push ou déploiement. Signatures, secrets,
exports SQL, quarantaine et production non modifiés.
Sauvegarde avant modification : `/tmp/banahealth-before-update.w8DoGJ`.
Photos/prompts : `design/PHOTO-PROMPTS.md`, fichiers dans `src/assets/media/`.
