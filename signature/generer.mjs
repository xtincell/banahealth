/**
 * Generateur de signatures de courriel BanaHealth.
 *
 *   node signature/generer.mjs
 *
 * Produit un fichier HTML par personne listee plus bas, ainsi qu'un
 * gabarit vierge. Passer par un generateur evite que les signatures
 * divergent au fil des copies manuelles.
 *
 * Le HTML est en tableaux imbriques et styles en ligne : Outlook rend
 * le courriel avec le moteur de Word, qui ignore la mise en page
 * moderne et les feuilles de style externes.
 */
import fs from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';

const DOSSIER = path.dirname(new URL(import.meta.url).pathname);
const SITE = 'https://banahealth.care';

// Source unique : le meme fichier que celui qui alimente le site.
const COORD = yaml.load(
  fs.readFileSync(path.join(DOSSIER, '../src/textes/coordonnees.yaml'), 'utf8'),
);

/**
 * Mode d'inclusion des visuels.
 *
 *   node signature/generer.mjs            visuels appeles par URL
 *   node signature/generer.mjs --embarque visuels inclus dans le HTML
 *
 * Beaucoup de messageries — Zoho, Gmail, Outlook — bloquent par defaut
 * les images distantes, parce que c'est ainsi que fonctionnent les
 * pisteurs. Le mode embarque supprime la dependance : l'image voyage
 * dans le message. Il alourdit chaque envoi d'une douzaine de
 * kilo-octets, et Outlook pour Windows peut presenter les images
 * embarquees comme des pieces jointes.
 */
const EMBARQUE = process.argv.includes('--embarque');

/** Transforme un fichier local en adresse de donnees. */
function enDonnees(nomFichier) {
  const chemin = path.join(DOSSIER, '../public/signature', nomFichier);
  const b64 = fs.readFileSync(chemin).toString('base64');
  return `data:image/png;base64,${b64}`;
}

const visuel = (nomFichier) =>
  EMBARQUE ? enDonnees(nomFichier) : `${SITE}/signature/${nomFichier}`;

// Le logo est appele depuis le site. Ne pas le recopier ailleurs :
// si son adresse change, toutes les signatures cassent d'un coup.
const LOGO = { fichier: 'banahealth-horizontal.png', largeur: 190, hauteur: 50 };

const COULEURS = {
  nom: '#242A29',
  fonction: '#0AA89E',
  texte: '#5A6160',
  discret: '#838484',
  lien: '#0AA89E',
  filet: '#F1592F',
  separateur: '#D8E2E1',
};

const ADRESSE = [
  `${COORD.adresse.rue}, ${COORD.adresse.ville}, ${COORD.adresse.pays.en} ${COORD.adresse.code_postal}`,
  COORD.adresse.boite_postale,
];

const FAX = COORD.fax;

const RESEAUX = COORD.reseaux;

/**
 * Numero affichable -> forme composable.
 * Le "(0)" est le prefixe national sud-africain : il ne se compose
 * pas depuis l’etranger et doit disparaitre du format international,
 * faute de quoi le lien ne joint personne.
 */
const composable = (n) => '+' + n.replace(/\(0\)/, '').replace(/[^0-9]/g, '');

const equipe = [
  {
    fichier: 'marie-ngameni.html',
    nom: 'Marie Ngameni',
    fonction: 'Founder & CEO',
    mobile: '+27 (0) 82 775 6975',
    courriel: 'marie.ngameni@banahealth.care',
  },
  {
    fichier: 'nina-ngameni.html',
    nom: 'Nina Ngameni',
    fonction: 'Case Manager',
    mobile: '+27 (0) 82 684 4154',
    courriel: 'nina.ngameni@banahealth.care',
  },
];

