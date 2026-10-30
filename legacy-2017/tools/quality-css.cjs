const fs = require('node:fs');
const postcss = require('postcss');
const cssnano = require('cssnano');
const { PurgeCSS } = require('purgecss');

(async () => {
  const [input, output, contentRoot] = process.argv.slice(2);
  const root = postcss.parse(fs.readFileSync(input, 'utf8'));
  // Preserve the theme's icon sizes/colours, but draw actual inline SVG paths.
  root.walkRules(rule => {
    if (!rule.selector.includes('btIcoHolder:')) return;
    const selectors = rule.selectors.filter(s => /\.btIcoHolder::?after/.test(s));
    if (!selectors.length) return;
    const clone = rule.clone({selector:selectors.map(s => s.replace(/\.btIcoHolder::?after/g, '.btIcoHolder > .restored-svg')).join(',')});
    clone.walkDecls(/^(content|font-family)$/, d=>d.remove());
    rule.after(clone);
  });
  const result = await new PurgeCSS().purge({
    content:[`${contentRoot}/**/*.html`, `${contentRoot}/reconstruction.js`],
    css:[{raw:root.toString()}],
    safelist:{standard:[/^is-/, /^submenu-/, /^gallery-/, /^slider-/, 'reconstruction-js', 'open']},
    keyframes:true,
    fontFace:false,
  });
  const compact = await postcss([cssnano({preset:['default', {discardComments:{removeAll:true}}]})]).process(result[0].css,{from:undefined});
  fs.writeFileSync(output, compact.css);
})().catch(e=>{console.error(e.name+': '+e.message);process.exit(1)});
