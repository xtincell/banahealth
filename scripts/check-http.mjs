import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { get } from 'node:http';

// Local Apache: BANAHEALTH_HTTP_ORIGIN=http://127.0.0.1:8431 node scripts/check-http.mjs
// Production: node scripts/check-http.mjs
const origin = process.env.BANAHEALTH_HTTP_ORIGIN ?? 'https://banahealth.care';
const local = origin.startsWith('http://127.0.0.1:');
const request = (path, host = 'banahealth.care') => local ? new Promise((resolve, reject) => {
  // Native fetch normalizes Host: use node:http to exercise virtual-host rules.
  const req = get(origin + path, {headers: {host, 'x-forwarded-proto':'https'}}, res => {
    const chunks = []; res.on('data', chunk => chunks.push(chunk));
    res.on('end', () => resolve(new Response(Buffer.concat(chunks), {status: res.statusCode, headers: res.headers})));
  });
  req.setTimeout(20000, () => req.destroy(new Error('HTTP timeout'))); req.on('error', reject);
}) : fetch(origin + path, {
  headers: { 'User-Agent': 'Mozilla/5.0 BanaHealth-Verification' },
  redirect: 'manual', signal: AbortSignal.timeout(20000),
});
const redirects = [
  ['/?lang=en','/en/'], ['/index.php','/'], ['/index.php?lang=en','/en/'],
  ['/wordpress/index.php?lang=en','/en/'], ['/wordpress/?lang=en','/en/'],
  ['/en/?lang=fr','/'], ['/services/?lang=fr','/nos-services/'],
  ['/services/?lang=en','/en/our-services/'], ['/meet-the-founder/','/en/our-founder/'],
];
const htaccess = await readFile('public/.htaccess', 'utf8');
// Verify each generated language mapping against Apache, not only a regex lint.
for (const m of htaccess.matchAll(/RewriteRule \^([^?\s]+)\/\?\$ https:\/\/banahealth\.care(\S+) \[R=301,L,QSD\]/g)) {
  const path = m[1];
  if (/[()|*]/.test(path)) continue;
  const preceding = htaccess.slice(0, m.index).split('\n').at(-2) ?? '';
  const lang = preceding.match(/lang=(fr|en)/)?.[1];
  if (lang) redirects.push([`/${path}/?lang=${lang}`, m[2]]);
}
for (const [path, destination] of redirects) {
  const r = await request(path);
  assert.equal(r.status, 301, path);
  assert.equal(r.headers.get('location'), 'https://banahealth.care'+destination, path);
  await r.body?.cancel();
}
for (const path of ['/random/index.php','/random/index.PHP','/test.PHP','/wp-config.php','/.env','/backup.SQL']) {
  const r = await request(path); assert.equal(r.status,403,path); await r.body?.cancel();
}
assert.equal((await request('/missing-classic-check-20261028/')).status,404);
const home = await request('/'); assert.equal(home.status,200);
assert.ok(!(await home.text()).includes('data-design-discovery'));
const js = await request('/js/site.js?v=20261028');
assert.equal(js.status,200); assert.match(js.headers.get('cache-control'), /max-age=300/);
assert.ok(!js.headers.get('cache-control').includes('immutable'));
const font = await request('/fonts/mulish-v18-latin-normal.woff2');
assert.equal(font.status,200); assert.match(font.headers.get('cache-control'), /immutable/);
const www = local ? await request('/en/?keep=1','www.banahealth.care') : await fetch('https://www.banahealth.care/en/?keep=1',{headers:{'User-Agent':'Mozilla/5.0'},redirect:'manual'});
assert.equal(www.status,301); assert.equal(www.headers.get('location'),'https://banahealth.care/en/?keep=1');
const signature = local ? await request('/signature/banahealth-horizontal.png','www.banahealth.care') : await fetch('https://www.banahealth.care/signature/banahealth-horizontal.png',{headers:{'User-Agent':'Mozilla/5.0'},redirect:'manual'});
assert.equal(signature.status,200, 'Email logo must remain directly accessible on www');
console.log(JSON.stringify({origin, redirects: redirects.length, scriptsAndSecretsDenied: 6, notFound: true, cache: true, www: true}));
