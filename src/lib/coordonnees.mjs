/** Coordonnées éditables, partagées par les cartes Contact et les signatures. */
function heureAffichable(heure, langue) {
  if (!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(heure)) {
    throw new Error(`Horaire invalide : ${heure}`);
  }
  const [h, m] = heure.split(':').map(Number);
  if (langue === 'fr') return `${h} h${m ? ` ${String(m).padStart(2, '0')}` : ''}`;
  return `${h % 12 || 12}${m ? `:${String(m).padStart(2, '0')}` : ''} ${h < 12 ? 'a.m.' : 'p.m.'}`;
}

/** Remplace uniquement les repères de coordonnées ; aucun HTML ni code évalué. */
export function resoudreCartesContact(cartes, coord, langue) {
  if (!['fr', 'en'].includes(langue)) throw new Error(`Langue inconnue : ${langue}`);
  const telephone = coord.telephones[0];
  const valeurs = {
    courriel: coord.courriel,
    telephone_affichage: telephone.affichage,
    telephone_appel: telephone.appel,
    jours: coord.horaires.jours[langue],
    ouverture: heureAffichable(coord.horaires.ouverture, langue),
    fermeture: heureAffichable(coord.horaires.fermeture, langue),
    fuseau: coord.horaires.fuseau,
    numero_vert: coord.numero_vert,
    adresse: `${coord.adresse.rue}, ${coord.adresse.ville}, ${coord.adresse.pays[langue]} ${coord.adresse.code_postal}`,
    boite_postale: coord.adresse.boite_postale,
  };
  const resoudre = (texte) => {
    if (texte === undefined) return texte;
    return texte.replace(/\{\{([^{}]*)\}\}/g, (_, repere) => {
      const cle = repere.trim();
      if (!Object.hasOwn(valeurs, cle) || typeof valeurs[cle] !== 'string') {
        throw new Error(`Repère de coordonnées inconnu ou incomplet : ${cle}`);
      }
      return valeurs[cle];
    });
  };
  return cartes.map((carte) => ({
    ...carte,
    texte: resoudre(carte.texte),
    lien: resoudre(carte.lien),
    lienLibelle: resoudre(carte.lienLibelle),
  }));
}

/** Une personne référence un téléphone stable, jamais sa position dans la liste. */
export function resoudreEquipeSignatures(coord) {
  const telephones = new Map();
  for (const tel of coord.telephones) {
    if (!tel.id || telephones.has(tel.id)) throw new Error('Identifiant de téléphone absent ou dupliqué');
    telephones.set(tel.id, tel);
  }
  const fichiers = new Set();
  return coord.signatures.map((personne) => {
    const tel = telephones.get(personne.telephone);
    if (!tel) throw new Error(`Téléphone de signature inconnu : ${personne.telephone}`);
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*\.html$/.test(personne.fichier) || fichiers.has(personne.fichier)) {
      throw new Error('Nom de fichier de signature invalide ou dupliqué');
    }
    fichiers.add(personne.fichier);
    return { ...personne, mobile: tel.affichage, appel: tel.appel };
  });
}
