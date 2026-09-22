// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import yaml from '@rollup/plugin-yaml';

export default defineConfig({
  site: 'https://banahealth.care',
  i18n: {
    defaultLocale: 'fr',
    locales: ['fr', 'en'],
    routing: { prefixDefaultLocale: false },
  },
  integrations: [sitemap()],
  build: { inlineStylesheets: 'auto' },
  // Les textes du site vivent dans src/textes/*.yaml, pour etre
  // modifiables sans toucher au code.
  vite: { plugins: [yaml()] },
});
