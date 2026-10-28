import { readdir, readFile, writeFile, stat } from 'node:fs/promises';
import { resolve, join, relative } from 'node:path';
import { createHash } from 'node:crypto';

// Generate a reviewed, incremental SFTP batch. This script never connects.
const [backupArg, outputArg] = process.argv.slice(2);
if (!backupArg || !outputArg) throw new Error('Pass the verified backup and a private output directory.');
const backup = resolve(backupArg), output = resolve(outputArg), root = resolve('dist');
if (output.startsWith(process.cwd() + '/')) throw new Error('Keep release manifests outside the public repository.');
await stat(join(backup, 'index.html')); await stat(join(backup, '.htaccess'));
async function files(dir) {
  return (await Promise.all((await readdir(dir,{withFileTypes:true})).filter(e=>!['legacy','nouveau','signature','.DS_Store'].includes(e.name)).map(e=>
    e.isDirectory()?files(join(dir,e.name)):[join(dir,e.name)]))).flat();
}
const hash = data => createHash('sha256').update(data).digest('hex');
const changes = [];
const builtFiles = await files(root);
const references = (await Promise.all(builtFiles.filter(f=>/\.(html|css|js)$/.test(f)).map(f=>readFile(f,'utf8')))).join('\n');
for (const file of builtFiles) {
  const path = relative(root, file);
  if (path.startsWith('_astro/') && !references.includes('/'+path)) continue;
  if (!/^(?:[\w.\/-]+)$/.test(path) || !/(?:\.html|\.css|\.js|\.xml|\.txt|\.md|\.webmanifest|\.woff2?|\.ttf|\.png|\.jpe?g|\.svg|\.webp|\.avif|\.ico|\.htaccess)$/.test(path)) throw new Error(`Unexpected build file: ${path}`);
  const data = await readFile(file), prior = await readFile(join(backup,path)).catch(()=>null);
  if (prior && hash(prior)===hash(data)) continue;
  changes.push({path,sha256:hash(data),before:prior?hash(prior):null,bytes:data.length});
}
// Assets first; HTML is replaced individually via rename; Apache rules last.
changes.sort((a,b)=>Number(a.path==='.htaccess')-Number(b.path==='.htaccess') || Number(a.path.endsWith('.html'))-Number(b.path.endsWith('.html')) || a.path.localeCompare(b.path));
const q = x => `"${x.replaceAll('"','\\"')}"`;
const batch=['cd banahealth_2'];
for (const {path} of changes) {
  const stage=path+'.maintenance-20261028';
  batch.push(`put ${q(join(root,path))} ${q(stage)}`,`chmod 644 ${q(stage)}`,`rename ${q(stage)} ${q(path)}`);
}
await writeFile(join(output,'upload-classic.sftp'),batch.join('\n')+'\n',{mode:0o600});
await writeFile(join(output,'release-manifest.json'),JSON.stringify({created:new Date().toISOString(),changes},null,2),{mode:0o600});
const rollback=['cd banahealth_2'];
for (const {path,before} of [...changes].reverse()) if(before) {
  const stage=path+'.restore-20261028';
  rollback.push(`put ${q(join(backup,path))} ${q(stage)}`,`chmod 644 ${q(stage)}`,`rename ${q(stage)} ${q(path)}`);
}
await writeFile(join(output,'rollback-classic.sftp'),rollback.join('\n')+'\n',{mode:0o600});
console.log(JSON.stringify({changed:changes.length,html:changes.filter(x=>x.path.endsWith('.html')).length,bytes:changes.reduce((sum,x)=>sum+x.bytes,0),paths:changes.map(x=>x.path),signatures:'excluded',preview:'excluded'}));
