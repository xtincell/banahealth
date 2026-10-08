import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';
import yaml from 'js-yaml';

test('modifier le YAML irrigue les vrais HTML compilés et les deux formats de signature', { timeout: 180000 }, () => {
  const racine = fileURLToPath(new URL('../', import.meta.url));
  const copie = fs.mkdtempSync(path.join(os.tmpdir(), 'banahealth-coordonnees-'));
  const lancer = (commande, args) => execFileSync(commande, args, { cwd: copie, stdio: 'pipe', timeout: 90000 });
  try {
    for (const nom of ['src', 'public', 'signature', 'package.json', 'astro.config.mjs']) {
      fs.cpSync(path.join(racine, nom), path.join(copie, nom), { recursive: true });
    }
    fs.symlinkSync(path.join(racine, 'node_modules'), path.join(copie, 'node_modules'), 'dir');
    const fichier = path.join(copie, 'src/textes/coordonnees.yaml');
    const coord = yaml.load(fs.readFileSync(fichier, 'utf8'));
    coord.courriel = 'audit@example.invalid';
    coord.telephones[0].appel = '+27999900000';
    coord.telephones[0].affichage = '+27 (0) 99 990 0000';
    coord.adresse.rue = 'Audit Avenue';
    coord.adresse.boite_postale = 'Audit Postal';
    coord.numero_vert = '0800 00 00 00';
    coord.horaires.ouverture = '09:30';
    coord.horaires.fermeture = '18:15';
    fs.writeFileSync(fichier, yaml.dump(coord));
    lancer('npm', ['run', 'build']);
    for (const [rel, heures] of [['contact/index.html', ['9 h 30', '18 h 15']], ['en/contact/index.html', ['9:30 a.m.', '6:15 p.m.']]]) {
      const html = fs.readFileSync(path.join(copie, 'dist', rel), 'utf8');
      const principal = html.match(/<main\b[^>]*>([\s\S]*?)<\/main>/)?.[1];
      assert.ok(principal, rel);
      for (const valeur of ['mailto:audit@example.invalid', 'tel:+27999900000', 'Audit Avenue', 'Audit Postal', '0800 00 00 00', ...heures]) {
        assert.ok(principal.includes(valeur), `${rel} : ${valeur}`);
      }
      assert.ok(html.includes('"email":"audit@example.invalid"'));
      assert.ok(html.includes('"opens":"09:30"'));
    }
    for (const args of [[], ['--embarque']]) {
      lancer('node', ['signature/generer.mjs', ...args]);
      const personne = coord.signatures.find((p) => p.telephone === coord.telephones[0].id);
      const nom = args.length ? personne.fichier.replace('.html', '-embarque.html') : personne.fichier;
      const html = fs.readFileSync(path.join(copie, 'signature', nom), 'utf8');
      for (const valeur of ['tel:+27999900000', '+27 (0) 99 990 0000', 'Audit Avenue', 'Audit Postal']) assert.ok(html.includes(valeur));
    }
  } finally {
    fs.rmSync(copie, { recursive: true, force: true });
  }
});
