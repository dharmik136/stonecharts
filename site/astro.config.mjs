import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://example.com',
  output: 'static',
  integrations: [
    sitemap({
      filter: (page) => !page.includes('/demo/'),
    }),
  ],
  build: {
    assets: '_assets',
  },
  vite: {
    build: {
      assetsInlineLimit: 0,
    },
  },
});
