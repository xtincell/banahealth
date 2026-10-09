import { readFile, writeFile, readdir, mkdir, cp, access } from 'node:fs/promises';
import { join, resolve, relative } from 'node:path';
import { createHash } from 'node:crypto';
import { parse, renderSync, walkSync, TEXT_NODE } from 'ultrahtml';
import { querySelector, querySelectorAll } from 'ultrahtml/selector';
import { decodeHTML } from 'entities';
import { load } from 'js-yaml';

// Produces a separate release; never changes dist, the backup or production.
// Usage: node scripts/prepare-design-preview.mjs <empty-output> <verified-live-backup>
const [outputArg, liveArg] = process.argv.slice(2);
if (!outputArg || !liveArg) throw new Error('Pass an empty output directory and the complete live-site backup.');
const root = new URL('../', import.meta.url).pathname;
const output = resolve(outputArg), live = resolve(liveArg), mount = '/nouveau';
if (output === root || output.startsWith(live) || live.startsWith(output)) throw new Error('Unsafe output or overlapping backup.');
await mkdir(output, { recursive: true });
if ((await readdir(output)).length) throw new Error('Output directory must be empty.');
const labels = load(await readFile(join(root, 'src/textes/presentation.yaml'), 'utf8'));
const text = node => !node ? '' : node.type === TEXT_NODE ? node.value : (node.children ?? []).map(text).join(' ');
const norm = value => decodeHTML(value).replace(/\s+/g, ' ').trim();
const hash = data => createHash('sha256').update(data).digest('hex');
const safeExtensions = /(?:\.html|\.css|\.js|\.webmanifest|\.xml|\.txt|\.ttf|\.otf|\.woff2?|\.png|\.webp|\.jpe?g|\.ico|\.svg|\.avif|\/fonts\/LISEZ-MOI\.md|\/\.htaccess)$/i;
async function files(dir) {
  return (await Promise.all((await readdir(dir, { withFileTypes: true })).map(e => e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)]))).flat();
}
const backupFiles = await files(live);
for (const required of ['index.html', 'en/index.html', '.htaccess', 'signature/banahealth-horizontal.png']) await access(join(live, required));
// A full public-site copy makes the staged preview independently browser-testable.
for (const file of backupFiles) {
  if (!safeExtensions.test(file)) throw new Error(`Unexpected non-public backup file: ${relative(live, file)}`);
  const target = join(output, relative(live, file));
  await mkdir(resolve(target, '..'), { recursive: true });
  await cp(file, target);
}
const preview = join(output, 'nouveau');
await mkdir(preview);
const rooted = value => {
  if (!value?.startsWith('/') || value.startsWith('//') || value.startsWith('/signature/')) return value;
  return `${mount}${value}`;
};
const assets = value => value.replace(/url\((['"]?)(\/[^)'"\s]+)\1\)/g, (_, quote, path) => `url(${quote}${rooted(path)}${quote})`);
let pages = 0;
for (const file of await files(join(root, 'dist'))) {
  const path = relative(join(root, 'dist'), file);
  if (/^(legacy|signature)\//.test(path) || /^sitemap.*\.xml$/.test(path) || path === 'robots.txt' || path === '.htaccess') continue;
  if (!safeExtensions.test(file)) throw new Error(`Unexpected build file: ${path}`);
  const target = join(preview, path);
  await mkdir(resolve(target, '..'), { recursive: true });
  if (path.endsWith('.html')) {
    const html = await readFile(file, 'utf8'), tree = parse(html);
    const main = norm(text(querySelector(tree, 'main')));
    const lang = querySelector(tree, 'html').attributes.lang;
    walkSync(tree, node => {
      if (node.name === 'meta' && node.attributes.name === 'robots') node.attributes.content = 'noindex, follow';
      if (node.name === 'a' && 'data-view-switch' in node.attributes) {
        node.attributes.href = node.attributes.href.replace(/^\/legacy(?=\/)/, '');
        if (path === '404.html') node.attributes.href = '/';
        node.children = parse(labels[lang].retourSiteActuel).children;
      } else if (node.name === 'a' && node.attributes.href) node.attributes.href = rooted(node.attributes.href);
      if (node.attributes?.src) node.attributes.src = rooted(node.attributes.src);
      if (node.attributes?.srcset) node.attributes.srcset = node.attributes.srcset.split(',').map(c => c.trim().split(/\s+/).map((part, i) => i ? part : rooted(part)).join(' ')).join(', ');
      if (node.name === 'link' && !['canonical', 'alternate'].includes(node.attributes.rel)) node.attributes.href = rooted(node.attributes.href);
      if (node.attributes?.style) node.attributes.style = assets(node.attributes.style);
      if (node.name === 'style') for (const child of node.children ?? []) if (child.type === TEXT_NODE) child.value = assets(child.value);
    });
    if (norm(text(querySelector(tree, 'main'))) !== main) throw new Error(`Editorial mutation: ${path}`);
    for (const a of querySelectorAll(tree, 'a[href]')) {
      if (a.attributes.href.startsWith('/') && !a.attributes.href.startsWith(`${mount}/`) && !('data-view-switch' in a.attributes)) throw new Error(`Navigation escapes preview: ${path}: ${a.attributes.href}`);
    }
    await writeFile(target, renderSync(tree));
    pages++;
  } else if (path.endsWith('.css')) await writeFile(target, assets(await readFile(file, 'utf8')));
  else if (path.endsWith('.webmanifest')) {
    const manifest = JSON.parse(await readFile(file, 'utf8'));
    if (manifest.start_url) manifest.start_url = rooted(manifest.start_url);
    for (const icon of manifest.icons ?? []) icon.src = rooted(icon.src);
    await writeFile(target, JSON.stringify(manifest));
  } else await cp(file, target);
}
if (pages !== 35) throw new Error(`Expected 34 preview pages and 404, got ${pages}.`);
await writeFile(join(preview, '.htaccess'), `# Preview only; production root configuration is untouched.\nOptions -Indexes -ExecCGI\nDirectoryIndex index.html\nErrorDocument 404 /nouveau/404.html\n<IfModule mod_headers.c>\n  Header always set X-Robots-Tag "noindex, follow"\n  <FilesMatch "\\.html$">\n    Header always set Cache-Control "no-cache, must-revalidate"\n  </FilesMatch>\n</IfModule>\n`);
const homepages = [];
for (const [lang, path] of [['fr', 'index.html'], ['en', 'en/index.html']]) {
  const original = await readFile(join(live, path), 'utf8');
  if (!original.includes('</header>') || original.includes('data-design-discovery')) throw new Error(`Unexpected live entry: ${path}`);
  const banner = `<aside data-design-discovery style="display:flex;justify-content:center;padding:.65rem 1.25rem;background:#eef8f5;border-bottom:1px solid #cbd8d1"><a href="${mount}/${lang === 'en' ? 'en/' : ''}" style="display:inline-flex;align-items:center;min-height:2rem;color:#08685f;font-size:.9rem;text-underline-offset:.25em">${labels[lang].decouvrirDesign}</a></aside>`;
  const modified = original.replace('</header>', `</header>${banner}`);
  if (modified.replace(banner, '') !== original) throw new Error(`Primary site changed beyond link: ${path}`);
  await writeFile(join(output, path), modified);
  homepages.push({ path, before: hash(original), after: hash(modified) });
}
const previewFiles = await files(preview);
await writeFile(join(output, 'release-manifest.json'), JSON.stringify({ mount, pages, homepages, files: await Promise.all(previewFiles.map(async f => ({ path: relative(output, f), sha256: hash(await readFile(f)) }))) }, null, 2));
console.log(JSON.stringify({ output, mount, previewPages: pages, previewFiles: previewFiles.length, liveBackupFiles: backupFiles.length, primaryChanges: homepages.map(h => h.path), signatures: 'untouched; references remain at /signature/', deployment: 'not performed' }, null, 2));
