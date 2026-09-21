import type { Langue } from './ui';

export interface Diapo {
  /** Nom du fichier dans src/assets/media */
  image: string;
  /** Titre ; la portion entre * * est mise en valeur, comme dans le logo */
  titre: string;
  texte: string;
  auteur?: string;
  lienLibelle: string;
  lien: string;
}

export interface Temoignage {
  texte: string;
  auteur?: string;
}

export interface ContenuAccueil {
  diapos: Diapo[];
  diapoPrecedente: string;
  diapoSuivante: string;
  diapoAller: string;
  toujoursDisponible: string;

  piliersSurtitre: string;
  piliersTitre: string;
  piliers: { titre: string; texte: string; lien: string; image: string }[];

  raisonsSurtitre: string;
  raisonsTitre: string;
  raisons: { chiffre: string; titre: string; texte: string }[];
  raisonsLien: string;

  fondatriceSurtitre: string;
  fondatriceTitre: string;
  fondatriceTexte: string;
  fondatriceLien: string;

  temoignagesSurtitre: string;
  temoignagesTitre: string;
  temoignages: Temoignage[];
  temoignagesLien: string;

  appelTitre: string;
  appelTexte: string;
}

export const accueil: Record<Langue, ContenuAccueil> = {
  fr: {
    // Les trois messages du carrousel d'origine, repris mot pour mot
    diapos: [
      {
        image: 'accueil-slide-1',
        titre: 'Les *soins* que vous méritez',
        texte:
          'À BanaHealth, nous plaçons nos patients au cœur de tout ce que nous faisons. Leur guérison est ce qui nous pousse, jour et nuit.',
        lienLibelle: 'Nos services',
        lien: 'nos-services',
      },
      {
        image: 'accueil-slide-2',
        titre: 'Nous sommes là *pour vous*',
        texte:
          "Vous ne connaissez jamais votre force, jusqu'au jour où vous n'avez pas d'autre choix que d'être fort.",
        auteur: 'Cayla Mills',
        lienLibelle: 'Qui sommes-nous',
        lien: 'notre-fondatrice',
      },
      {
        image: 'accueil-slide-3',
        titre: "La plus grande richesse, c'est *la santé*",
        texte:
          "À BanaHealth, nous nous engageons à vous aider à surmonter tous vos problèmes de santé, qu'il s'agisse d'une chirurgie esthétique ou d'une maladie grave.",
        auteur: 'Virgile',
        lienLibelle: 'Nos réseaux',
        lien: 'nos-reseaux',
      },
    ],
    diapoPrecedente: 'Message précédent',
    diapoSuivante: 'Message suivant',
    diapoAller: 'Aller au message',
    toujoursDisponible: 'Toujours disponible',

    piliersSurtitre: 'Nos services',
    piliersTitre: 'Un accompagnement sur trois fronts',
    piliers: [
      {
        titre: 'Facilitation des soins',
        texte:
          'Nous trouvons les médecins qui répondent le mieux à vos besoins, obtenons des devis pour vos traitements et organisons tous vos rendez-vous médicaux.',
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
          'Nous vous trouvons un hébergement, organisons sur demande vos activités de loisir et de tourisme, et restons votre famille loin de chez vous.',
        lien: 'hebergement',
        image: 'icone-hebergement',
      },
    ],

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
        texte:
          "Une intervention coûte couramment 30 à 70 % de moins qu'en Europe de l'Ouest ou aux États-Unis.",
      },
      {
        chiffre: '7 M',
        titre: 'Dossiers en attente en Angleterre',
        texte:
          'Près de quatre patients sur dix y dépassent le délai officiel de dix-huit semaines.',
      },
    ],
    raisonsLien: 'pourquoi-afrique-du-sud',

    fondatriceSurtitre: 'Notre fondatrice',
    fondatriceTitre: "L'histoire de Marie Ngameni",
    fondatriceTexte:
      "Tout a commencé au début des années 2000 par un geste : aider la sœur d'une amie à trouver un traitement de fertilité. Ce geste est devenu une société bâtie sur la bienveillance.",
    fondatriceLien: 'notre-fondatrice',

    temoignagesSurtitre: 'Ce que nos clients disent de nous',
    temoignagesTitre: 'Des parcours, des retours',
    temoignages: [
      {
        texte:
          "J'ai été vraiment touché par la qualité des soins personnalisés et des services que j'ai reçus de l'équipe de BanaHealth et du corps médical au centre médical Wits Donald Gordon. Ils m'ont soutenu à chaque étape de mon traitement et sont véritablement devenus ma seconde famille.",
        auteur: 'Thomas',
      },
      {
        texte:
          "Je suis venue en Afrique du Sud pour un bilan de santé complet. On a constaté que j'étais presque diabétique et que je devais changer complètement mon style de vie. Je remercie le médecin pour m'avoir fait prendre conscience de mon mode de vie : j'ai depuis adopté des habitudes plus saines et perdu 18 kg. Cette expérience m'a donné un nouveau souffle.",
        auteur: 'Arlette',
      },
      {
        texte:
          "Je suis cliente de BanaHealth depuis 2014, lorsqu'on m'a diagnostiqué un cancer. Je suis restée six mois en Afrique du Sud pour suivre une chimiothérapie, et chaque année depuis, j'y retourne consulter mon oncologue. La relation de longue date que j'ai tissée avec l'équipe est spéciale.",
      },
      {
        texte:
          "J'étais assez nerveuse de me retrouver au bloc pour une si grosse opération, je dois l'avouer. Ma chirurgie fut un succès et mon médecin m'a demandé de rester couchée six semaines. J'ai trouvé les appartements de BanaHealth très confortables et propres, un environnement propice à un prompt rétablissement.",
      },
    ],
    temoignagesLien: 'temoignages',

    appelTitre: 'Parlons de votre situation',
    appelTexte:
      "Chaque parcours est particulier. Écrivez-nous avec votre rapport médical si vous en avez un : nous étudions votre dossier et revenons vers vous avec des éléments concrets.",
  },

  en: {
    diapos: [
      {
        image: 'accueil-slide-1',
        titre: 'The *care* you deserve',
        texte:
          'At BanaHealth, our patients are at the heart of all we do. Their recovery is what drives us day and night.',
        lienLibelle: 'What we do',
        lien: 'our-services',
      },
      {
        image: 'accueil-slide-2',
        titre: 'We are here *for you*',
        texte:
          'You never know how strong you are until being strong is the only choice you have.',
        auteur: 'Cayla Mills',
        lienLibelle: 'Who we are',
        lien: 'our-founder',
      },
      {
        image: 'accueil-slide-3',
        titre: 'The greatest wealth is *health*',
        texte:
          'We at BanaHealth are committed to helping you overcome any health issue, be it cosmetic surgery or a life-threatening condition.',
        auteur: 'Virgil',
        lienLibelle: 'Our network',
        lien: 'our-network',
      },
    ],
    diapoPrecedente: 'Previous message',
    diapoSuivante: 'Next message',
    diapoAller: 'Go to message',
    toujoursDisponible: 'Always available',

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

    raisonsSurtitre: 'Why South Africa',
    raisonsTitre: 'A leading destination',
    raisons: [
      {
        chiffre: '10',
        titre: 'Among the world’s ten best healthcare systems',
        texte:
          'The South African private sector ranks ahead of France, the United Kingdom and Germany.',
      },
      {
        chiffre: '−70 %',
        titre: 'Up to 70 % less',
        texte:
          'A procedure commonly costs 30 to 70 % less than in Western Europe or the United States.',
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

    temoignagesSurtitre: 'What our clients say',
    temoignagesTitre: 'Journeys, in their own words',
    temoignages: [
      {
        texte:
          'I was really moved by the high level of personal care and service I received from the BanaHealth team and the general medical body at DGMC. They supported me every step of the way and truly became my family away from home.',
        auteur: 'Thomas',
      },
      {
        texte:
          'I came to South Africa for a thorough medical checkup. It was found that I was borderline diabetic and needed a complete lifestyle change. I thank the doctor for the rude awakening he gave me — I have since adopted a healthier lifestyle and shed 18 kg. This experience has given me a new lease on life.',
        auteur: 'Arlette',
      },
      {
        texte:
          'I have been a client of BanaHealth since 2014, when I was diagnosed with cancer. I remained in South Africa for six months to receive chemotherapy, and every year since, I return to consult my treating oncologist. The long-standing relationship I have forged with the team is special.',
      },
      {
        texte:
          'Going into theatre for such a major operation made me quite nervous, I must admit. Thankfully my surgery was successful, and my doctor instructed that I remain on my back for six weeks. I found BanaHealth’s accommodation very cosy and clean — a setting conducive to a speedy recovery.',
      },
    ],
    temoignagesLien: 'testimonials',

    appelTitre: 'Let’s talk about your situation',
    appelTexte:
      'Every journey is particular. Write to us with your medical report if you have one: we will review your case and come back with concrete answers.',
  },
};
