export const langues = ['fr', 'en'] as const;
export type Langue = (typeof langues)[number];
export const langueParDefaut: Langue = 'fr';

/** Libelles d'interface, par langue. */
export const ui = {
  fr: {
    'nom': 'BanaHealth',
    'slogan': 'Votre santé nous tient à cœur',
    'nav.accueil': 'Accueil',
    'nav.fondatrice': 'Notre fondatrice',
    'nav.vision': 'Vision et mission',
    'nav.services': 'Nos services',
    'nav.soins': 'Soins médicaux',
    'nav.hebergement': 'Hébergement',
    'nav.pourquoi': "Pourquoi l'Afrique du Sud",
    'nav.reseaux': 'Nos réseaux',
    'nav.contact': 'Nous contacter',
    'nav.menu': 'Menu',
    'nav.fermer': 'Fermer',
    'nav.evitement': 'Aller au contenu principal',
    'pied.plan': 'Le site',
    'pied.legal': 'Informations légales',
    'pied.contact': 'Contact',
    'pied.confidentialite': 'Politique de confidentialité',
    'pied.conditions': 'Conditions générales',
    'pied.droits': 'Tous droits réservés.',
    'langue.bascule': 'English',
    'langue.libelle': 'Choisir la langue',
    'cta.contact': 'Parler à un accompagnateur',
    'cta.services': 'Découvrir nos services',
    'cta.suite': 'En savoir plus',
    'cta.site': 'Visiter le site',
    'erreur.titre': 'Page introuvable',
    'erreur.texte': "Cette page n'existe pas ou a été déplacée.",
    'erreur.retour': "Revenir à l'accueil",
  },
  en: {
    'nom': 'BanaHealth',
    'slogan': 'Because we care',
    'nav.accueil': 'Home',
    'nav.fondatrice': 'Our founder',
    'nav.vision': 'Vision and mission',
    'nav.services': 'Our services',
    'nav.soins': 'Medical care',
    'nav.hebergement': 'Accommodation',
    'nav.pourquoi': 'Why South Africa',
    'nav.reseaux': 'Our network',
    'nav.contact': 'Contact us',
    'nav.menu': 'Menu',
    'nav.fermer': 'Close',
    'nav.evitement': 'Skip to main content',
    'pied.plan': 'The site',
    'pied.legal': 'Legal',
    'pied.contact': 'Contact',
    'pied.confidentialite': 'Privacy policy',
    'pied.conditions': 'Terms and conditions',
    'pied.droits': 'All rights reserved.',
    'langue.bascule': 'Français',
    'langue.libelle': 'Choose language',
    'cta.contact': 'Speak to a facilitator',
    'cta.services': 'Explore our services',
    'cta.suite': 'Learn more',
    'cta.site': 'Visit website',
    'erreur.titre': 'Page not found',
    'erreur.texte': 'This page does not exist or has been moved.',
    'erreur.retour': 'Back to home',
  },
} as const;

export function t(lang: Langue) {
  return (cle: keyof (typeof ui)['fr']) => ui[lang][cle] ?? ui.fr[cle];
}

/** Chemin d'une page, prefixe /en pour l'anglais. */
export function chemin(lang: Langue, slug = ''): string {
  const base = lang === langueParDefaut ? '' : `/${lang}`;
  return slug ? `${base}/${slug}/` : `${base}/` || '/';
}

/** Correspondance des pages entre langues, pour le selecteur. */
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
};

export const equivalencesInverses: Record<string, string> = Object.fromEntries(
  Object.entries(equivalences).map(([fr, en]) => [en, fr]),
);

/** Menu principal : slug francais + cle de libelle. */
export const menu = [
  { fr: 'notre-fondatrice', cle: 'nav.fondatrice' },
  { fr: 'nos-services', cle: 'nav.services' },
  { fr: 'soins-medicaux', cle: 'nav.soins' },
  { fr: 'pourquoi-afrique-du-sud', cle: 'nav.pourquoi' },
  { fr: 'nos-reseaux', cle: 'nav.reseaux' },
  { fr: 'contact', cle: 'nav.contact' },
] as const;
