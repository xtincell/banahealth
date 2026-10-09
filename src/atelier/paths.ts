import { equivalences, equivalencesInverses, type Langue } from '../i18n/ui';

export type Direction = 'a' | 'b';
export const path = (direction: Direction, lang: Langue, slug = '') =>
  `/atelier/${direction}/${lang === 'en' ? 'en/' : ''}${slug ? `${slug}/` : ''}`;
export const translated = (lang: Langue, slug: string) =>
  (lang === 'fr' ? equivalences[slug] : equivalencesInverses[slug]) ?? '';
export function localLink(href: string, direction: Direction, lang: Langue) {
  if (!href.startsWith('/') || href.startsWith('//') || href.startsWith('/signature/')) return href;
  const clean = href.replace(/^\/en(?=\/)/, '').replace(/^\/+|\/+$/g, '');
  return path(direction, href.startsWith('/en/') ? 'en' : lang, clean);
}
