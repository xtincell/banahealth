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
    url: z.string(),
    ordre: z.number().default(99),
  }),
});

export const collections = { pages };
