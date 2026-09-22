/**
 * Acces au contenu de la page d'accueil.
 *
 * Le texte ne vit pas ici mais dans src/textes/accueil.*.yaml, pour
 * qu'il puisse etre modifie sans toucher au code.
 */
import accueilFr from '../textes/accueil.fr.yaml';
import accueilEn from '../textes/accueil.en.yaml';
import type { Langue } from './ui';

export interface Diapo {
  image: string;
  /** La portion entre *asterisques* est mise en valeur */
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
  fr: accueilFr as ContenuAccueil,
  en: accueilEn as ContenuAccueil,
};