function signature(p) {
  return `<table cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;background-color:#ffffff;font-family:Arial,Helvetica,sans-serif;">
  <tr>
    <!-- Logo, verrou horizontal de la charte (p.4) -->
    <td valign="middle" style="padding:0 0 0 0;">
      <a href="${SITE}" style="text-decoration:none;border:0;">
        <img src="${visuel(LOGO.fichier)}"
             alt="BanaHealth — Medical Facilitation"
             width="${LOGO.largeur}" height="${LOGO.hauteur}"
             style="display:block;border:0;outline:none;width:${LOGO.largeur}px;height:${LOGO.hauteur}px;" />
      </a>
    </td>

    <td width="22" style="width:22px;font-size:0;line-height:0;">&nbsp;</td>

    <!-- Filet : une cellule coloree, les bordures CSS etant mal rendues par Outlook -->
    <td width="3" style="width:3px;background-color:${COULEURS.filet};font-size:0;line-height:0;">&nbsp;</td>

    <td width="18" style="width:18px;font-size:0;line-height:0;">&nbsp;</td>

    <td valign="top" style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:20px;color:${COULEURS.texte};padding:2px 0 0 0;">

      <div style="font-size:17px;font-weight:bold;color:${COULEURS.nom};line-height:22px;">${p.nom}</div>
      <div style="font-size:13px;color:${COULEURS.fonction};padding-bottom:9px;">${p.fonction}</div>

      <div>
        <span style="color:${COULEURS.discret};">C</span>
        <a href="tel:${composable(p.mobile)}" style="color:${COULEURS.texte};text-decoration:none;">${p.mobile}</a>
        <span style="color:${COULEURS.separateur};">&nbsp;|&nbsp;</span>
        <span style="color:${COULEURS.discret};">F</span> ${FAX}
      </div>

      <div>
        <span style="color:${COULEURS.discret};">E</span>
        <a href="mailto:${p.courriel}" style="color:${COULEURS.lien};text-decoration:none;">${p.courriel}</a>
        <span style="color:${COULEURS.separateur};">&nbsp;|&nbsp;</span>
        <a href="${SITE}" style="color:${COULEURS.lien};text-decoration:none;">banahealth.care</a>
      </div>

      <div style="padding-top:8px;font-size:12px;line-height:18px;color:${COULEURS.discret};">
        ${ADRESSE.join('<br />\n        ')}
      </div>

      <table cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;margin-top:12px;">
        <tr>
          ${RESEAUX.map(
            (r, i) =>
              (i ? '<td width="12" style="width:12px;font-size:0;line-height:0;">&nbsp;</td>' : '') +
              `<td style="padding:0;"><a href="${r.url}" style="text-decoration:none;border:0;"><img src="${visuel(r.icone + '.png')}" alt="${r.nom}" width="28" height="28" style="display:block;border:0;outline:none;width:28px;height:28px;" /></a></td>`,
          ).join('')}
        </tr>
      </table>

    </td>
  </tr>
</table>
`;
}

for (const p of equipe) {
  const nom = EMBARQUE ? p.fichier.replace('.html', '-embarque.html') : p.fichier;
  const html = signature(p);
  fs.writeFileSync(path.join(DOSSIER, nom), html);
  console.log(`  ${nom.padEnd(34)} ${(html.length / 1024).toFixed(1)} ko  ${p.nom}`);
}

// Gabarit vierge, pour ceux qui preferent remplir a la main
const gabarit = signature({
  nom: '[PRÉNOM NOM]',
  fonction: '[Fonction]',
  mobile: '+27 (0) 00 000 0000',
  courriel: 'prenom.nom@banahealth.care',
});
fs.writeFileSync(
  path.join(DOSSIER, EMBARQUE ? 'modele-embarque.html' : 'modele.html'),
  `<!--\n  Gabarit : remplacez ce qui est entre crochets, ainsi que le\n  numero et l'adresse de courriel. Ne touchez ni aux balises\n  <table>, ni aux styles.\n\n  Mieux : ajoutez la personne dans generer.mjs et relancez le\n  script, pour que toutes les signatures restent identiques.\n-->\n${gabarit}`,
);
console.log('  modele.html              gabarit vierge');
console.log(`\n${equipe.length + 1} fichiers ecrits dans ${DOSSIER}`);
