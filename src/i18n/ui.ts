/**
 * Acces aux textes d'interface.
 *
 * Les libelles ne vivent pas ici mais dans src/textes/*.yaml, pour
 * qu'ils puissent etre modifies sans toucher au code. Ce fichier ne
 * fait que les charger et les exposer.
 */
import interfaceFr from '../textes/interface.fr.yaml';
import interfaceEn from '../textes/interface.en.yaml';
import coordonnees from '../textes/coordonnees.yaml';

export const langues = ['fr', 'en'] as const;
export type Langue = (typeof langues)[number];
export const langueParDefaut: Langue = 'fr';

const textes: Record<Langue, any> = { fr: interfaceFr, en: interfaceEn };

export { coordonnees };

/**
 * Renvoie une fonction de lecture pour la langue donnee.
 * Les cles sont pointees : t('nav.contact'), t('cta.suite').
 * Une cle absente retombe sur le francais plutot que d'afficher un vide.
 */
export function t(lang: Langue) {
  return (cle: string): string => {
    const lire = (source: any) =>
      cle.split('.').reduce((n, part) => (n == null ? undefined : n[part]), source);
    return lire(textes[lang]) ?? lire(textes.fr) ?? cle;
  };
}

/** Chemin d'une page, prefixe /en pour l'anglais. */
export function chemin(lang: Langue, slug = ''): string {
  const base = lang === langueParDefaut ? '' : `/${lang}`;
  return slug ? `${base}/${slug}/` : `${base}/` || '/';
}

/**
 * Correspondance des pages entre langues, pour le selecteur.
 * A completer lors de l'ajout d'une page dans les deux langues.
 */
export const equivalences: Record<string, string> = {
  '': '',
  'notre-fondatrice': 'our-founder',
  'vision-et-mission': 'vision-and-mission',
  'nos-services': 'our-services',
  'soins-medicaux': 'medical-care',
  'hebergement': 'accommodation',
  'pourquoi-afrique-du-sud': 'why-south-africa',
  'nos-reseaux': 'our-network',
  'contact': 'contact',
  'confidentialite': 'privacy-policy',
  'conditions-generales': 'terms-and-conditions',
  'temoignages': 'testimonials',
  'liens-utiles': 'useful-links',
  'fecondation-in-vitro': 'in-vitro-fertilisation',
  'oncologie': 'oncology',
  'interventions-chirurgicales': 'surgeries',
  'bilan-de-sante': 'general-check-up',
};

export const equivalencesInverses: Record<string, string> = Object.fromEntries(
  Object.entries(equivalences).map(([fr, en]) => [en, fr]),
);

/** Menu principal : slug francais + cle du libelle dans les fichiers de textes. */
export const menu = [
  { fr: 'notre-fondatrice', cle: 'nav.fondatrice' },
  { fr: 'nos-services', cle: 'nav.services' },
  { fr: 'soins-medicaux', cle: 'nav.soins' },
  { fr: 'pourquoi-afrique-du-sud', cle: 'nav.pourquoi' },
  { fr: 'nos-reseaux', cle: 'nav.reseaux' },
  { fr: 'contact', cle: 'nav.contact' },
] as const;

/** Pages secondaires, listees dans le pied de page. */
export const menuPied = [
  { fr: 'vision-et-mission', cle: 'nav.vision' },
  { fr: 'hebergement', cle: 'nav.hebergement' },
  { fr: 'temoignages', cle: 'nav.temoignages' },
  { fr: 'liens-utiles', cle: 'nav.liens' },
] as const;

/** Sous-pages de soins, listees depuis la page Soins medicaux. */
export const sousPagesSoins = [
  { fr: 'fecondation-in-vitro', cle: 'soins.fiv', image: 'soin-fiv' },
  { fr: 'oncologie', cle: 'soins.oncologie', image: 'soin-oncologie' },
  { fr: 'interventions-chirurgicales', cle: 'soins.chirurgie', image: 'soin-chirurgie' },
  { fr: 'bilan-de-sante', cle: 'soins.bilan', image: 'soin-bilans' },
] as const;
