import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import yaml from 'js-yaml';
import { resoudreCartesContact, resoudreEquipeSignatures } from '../src/lib/coordonnees.mjs';

const source = () => yaml.load(fs.readFileSync(new URL('../src/textes/coordonnees.yaml', import.meta.url), 'utf8'));

test('les cartes suivent les coordonnées sans modifier la source ni les libellés', () => {
  const coord = source();
  coord.courriel = 'audit@example.invalid';
  coord.telephones[0].appel = '+27999900000';
  const cartes = [{ titre: 'Write to us', lien: 'mailto:{{courriel}}', lienLibelle: '{{courriel}}' }, { titre: 'Call us', lien: 'tel:{{telephone_appel}}' }];
  const avant = JSON.stringify({ coord, cartes });
  const resultat = resoudreCartesContact(cartes, coord, 'en');
  assert.equal(resultat[0].lien, 'mailto:audit@example.invalid');
  assert.equal(resultat[0].lienLibelle, 'audit@example.invalid');
  assert.equal(resultat[0].titre, 'Write to us');
  assert.equal(resultat[1].lien, 'tel:+27999900000');
  assert.equal(JSON.stringify({ coord, cartes }), avant);
});

test('minuit, midi et les minutes sont lisibles dans chaque langue', () => {
  const coord = source();
  coord.horaires.ouverture = '00:05';
  coord.horaires.fermeture = '12:00';
  const cartes = [{ texte: '{{ouverture}} / {{fermeture}}' }];
  assert.equal(resoudreCartesContact(cartes, coord, 'fr')[0].texte, '0 h 05 / 12 h');
  assert.equal(resoudreCartesContact(cartes, coord, 'en')[0].texte, '12:05 a.m. / 12 p.m.');
});

test('un repère inconnu ou une donnée manquante arrête la compilation', () => {
  assert.throws(() => resoudreCartesContact([{ texte: '{{couriel}}' }], source(), 'fr'), /Repère/);
  assert.throws(() => resoudreCartesContact([{ texte: '{{constructor}}' }], source(), 'fr'), /Repère/);
  const coord = source();
  delete coord.numero_vert;
  assert.throws(() => resoudreCartesContact([{ texte: '{{numero_vert}}' }], coord, 'en'), /Repère/);
});

test('un horaire invalide et une langue inconnue ne sont pas devinés', () => {
  const coord = source();
  coord.horaires.ouverture = '25:90';
  assert.throws(() => resoudreCartesContact([], coord, 'fr'), /Horaire invalide/);
  assert.throws(() => resoudreCartesContact([], source(), 'de'), /Langue inconnue/);
});

test('réordonner les numéros ne les attribue pas à une autre personne', () => {
  const coord = source();
  const avant = resoudreEquipeSignatures(coord);
  coord.telephones.reverse();
  assert.deepEqual(resoudreEquipeSignatures(coord), avant);
});

test('un numéro modifié irrigue la personne qui le référence', () => {
  const coord = source();
  const tel = coord.telephones.find((t) => t.id === 'nina');
  tel.appel = '+27999900000';
  tel.affichage = '+27 (0) 99 990 0000';
  const equipe = resoudreEquipeSignatures(coord);
  assert.equal(equipe.find((p) => p.telephone === 'nina').appel, tel.appel);
  assert.equal(equipe.find((p) => p.telephone === 'nina').mobile, tel.affichage);
  assert.notEqual(equipe.find((p) => p.telephone === 'marie').appel, tel.appel);
});

test('une référence absente ou des identifiants ambigus sont refusés', () => {
  const coord = source();
  coord.signatures[0].telephone = 'absent';
  assert.throws(() => resoudreEquipeSignatures(coord), /Téléphone de signature inconnu/);
  const doublon = source();
  doublon.telephones[1].id = doublon.telephones[0].id;
  assert.throws(() => resoudreEquipeSignatures(doublon), /dupliqué/);
});

test('les fichiers éditables ne peuvent pas sortir du dossier ni s’écraser', () => {
  const coord = source();
  coord.signatures[0].fichier = '../index.html';
  assert.throws(() => resoudreEquipeSignatures(coord), /invalide ou dupliqué/);
  const doublon = source();
  doublon.signatures[1].fichier = doublon.signatures[0].fichier;
  assert.throws(() => resoudreEquipeSignatures(doublon), /invalide ou dupliqué/);
});
