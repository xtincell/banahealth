import { readFile, readdir, access } from 'node:fs/promises';
import { join } from 'node:path';
import { createHash } from 'node:crypto';
import { load } from 'js-yaml';
import { parse, TEXT_NODE } from 'ultrahtml';
import { querySelector, querySelectorAll } from 'ultrahtml/selector';
import { decodeHTML } from 'entities';

// HTTP/static verification only. This does not test a browser layout or usability.
const origin = 'http://127.0.0.1:4322';
const root = new URL('../', import.meta.url).pathname;
const failures = [], cache = new Map(), sourceHashes = {};
let contentChecks = 0;
const normalize = value => decodeHTML(String(value)).replace(/\s+/g, ' ').trim();
const text = node => {
  if (!node) return '';
  if (node.type === TEXT_NODE) return node.value;
  if (['script', 'style'].includes(node.name)) return '';
  const value = (node.children ?? []).map(text).join('');
  return ['p', 'h1', 'h2', 'h3', 'li', 'div', 'section', 'a', 'summary', 'figcaption', 'blockquote'].includes(node.name) ? ` ${value} ` : value;
};
const check = (condition, detail) => { if (!condition) failures.push(detail); };
async function files(dir) {
  return (await Promise.all((await readdir(dir, { withFileTypes: true })).map(e => e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)]))).flat();
}
async function source(file) {
  const value = await readFile(join(root, file), 'utf8');
  sourceHashes[file] = createHash('sha256').update(value).digest('hex');
  return value;
}
async function get(url) {
  const full = new URL(url, origin).href;
  if (!cache.has(full)) cache.set(full, (async () => {
    try { const response = await fetch(full); return { status: response.status, html: await response.text() }; }
    catch (error) { return { status: 0, html: '', error: error.message }; }
  })());
  return cache.get(full);
}
const routes = [];
for (const file of await files(join(root, 'src/content/pages'))) {
  const relative = file.slice(root.length);
  const raw = await source(relative);
  const data = load(raw.match(/^---\s*\n([\s\S]*?)\n---/)[1]);
  routes.push({ data, source: relative });
}
const homes = {};
for (const lang of ['fr', 'en']) homes[lang] = load(await source(`src/textes/accueil.${lang}.yaml`));
for (const file of await files(join(root, 'src/textes'))) if (!sourceHashes[file.slice(root.length)]) await source(file.slice(root.length));
const navigation = new Set(), images = new Set();
function inspect(tree, route) {
  check(querySelectorAll(tree, 'h1').length === 1, `${route}: expected one h1`);
  check(querySelector(tree, 'meta[name="robots"]')?.attributes.content === 'noindex,nofollow', `${route}: noindex`);
  for (const a of querySelectorAll(tree, 'a[href]')) {
    const url = new URL(decodeHTML(a.attributes.href), new URL(route, origin));
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) continue;
    if (!['http:', 'https:'].includes(url.protocol)) continue;
    if (url.hash && url.pathname === route) check(querySelector(tree, `[id="${url.hash.slice(1)}"]`), `${route}: missing anchor ${url.hash}`);
    url.hash = '';
    navigation.add(url.href);
  }
  for (const image of querySelectorAll(tree, 'img')) {
    check('alt' in image.attributes, `${route}: img without alt`);
    if (image.attributes.src) images.add(new URL(decodeHTML(image.attributes.src), origin).href);
  }
}
function contains(tree, value, route, field) {
  if (!value) return;
  contentChecks++;
  check(normalize(text(tree)).includes(normalize(value.replace(/\*/g, ''))), `${route}: missing/changed ${field}`);
}
for (const direction of ['a', 'b']) {
  for (const { data: d } of routes) {
    const route = `/atelier/${direction}/${d.langue === 'en' ? 'en/' : ''}${d.url}/`;
    const response = await get(route);
    check(response.status === 200, `${route}: HTTP ${response.status}`);
    const tree = parse(response.html);
    inspect(tree, route);
    for (const key of ['titre', 'surtitre', 'chapeau']) contains(querySelector(tree, 'main'), d[key], route, key);
    for (const key of ['cartes', 'etapes', 'galerie']) for (const item of d[key] ?? []) for (const field of ['titre', 'texte', 'legende', 'lienLibelle']) contains(querySelector(tree, 'main'), item[field], route, `${key}.${field}`);
    check(querySelector(tree, 'meta[name="description"]')?.attributes.content === d.description, `${route}: description`);
    const modern = `/${d.langue === 'en' ? 'en/' : ''}${d.url}/`;
    check(querySelector(tree, 'link[rel="canonical"]')?.attributes.href === `https://banahealth.care${modern}`, `${route}: canonical`);
    const reference = parse(await readFile(join(root, 'dist', modern, 'index.html'), 'utf8'));
    contentChecks++;
    check(normalize(text(querySelector(reference, '.prose'))) === normalize(text(querySelector(tree, '.reading'))), `${route}: Markdown body differs from existing build`);
  }
  for (const lang of ['fr', 'en']) {
    const route = `/atelier/${direction}/${lang === 'en' ? 'en/' : ''}`;
    const response = await get(route), tree = parse(response.html), home = homes[lang];
    check(response.status === 200, `${route}: HTTP ${response.status}`);
    inspect(tree, route);
    for (const [key, value] of Object.entries(home)) {
      if (Array.isArray(value)) for (const item of value) for (const field of ['titre', 'texte', 'auteur', 'chiffre', 'lienLibelle']) contains(querySelector(tree, 'main'), item[field], route, `${key}.${field}`);
      else if (!['diapoPrecedente', 'diapoSuivante', 'diapoAller', 'raisonsLien', 'fondatriceLien', 'temoignagesLien'].includes(key)) contains(tree, value, route, key);
    }
  }
}
for (const url of navigation) check((await get(url)).status === 200, `navigation HTTP error: ${url}`);
for (const url of images) check((await get(url)).status === 200, `image HTTP error: ${url}`);
let productionExcluded = false;
try { await access(join(root, 'dist/atelier')); } catch { productionExcluded = true; }
check(productionExcluded, 'Workshop routes leaked into production build');
console.log(JSON.stringify({ type: 'HTTP and static, not browser QA', pages: routes.length * 2 + 4, contentChecks, navigationTargets: navigation.size, imageTargets: images.size, productionExcluded, failures, sourceHashes }, null, 2));
process.exitCode = failures.length ? 1 : 0;
