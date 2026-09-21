# banahealth.care

Refonte du site BanaHealth en site statique.

## Stack

- **[Astro](https://astro.build)** — generation statique, aucun code execute cote serveur
- **TypeScript**
- Contenu en Markdown, versionne dans ce depot

## Pourquoi un site statique

Le site precedent reposait sur WordPress. La refonte supprime PHP et la base
de donnees : les pages sont pre-generees a la compilation et servies comme
simples fichiers HTML. Il n'y a plus de code execute a la demande sur le
serveur, donc plus de surface d'attaque applicative a maintenir.

## Demarrer

```bash
npm install
npm run dev      # serveur de developpement
npm run build    # generation dans dist/
npm run preview  # previsualisation du resultat
```

## Structure

```
src/
  pages/       une route par fichier
  layouts/     gabarits partages
  components/  composants reutilisables
  content/     contenu editorial en Markdown
public/        fichiers servis tels quels (images, favicon)
```

## Regles du depot

Ce depot est **public**. Aucun secret ne doit y figurer : pas d'identifiants,
pas de cles d'API, pas d'export de base de donnees. La configuration sensible
passe par des variables d'environnement, absentes du depot.
