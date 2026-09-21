import type { Langue } from './ui';

export interface ContenuAccueil {
  heroSurtitre: string;
  heroTitre: string[];
  heroTexte: string;
  piliersSurtitre: string;
  piliersTitre: string;
  piliers: { titre: string; texte: string; lien: string; image: string }[];
  citation: string;
  citationAuteur: string;
  engagement: string;
  raisonsSurtitre: string;
  raisonsTitre: string;
  raisons: { chiffre: string; titre: string; texte: string }[];
  raisonsLien: string;
  fondatriceSurtitre: string;
  fondatriceTitre: string;
  fondatriceTexte: string;
  fondatriceLien: string;
  appelTitre: string;
  appelTexte: string;
}

export const accueil: Record<Langue, ContenuAccueil> = {
  fr: {
    heroSurtitre: 'Facilitation médicale en Afrique du Sud',
    heroTitre: ['Les soins', 'que vous méritez'],
    heroTexte:
      "À BanaHealth, nous plaçons nos patients au cœur de tout ce que nous faisons. Leur guérison est ce qui nous pousse, jour et nuit.",
    piliersSurtitre: 'Nos services',
    piliersTitre: 'Un accompagnement sur trois fronts',
    piliers: [
      {
        titre: 'Facilitation des soins',
        texte:
          "Nous trouvons les médecins qui répondent le mieux à vos besoins, obtenons des devis pour vos traitements et organisons tous vos rendez-vous médicaux.",
        lien: 'nos-services',
        image: 'icone-medecins',
      },
      {
        titre: 'Facilitation de voyage',
        texte:
          "Nous facilitons l'obtention de votre visa et de ses extensions, vous aidons à organiser vos vols et prenons en charge vos déplacements entre l'aéroport et l'hôpital.",
        lien: 'nos-services',
        image: 'icone-visa',
      },
      {
        titre: 'Séjour',
        texte:
          "Nous vous trouvons un hébergement, organisons sur demande vos activités de loisir et de tourisme, et restons votre famille loin de chez vous.",
        lien: 'hebergement',
        image: 'icone-hebergement',
      },
    ],
    citation:
      "Vous ne connaissez jamais votre force, jusqu'au jour où vous n'avez pas d'autre choix que d'être fort.",
    citationAuteur: 'Cayla Mills',
    engagement:
      "À BanaHealth, nous nous engageons à vous aider à surmonter tous vos problèmes de santé, qu'il s'agisse d'une chirurgie esthétique ou d'une maladie grave.",
    raisonsSurtitre: "Pourquoi l'Afrique du Sud",
    raisonsTitre: 'Une destination de premier plan',
    raisons: [
      {
        chiffre: '10',
        titre: 'Parmi les dix meilleurs systèmes de santé au monde',
        texte: "Le secteur privé sud-africain devance la France, le Royaume-Uni et l'Allemagne.",
      },
      {
        chiffre: '−70 %',
        titre: "Jusqu'à 70 % d'économie",
        texte: "Une intervention coûte couramment 30 à 70 % de moins qu'en Europe de l'Ouest ou aux États-Unis.",
      },
      {
        chiffre: "7 M",
        titre: "Dossiers en attente en Angleterre",
        texte: "Près de quatre patients sur dix y dépassent le délai officiel de dix-huit semaines.",
      },
    ],
    raisonsLien: 'pourquoi-afrique-du-sud',
    fondatriceSurtitre: 'Notre fondatrice',
    fondatriceTitre: "L'histoire de Marie Ngameni",
    fondatriceTexte:
      "Tout a commencé au début des années 2000 par un geste : aider la sœur d'une amie à trouver un traitement de fertilité. Ce geste est devenu une société bâtie sur la bienveillance.",
    fondatriceLien: 'notre-fondatrice',
    appelTitre: 'Parlons de votre situation',
    appelTexte:
      "Chaque parcours est particulier. Écrivez-nous avec votre rapport médical si vous en avez un : nous étudions votre dossier et revenons vers vous avec des éléments concrets.",
  },

  en: {
    heroSurtitre: 'Medical facilitation in South Africa',
    heroTitre: ['The care', 'you deserve'],
    heroTexte:
      'At BanaHealth we put our patients at the heart of everything we do. Their recovery is what drives us, day and night.',
    piliersSurtitre: 'Our services',
    piliersTitre: 'Support on three fronts',
    piliers: [
      {
        titre: 'Medical facilitation',
        texte:
          'We find the doctors best suited to your needs, obtain quotes for your treatment and arrange every medical appointment.',
        lien: 'our-services',
        image: 'icone-medecins',
      },
      {
        titre: 'Travel facilitation',
        texte:
          'We ease the process of obtaining your visa and its extensions, help you arrange flights and handle transfers between airport and hospital.',
        lien: 'our-services',
        image: 'icone-visa',
      },
      {
        titre: 'Your stay',
        texte:
          'We find you accommodation, arrange leisure and tourism on request, and remain your family away from home.',
        lien: 'accommodation',
        image: 'icone-hebergement',
      },
    ],
    citation:
      'You never know how strong you are until being strong is the only choice you have.',
    citationAuteur: 'Cayla Mills',
    engagement:
      'At BanaHealth we are committed to helping you overcome whatever you face, from cosmetic surgery to serious illness.',
    raisonsSurtitre: 'Why South Africa',
    raisonsTitre: 'A leading destination',
    raisons: [
      {
        chiffre: '10',
        titre: 'Among the world’s ten best healthcare systems',
        texte: 'The South African private sector ranks ahead of France, the United Kingdom and Germany.',
      },
      {
        chiffre: '−70 %',
        titre: 'Up to 70 % less',
        texte: 'A procedure commonly costs 30 to 70 % less than in Western Europe or the United States.',
      },
      {
        chiffre: '7 M',
        titre: 'Cases waiting in England',
        texte: 'Nearly four patients in ten there exceed the official eighteen-week standard.',
      },
    ],
    raisonsLien: 'why-south-africa',
    fondatriceSurtitre: 'Our founder',
    fondatriceTitre: 'The story of Marie Ngameni',
    fondatriceTexte:
      'It began in the early 2000s with a single gesture: helping a friend’s sister find fertility treatment. That gesture has become a company built on kindness.',
    fondatriceLien: 'our-founder',
    appelTitre: 'Let’s talk about your situation',
    appelTexte:
      'Every journey is particular. Write to us with your medical report if you have one: we will review your case and come back with concrete answers.',
  },
};
