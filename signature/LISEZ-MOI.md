# Signatures de courriel

## Pourquoi l'ancienne s'est cassée

Le logo était hébergé dans l'installation WordPress. Celle-ci a été
supprimée lors de la reconstruction du site, et toutes les signatures
qui pointaient vers cette image se sont brisées le même jour.

Les visuels vivent désormais dans `public/signature/` du site, à des
adresses stables :

- `https://banahealth.care/signature/banahealth.png` — logo, 276 × 64
- `https://banahealth.care/signature/facebook.png` — 24 × 24
- `https://banahealth.care/signature/linkedin.png` — 24 × 24

**Ne déplacez pas ces fichiers.** Si leur adresse change, toutes les
signatures cassent à nouveau, d'un coup et sans avertissement.

## Installer une signature

1. Ouvrez le fichier HTML voulu dans un navigateur
2. Sélectionnez tout (⌘A / Ctrl+A) puis copiez (⌘C / Ctrl+C)
3. Collez dans les réglages de signature de votre messagerie

Coller le rendu, et non le code source : les messageries attendent du
contenu formaté, pas du HTML brut.

## Créer une signature pour quelqu'un d'autre

Dupliquez `modele.html` et remplacez ce qui est entre crochets.
Ne modifiez ni les balises `<table>`, ni les styles.

## Pourquoi des tableaux et des styles en ligne

Les logiciels de messagerie ne sont pas des navigateurs. Outlook rend
le HTML avec le moteur de Microsoft Word, qui ignore la mise en page
moderne et les feuilles de style externes. Les tableaux imbriqués et
les styles écrits dans chaque balise restent la seule approche qui
fonctionne partout.

Le filet orange est une cellule de tableau colorée plutôt qu'une
bordure CSS, pour la même raison.

## Mode sombre

Le fond blanc est forcé sur le tableau extérieur. Certaines messageries
l'ignorent et inversent quand même les couleurs : le gris du texte
secondaire peut alors manquer de contraste. C'est une limite connue du
courriel, qu'aucune signature ne contourne vraiment.
