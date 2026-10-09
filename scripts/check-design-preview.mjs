import { readFile, readdir, stat } from 'node:fs/promises';
import { resolve, join, relative } from 'node:path';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { parse, TEXT_NODE } from 'ultrahtml';
import { querySelector, querySelectorAll } from 'ultrahtml/selector';
import { decodeHTML } from 'entities';

const [releaseArg, backupArg, origin = ''] = process.argv.slice(2);
if (!releaseArg || !backupArg) throw new Error('Pass release, complete backup and optionally an HTTP origin.');
const release = resolve(releaseArg), backup = resolve(backupArg);
const hash = b => createHash('sha256').update(b).digest('hex');
const text = n => !n ? '' : n.type === TEXT_NODE ? n.value : (n.children ?? []).map(text).join(' ');
const norm = v => decodeHTML(v).replace(/\s+/g, ' ').trim();
async function files(dir) { return (await Promise.all((await readdir(dir, { withFileTypes: true })).map(e => e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)]))).flat(); }
const manifest = JSON.parse(await readFile(join(release, 'release-manifest.json')));
let unchanged = 0, pages = 0;
const targets = new Set();
for (const f of await files(backup)) {
  const path = relative(backup, f), a = await readFile(f), b = await readFile(join(release, path));
  if (manifest.homepages.some(h => h.path === path)) {
    const stripped = b.toString().replace(/<aside data-design-discovery[^]*?<\/aside>/, '');
    if (hash(stripped) !== hash(a)) throw new Error(`Root mutation beyond discovery link: ${path}`);
  } else if (hash(a) !== hash(b)) throw new Error(`Changed primary file: ${path}`);
  unchanged++;
}
for (const f of await files(join(release, 'nouveau'))) {
  const path = relative(release, f);
  if (!f.endsWith('.html')) continue;
  const tree = parse(await readFile(f, 'utf8'));
  const original = parse(await readFile(join('dist', relative(join(release, 'nouveau'), f)), 'utf8'));
  if (norm(text(querySelector(tree, 'main'))) !== norm(text(querySelector(original, 'main')))) throw new Error(`Editorial mutation: ${path}`);
  if (querySelector(tree, 'meta[name="robots"]')?.attributes.content !== 'noindex, follow') throw new Error(`Indexable preview: ${path}`);
  if (querySelector(tree, 'link[rel="canonical"]')?.attributes.href.includes('/nouveau/')) throw new Error(`Preview canonical: ${path}`);
  const url = '/' + path.replace(/index\.html$/, '');
  targets.add(url);
  for (const n of querySelectorAll(tree, '[href], [src], [srcset]')) {
    if (n.name === 'link' && ['canonical', 'alternate'].includes(n.attributes.rel)) continue;
    const refs = [n.attributes.href, n.attributes.src, ...(n.attributes.srcset?.split(',').map(v => v.trim().split(/\s+/)[0]) ?? [])];
    for (const ref of refs.filter(r => r?.startsWith('/') && !r.startsWith('//'))) {
      const local = decodeURIComponent(ref.split(/[?#]/)[0]);
      const candidate = join(release, local.endsWith('/') ? local + 'index.html' : local);
      await stat(candidate).catch(() => { throw new Error(`Missing target: ${path} -> ${ref}`); });
      targets.add(local);
    }
  }
  pages++;
}
if (process.env.BANA_VERIFY_REMOTE_BACKUP === '1') {
  const { BANA_SFTP_PASSWORD_FILE: passwordFile, BANA_SFTP_TARGET: target, BANA_SFTP_WEBROOT: webroot } = process.env;
  if (!passwordFile || !target || !/^[\w/-]+$/.test(webroot ?? '')) throw new Error('Set the private SFTP password-file path, target and webroot through environment variables.');
  const dirs = new Set(['']);
  for (const f of await files(backup)) dirs.add(relative(backup, resolve(f, '..')));
  const commands = [...dirs].map(d => `ls -la "${webroot}/${d}"`).join('\n') + '\n';
  const r = spawnSync('sshpass', ['-f', passwordFile, 'sftp', '-o', 'BatchMode=no', '-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=3', '-b', '-', target], { input: commands, encoding: 'utf8', maxBuffer: 4e6 });
  if (r.status !== 0) throw new Error(`Remote inventory failed: ${r.stderr}`);
  let checked = 0, directory = '';
  for (const line of r.stdout.split('\n')) {
    const command = line.match(/^sftp> ls -la "([^]*)"$/);
    if (command) directory = command[1].slice(webroot.length + 1);
    if (!line.startsWith('-')) continue;
    const m = line.match(/^\S+\s+\d+\s+\S+\s+\S+\s+(\d+)\s+\S+\s+\S+\s+\S+\s+(.+)$/);
    if (!m) throw new Error('Unrecognized SFTP inventory line.');
    const p = m[2].startsWith(`${webroot}/`) ? m[2].slice(webroot.length + 1) : join(directory, m[2]);
    if ((await stat(join(backup, p))).size !== Number(m[1])) throw new Error(`Incomplete backup: ${p}`);
    checked++;
  }
  if (checked !== (await files(backup)).length) throw new Error(`Remote file count mismatch: ${checked}`);
  console.log(`Remote backup inventory: ${checked} files and sizes verified.`);
}
let http = 0;
if (origin) {
  for (const target of targets) {
    const response = await fetch(new URL(target, origin), { headers: { 'User-Agent': 'Mozilla/5.0 BanaHealth-publication-check' } });
    if (response.status !== 200 && !target.endsWith('404.html')) throw new Error(`HTTP ${response.status}: ${target}`);
    if (target.startsWith('/nouveau/') && (target.endsWith('/') || target.endsWith('.html'))) {
      const expected = await readFile(join(release, target.endsWith('/') ? target + 'index.html' : target));
      if (hash(Buffer.from(await response.arrayBuffer())) !== hash(expected)) throw new Error(`Unexpected live HTML: ${target}`);
    } else await response.arrayBuffer();
    http++;
  }
}
console.log(JSON.stringify({ pages, primaryFilesPreserved: unchanged, targets: targets.size, httpChecks: http, previewExcludedFromRootSitemap: !(await readFile(join(release, 'sitemap-0.xml'), 'utf8')).includes('/nouveau/'), evidence: 'Static / HTTP; no browser or measured performance claim' }, null, 2));
