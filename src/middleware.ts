import { defineMiddleware } from 'astro:middleware';
import { equivalences } from './i18n/ui';

const routes = new Set(['/', '/en/', ...Object.entries(equivalences).filter(([fr]) => fr).flatMap(([fr, en]) => [`/${fr}/`, `/en/${en}/`])]);
// Rewrites navigation only. Both renderers retain one shared editable corpus.
// Works in development as well as static generation; never rewrites metadata or assets.
export const onRequest = defineMiddleware(async (context, next) => {
  const response = await next();
  if (!context.url.pathname.startsWith('/legacy/') || !response.headers.get('content-type')?.includes('text/html')) return response;
  const html = await response.text();
  const body = html.replace(/<a\b[^>]*>[\s\S]*?<\/a>/g, anchor => {
    if (anchor.includes('data-view-switch')) return anchor;
    return anchor.replace(/href="(\/[^"#?]*)([^\"]*)"/, (match, path, suffix) => {
      const normalized = path.endsWith('/') ? path : `${path}/`;
      return routes.has(normalized) ? `href="/legacy${path}${suffix}"` : match;
    });
  });
  const headers = new Headers(response.headers);
  headers.delete('content-length');
  return new Response(body, { status: response.status, statusText: response.statusText, headers });
});
