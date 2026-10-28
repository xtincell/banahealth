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
serveur. Cela reduit la surface d'attaque ; l'hebergement, les droits,
les regles d'acces et les dependances de compilation restent a maintenir.

## Presentation publique

La presentation classique est la presentation par defaut (decision du
28 octobre 2026). Les textes YAML/Markdown et les signatures email ne changent pas.
L'ancien apercu `/nouveau/` reste separe : ne pas l'ecraser avec le build classique.
Les routes `/legacy/` du build ne sont pas publiees a la racine ni indexees.

## Demarrer

```bash
npm install
npm run dev      # serveur de developpement
npm run build    # generation dans dist/
npm run preview  # previsualisation du resultat
node scripts/check-classic.mjs  # contenu, liens, metadonnees
```

Pour comparer mot pour mot avec une sauvegarde publique verifiee, passer
son chemin dans `BANAHEALTH_BASELINE` au controle classique.
`scripts/check-http.mjs` verifie les redirections, refus de scripts et caches
sur Apache local (`BANAHEALTH_HTTP_ORIGIN`) ou sur le domaine public.

`scripts/prepare-classic-release.mjs <sauvegarde> <dossier-prive>` prepare
une liste incrementale d'envois SFTP et un retour arriere, sans se connecter.
Il exclut les signatures, l'apercu et les metadonnees locales. Les fichiers
sont verifies avant publication, puis les assets sont envoyes avant le HTML
et les regles serveur en dernier. Ne jamais envoyer `dist/` en bloc.
Conserver hors depot la sauvegarde complete et la configuration OVH.

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
