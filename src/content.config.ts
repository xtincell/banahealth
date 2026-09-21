import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const pages = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/pages' }),
  schema: z.object({
    titre: z.string(),
    surtitre: z.string().optional(),
    chapeau: z.string().optional(),
    description: z.string(),
    langue: z.enum(['fr', 'en']),
    // `url` et non `slug` : `slug` est un nom reserve par Astro,
    // deux pages de langues differentes portant la meme valeur
    // s'ecrasent silencieusement.
    url: z.string(),
    ordre: z.number().default(99),
    /** Nom de fichier (sans extension) dans src/assets/media */
    banniere: z.string().optional(),
    /**
     * large    : photo paysage, recadree en bandeau pleine largeur
     * portrait : image verticale, posee a cote du texte d'introduction
     * entier   : affichee sans recadrage (infographie, schema)
     */
    banniere_cadrage: z.enum(['large', 'portrait', 'entier']).default('large'),
    /** Cartes illustrees, affichees avant le texte */
    cartes: z
      .array(
        z.object({
          image: z.string().optional(),
          titre: z.string(),
          texte: z.string().optional(),
          lien: z.string().optional(),
          lienLibelle: z.string().optional(),
        }),
      )
      .optional(),
    /** Galerie affichee apres le texte */
    galerie: z
      .array(
        z.object({
          image: z.string(),
          legende: z.string().optional(),
          /** photo : l'image remplit le cadre. logo : elle y est contenue. */
          cadrage: z.enum(['photo', 'logo']).default('photo'),
        }),
      )
      .optional(),
  }),
});

export const collections = { pages };
