# Modifier le site

Tout le texte du site est modifiable sans toucher au code. Ce document
dit où se trouve quoi.

## Où se trouve quoi

| Ce que vous voulez changer | Fichier |
|---|---|
| Le texte d'une page | `src/content/pages/fr/…` ou `…/en/…` |
| Menus, boutons, pied de page | `src/textes/interface.fr.yaml` · `interface.en.yaml` |
| La page d'accueil entière | `src/textes/accueil.fr.yaml` · `accueil.en.yaml` |
| Adresse, téléphones, courriel, réseaux | `src/textes/coordonnees.yaml` |
| Les signatures de courriel | `signature/generer.mjs` |

`coordonnees.yaml` alimente le pied de page, la page contact, les
données transmises à Google **et** les signatures de courriel. Changer
une adresse à cet endroit la met à jour partout.

---

## Modifier depuis GitHub, sans rien installer

C'est la voie la plus simple.

1. Ouvrez [github.com/xtincell/banahealth](https://github.com/xtincell/banahealth)
2. Naviguez jusqu'au fichier voulu
3. Cliquez sur l'icône crayon, en haut à droite du fichier
4. Modifiez le texte
5. En bas de page, décrivez votre changement en une ligne, puis
   **Commit changes**

Le site ne se met pas à jour tout seul : il faut le recompiler et le
téléverser. Dites-le moi et je m'en charge, ou suivez la section
« Publier » plus bas.

---

## Les pages

Une page ressemble à ceci :

```markdown
---
titre: Notre fondatrice
description: Comment Marie Ngameni a bâti BanaHealth…
langue: fr
url: notre-fondatrice
ordre: 1
banniere: marie-ngameni
banniere_cadrage: portrait
---

## L'histoire de Marie Ngameni

Son aventure a démarré…
```

Ce qui est entre les deux lignes `---` est la fiche d'identité de la
page. Ce qui suit est le texte.

**Dans la fiche d'identité :**

- `titre` — le grand titre en haut de page, et le nom dans l'onglet
- `description` — le résumé affiché par Google. Visez 150 caractères
- `url` — l'adresse de la page. **Ne la changez pas** sans me le dire :
  un lien existant deviendrait mort
- `banniere` — nom d'une image de `src/assets/media/`, sans extension
- `banniere_cadrage` — `large` (bandeau), `portrait` (à côté du texte)
  ou `entier` (jamais recadrée, pour une infographie)
- `ordre` — la place dans les listes

**Dans le texte :**

- `## Titre` fait un intertitre
- `**mot**` met en gras, `_mot_` en italique
- `[texte](https://adresse)` fait un lien
- Une ligne vide sépare deux paragraphes

**Un piège à connaître.** Si une valeur de la fiche d'identité contient
deux-points suivis d'un espace, entourez-la de guillemets :

```yaml
description: "Nos services : soins, voyage et séjour"
```

Sans les guillemets, la page ne se compilera pas. C'est la règle du
format, pas une lubie.

---

## Les fichiers de textes

Ils utilisent le même format. Deux règles suffisent :

**L'indentation compte.** Les espaces en début de ligne indiquent la
hiérarchie. Ne les remplacez jamais par des tabulations.

**Ne changez pas les noms à gauche des deux-points.** `slogan:`,
`nav:`, `contact:` sont des repères utilisés par le code. Seule la
valeur à droite se modifie.

```yaml
nav:
  contact: Nous contacter      ← modifiable
  ↑
  ne pas toucher
```

Pour du texte long, la notation `>-` permet de passer à la ligne sans
créer de paragraphe :

```yaml
texte: >-
  Une phrase qui tient
  sur plusieurs lignes.
```

---

## Publier les changements

```bash
npm install     # la première fois seulement
npm run build
```

La compilation échoue si un fichier comporte une erreur, en indiquant
le fichier et la ligne. C'est un garde-fou : mieux vaut une erreur ici
qu'une page cassée en ligne.

Ensuite, téléversez le contenu de `dist/` dans `banahealth_2/` sur le
serveur OVH, par SFTP.

---

## Ce qu'il vaut mieux me demander

- Ajouter ou supprimer une page
- Changer l'adresse d'une page existante
- Ajouter une langue
- Modifier la mise en page ou les couleurs
- Ajouter des images

Ces opérations touchent à plusieurs fichiers à la fois, et une page
supprimée sans redirection laisse un lien mort dans Google.
