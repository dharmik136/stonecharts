import type { APIRoute } from 'astro';

export const prerender = true;

export const GET: APIRoute = () => {
  const publicSiteUrl = import.meta.env.PUBLIC_SITE_URL?.trim();
  const body = publicSiteUrl
    ? `User-agent: *\nAllow: /\nDisallow: /demo/\nSitemap: ${new URL('/sitemap-index.xml', publicSiteUrl).href}\n`
    : 'User-agent: *\nDisallow: /\n';

  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
