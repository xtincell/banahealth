import assert from 'node:assert/strict';
import { readdir, readFile, stat } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { parse } from 'ultrahtml';
import { decodeHTML } from 'entities';

const root = resolve('dist');
const before = process.env.BANAHEALTH_BASELINE;
async function files(dir) {
  return (await Promise.all((await readdir(dir, { withFileTypes: true })).filter(e => !['legacy', 'nouveau'].includes(e.name)).map(e =>
    e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)]))).flat();
}
function nodes(node) { return [node, ...(node.children ?? []).flatMap(nodes)]; }
function editorial(node) {
  if (['style', 'script', 'noscript', 'button'].includes(node.name)) return '';
  return node.type === 2 ? node.value : (node.children ?? []).map(editorial).join('');
}
function mainText(tree) {
  return decodeHTML(editorial(nodes(tree).find(n => n.name === 'main'))).replace(/\s+/g, ' ').trim();
}
const pages = (await files(root)).filter(f => f.endsWith('.html'));
assert.equal(pages.length, 35, '34 content pages and 404');
let links = 0;
for (const file of pages) {
  const rel = file.slice(root.length + 1);
  const html = await readFile(file, 'utf8');
  const tree = parse(html);
  const all = nodes(tree);
  assert.match(html, /data-view="classic"/, rel);
  assert.equal(all.filter(n => n.name === 'h1').length, 1, `${rel}: one H1`);
  assert.ok(!html.includes('fonts.googleapis.com'), `${rel}: local fonts`);
  assert.ok(!html.includes('href="/nouveau/'), `${rel}: no redesign promotion`);
  assert.ok(!html.includes('href="/legacy/'), `${rel}: navigation stays on main site`);
  assert.equal(all.filter(n => n.name === 'link' && n.attributes.rel === 'canonical').length, 1, rel);
  if (before) {
    const previous = parse(await readFile(join(before, rel), 'utf8'));
    assert.equal(mainText(tree), mainText(previous), `${rel}: editorial text must be verbatim`);
  }
  for (const n of all) {
    const a = n.attributes ?? {};
    const refs = [a.href, a.src, ...(a.srcset?.split(',').map(x => x.trim().split(/\s/)[0]) ?? [])].filter(Boolean);
    for (const ref of refs) {
      if (!ref.startsWith('/') || ref.startsWith('//')) continue;
      const url = new URL(ref, 'https://banahealth.care');
      let path = join(root, decodeURIComponent(url.pathname));
      const info = await stat(path).catch(() => null);
      assert.ok(info, `${rel}: missing ${ref}`);
      if (info.isDirectory()) { path = join(path, 'index.html'); await stat(path); }
      links++;
    }
  }
}
let signatures = 0;
if (before) {
  for (const name of await readdir(join(root, 'signature'))) {
    const hash = async f => createHash('sha256').update(await readFile(f)).digest('hex');
    assert.equal(await hash(join(root, 'signature', name)), await hash(join(before, 'signature', name)), `Signature changed: ${name}`);
    signatures++;
  }
}
assert.ok(!(await readFile(join(root, 'sitemap-0.xml'), 'utf8')).includes('/legacy/'));
console.log(JSON.stringify({pages: pages.length, internalReferences: links, verbatimBaseline: Boolean(before), unchangedSignatures: signatures}));
