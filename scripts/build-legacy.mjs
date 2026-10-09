import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
const root = new URL('../dist/', import.meta.url).pathname;
async function pages(dir) {
  return (await Promise.all((await readdir(dir, { withFileTypes: true })).map(e =>
    e.isDirectory() ? pages(join(dir, e.name)) : e.name.endsWith('.html') ? [join(dir, e.name)] : []
  ))).flat();
}
const files = await pages(join(root, 'legacy'));
for (const file of files) {
  const html = await readFile(file, 'utf8');
  if (!html.includes('data-view="legacy"') || !html.includes('noindex, follow')) throw new Error(`Invalid Legacy page: ${file}`);
  if (/rel="canonical" href="[^\"]*\/legacy\//.test(html)) throw new Error(`Legacy canonical points at itself: ${file}`);
}
if (files.length !== 34) throw new Error(`Expected 34 independent Legacy pages, got ${files.length}`);
console.log(`Legacy: ${files.length} independent pages verified; shared editable content.`);
