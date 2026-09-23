import fs from 'node:fs';
import { createCanvas, loadImage } from '@napi-rs/canvas';

/**
 * Allege un visuel de marque sans en alterer les couleurs.
 *
 * Le principe : les aplats sont ramenes aux teintes exactes de la
 * charte, et seule la transparence des bords antialiases est
 * quantifiee. Une quantification naive des canaux RVB deplacerait
 * l'orange et le turquoise, ce qui est exclu pour un logo.
 */
const CHARTE = [
  [241, 89, 47],    // orange  #F1592F
  [10, 168, 158],   // turquoise #0AA89E
  [131, 132, 132],  // gris    #838484
  [255, 255, 255],  // blanc
];

function distance(r, g, b, [pr, pg, pb]) {
  const dr = r - pr, dg = g - pg, db = b - pb;
  return dr * dr + dg * dg + db * db;
}

export async function alleger(chemin, pasAlpha = 8) {
  const img = await loadImage(chemin);
  const c = createCanvas(img.width, img.height);
  const ctx = c.getContext('2d');
  ctx.drawImage(img, 0, 0);
  const image = ctx.getImageData(0, 0, img.width, img.height);
  const d = image.data;

  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] === 0) { d[i] = d[i + 1] = d[i + 2] = 0; continue; }

    // Teinte exacte de la charte la plus proche
    let meilleure = CHARTE[0], min = Infinity;
    for (const p of CHARTE) {
      const dist = distance(d[i], d[i + 1], d[i + 2], p);
      if (dist < min) { min = dist; meilleure = p; }
    }
    d[i] = meilleure[0];
    d[i + 1] = meilleure[1];
    d[i + 2] = meilleure[2];

    // La finesse des bords vit dans la transparence, pas dans la teinte
    d[i + 3] = Math.min(255, Math.round(d[i + 3] / pasAlpha) * pasAlpha);
  }

  ctx.putImageData(image, 0, 0);
  return c.toBuffer('image/png');
}

if (process.argv[1].endsWith('alleger.mjs')) {
  // Tous les visuels du dossier, pour qu'un fichier ajoute plus tard
  // ne passe pas au travers de l'optimisation.
  const DOSSIER = new URL('../public/signature/', import.meta.url).pathname;
  const cibles = fs
    .readdirSync(DOSSIER)
    .filter((n) => n.endsWith('.png'))
    .map((n) => DOSSIER + n);
  let avant = 0, apres = 0;
  for (const f of cibles) {
    const o = fs.statSync(f).size;
    const buf = await alleger(f);
    avant += o;
    apres += buf.length;
    const nom = f.split('/').pop();
    console.log(`  ${nom.padEnd(28)} ${(o / 1024).toFixed(1)} -> ${(buf.length / 1024).toFixed(1)} ko`);
    fs.writeFileSync(f, buf);
  }
  console.log(`\ntotal : ${(avant / 1024).toFixed(1)} -> ${(apres / 1024).toFixed(1)} ko  (-${((1 - apres / avant) * 100).toFixed(0)} %)`);
}
