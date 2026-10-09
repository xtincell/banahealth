# Publication d'essai — 9 octobre 2026

## Contrat

La demande autorise une publication d'essai, pas une inversion du site principal.
Le site actuellement en ligne reste à la racine. La nouvelle présentation se
trouve sous `/nouveau/` et `/nouveau/en/`. Un lien de découverte est ajouté aux
deux accueils actuels ; chaque page d'essai permet de revenir à son équivalent.

## Préparation vérifiée

- Sauvegarde privée complète : 113 fichiers du site actuel ; inventaire et
  tailles comparés au serveur SFTP. Pas de sauvegarde ni d'export privé dans Git.
- Compilation Astro réussie : 34 pages modernes, 34 Legacy, une page 404.
- Contrôle du corpus : 542 comparaisons ; 37 sources éditoriales et six fichiers
  de signature inchangés ; zéro échec.
- Montage d'essai : 35 HTML, 178 fichiers publics. Texte de chaque `main`
  identique au build ; seules les destinations de navigation sont préfixées.
- Tous les fichiers principaux restent identiques ; sur les deux accueils,
  retirer le seul bandeau ajouté restitue exactement les fichiers précédents.
- Contrôle HTTP local : 164 destinations et ressources répondent correctement.
- Navigateur local : parcours racine FR → découverte → EN → services → retour
  à la page actuelle EN, puis accueil EN → découverte. Images visibles chargées,
  pas de débordement à 390 px sur Services.
- Dépendances de build corrigées, installées puis recompilées : `npm audit`
  ne signale plus de vulnérabilité. Cela ne constitue pas un audit de sécurité
  exhaustif, une mesure de performance ni un test de délivrabilité email.

## Procédure

`scripts/prepare-design-preview.mjs <sortie-vide> <sauvegarde-complète>` prépare
un dossier indépendant, sans changer le build ni la sauvegarde. Son manifeste
de hashes est privé et ne doit pas être envoyé au serveur public.

`scripts/check-design-preview.mjs <sortie> <sauvegarde> [origine-http]` compare
les contenus, les fichiers principaux, les liens, les ressources et les HTML
servis. L'inventaire SFTP est optionnel, avec configuration privée par variables
d'environnement ; aucun identifiant ni mot de passe n'est stocké dans le code.

Le transfert crée un dossier neuf puis le renomme `/nouveau/`. Seuls ce dossier
et les deux accueils modifiés sont publiés. Le `.htaccess` principal, les assets
actuels, signatures, robots et sitemaps ne sont pas remplacés.

## Restauration

Restaurer exactement `index.html` et `en/index.html` depuis la sauvegarde privée
retire immédiatement les deux liens de découverte, sans altérer les pages ni
les ressources existantes. Le dossier d'essai peut rester non lié et `noindex`.
La future inversion des présentations nécessite une nouvelle validation.

## Statut serveur

Nouvelle présentation transférée puis montée sous `/nouveau/` : 35 HTML vérifiés
octet pour octet par HTTP public ; 164 destinations et ressources contrôlées.
Accueil d'essai : HTTP 200, en-tête `X-Robots-Tag: noindex, follow`, politique
de sécurité principale héritée et cache HTML désactivé. Navigateur public :
Services anglais avec images chargées, changement FR, retour de l'accueil
anglais au site actuel, commande du diaporama fonctionnelle, aucune erreur
ou alerte console observée.

Les liens sont activés sur les accueils FR et EN. 111 fichiers racine publics
ont été téléchargés par HTTP et comparés octet pour octet : les deux accueils
ne diffèrent que par le bandeau ; toutes les autres pages et ressources,
dont les six signatures, correspondent à la sauvegarde. Les sitemaps et
robots sont inchangés. Le lien FR a été cliqué dans le navigateur public et
mène bien à `/nouveau/`. Preuve visuelle : `preview/discovery-live.png`.

Le code est sauvegardé sur la branche `codex/design-preview-20261009`, sans
remplacer la branche principale GitHub, qui a évolué indépendamment. La
présentation actuelle n'a pas été déplacée sous `/legacy/` : cette inversion
reste une opération future, à valider.
