// @ts-check
import { defineConfig } from 'astro/config';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import mdx from '@astrojs/mdx';
import react from '@astrojs/react';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const shikiTheme = JSON.parse(
  readFileSync(fileURLToPath(new URL('./src/lib/shiki-theme.json', import.meta.url)), 'utf-8')
);

export default defineConfig({
  // GitHub project page: served at https://<user>.github.io/Portfolio/.
  // When a custom domain is bought, switch `base` to '/' and `site` to it.
  site: 'https://mariocasanovacf.github.io',
  base: '/Portfolio',
  integrations: [
    mdx({
      remarkPlugins: [remarkMath],
      rehypePlugins: [rehypeKatex],
    }),
    react(),
  ],
  markdown: {
    shikiConfig: {
      theme: shikiTheme,
    },
  },
  vite: {
    resolve: {
      alias: {
        '~': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  },
});
