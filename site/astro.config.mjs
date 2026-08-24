import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const publicSiteUrl = process.env.PUBLIC_SITE_URL?.trim();

export default defineConfig({
  site: publicSiteUrl || undefined,
  output: 'static',
  integrations: publicSiteUrl
    ? [
        sitemap({
          filter: (page) => !page.includes('/demo/'),
        }),
      ]
    : [],
  build: {
    assets: '_assets',
  },
  vite: {
    build: {
      assetsInlineLimit: 0,
    },
  },
});
