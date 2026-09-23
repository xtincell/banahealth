# Signatures de courriel

## Deux versions, et laquelle choisir

| Fichier | Poids | Quand l'utiliser |
|---|---|---|
| `marie-ngameni.html` | 2,9 ko | Le logo est appelé depuis le site |
| `marie-ngameni-embarque.html` | 14,9 ko | Le logo voyage dans le message |

**Si les images s'affichent mal, prenez la version embarquée.**

La plupart des messageries — Zoho, Gmail, Outlook — bloquent par
défaut les images distantes. Ce n'est pas un défaut : c'est ainsi que
fonctionnent les pisteurs publicitaires, et une image appelée depuis
un serveur extérieur en est exactement la signature.

La version embarquée supprime le problème en incluant l'image dans le
message. Rien à télécharger, donc rien à bloquer.

Sa contrepartie : chaque courriel pèse douze kilo-octets de plus, et
Outlook pour Windows présente parfois les images embarquées comme des
pièces jointes.

## Une troisième voie, la plus sûre dans Zoho

Zoho héberge lui-même les images insérées depuis son propre éditeur de
signature. C'est la solution la plus fiable pour un utilisateur Zoho,
puisque l'image vient alors du domaine de Zoho et n'est jamais bloquée.

1. Zoho Mail → Paramètres → Signatures
2. Collez la version **par URL** (`marie-ngameni.html`)
3. Supprimez le logo cassé
4. Cliquez sur l'icône d'image de la barre d'outils
5. Téléversez `public/signature/banahealth-horizontal.png`
6. Réglez la largeur à 190 pixels
7. Même opération pour les deux pastilles, à 28 pixels

## Installer une signature

1. Ouvrez le fichier HTML dans un navigateur
2. Sélectionnez tout (⌘A / Ctrl+A) puis copiez (⌘C / Ctrl+C)
3. Collez dans les réglages de signature de votre messagerie

Collez le rendu, pas le code source.

## Produire les signatures

```bash
node signature/generer.mjs              # version par URL
node signature/generer.mjs --embarque   # version embarquée
```

Pour ajouter quelqu'un, complétez la liste `equipe` dans
`generer.mjs` et relancez. Les coordonnées communes — adresse, fax,
réseaux — viennent de `src/textes/coordonnees.yaml`, le même fichier
qui alimente le site.

## Pourquoi des tableaux et des styles en ligne

Les messageries ne sont pas des navigateurs. Outlook rend le HTML avec
le moteur de Microsoft Word, qui ignore la mise en page moderne et les
feuilles de style externes. Les tableaux imbriqués et les styles écrits
dans chaque balise restent la seule approche qui fonctionne partout.

Le filet orange est une cellule de tableau colorée plutôt qu'une
bordure, pour la même raison.

## Ne déplacez pas les visuels

Ils vivent dans `public/signature/` et sont servis par le site :

- `banahealth-horizontal.png` — logo, 190 × 50
- `facebook.png` et `linkedin.png` — 28 × 28

Changer leur adresse casse toutes les signatures qui les appellent.
C'est exactement ce qui s'est produit lors de la reconstruction du
site, quand l'ancien logo hébergé dans WordPress a disparu.
