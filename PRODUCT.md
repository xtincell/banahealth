# BanaHealth

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Patients internationaux et leurs familles qui envisagent des soins en Afrique
du Sud. Le site existant s'adresse notamment à des publics africains et dispose
de versions française et anglaise. Aucun profil démographique plus précis n'est
confirmé.

## Product Purpose

Présenter la facilitation médicale de BanaHealth : coordination des soins,
organisation du voyage et accompagnement du séjour. Permettre de comprendre
les services, découvrir l'équipe et prendre contact.

## Positioning

L'accompagnement personnel de Marie Ngameni et de son équipe constitue le récit
central du contenu existant. BanaHealth n'est pas présenté comme un hôpital,
un outil de diagnostic ou une plateforme de réservation instantanée.

## Operating Context

Le site met en relation par téléphone et courriel. Les pages présentent les
services, les soins, les réseaux, l'hébergement, la fondatrice et des témoignages.
Les photographies et les témoignages présents dans le dépôt sont des sources
éditoriales existantes, pas des éléments nouvellement authentifiés par cet audit.

## Capabilities and Constraints

- Site statique Astro, FR/EN, contenus Markdown et YAML éditables.
- Conserver les URL, le contenu mot pour mot et le framework.
- Aucun CMS supplémentaire, formulaire médical ou compte patient à inventer.
- Conserver une présentation Legacy accessible et réversible, sans JavaScript.
- Ne pas modifier les images ou chemins des signatures de courriel.
- Une seule proposition intégrée localement, demandée le 9 octobre 2026 ; pas de nouveau choix A/B.
- Hero diaporama conservé : trois slides de même hauteur, titres sur la photo,
  textes, auteurs et liens d'origine. Une doctrine de design ne doit pas
  supprimer une fonctionnalité demandée.
- Aucun déploiement ou push GitHub avant validation.
- Autorisation du 9 octobre : publication d'essai uniquement sous `/nouveau/`,
  site principal conservé, inversion soumise à une validation ultérieure.

## Brand Commitments

BanaHealth, son logo existant, Mulish et les couleurs reconnaissables turquoise
et orange sont conservés. Le registre des textes anglais existants ne doit pas
être réécrit pour satisfaire un style graphique. Pas de personnes, témoignages,
partenariats, chiffres ni résultats médicaux fabriqués. Deux photos illustratives
générées sont autorisées pour l'accompagnement et le voyage, avec personnages
matures et âgés de carnation africaine, contexte sud-africain et mention de
fiction. Les photos documentaires ne sont pas remplacées par des images générées.

## Evidence on Hand

- Textes : `src/textes/` et `src/content/pages/`.
- Images : `src/assets/media/`, logo `src/assets/logo-banahealth.png`.
- Sources de la première passe : `DESIGN.md`, statut prototype non approuvé.
- Les affirmations historiques de classement, coût, délais et ancienneté ne
  constituent pas des preuves actuelles. Voir `design/CONTENT-REVIEW.md`.

## Product Principles

1. Comprendre l'accompagnement avant de solliciter des informations personnelles.
2. Rendre le contact humain facile à trouver, sans promesse nouvelle.
3. Concevoir pour la lecture en français comme en anglais.
4. Préserver le choix, le retour arrière et la liberté de navigation.
5. Mesurer la clarté et la qualité, pas une rétention artificielle.

## Accessibility & Inclusion

Objectif de réalisation : contraste WCAG AA, clavier, zoom 200 %, mouvement réduit,
affichage mobile et contenu disponible sans JavaScript. Hypothèse de conception :
la consultation peut se faire sur téléphone dans des conditions de réseau variables.
