# Walkway

Police de la charte graphique BanaHealth, fournie avec celle-ci.

La charte (p. 11) la prescrit explicitement pour un « usage pluriel
(impression, et web) en titre et sous titre en jouant sur les
différentes épaisseurs ».

Graisses embarquées, toutes en variante **Expand** conformément
aux spécifications typographiques (p. 10) :

| Fichier                      | Graisse CSS | Usage selon la charte        |
|------------------------------|-------------|------------------------------|
| `walkway-expand.ttf`         | 400         | Sous-titres (14 pt / 24 pt)  |
| `walkway-expand-semibold.ttf`| 600         | Nom dans le logotype         |
| `walkway-expand-bold.ttf`    | 700         | Intertitres                  |
| `walkway-expand-black.ttf`   | 900         | Titres (24 pt / 30 pt)       |

Couverture des caractères vérifiée à l'intégration : é è à ç ù ê î ô û
ë ï ü œ æ, ainsi que € et les guillemets français « ». Aucun caractère
manquant.

Walkway ne possède **pas de véritable italique**. Ne pas appliquer
`font-style: italic` : le navigateur en synthétiserait une version
penchée qui déforme les lettres.

Le corps de texte n'utilise pas Walkway mais Mulish : la variante
Expand Regular est trop fine pour de longs paragraphes, et la charte
ne prescrit rien pour le texte courant.
