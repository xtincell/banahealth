import { readFile, readdir, access } from 'node:fs/promises';
import { join, relative } from 'node:path';
import { createHash } from 'node:crypto';
import { load } from 'js-yaml';
import { parse, TEXT_NODE } from 'ultrahtml';
import { querySelector, querySelectorAll } from 'ultrahtml/selector';
import { decodeHTML } from 'entities';

// Static + HTTP evidence only: never a substitute for browser/gesture QA.
const root = new URL('../', import.meta.url).pathname;
const before = process.argv[2];
if (!before) throw new Error('Pass the absolute pre-update snapshot directory.');
const origin = process.env.BANA_PREVIEW_ORIGIN ?? 'http://127.0.0.1:4322';
const developmentOrigin = process.env.BANA_DEV_ORIGIN ?? 'http://127.0.0.1:4322';
const failures = [], navigation = new Set(), assets = new Set();
let pages = 0, contentChecks = 0, sourceFiles = 0, signatureFiles = 0;
const check = (ok, message) => { if (!ok) failures.push(message); };
const normalized = value => decodeHTML(String(value)).replace(/\s+/g, ' ').trim();
function text(node) {
  if (!node) return '';
  if (node.type === TEXT_NODE) return node.value;
  if (['script', 'style'].includes(node.name)) return '';
  const value = (node.children ?? []).map(text).join('');
  return ['p', 'h1', 'h2', 'h3', 'li', 'div', 'section', 'a', 'summary', 'figcaption', 'blockquote'].includes(node.name) ? ` ${value} ` : value;
}
async function files(dir) {
  return (await Promise.all((await readdir(dir, { withFileTypes: true })).map(e => e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)]))).flat();
}
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
for (const directory of ['src/textes', 'src/content/pages']) {
  for (const file of await files(join(before, directory))) {
    const name = relative(before, file);
    sourceFiles++;
    check(hash(await readFile(file)) === hash(await readFile(join(root, name))), `Source changed: ${name}`);
  }
}
for (const file of await files(join(root, 'public/signature'))) {
  const name = relative(join(root, 'public'), file);
  signatureFiles++;
  check(hash(await readFile(file)) === hash(await readFile(join(before, 'dist', name))), `Signature changed: ${name}`);
}
const routes = [];
for (const file of await files(join(root, 'src/content/pages'))) {
  const raw = await readFile(file, 'utf8');
  const data = load(raw.match(/^---\s*\n([\s\S]*?)\n---/)[1]);
  routes.push({ data, route: `/${data.langue === 'en' ? 'en/' : ''}${data.url}/` });
}
const contains = (tree, value, route, field) => {
  if (!value) return;
  contentChecks++;
  check(normalized(text(tree)).includes(normalized(String(value).replace(/\*/g, ''))), `${route}: missing/changed ${field}`);
};
async function document(route) {
  const html = await readFile(join(root, 'dist', route, 'index.html'), 'utf8');
  const tree = parse(html);
  const legacy = route.startsWith('/legacy/');
  const modern = legacy ? route.slice('/legacy'.length) : route;
  pages++;
  // Preserve the legacy carousel's existing heading structure as well as its layout.
  // Modern pages use one h1; Legacy home keeps its three original slide headings.
  const expectedHeadings = legacy && ['/', '/en/'].includes(modern) ? 3 : 1;
  check(querySelectorAll(tree, 'h1').length === expectedHeadings, `${route}: h1 count`);
  check(querySelector(tree, 'html')?.attributes['data-view'] === (legacy ? 'legacy' : 'modern'), `${route}: renderer`);
  check(querySelector(tree, 'html')?.attributes.lang === (modern.startsWith('/en/') ? 'en' : 'fr'), `${route}: language`);
  check(querySelector(tree, 'link[rel="canonical"]')?.attributes.href === `https://banahealth.care${modern}`, `${route}: canonical`);
  check(querySelector(tree, 'meta[name="robots"]')?.attributes.content.startsWith(legacy ? 'noindex' : 'index'), `${route}: robots`);
  const switchTarget = legacy ? modern : `/legacy${modern}`;
  check(querySelectorAll(tree, 'a').some(a => a.attributes.href === switchTarget), `${route}: equivalent view link`);
  if (!legacy && !['/', '/en/'].includes(route)) check(!querySelector(tree, 'script[src="/js/site.js"]'), `${route}: article requires carousel JavaScript`);
  if (!legacy && ['/en/our-services/', '/nos-services/'].includes(route)) {
    check(querySelectorAll(tree, '.bh-service-chapter').length === 3 && querySelectorAll(tree, '.bh-service-detail').length === 11, `${route}: three service chapters and eleven complete details`);
    check(querySelector(tree, '.bh-original-document img'), `${route}: original infographic must remain available`);
  }
  if (!legacy && ['/en/medical-care/', '/soins-medicaux/'].includes(route)) check(querySelectorAll(tree, '.bh-care-photo').length === 4, `${route}: four photographic care links`);
  if (!legacy && ['/en/why-south-africa/', '/pourquoi-afrique-du-sud/'].includes(route)) check(querySelectorAll(tree, '.bh-reason').length === 5 && querySelectorAll(tree, '.bh-editorial figure').length === 5, `${route}: five reasons and five original photographs without repetition`);
  if (!legacy && ['/en/our-network/', '/nos-reseaux/'].includes(route)) check(querySelectorAll(tree, '.bh-institution details').length === 7 && querySelectorAll(tree, '.bh-institution-link').length === 7, `${route}: seven complete institution details and official links`);
  if (!legacy && ['/', '/en/'].includes(route)) check(querySelectorAll(tree, '[data-diapo]').length === 3 && querySelector(tree, '[data-precedent]') && querySelector(tree, '[data-suivant]') && querySelector(tree, '[data-pause]'), `${route}: original three-slide hero and controls must be preserved`);
  for (const a of querySelectorAll(tree, 'a[href]')) {
    const url = new URL(decodeHTML(a.attributes.href), new URL(route, origin));
    if (url.origin !== origin) continue;
    if (url.hash && url.pathname === route) check(querySelector(tree, `[id="${url.hash.slice(1)}"]`), `${route}: anchor ${url.hash}`);
    url.hash = '';
    navigation.add(url.href);
    if (legacy && a.attributes['data-view-switch'] === undefined && !url.pathname.startsWith('/legacy/')) check(false, `${route}: navigation escapes Legacy: ${url.pathname}`);
  }
  for (const image of querySelectorAll(tree, 'img')) {
    check('alt' in image.attributes, `${route}: missing alt`);
    if (image.attributes.src) assets.add(new URL(decodeHTML(image.attributes.src), origin).href);
    for (const candidate of (image.attributes.srcset ?? '').split(',')) {
      const src = candidate.trim().split(/\s+/)[0];
      if (src) assets.add(new URL(decodeHTML(src), origin).href);
    }
  }
  const response = await fetch(new URL(route, origin));
  check(response.status === 200, `${route}: HTTP ${response.status}`);
  const live = parse(await response.text());
  check(querySelector(live, 'html')?.attributes['data-view'] === (legacy ? 'legacy' : 'modern'), `${route}: HTTP renderer differs`);
  return tree;
}
for (const { data, route } of routes) {
  const reference = parse(await readFile(join(before, 'dist', route, 'index.html'), 'utf8'));
  for (const target of [route, `/legacy${route}`]) {
    const tree = await document(target), main = querySelector(tree, 'main');
    for (const key of ['titre', 'surtitre', 'chapeau']) contains(main, data[key], target, key);
    for (const key of ['cartes', 'etapes', 'galerie']) for (const item of data[key] ?? []) for (const field of ['titre', 'texte', 'legende', 'lienLibelle']) contains(main, item[field], target, `${key}.${field}`);
    contentChecks++;
    // Page-specific compositions retain every rendered source fragment, in order.
    // Do not include UI labels, photo captions or frontmatter in the body check.
    const fragments = target.startsWith('/legacy/') ? [] : querySelectorAll(tree, '[data-editorial]');
    const body = fragments.length ? fragments.map(text).join(' ') : text(querySelector(tree, target.startsWith('/legacy/') ? '.prose' : '.bh-reading'));
    check(normalized(text(querySelector(reference, '.prose'))) === normalized(body), `${target}: Markdown body differs from before snapshot`);
    check(normalized(querySelector(tree, 'meta[name="description"]')?.attributes.content) === normalized(data.description), `${target}: description`);
    check(normalized(text(querySelector(tree, 'title'))) === normalized(text(querySelector(reference, 'title'))), `${target}: title changed`);
    for (const link of querySelectorAll(reference, 'link[rel="alternate"]')) check(querySelectorAll(tree, 'link[rel="alternate"]').some(current => current.attributes.hreflang === link.attributes.hreflang && current.attributes.href === link.attributes.href), `${target}: hreflang changed`);
  }
}
for (const lang of ['fr', 'en']) {
  const route = lang === 'en' ? '/en/' : '/';
  const home = load(await readFile(join(root, `src/textes/accueil.${lang}.yaml`), 'utf8'));
  for (const target of [route, `/legacy${route}`]) {
    const tree = await document(target), main = querySelector(tree, 'main');
    for (const [key, value] of Object.entries(home)) {
      if (Array.isArray(value)) for (const item of value) for (const field of ['titre', 'texte', 'auteur', 'chiffre', 'lienLibelle']) contains(main, item[field], target, `${key}.${field}`);
      else if (!['diapoPrecedente', 'diapoSuivante', 'diapoAller', 'raisonsLien', 'fondatriceLien', 'temoignagesLien'].includes(key)) contains(main, value, target, key);
    }
  }
}
const targetQueue = [...navigation, ...assets];
await Promise.all(Array.from({ length: 6 }, async () => {
  while (targetQueue.length) {
    const url = targetQueue.shift();
    try { const response = await fetch(url); check(response.status === 200, `Target HTTP ${response.status}: ${url}`); await response.arrayBuffer(); }
    catch (error) { check(false, `Target failure: ${url}: ${error.message}`); }
  }
}));
for (const path of ['/atelier/a/en/', '/atelier/b/en/']) {
  const response = await fetch(new URL(path, developmentOrigin), { redirect: 'manual' });
  check(response.status === 302 && response.headers.get('location') === '/en/', `${path}: old workshop must redirect to the single modern view`);
}
let productionExcluded = false;
try { await access(join(root, 'dist/atelier')); } catch { productionExcluded = true; }
check(productionExcluded, 'Workshop routes in production');
const sitemap = await readFile(join(root, 'dist/sitemap-0.xml'), 'utf8');
check(!sitemap.includes('/legacy/') && !sitemap.includes('/atelier/'), 'Noncanonical views in sitemap');
console.log(JSON.stringify({ evidence: 'Static and HTTP only; browser layout, keyboard, zoom and measured performance NOT tested', pages, contentChecks, sourceFiles, signatureFiles, navigationTargets: navigation.size, imageTargets: assets.size, productionExcluded, failures }, null, 2));
process.exitCode = failures.length ? 1 : 0;
