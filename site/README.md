# StoneCharts preview site

This directory builds a static preview artifact; the repository does not currently
claim a production deployment. A build without `PUBLIC_SITE_URL` is intentionally
marked `noindex`, emits no canonical URL or sitemap, and disallows crawling in
`robots.txt`.

```bash
npm ci
npm run build
```

For an authorized deployment, set `PUBLIC_SITE_URL` to the final HTTPS origin before
building. Hosting credentials and provider configuration are deployment-owner
settings and are not stored in this repository.
