import { parse, renderSync, TEXT_NODE, type Node } from 'ultrahtml';
import { decodeHTML } from 'entities';

// Layout only: split Astro's already-rendered Markdown at existing h2 nodes.
// No second Markdown compiler, rewriting, translation or client-side DOM mutation.
export function editorialSections(html: string) {
  const document = parse(html);
  const sections: { heading: string; body: string; label: string }[] = [];
  let intro = '';
  const text = (node: Node): string => node.type === TEXT_NODE ? node.value : (node.children ?? []).map(text).join('');
  for (const node of document.children as Node[]) {
    if (node.name === 'h2') sections.push({ heading: renderSync(node), body: '', label: decodeHTML(text(node)) });
    else if (sections.length) sections[sections.length - 1].body += renderSync(node);
    else intro += renderSync(node);
  }
  return { intro, sections };
}

export function serviceChapters(sections: ReturnType<typeof editorialSections>['sections']) {
  // Both languages have the same three chapters. French also has an empty
  // introductory "Services" heading, which must remain verbatim.
  const starts = sections.flatMap((section, i) => section.body.trim() === '' ? [i] : []).slice(-3);
  if (starts.length !== 3) throw new Error('Services: expected three source chapter headings.');
  return {
    prefix: sections.slice(0, starts[0]),
    chapters: starts.map((start, i) => ({ title: sections[start], entries: sections.slice(start + 1, starts[i + 1] ?? sections.length) })),
  };
}
